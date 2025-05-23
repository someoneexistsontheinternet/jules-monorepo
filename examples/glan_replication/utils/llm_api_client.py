import openai
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
# This should be in the root of your project or where the main script is run from,
# or ensure utils/.env is loaded if scripts in utils/ are run directly.
# For scripts in sibling directories calling this, .env in the project root is typical.
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env') # Assuming .env is in glan_replication
if not os.path.exists(dotenv_path):
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env') # Check for .env in utils/ as fallback for direct testing
load_dotenv(dotenv_path=dotenv_path, override=True)


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

DEFAULT_MODEL = "gpt-3.5-turbo"
DEFAULT_MAX_WORKERS = 5

class LLMAPIClient:
    def __init__(self, api_key=None, max_retries=3, initial_backoff=1.0, max_backoff=16.0):
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            # Allow initialization without key if it might be set later,
            # but calls will fail until it's set. Or raise error immediately.
            print("Warning: LLMAPIClient initialized without an API key. Calls will fail unless key is provided later or OPENAI_API_KEY is set.")
            self.client = None
        else:
            self.client = openai.OpenAI(api_key=self.api_key)
        
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff

    def _ensure_client_initialized(self):
        if not self.client:
            if not self.api_key: # Try re-fetching from env if it was missing at init
                 self.api_key = os.environ.get("OPENAI_API_KEY")
            if self.api_key:
                self.client = openai.OpenAI(api_key=self.api_key)
            else:
                raise ValueError("OpenAI API key is not configured. Cannot make API call.")
        return True


    def _make_request_with_retry(self, model_name, messages, temperature, max_tokens, top_p):
        self._ensure_client_initialized()
        current_retries = 0
        backoff_seconds = self.initial_backoff
        
        while current_retries < self.max_retries:
            try:
                chat_completion = self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p
                )
                return chat_completion.choices[0].message.content
            except openai.RateLimitError as e:
                error_message = f"Rate limit error: {e}."
                current_retries += 1
            except openai.APIConnectionError as e: # Handles connection errors
                error_message = f"API connection error: {e}."
                current_retries += 1
            except openai.APIStatusError as e: # Handles other API errors (e.g. 500, 503)
                error_message = f"OpenAI API status error {e.status_code}: {e.response}."
                current_retries += 1
            except Exception as e: # Catch other potential errors like malformed requests etc.
                error_message = f"An unexpected error occurred: {e}."
                # For unexpected errors, might not be worth retrying in the same way.
                # Depending on the error, could break or retry once.
                # For this implementation, we'll retry all caught exceptions.
                current_retries += 1

            if current_retries >= self.max_retries:
                print(f"{error_message} Failed to get response after {self.max_retries} retries.")
                break
            
            print(f"{error_message} Retrying in {backoff_seconds:.2f}s... (Attempt {current_retries}/{self.max_retries})")
            time.sleep(backoff_seconds + random.uniform(0, 0.1 * backoff_seconds)) # Add jitter
            backoff_seconds = min(self.max_backoff, backoff_seconds * 2)
        
        return None # Or raise an exception like openai.APIError("Failed after max retries")

    def generate_text(self, prompt_or_messages, model_name=DEFAULT_MODEL, temperature=0.7, max_tokens=1024, top_p=1.0, system_message=None):
        if isinstance(prompt_or_messages, str):
            messages = [{"role": "user", "content": prompt_or_messages}]
            if system_message:
                messages.insert(0, {"role": "system", "content": system_message})
        elif isinstance(prompt_or_messages, list):
            messages = prompt_or_messages
            if system_message and (not messages or messages[0]['role'] != 'system'):
                 messages.insert(0, {"role": "system", "content": system_message})
        else:
            raise ValueError("prompt_or_messages must be a string or a list of message objects.")

        return self._make_request_with_retry(model_name, messages, temperature, max_tokens, top_p)

    def generate_batch(self, batch_prompts_or_messages, max_workers=DEFAULT_MAX_WORKERS, **kwargs):
        self._ensure_client_initialized()
        results = [None] * len(batch_prompts_or_messages)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(self.generate_text, item, **kwargs): i 
                for i, item in enumerate(batch_prompts_or_messages)
            }
            
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    print(f"Error processing batch item {index} in future: {e}")
                    results[index] = None 
        return results

if __name__ == '__main__':
    print("Testing LLMAPIClient...")
    
    # Ensure .env is in examples/glan_replication/ for this test, or key is globally set
    # For local testing, one might place a .env file in the utils directory temporarily.
    # The load_dotenv path is now relative to this file, trying ../.env first.
    
    if not OPENAI_API_KEY or "your_actual_openai_key_here" in OPENAI_API_KEY: # Second part is a placeholder check
        print("Skipping live API call test as OPENAI_API_KEY is not properly set or is a placeholder.")
        print("Please create 'examples/glan_replication/.env' with your OPENAI_API_KEY or set it as an environment variable.")
    else:
        client = LLMAPIClient()
        
        print("\n--- Test Single Generation ---")
        single_prompt = "What is the color of the sky on a clear day?"
        try:
            response = client.generate_text(single_prompt, model_name="gpt-3.5-turbo", temperature=0.5, max_tokens=50)
            print(f"Prompt: {single_prompt}")
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error during single generation test: {e}")

        print("\n--- Test Batch Generation ---")
        batch_prompts_for_api = [
             "What is the capital of Canada?",
             "Write a two-sentence horror story.",
             [{"role": "system", "content": "You are a poetic assistant."}, {"role": "user", "content": "Describe a sunset."}]
        ]
        try:
            batch_responses = client.generate_batch(batch_prompts_for_api, max_workers=2, model_name="gpt-3.5-turbo", max_tokens=60)
            for i, (prompt, resp) in enumerate(zip(batch_prompts_for_api, batch_responses)):
                print(f"Batch Prompt {i+1}: {prompt}")
                print(f"Batch Response {i+1}: {resp}")
        except Exception as e:
            print(f"Error during batch generation test: {e}")
            
    print("\nLLMAPIClient test script finished.")
