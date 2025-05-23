import os
import json
import asyncio # Import asyncio
from llm_interface import call_llm # Assuming llm_interface.py is in the same directory or PYTHONPATH

# --- Configuration ---
DEFAULT_GEN_PROVIDER = os.getenv("SYLLABUS_GEN_LLM_PROVIDER", "openai")
DEFAULT_GEN_MODEL = os.getenv("SYLLABUS_GEN_LLM_MODEL", "gpt-4-turbo") 
DEFAULT_FORMAT_PROVIDER = os.getenv("SYLLABUS_FORMAT_LLM_PROVIDER", "openai")
DEFAULT_FORMAT_MODEL = os.getenv("SYLLABUS_FORMAT_LLM_MODEL", "gpt-3.5-turbo")

SUBJECTS_DIR = "checkpoints/subjects"
OUTPUT_DIR = "checkpoints/syllabi"
# Caching for LLM calls is handled by llm_interface.py

def generate_syllabus_prompt(subject_name, subject_level, subject_introduction):
    """(Prompt remains the same)"""
    prompt = (
        f"You are an expert curriculum designer. Please design a detailed syllabus for the subject: '{subject_name}'.\n"
        f"Subject Level: {subject_level}\n"
        f"Subject Introduction: {subject_introduction}\n\n"
        "The syllabus should be comprehensive and well-structured. It must include:"
        "1. Overall Subject Objectives/Goals.\n"
        "2. A list of Class Sessions (e.g., Week 1, Module 1, Session 1). Each session should cover a distinct topic or set of topics.\n"
        "3. For each Class Session, provide:\n"
        "    a. A brief Description of what the session covers.\n"
        "    b. A list of Key Concepts or Learning Outcomes students should master in that session.\n"
        "Structure the output clearly. For example:\n\n"
        "Subject: [Subject Name]\n"
        "Level: [Subject Level]\n"
        "Introduction: [Subject Introduction]\n\n"
        "Overall Objectives:\n"
        "- Objective 1\n"
        "- Objective 2\n\n"
        "Class Sessions:\n\n"
        "Session 1: [Session 1 Title/Topic]\n"
        "  Description: [Brief description of Session 1]\n"
        "  Key Concepts:\n"
        "    - Concept 1.1\n"
        "    - Concept 1.2\n\n"
        "Session 2: [Session 2 Title/Topic]\n"
        "  Description: [Brief description of Session 2]\n"
        "  Key Concepts:\n"
        "    - Concept 2.1\n"
        "    - Concept 2.2\n"
        "Please provide a syllabus with a reasonable number of sessions (e.g., 10-15 sessions, or more if appropriate for the subject's depth)."
    )
    return prompt

def generate_class_details_extraction_prompt(raw_syllabus_text, subject_name):
    """(Prompt remains the same)"""
    prompt = (
        f"The following is an unstructured syllabus for the subject '{subject_name}':\n\n"
        f"--- BEGIN SYLLABUS TEXT ---\n{raw_syllabus_text}\n--- END SYLLABUS TEXT ---\n\n"
        "Please extract the details for each class session from this syllabus and format them as a JSONL string. "
        "Each line in the JSONL output must be a valid JSON object representing a single class session. "
        "Each JSON object should have the following keys:\n"
        "  - \"class_session_name\" (string): The title or name of the class session (e.g., 'Session 1: Introduction to X').\n"
        "  - \"class_session_description\" (string): The brief description of what the session covers.\n"
        "  - \"key_concepts\" (list of strings): A list of key concepts or learning outcomes for that session.\n\n"
        "Example of a line in JSONL format:\n"
        '{"class_session_name": "Week 1: Fundamentals", "class_session_description": "Covers basic principles.", "key_concepts": ["Principle A", "Principle B"]}\n\n'
        "Ensure the entire output consists ONLY of these JSON objects, one per line. If the syllabus text does not contain clear class session structures, try your best to infer them or return an empty list if not possible."
    )
    return prompt

async def main(): # Changed to async def
    print("Starting asynchronous syllabus generation (Part 1: First subject of first discipline file)...")
    print(f"Syllabus Gen Provider: {DEFAULT_GEN_PROVIDER}, Model: {DEFAULT_GEN_MODEL}")
    print(f"Details Format Provider: {DEFAULT_FORMAT_PROVIDER}, Model: {DEFAULT_FORMAT_MODEL}")

    # Synchronous os.path checks are generally fine for setup.
    if not os.path.exists(SUBJECTS_DIR) or not os.listdir(SUBJECTS_DIR):
        print(f"Error: Subjects directory '{SUBJECTS_DIR}' is empty or not found.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    processed_one_subject = False
    subject_files = sorted([f for f in os.listdir(SUBJECTS_DIR) if f.endswith('_subjects.jsonl')])

    if not subject_files:
        print(f"No subject files found in {SUBJECTS_DIR}.")
        return

    first_subject_file_path = os.path.join(SUBJECTS_DIR, subject_files[0])
    print(f"Reading subjects from: {first_subject_file_path}")
    
    try:
        # File I/O for selecting the subject to process is synchronous.
        # This is acceptable as it's not the main performance-critical path.
        with open(first_subject_file_path, 'r') as f_subjects:
            for line_num, line in enumerate(f_subjects):
                if processed_one_subject:
                    break 
                
                try:
                    subject_data = json.loads(line.strip())
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON from line {line_num+1} in {first_subject_file_path}. Skipping.")
                    continue

                subject_name = subject_data.get("subject_name")
                subject_level = subject_data.get("level", "N/A")
                subject_intro = subject_data.get("introduction", "N/A")

                if not subject_name:
                    print(f"Warning: Subject on line {line_num+1} in {first_subject_file_path} missing 'subject_name'. Skipping.")
                    continue
                
                print(f"\nAttempting to process subject: '{subject_name}' (Level: {subject_level})")

                safe_subject_name = "".join(c if c.isalnum() else "_" for c in subject_name)
                output_syllabus_file = os.path.join(OUTPUT_DIR, f"{safe_subject_name}_syllabus.txt")
                output_class_details_file = os.path.join(OUTPUT_DIR, f"{safe_subject_name}_class_details.jsonl")

                if os.path.exists(output_syllabus_file) and os.path.exists(output_class_details_file):
                    print(f"Output files for '{subject_name}' already exist. Skipping generation.")
                    processed_one_subject = True 
                    continue # Move to the next subject file or finish if only processing one

                # 1. Generate raw syllabus text using async LLM call
                syllabus_prompt_text = generate_syllabus_prompt(subject_name, subject_level, subject_intro)
                raw_syllabus_text = await call_llm( # Changed to await
                    prompt_text=syllabus_prompt_text,
                    provider=DEFAULT_GEN_PROVIDER,
                    model_name=DEFAULT_GEN_MODEL
                )

                if not raw_syllabus_text:
                    print(f"Failed to generate raw syllabus for '{subject_name}'. Skipping.")
                    continue
                
                print(f"Raw syllabus generated for '{subject_name}' (first 300 chars):\n{raw_syllabus_text[:300]}...")
                # Synchronous file write for syllabus text.
                # Could be made async with asyncio.to_thread if it becomes a bottleneck.
                with open(output_syllabus_file, 'w') as f_out_syllabus:
                    f_out_syllabus.write(raw_syllabus_text)
                print(f"Full syllabus saved to {output_syllabus_file}")

                # 2. Extract class details into JSONL format using async LLM call
                extraction_prompt_text = generate_class_details_extraction_prompt(raw_syllabus_text, subject_name)
                extracted_class_details_jsonl_str = await call_llm( # Changed to await
                    prompt_text=extraction_prompt_text,
                    provider=DEFAULT_FORMAT_PROVIDER,
                    model_name=DEFAULT_FORMAT_MODEL
                )

                if not extracted_class_details_jsonl_str:
                    print(f"Failed to extract class details for '{subject_name}'. Corresponding syllabus text file was saved.")
                    continue
                
                print(f"Extracted class details (JSONL) for '{subject_name}' (first 300 chars):\n{extracted_class_details_jsonl_str[:300]}...")
                
                # Synchronous file write for class details.
                try:
                    with open(output_class_details_file, 'w') as f_out_details:
                        lines_written = 0
                        for detail_line in extracted_class_details_jsonl_str.strip().split('\n'):
                            detail_line = detail_line.strip()
                            if not detail_line:
                                continue
                            try:
                                json.loads(detail_line) 
                                f_out_details.write(detail_line + '\n')
                                lines_written += 1
                            except json.JSONDecodeError as je:
                                print(f"Warning: Invalid JSON line from LLM for '{subject_name}' class details: '{detail_line}'. Error: {je}. Skipping line.")
                        print(f"Successfully wrote {lines_written} class detail entries to {output_class_details_file}")
                except Exception as e:
                    print(f"Error writing class details JSONL for '{subject_name}': {e}")
                    if os.path.exists(output_class_details_file): 
                        os.remove(output_class_details_file) # Clean up partial file
                    continue
                
                processed_one_subject = True 
                # Since this script (Part 1) is designed to process only one subject,
                # break from the loop over lines in the current subject file.
                break 
            
            if not processed_one_subject: # This check is after iterating lines of the first file
                 print(f"No valid subjects found or processed in {first_subject_file_path}.")


    except FileNotFoundError:
        print(f"Error: The subject file {first_subject_file_path} was not found.")
    except Exception as e:
        print(f"An unexpected error occurred in syllabus_generator: {e}")

    if processed_one_subject:
        print("\nAsync syllabus generation (Part 1) finished for one subject.")
    else:
        print("\nAsync syllabus generation (Part 1) did not complete for any subject.")


if __name__ == "__main__":
    print("--- Async Syllabus Generation Script (Part 1: Single Subject) ---")
    print("This script generates a syllabus for the FIRST subject found in the FIRST subject file from checkpoints/subjects/.")
    print("Ensure LLM provider API keys and other env vars are set (for llm_interface.py).")
    print(f"Default Syllabus Gen Provider: {DEFAULT_GEN_PROVIDER}, Model: {DEFAULT_GEN_MODEL}")
    print(f"Default Details Format Provider: {DEFAULT_FORMAT_PROVIDER}, Model: {DEFAULT_FORMAT_MODEL}")
    print(f"Outputs saved to '{OUTPUT_DIR}/[subject_name]_syllabus.txt' and '[subject_name]_class_details.jsonl'.")
    print("LLM call caching is handled by llm_interface.py.")
    print("------------------------------------------------------------------------------------\n")
    asyncio.run(main()) # Run the async main function
```
