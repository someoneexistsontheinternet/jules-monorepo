import os
import json
import asyncio # Import asyncio
from llm_interface import call_llm # Assuming llm_interface.py is in the same directory or PYTHONPATH

# --- Configuration ---
DEFAULT_GEN_PROVIDER = os.getenv("SUBJECT_GEN_LLM_PROVIDER", "openai")
DEFAULT_GEN_MODEL = os.getenv("SUBJECT_GEN_LLM_MODEL", "gpt-4-turbo") 
DEFAULT_FORMAT_PROVIDER = os.getenv("SUBJECT_FORMAT_LLM_PROVIDER", "openai")
DEFAULT_FORMAT_MODEL = os.getenv("SUBJECT_FORMAT_LLM_MODEL", "gpt-3.5-turbo")

DISCIPLINES_FILE = "disciplines.jsonl"
OUTPUT_DIR = "checkpoints/subjects"
# Caching is handled by llm_interface.call_llm

def generate_subject_list_prompt(discipline_name, discipline_field=None, discipline_sub_field=None):
    """(Prompt remains the same)"""
    prompt = (
        f"You are an education expert specializing in the discipline of '{discipline_name}'. "
        f"This discipline falls under the field '{discipline_field}'"
        f"{f' and sub-field {discipline_sub_field}' if discipline_sub_field else ''}. "
        "Please generate a comprehensive list of subjects that a student should learn to master this discipline. "
        "For each subject, provide a brief one-sentence introduction. "
        "Consider subjects ranging from introductory to advanced levels. "
        "Present the output as a clear, itemized list. For example:\n"
        "- Subject Name 1: Brief introduction to Subject Name 1.\n"
        "- Subject Name 2: Brief introduction to Subject Name 2.\n"
        "Generate at least 10-20 subjects if appropriate for the discipline."
    )
    return prompt

def generate_jsonl_formatting_prompt(raw_subject_list_text, discipline_name):
    """(Prompt remains the same)"""
    prompt = (
        "The following is an unstructured list of subjects and their introductions for the discipline "
        f"'{discipline_name}':\n\n{raw_subject_list_text}\n\n"
        "Please transform this list into a JSONL format. Each line in the JSONL output should be a valid JSON object "
        "representing a single subject. Each JSON object should have the following keys: "
        "\"subject_name\" (string), \"level\" (string, e.g., 'Introductory', 'Intermediate', 'Advanced', 'All Levels'), "
        "and \"introduction\" (string, the brief introduction provided). "
        "Infer the 'level' based on the subject name or introduction if possible, otherwise default to 'All Levels'. "
        "Example of a line in JSONL format:\n"
        '{"subject_name": "Example Subject", "level": "Introductory", "introduction": "This is an example subject."}\n'
        "Ensure the entire output consists only of JSON objects, one per line. The response should be a string, where each line is a separate JSON object."
    )
    return prompt

async def main(): # Changed to async def
    print("Starting asynchronous subject generation for ALL disciplines...")
    print(f"Using Gen Provider: {DEFAULT_GEN_PROVIDER}, Gen Model: {DEFAULT_GEN_MODEL}")
    print(f"Using Format Provider: {DEFAULT_FORMAT_PROVIDER}, Format Model: {DEFAULT_FORMAT_MODEL}")

    if not os.path.exists(DISCIPLINES_FILE):
        print(f"Error: Disciplines file '{DISCIPLINES_FILE}' not found.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    disciplines_processed_count = 0
    total_disciplines_in_file = 0
    try:
        # Synchronous file read for initial count is generally acceptable as it's done once.
        with open(DISCIPLINES_FILE, 'r') as f_disciplines_count:
            total_disciplines_in_file = sum(1 for _ in f_disciplines_count)
    except Exception as e:
        print(f"Warning: Could not accurately count disciplines in {DISCIPLINES_FILE}: {e}")
    
    print(f"Found {total_disciplines_in_file if total_disciplines_in_file > 0 else 'an unknown number of'} discipline(s) in {DISCIPLINES_FILE} to process.")

    # Reading the disciplines file synchronously line by line.
    # The main async operations are the LLM calls within the loop.
    try:
        with open(DISCIPLINES_FILE, 'r') as f_disciplines:
            for line_num, line in enumerate(f_disciplines):
                current_discipline_number = line_num + 1
                progress_indicator = f"{current_discipline_number} of {total_disciplines_in_file}" if total_disciplines_in_file > 0 else f"{current_discipline_number}"
                print(f"\n--- Processing discipline {progress_indicator} ---")
                
                try:
                    discipline = json.loads(line.strip())
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON from line {current_discipline_number} in {DISCIPLINES_FILE}. Skipping.")
                    continue

                discipline_name = discipline.get("discipline_name")
                discipline_field = discipline.get("field")
                discipline_sub_field = discipline.get("sub_field")

                if not discipline_name:
                    print(f"Warning: Discipline on line {current_discipline_number} missing 'discipline_name'. Skipping.")
                    continue
                
                safe_discipline_name = "".join(c if c.isalnum() else "_" for c in discipline_name)
                output_subject_file = os.path.join(OUTPUT_DIR, f"{safe_discipline_name}_subjects.jsonl")

                # Synchronous os.path.exists check is fine here.
                if os.path.exists(output_subject_file):
                    print(f"Output file found for '{discipline_name}' at {output_subject_file}. Skipping.")
                    # disciplines_processed_count is incremented for successfully processed *new* files.
                    # If we want to count skipped files as "processed" in a broader sense, this logic would differ.
                    continue

                print(f"Processing discipline: {discipline_name} (Field: {discipline_field}, Sub-field: {discipline_sub_field})")

                # 1. Generate raw subject list - Await LLM call
                raw_list_prompt_text = generate_subject_list_prompt(discipline_name, discipline_field, discipline_sub_field)
                raw_subject_list_text_response = await call_llm(
                    prompt_text=raw_list_prompt_text,
                    provider=DEFAULT_GEN_PROVIDER,
                    model_name=DEFAULT_GEN_MODEL
                )

                if not raw_subject_list_text_response:
                    print(f"Failed to generate raw subject list for {discipline_name} via llm_interface. Skipping this discipline.")
                    continue
                
                print(f"Raw subject list for {discipline_name} (first 300 chars):\n{raw_subject_list_text_response[:300]}...")

                # 2. Format raw list into JSONL - Await LLM call
                jsonl_format_prompt_text = generate_jsonl_formatting_prompt(raw_subject_list_text_response, discipline_name)
                formatted_subjects_jsonl_str = await call_llm(
                    prompt_text=jsonl_format_prompt_text,
                    provider=DEFAULT_FORMAT_PROVIDER,
                    model_name=DEFAULT_FORMAT_MODEL
                )

                if not formatted_subjects_jsonl_str:
                    print(f"Failed to format subjects into JSONL for {discipline_name} via llm_interface. Skipping this discipline.")
                    continue
                
                print(f"Formatted subjects (JSONL) for {discipline_name} (first 300 chars):\n{formatted_subjects_jsonl_str[:300]}...")

                # Synchronous file write for the output of this discipline's processing.
                # Can be made async with asyncio.to_thread if it becomes a bottleneck.
                try:
                    with open(output_subject_file, 'w') as outfile:
                        lines_written = 0
                        for subject_line in formatted_subjects_jsonl_str.strip().split('\n'):
                            subject_line = subject_line.strip()
                            if not subject_line: continue
                            try:
                                json.loads(subject_line) 
                                outfile.write(subject_line + '\n')
                                lines_written +=1
                            except json.JSONDecodeError as je:
                                print(f"Warning: Invalid JSON line from LLM for {discipline_name}: '{subject_line}'. Error: {je}. Skipping this line.")
                        print(f"Successfully wrote {lines_written} subjects for '{discipline_name}' to {output_subject_file}")
                        disciplines_processed_count += 1 # Increment for successful processing
                except Exception as e:
                    print(f"Error writing JSONL for {discipline_name}: {e}")
                    if os.path.exists(output_subject_file): os.remove(output_subject_file) # Clean up partial file
                    continue
                
    except FileNotFoundError:
        print(f"Error: The disciplines file {DISCIPLINES_FILE} was not found during processing.")
    except Exception as e:
        print(f"An unexpected error occurred in subject_generator's main loop: {e}")

    final_report_str = f"Async subject generation run finished."
    if total_disciplines_in_file > 0 :
        final_report_str += f" Successfully generated subject files for {disciplines_processed_count} out of {total_disciplines_in_file} disciplines for which files didn't already exist."
    else:
        final_report_str += f" Successfully generated subject files for {disciplines_processed_count} discipline(s)."
        final_report_str += f" (Could not determine total number of disciplines in the input file for a precise progress count)."
    print(f"\n{final_report_str}")

if __name__ == "__main__":
    print("--- Async Subject Generation Script (ALL Disciplines, using llm_interface) ---")
    print("This script generates subject lists for ALL disciplines using an LLM via the async llm_interface.py.")
    print("Ensure your LLM provider API keys and any other necessary env vars are set.")
    print(f"Default Generation Provider: {DEFAULT_GEN_PROVIDER}, Model: {DEFAULT_GEN_MODEL}")
    print(f"Default Formatting Provider: {DEFAULT_FORMAT_PROVIDER}, Model: {DEFAULT_FORMAT_MODEL}")
    print(f"Reads from '{DISCIPLINES_FILE}'.")
    print(f"Output is saved to '{OUTPUT_DIR}/[discipline_name]_subjects.jsonl'.")
    print("Caching for LLM calls is handled by llm_interface.py.")
    print("----------------------------------------------------------------------------------\n")
    asyncio.run(main()) # Run the async main function
```
