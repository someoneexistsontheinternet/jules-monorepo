import asyncio
import os
import json
import shutil # For cleaning up cache if needed
from llm_interface import get_prompt_hash, call_llm, CACHE_DIR, AsyncOpenAI # Import AsyncOpenAI directly for mocking

# --- Mocking Setup (if not using real API keys for testing) ---
# This allows testing the caching logic without actual LLM calls.

# Store the original AsyncOpenAI client if it exists
ORIGINAL_ASYNC_OPENAI_CLIENT = AsyncOpenAI

class MockAsyncChoice:
    def __init__(self, text):
        self.message = MockAsyncMessage(text)
class MockAsyncMessage:
    def __init__(self, text):
        self.content = text
class MockAsyncCompletion:
    def __init__(self, text):
        self.choices = [MockAsyncChoice(text)]

class MockedAsyncOpenAI:
    _is_mock = True
    # Keep track of whether the create method was called
    create_called_count = 0

    def __init__(self, api_key):
        print("MockedAsyncOpenAI client initialized.")
        MockedAsyncOpenAI.create_called_count = 0 # Reset on init for clean tests

    class Chat:
        class Completions:
            async def create(self, model, messages, **kwargs):
                MockedAsyncOpenAI.create_called_count += 1
                print(f"MockedAsyncOpenAI.create CALLED ({MockedAsyncOpenAI.create_called_count} times this instance). Model: {model}...")
                await asyncio.sleep(0.01) # Simulate tiny delay
                return MockAsyncCompletion(f"Mocked response for: {messages[0]['content'][:30]}")
        completions = Completions()
    chat = Chat()

def setup_mock_openai():
    """Sets up the mock OpenAI client."""
    # Access llm_interface's global scope for AsyncOpenAI if needed, or modify directly if imported.
    # For this script, we've imported AsyncOpenAI from llm_interface, so we can patch it here.
    if ORIGINAL_ASYNC_OPENAI_CLIENT is None:
        print("Mocking cannot proceed: Original AsyncOpenAI client from llm_interface is None (not installed?).")
        return False
    
    # Dynamically get the llm_interface module if needed, or rely on direct import
    # import llm_interface
    # llm_interface.AsyncOpenAI = MockedAsyncOpenAI
    # For this setup, since we imported `from llm_interface import AsyncOpenAI`,
    # we need to be careful. Re-assigning AsyncOpenAI in *this* script's global scope
    # might not patch it inside `llm_interface` if `llm_interface` itself uses `from openai import AsyncOpenAI`.
    # The most robust way is to patch it where it's looked up by `call_llm`.
    # Assuming `call_llm` uses the `AsyncOpenAI` that is in its own module's scope.
    # A common pattern for testing is to allow the dependency to be injected or to patch it globally.
    # For simplicity here, we'll assume the llm_interface.py will pick up this global mock
    # if we modify what `AsyncOpenAI` points to *before* `call_llm` is first executed in a test context.
    # This is a bit tricky with Python's import system.
    # A cleaner way: have call_llm accept a client factory or instance.
    # Given the current structure of llm_interface.py, we will try to patch it in its module.
    import llm_interface
    llm_interface.AsyncOpenAI = MockedAsyncOpenAI
    print("Patched llm_interface.AsyncOpenAI with MockedAsyncOpenAI.")
    return True


def restore_openai_if_mocked():
    """Restores the original OpenAI client."""
    if ORIGINAL_ASYNC_OPENAI_CLIENT is not None:
        import llm_interface
        llm_interface.AsyncOpenAI = ORIGINAL_ASYNC_OPENAI_CLIENT
        print("Restored original AsyncOpenAI client in llm_interface.")


async def test_get_prompt_hash_function():
    print("\n--- Testing get_prompt_hash Function ---")
    hash1 = get_prompt_hash("Hello", "model1", "prov1", temp=0.5)
    hash2 = get_prompt_hash("Hello", "model1", "prov1", temp=0.5)
    hash3 = get_prompt_hash("Goodbye", "model1", "prov1", temp=0.5)
    hash4 = get_prompt_hash("Hello", "model2", "prov1", temp=0.5)
    hash5 = get_prompt_hash("Hello", "model1", "prov2", temp=0.5)
    hash6 = get_prompt_hash("Hello", "model1", "prov1", temp=0.6)
    hash7 = get_prompt_hash("Hello", "model1", "prov1", temp=0.5, extra_arg="val1")
    hash8 = get_prompt_hash("Hello", "model1", "prov1", temp=0.5, extra_arg="val2")


    assert hash1 == hash2, "Test Case 1 Failed: Same inputs should produce same hash."
    print("Test Case 1 Passed: Same inputs, same hash.")

    assert hash1 != hash3, "Test Case 2 Failed: Different prompt, different hash."
    print("Test Case 2 Passed: Different prompt, different hash.")

    assert hash1 != hash4, "Test Case 3 Failed: Different model, different hash."
    print("Test Case 3 Passed: Different model, different hash.")

    assert hash1 != hash5, "Test Case 4 Failed: Different provider, different hash."
    print("Test Case 4 Passed: Different provider, different hash.")
    
    assert hash1 != hash6, "Test Case 5 Failed: Different kwarg value (temp), different hash."
    print("Test Case 5 Passed: Different kwarg value (temp), different hash.")

    assert hash1 != hash7, "Test Case 6 Failed: Different kwarg key/val, different hash."
    print("Test Case 6 Passed: Different kwarg key/val, different hash.")
    
    assert hash7 != hash8, "Test Case 7 Failed: Different value for same extra_arg, different hash."
    print("Test Case 7 Passed: Different value for same extra_arg, different hash.")
    
    print("--- get_prompt_hash tests completed successfully! ---")

async def test_call_llm_caching():
    print("\n--- Testing call_llm Caching (with mocked OpenAI) ---")
    
    os.environ["OPENAI_API_KEY"] = "sk-placeholderkey-for-mock" # Ensure some key is present
    
    if not setup_mock_openai():
        print("Skipping caching test as mocking could not be set up.")
        return

    test_provider = "openai"
    test_model = "gpt-3.5-turbo-mockcache" 
    test_prompt = "This is a caching test prompt. What time is it?"
    test_kwargs = {"temperature": 0.1, "max_tokens": 5}

    # Clean slate for this specific test
    prompt_hash_for_test1 = get_prompt_hash(test_prompt, test_model, test_provider, **test_kwargs)
    cache_file_to_clear1 = os.path.join(CACHE_DIR, f"{prompt_hash_for_test1}.json")
    if os.path.exists(cache_file_to_clear1):
        os.remove(cache_file_to_clear1)
        print(f"Cleared pre-existing cache file: {cache_file_to_clear1}")

    # 1. First call: Cache miss, should call (mocked) LLM
    print("\n1. First call (cache miss):")
    MockedAsyncOpenAI.create_called_count = 0 # Reset mock counter
    response1 = await call_llm(test_prompt, test_provider, test_model, use_cache=True, **test_kwargs)
    assert response1 is not None, "Test Case 8 Failed: Response1 should not be None."
    assert "Mocked response for: This is a caching test prompt." in response1, "Test Case 8 Failed: Response1 has unexpected content."
    assert MockedAsyncOpenAI.create_called_count == 1, "Test Case 8 Failed: Mocked LLM create() should have been called once."
    print(f"Response 1: {response1}")
    assert os.path.exists(cache_file_to_clear1), "Test Case 8 Failed: Cache file not created after first call."
    print("Test Case 8 Passed: First call successful, cache file created, LLM mock called once.")

    # 2. Second call: Cache hit, should NOT call (mocked) LLM
    print("\n2. Second call (cache hit):")
    MockedAsyncOpenAI.create_called_count = 0 # Reset mock counter
    response2 = await call_llm(test_prompt, test_provider, test_model, use_cache=True, **test_kwargs)
    assert response2 == response1, "Test Case 9 Failed: Response2 (cache hit) should be same as Response1."
    assert MockedAsyncOpenAI.create_called_count == 0, "Test Case 9 Failed: Mocked LLM create() should NOT have been called for a cache hit."
    print(f"Response 2: {response2}")
    print("Test Case 9 Passed: Second call successful (cache hit), LLM mock not called.")

    # 3. Third call: Different prompt, cache miss
    print("\n3. Third call (different prompt, cache miss):")
    test_prompt_3 = "This is a different caching test prompt."
    prompt_hash_for_test3 = get_prompt_hash(test_prompt_3, test_model, test_provider, **test_kwargs)
    cache_file_to_clear3 = os.path.join(CACHE_DIR, f"{prompt_hash_for_test3}.json")
    if os.path.exists(cache_file_to_clear3):
        os.remove(cache_file_to_clear3)

    MockedAsyncOpenAI.create_called_count = 0 # Reset
    response3 = await call_llm(test_prompt_3, test_provider, test_model, use_cache=True, **test_kwargs)
    assert response3 is not None, "Test Case 10 Failed: Response3 should not be None."
    assert response3 != response1, "Test Case 10 Failed: Response3 should be different from Response1."
    assert "Mocked response for: This is a different caching te" in response3, "Test Case 10 Failed: Response3 has unexpected content."
    assert MockedAsyncOpenAI.create_called_count == 1, "Test Case 10 Failed: Mocked LLM create() should have been called once for new prompt."
    print(f"Response 3: {response3}")
    print("Test Case 10 Passed: Third call (different prompt) successful (cache miss), LLM mock called once.")

    # 4. Fourth call: Same as first, but use_cache=False
    print("\n4. Fourth call (same as first, use_cache=False, should be a 'cache miss' effectively):")
    MockedAsyncOpenAI.create_called_count = 0 # Reset
    response4 = await call_llm(test_prompt, test_provider, test_model, use_cache=False, **test_kwargs)
    assert response4 is not None, "Test Case 11 Failed: Response4 should not be None."
    assert "Mocked response for: This is a caching test prompt." in response4, "Test Case 11 Failed: Response4 has unexpected content."
    assert MockedAsyncOpenAI.create_called_count == 1, "Test Case 11 Failed: Mocked LLM create() should have been called once as use_cache=False."
    print(f"Response 4: {response4}")
    print("Test Case 11 Passed: Fourth call (use_cache=False) successful, LLM mock called once.")

    restore_openai_if_mocked()
    
    # Clean up test cache files created by this test function
    if os.path.exists(cache_file_to_clear1): os.remove(cache_file_to_clear1)
    if os.path.exists(cache_file_to_clear3): os.remove(cache_file_to_clear3)
    print("Cleaned up specific cache files created during this test.")

    print("--- call_llm caching tests completed successfully! ---")


async def main():
    # It's important that mocking is set up correctly for the caching test.
    # The `llm_interface.py` should ideally use the `AsyncOpenAI` symbol that can be patched.
    
    # Ensure the main CACHE_DIR exists for the tests
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        print(f"Created main cache directory: {CACHE_DIR}")

    await test_get_prompt_hash_function()
    await test_call_llm_caching()


if __name__ == "__main__":
    print("--- Running Hashing and Caching Tests for llm_interface.py ---")
    # This script assumes llm_interface.py is in the same directory or PYTHONPATH.
    # Patching is done by directly modifying the llm_interface module's AsyncOpenAI attribute.
    asyncio.run(main())
```
