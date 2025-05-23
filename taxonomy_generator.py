import os
import json
import asyncio # Import asyncio
from llm_interface import call_llm # Assuming llm_interface.py is in the same directory or PYTHONPATH

# --- Configuration ---
DEFAULT_PROVIDER = os.getenv("TAXONOMY_LLM_PROVIDER", "openai")
DEFAULT_MODEL = os.getenv("TAXONOMY_LLM_MODEL", "gpt-4-turbo")

OUTPUT_FILE = "raw_taxonomy_draft.jsonl"
# Cache usage is handled by llm_interface.call_llm

def generate_taxonomy_prompt():
    """
    Creates the prompt for the LLM to generate the taxonomy.
    (Prompt remains the same)
    """
    prompt = (
        "Generate a comprehensive taxonomy of human knowledge and capabilities. "
        "The taxonomy should be hierarchical, starting with broad fields, "
        "then breaking down into sub-fields, and finally into specific disciplines. "
        "The goal is to cover a wide range of academic and vocational areas. "
        "Please provide the output as a list of JSON objects, where each object represents a discipline "
        "and includes its hierarchical path (e.g., field, sub-field, discipline name). "
        "Each JSON object should have the following keys: 'field', 'sub_field', 'discipline_name'. "
        "If a discipline doesn't fall under a sub-field, the 'sub_field' can be null or omitted. "
        "Ensure a broad coverage, including but not limited to: "
        "Natural Sciences, Humanities, Social Sciences, Formal Sciences (Math, Logic), "
        "Applied Sciences (Engineering, Medicine), Arts, Business, Education, Law, "
        "Services (vocational training like culinary arts, mechanics, cosmetology), "
        "and emerging interdisciplinary areas. "
        "Example of a few JSON objects in the list: "
        "{\"field\": \"Natural Sciences\", \"sub_field\": \"Physics\", \"discipline_name\": \"Quantum Mechanics\"}, "
        "{\"field\": \"Humanities\", \"sub_field\": \"History\", \"discipline_name\": \"Ancient History\"}, "
        "{\"field\": \"Applied Sciences\", \"sub_field\": \"Engineering\", \"discipline_name\": \"Software Engineering\"}, "
        "{\"field\": \"Services\", \"sub_field\": null, \"discipline_name\": \"Culinary Arts\"} "
        "Please output a single JSON list containing all the discipline objects. "
        "The LLM response should be a string that is a valid JSON list of these objects."
    )
    return prompt

async def main(): # Changed to async def
    print(f"Starting asynchronous taxonomy generation using {DEFAULT_PROVIDER} and model {DEFAULT_MODEL}...")
    
    prompt = generate_taxonomy_prompt()
    
    llm_response_str = await call_llm( # Changed to await
        prompt_text=prompt,
        provider=DEFAULT_PROVIDER,
        model_name=DEFAULT_MODEL
        # Add any specific kwargs for the call if needed, e.g. temperature
    )

    if not llm_response_str:
        print("Failed to get a response from LLM via async llm_interface. Exiting.")
        return

    print(f"Received LLM response string (first 200 chars): {llm_response_str[:200]}...")

    try:
        disciplines_list = json.loads(llm_response_str)
        if not isinstance(disciplines_list, list):
            if isinstance(disciplines_list, dict):
                if "disciplines" in disciplines_list and isinstance(disciplines_list["disciplines"], list):
                    disciplines_list = disciplines_list["disciplines"]
                elif "response" in disciplines_list and isinstance(disciplines_list["response"], list):
                    disciplines_list = disciplines_list["response"]
                else:
                    raise ValueError("LLM response was a JSON dict, but does not contain a 'disciplines' or 'response' list.")
            else:
                raise ValueError("LLM response was not a JSON list or a recognized JSON object containing a list.")

        # File writing is synchronous here. For this particular script, writing a single
        # file at the end is generally fine. If this were part of a larger async workflow
        # with many file operations, using asyncio.to_thread for file I/O would be
        # more appropriate to prevent blocking the event loop.
        with open(OUTPUT_FILE, 'w') as f:
            for discipline_entry in disciplines_list:
                if not isinstance(discipline_entry, dict):
                    print(f"Warning: Skipping entry not in dict format: {discipline_entry}")
                    continue
                if not ('field' in discipline_entry and 'discipline_name' in discipline_entry):
                    print(f"Warning: Skipping entry missing required keys ('field', 'discipline_name'): {discipline_entry}")
                    continue
                json.dump(discipline_entry, f)
                f.write('\n')
        print(f"Successfully wrote {len(disciplines_list)} disciplines to {OUTPUT_FILE}")

    except json.JSONDecodeError as e:
        print(f"Error decoding LLM JSON response: {e}")
        print(f"Raw response (first 500 chars): {llm_response_str[:500]}")
    except ValueError as e:
        print(f"Error processing LLM response: {e}")

if __name__ == "__main__":
    print("--- Async Taxonomy Generation Script ---")
    print("This script generates a raw draft of the taxonomy using an LLM via the async llm_interface.py.")
    print("Ensure your LLM provider API keys and any other necessary env vars are set.")
    print(f"Default provider for this script: {DEFAULT_PROVIDER}, Model: {DEFAULT_MODEL}")
    print(f"Output will be saved to {OUTPUT_FILE}.")
    print("Caching is handled by llm_interface.py.")
    print("-----------------------------------------------------\n")
    # Run the async main function
    asyncio.run(main())
```
