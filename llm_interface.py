import os
import json
import hashlib
import asyncio # Added for asyncio operations

# --- LLM Provider SDKs ---
try:
    from openai import AsyncOpenAI # Changed to AsyncOpenAI
except ImportError:
    AsyncOpenAI = None # type: ignore

try:
    from anthropic import AsyncAnthropic # Changed to AsyncAnthropic
except ImportError:
    AsyncAnthropic = None # type: ignore

try:
    from google.cloud import aiplatform # aiplatform itself is not fully async in the same way
    # For Vertex AI, especially with older models or certain client libraries,
    # true async operations might require running sync calls in a thread.
    # Gemini SDK has some async capabilities.
    from vertexai.generative_models import GenerativeModel # Gemini has async methods
except ImportError:
    aiplatform = None # type: ignore
    GenerativeModel = None # type: ignore

# --- Configuration ---
CACHE_DIR = "cache/llm_responses"
os.makedirs(CACHE_DIR, exist_ok=True)

# --- Utility Functions ---
def get_prompt_hash(prompt_text, model_name, provider, **kwargs):
    """Creates a SHA256 hash of the prompt and relevant parameters for caching."""
    hasher = hashlib.sha256()
    data_to_hash = {
        "prompt": prompt_text,
        "model": model_name,
        "provider": provider,
        "kwargs": sorted(kwargs.items())
    }
    hasher.update(json.dumps(data_to_hash, sort_keys=True).encode('utf-8'))
    return hasher.hexdigest()

# --- Asynchronous File I/O Wrappers ---
async def read_cache_file(file_path):
    def _read():
        with open(file_path, 'r') as f:
            return json.load(f)
    return await asyncio.to_thread(_read)

async def write_cache_file(file_path, data):
    def _write():
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    await asyncio.to_thread(_write)

# --- Provider-Specific Async Functions ---
async def _call_openai_async(client: AsyncOpenAI, model_name: str, prompt_text: str, **kwargs):
    """Sends a request to the OpenAI API asynchronously."""
    if not AsyncOpenAI or not client:
        raise RuntimeError("AsyncOpenAI SDK not installed or client not initialized.")
    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt_text}],
            **kwargs
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API async call failed: {e}")
        raise

async def _call_anthropic_async(client: AsyncAnthropic, model_name: str, prompt_text: str, **kwargs):
    """Sends a request to the Anthropic API asynchronously."""
    if not AsyncAnthropic or not client:
        raise RuntimeError("AsyncAnthropic SDK not installed or client not initialized.")
    try:
        response = await client.messages.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt_text}],
            **kwargs
        )
        if response.content and isinstance(response.content, list) and hasattr(response.content[0], 'text'):
            return response.content[0].text
        # Fallback for older models or different response structures
        return response.completion if hasattr(response, 'completion') else str(response)
    except Exception as e:
        print(f"Anthropic API async call failed: {e}")
        raise

async def _call_vertexai_async(project_id: str, location: str, model_name: str, prompt_text: str, **kwargs):
    """Sends a request to Google Vertex AI asynchronously (Gemini example)."""
    if not GenerativeModel: # Check if Gemini SDK is available
        raise RuntimeError("Vertex AI GenerativeModel SDK not available.")

    # aiplatform.init needs to be called, but it's synchronous.
    # It's usually called once at the application start.
    # If called per request, it might need to be run in a thread for async context,
    # but typically this setup is done once.
    # For this function, we assume aiplatform.init has been handled appropriately.
    
    try:
        model = GenerativeModel(model_name)
        # generate_content_async is available for Gemini models
        response = await model.generate_content_async(
            [prompt_text], # Simplified for single text prompt
            generation_config=kwargs # Pass temperature, max_output_tokens etc. here
        )
        if response.candidates:
            return response.candidates[0].content.parts[0].text
        return str(response) # Fallback
    except Exception as e:
        print(f"Vertex AI API async call failed: {e}")
        # It might be useful to run aiplatform.init here if it's context-specific
        # and hasn't been run, but this adds complexity.
        # For now, assume init is handled outside or is safe to call if needed.
        # If aiplatform.init needs to be called and is blocking:
        # await asyncio.to_thread(aiplatform.init, project=project_id, location=location)
        # Then proceed with the model call.
        raise

# --- Main Async Interface Function ---
async def call_llm(prompt_text: str,
                   provider: str,
                   model_name: str,
                   use_cache: bool = True,
                   **kwargs):
    """
    Main async function to call an LLM from a specified provider.
    Handles API key retrieval, client initialization, and provider-specific async calls.
    Implements caching based on prompt hash using async file I/O.
    """
    prompt_hash = get_prompt_hash(prompt_text, model_name, provider, **kwargs)
    cache_file_path = os.path.join(CACHE_DIR, f"{prompt_hash}.json")

    if use_cache and os.path.exists(cache_file_path): # os.path.exists is sync, but fast
        try:
            cached_data = await read_cache_file(cache_file_path)
            # print(f"Cache hit for prompt hash {prompt_hash}.")
            return cached_data.get("response")
        except Exception as e:
            print(f"Error reading from cache file {cache_file_path}: {e}. Proceeding with API call.")

    # print(f"Cache miss for prompt hash {prompt_hash}. Calling API.")
    response_text = None
    try:
        if provider.lower() == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key: raise ValueError("OPENAI_API_KEY not set.")
            if not AsyncOpenAI: raise RuntimeError("AsyncOpenAI SDK not found. pip install openai[async]")
            async_client = AsyncOpenAI(api_key=api_key)
            response_text = await _call_openai_async(async_client, model_name, prompt_text, **kwargs)
        
        elif provider.lower() == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key: raise ValueError("ANTHROPIC_API_KEY not set.")
            if not AsyncAnthropic: raise RuntimeError("AsyncAnthropic SDK not found. pip install anthropic[async]")
            async_client = AsyncAnthropic(api_key=api_key)
            response_text = await _call_anthropic_async(async_client, model_name, prompt_text, **kwargs)

        elif provider.lower() == "vertexai":
            gcp_project = os.getenv("GCP_PROJECT")
            gcp_location = os.getenv("GCP_LOCATION")
            # GOOGLE_APPLICATION_CREDENTIALS should be set for ADC
            if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                 print("Warning: GOOGLE_APPLICATION_CREDENTIALS not set for Vertex AI.")
            if not gcp_project or not gcp_location:
                raise ValueError("GCP_PROJECT and GCP_LOCATION must be set for Vertex AI.")
            
            # aiplatform.init() is synchronous. If it must be called per-use,
            # it should be run in a thread for a truly async setup,
            # or ideally called once when the application starts.
            # For simplicity, we're not explicitly calling it here assuming it's pre-configured
            # or ADC works. If issues arise, this is a point for review.
            # Example: await asyncio.to_thread(aiplatform.init, project=gcp_project, location=gcp_location)
            
            response_text = await _call_vertexai_async(gcp_project, gcp_location, model_name, prompt_text, **kwargs)
            
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}.")

        if response_text is not None and use_cache:
            await write_cache_file(cache_file_path, {"prompt": prompt_text, "response": response_text})
            # print(f"Response saved to cache: {cache_file_path}")
        
        return response_text

    except ValueError as ve:
        print(f"Configuration Error in call_llm: {ve}")
        return None
    except RuntimeError as rte:
        print(f"Runtime Error in call_llm: {rte}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred in async call_llm for {provider}: {e}")
        return None

async def test_async_llm_calls():
    print("--- Testing Async LLM Interface ---")

    # Test OpenAI Async
    print("\n--- Testing OpenAI Async ---")
    # os.environ["OPENAI_API_KEY"] = "YOUR_KEY_HERE" # Ensure this is set for a real test
    if os.getenv("OPENAI_API_KEY") and AsyncOpenAI:
        try:
            # Simple mock for testing if no real key is provided for workflow
            if os.getenv("OPENAI_API_KEY") == "YOUR_KEY_HERE" or os.getenv("OPENAI_API_KEY") == "sk-placeholderkey":
                 print("Using MOCK OpenAI client for async test as placeholder key detected.")
                 AsyncOpenAI_orig = AsyncOpenAI # type: ignore
                 class MockAsyncOpenAI: # type: ignore
                    def __init__(self, api_key): pass
                    class Chat:
                        class Completions:
                            async def create(self, model, messages, **kwargs):
                                await asyncio.sleep(0.1) # Simulate network latency
                                return type('obj', (object,), {'choices': [type('obj', (object,), {'message': type('obj', (object,),{'content': 'Mocked OpenAI Async Response'})})]})()
                        completions = Completions()
                    chat = Chat()
                 globals()['AsyncOpenAI'] = MockAsyncOpenAI # Monkey patch

            openai_response = await call_llm("Test prompt for OpenAI async", "openai", "gpt-3.5-turbo", temperature=0.1, max_tokens=5)
            print(f"OpenAI Async Response: {openai_response}")
            
            if 'MockAsyncOpenAI' in str(AsyncOpenAI): # Restore if monkey patched
                globals()['AsyncOpenAI'] = AsyncOpenAI_orig # type: ignore

        except Exception as e:
            print(f"OpenAI async test failed: {e}")
    else:
        print("OpenAI async not tested (API key or AsyncOpenAI SDK missing).")

    # Similar test blocks for Anthropic and VertexAI can be added here
    # For brevity, they are omitted but would follow the same pattern:
    # - Check for API key and SDK
    # - Optionally mock if placeholder key
    # - Make the call_llm
    # - Print response
    # - Restore if monkey patched

    print("\n--- Async Interface Test Complete ---")


if __name__ == '__main__':
    # To run the test, you would do:
    # asyncio.run(test_async_llm_calls())
    # But for now, just print info
    print("--- Async LLM Interface Module ---")
    print("This module provides an ASYNCHRONOUS interface to call different LLM providers.")
    print("Setup required (environment variables): See comments within the script.")
    print("To test, call `asyncio.run(test_async_llm_calls())` from an async context.")
```
