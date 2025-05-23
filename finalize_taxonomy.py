import os
import json
import shutil

RAW_DRAFT_FILE = "raw_taxonomy_draft.jsonl"
FINAL_DISCIPLINES_FILE = "disciplines.jsonl"
# To force overwrite for testing/reruns, you could use a flag or environment variable
# For simplicity, this script will check file existence.
FORCE_OVERWRITE = os.getenv("FORCE_OVERWRITE_DISCIPLINES", "false").lower() == "true"

def main():
    print("Starting taxonomy finalization...")

    if not os.path.exists(RAW_DRAFT_FILE):
        print(f"Error: Raw draft file '{RAW_DRAFT_FILE}' not found.")
        print("Please run taxonomy_generator.py first to create the draft.")
        return

    if os.path.exists(FINAL_DISCIPLINES_FILE) and not FORCE_OVERWRITE:
        print(f"Final disciplines file '{FINAL_DISCIPLINES_FILE}' already exists.")
        print("Skipping finalization to avoid overwriting.")
        print(f"To overwrite, set the environment variable FORCE_OVERWRITE_DISCIPLINES=true")
        return
    
    if os.path.exists(FINAL_DISCIPLINES_FILE) and FORCE_OVERWRITE:
        print(f"FORCE_OVERWRITE is true. '{FINAL_DISCIPLINES_FILE}' will be overwritten.")

    # Simulate human verification by directly copying and validating the structure.
    # In a real scenario, this step would involve a human review interface/process,
    # and this script would consume the output of that process.
    
    final_disciplines = []
    try:
        with open(RAW_DRAFT_FILE, 'r') as infile:
            for line_number, line in enumerate(infile, 1):
                try:
                    discipline = json.loads(line.strip())
                    # Basic validation: ensure essential keys are present
                    if not isinstance(discipline, dict):
                        print(f"Warning: Line {line_number} in {RAW_DRAFT_FILE} is not a valid JSON object. Skipping.")
                        continue
                    if 'field' not in discipline or 'discipline_name' not in discipline:
                        print(f"Warning: Line {line_number} in {RAW_DRAFT_FILE} is missing 'field' or 'discipline_name'. Skipping: {discipline}")
                        continue
                    # 'sub_field' is optional, can be None or missing
                    if 'sub_field' not in discipline:
                        discipline['sub_field'] = None # Normalize missing sub_field

                    final_disciplines.append(discipline)
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON from line {line_number} in {RAW_DRAFT_FILE}. Skipping line: {line.strip()}")
                    continue
        
        if not final_disciplines:
            print(f"No valid disciplines found in {RAW_DRAFT_FILE}. Output file {FINAL_DISCIPLINES_FILE} will not be created or will be empty.")
            # Optionally create an empty file or handle as an error
            if os.path.exists(FINAL_DISCIPLINES_FILE): # If overwriting an existing file with an empty one
                 with open(FINAL_DISCIPLINES_FILE, 'w') as outfile:
                    pass # Create an empty file
            return

        with open(FINAL_DISCIPLINES_FILE, 'w') as outfile:
            for discipline in final_disciplines:
                json.dump(discipline, outfile)
                outfile.write('\n')
        
        print(f"Simulated human verification complete.")
        print(f"{len(final_disciplines)} disciplines written to '{FINAL_DISCIPLINES_FILE}'.")

    except Exception as e:
        print(f"An error occurred during the finalization process: {e}")

if __name__ == "__main__":
    print("--- Finalize Taxonomy Script ---")
    print(f"This script reads from '{RAW_DRAFT_FILE}' (created by taxonomy_generator.py),")
    print("simulates human verification (by performing basic validation and copying),")
    print(f"and writes the result to '{FINAL_DISCIPLINES_FILE}'.")
    print(f"If '{FINAL_DISCIPLINES_FILE}' exists, it will not be overwritten unless FORCE_OVERWRITE_DISCIPLINES=true is set.")
    print("--------------------------------\n")
    main()
```
