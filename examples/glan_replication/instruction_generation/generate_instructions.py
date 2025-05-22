import json
import os
import glob
import random
import re

# --- Helper Functions ---
def slugify(text):
    """
    Convert text to a URL-friendly slug.
    Removes special characters, converts to lowercase, and replaces spaces with hyphens.
    """
    text = text.lower()
    text = re.sub(r'\s+', '-', text)  # Replace spaces with hyphens
    text = re.sub(r'[^\w\-]', '', text)  # Remove non-alphanumeric characters except hyphens
    return text.strip('-')

def load_processed_syllabus(processed_syllabus_file_path):
    """
    Reads a .json file containing processed syllabus details.
    Expected format: a list of class sessions, each with "class_session_name" and "key_concepts_list".
    """
    try:
        with open(processed_syllabus_file_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list) and all(
                isinstance(session, dict) and 
                "class_session_name" in session and 
                "key_concepts_list" in session and 
                isinstance(session["key_concepts_list"], list) 
                for session in data
            ):
                return data
            else:
                print(f"Warning: Syllabus file '{processed_syllabus_file_path}' has unexpected structure. Returning empty list.")
                return []
    except FileNotFoundError:
        print(f"Error: Processed syllabus file not found: '{processed_syllabus_file_path}'")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from '{processed_syllabus_file_path}': {e}")
        return []

def load_raw_syllabus_text(raw_syllabus_file_path):
    """
    Reads a raw syllabus text file.
    """
    try:
        with open(raw_syllabus_file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Raw syllabus text file not found: '{raw_syllabus_file_path}'. Returning empty string.")
        return ""

def sample_concepts_for_question(class_sessions_details):
    """
    Randomly samples class sessions and key concepts based on Strategy 1 or Strategy 2.
    Returns a tuple: (list_of_selected_session_names, list_of_sampled_key_concepts).
    """
    if not class_sessions_details:
        return [], []

    num_sessions_available = len(class_sessions_details)
    
    # Determine strategy (50/50 chance if 2+ sessions, else always Strategy 1 if 1 session)
    use_strategy_2 = (num_sessions_available >= 2 and random.random() < 0.5)

    selected_session_names = []
    sampled_key_concepts = []

    if use_strategy_2:
        # Strategy 2: Select 2 distinct class sessions
        idx1, idx2 = random.sample(range(num_sessions_available), 2)
        session1_details = class_sessions_details[idx1]
        session2_details = class_sessions_details[idx2]
        
        selected_session_names = [session1_details["class_session_name"], session2_details["class_session_name"]]

        concepts1_list = [c for c in session1_details.get("key_concepts_list", []) if c] # Filter empty concepts
        concepts2_list = [c for c in session2_details.get("key_concepts_list", []) if c]

        # Sample 1 to 4 concepts from session 1 (or fewer if not available)
        max_concepts_s1 = min(len(concepts1_list), 4)
        num_to_sample_s1 = random.randint(1, max_concepts_s1) if max_concepts_s1 > 0 else 0
        
        # Sample 1 to (5 - num_to_sample_s1, min 1) from session 2 (or fewer if not available)
        max_concepts_s2 = min(len(concepts2_list), max(1, 5 - num_to_sample_s1))
        num_to_sample_s2 = random.randint(1, max_concepts_s2) if max_concepts_s2 > 0 else 0
        
        # Ensure total concepts are between 2 and 5 if possible, adjust if one list was empty
        if num_to_sample_s1 == 0 and num_to_sample_s2 > 0: # Only session 2 has concepts
             num_to_sample_s2 = random.randint(min(2, max_concepts_s2) if max_concepts_s2 > 0 else 0, min(5, max_concepts_s2) if max_concepts_s2 > 0 else 0)
        elif num_to_sample_s2 == 0 and num_to_sample_s1 > 0: # Only session 1 has concepts
             num_to_sample_s1 = random.randint(min(2, max_concepts_s1) if max_concepts_s1 > 0 else 0, min(5, max_concepts_s1) if max_concepts_s1 > 0 else 0)
        elif num_to_sample_s1 + num_to_sample_s2 < 2 and (num_to_sample_s1 + num_to_sample_s2 > 0): # if total is 1, try to make it 2
            if num_to_sample_s1 < max_concepts_s1: num_to_sample_s1 = min(max_concepts_s1, num_to_sample_s1 +1)
            elif num_to_sample_s2 < max_concepts_s2: num_to_sample_s2 = min(max_concepts_s2, num_to_sample_s2 +1)

        if concepts1_list and num_to_sample_s1 > 0:
            sampled_key_concepts.extend(random.sample(concepts1_list, num_to_sample_s1))
        if concepts2_list and num_to_sample_s2 > 0:
            sampled_key_concepts.extend(random.sample(concepts2_list, num_to_sample_s2))

    else:
        # Strategy 1: Select 1 class session
        session_idx = random.choice(range(num_sessions_available))
        selected_session_details = class_sessions_details[session_idx]
        selected_session_names = [selected_session_details["class_session_name"]]
        
        concepts_list = [c for c in selected_session_details.get("key_concepts_list", []) if c] # Filter empty
        
        if concepts_list:
            # Sample 1 to 5 concepts (or fewer if not available)
            max_concepts_to_sample = min(len(concepts_list), 5)
            num_to_sample = random.randint(1, max_concepts_to_sample) if max_concepts_to_sample > 0 else 0
            if num_to_sample > 0:
                 sampled_key_concepts.extend(random.sample(concepts_list, num_to_sample))

    return selected_session_names, list(set(sampled_key_concepts)) # Ensure unique concepts

# --- Mock LLM API Call ---
def call_openai_api(prompt, model_name="gpt-4", temperature=1.0, top_p=0.95, max_tokens=500):
    """
    Mock function to simulate a call to an LLM API for question generation.
    """
    print(f"--- Simulating LLM API Call for Question Generation ---")
    print(f"Model: {model_name}, Temperature: {temperature}, Top_p: {top_p}")
    print(f"Prompt Snippet:\n{prompt[:300]}...\n--- End of Prompt Snippet ---")

    if "Kinematics" in prompt and "Uniform motion" in prompt:
        return "Explain the difference between average velocity and instantaneous velocity. Provide an example scenario where they would differ."
    elif "Newton's Laws of Motion" in prompt and "Action-Reaction" in prompt:
        return "A book rests on a table. Describe the action-reaction pairs of forces involved. If someone pushes down on the book, how do these pairs change?"
    elif "Structure and Bonding" in prompt and "Covalent bonds" in prompt:
        return "Draw the Lewis structure for methane (CH4) and explain how its tetrahedral geometry arises from VSEPR theory. What is the hybridization of the carbon atom?"
    elif "Alkanes" in prompt:
        return "Describe the process of free-radical halogenation of methane. Include the initiation, propagation, and termination steps."
    else:
        return "Based on the provided concepts, formulate a challenging question that requires critical thinking."

# --- Prompt Generation Function ---
def get_question_generation_prompt(sampled_class_session_names, sampled_key_concepts, full_syllabus_text, subject_name, discipline_name):
    """
    Generates a prompt for instructing an LLM to create a homework question.
    """
    sessions_str = ", ".join(sampled_class_session_names)
    concepts_str = "\n- ".join(sampled_key_concepts) if sampled_key_concepts else "N/A (focus on general understanding of the session(s))"

    return f"""
You are an expert educator tasked with creating a meaningful homework question for the subject '{subject_name}' in the discipline of '{discipline_name}'.

The question should specifically assess understanding of the following key concepts:
- {concepts_str}
These concepts are primarily covered in the class session(s): '{sessions_str}'.

Students are expected to have learned all material up to and including these sessions.
Consider the broader context of the entire syllabus provided below to ensure the question is appropriately pitched and leverages prior knowledge where applicable. Avoid simply asking for definitions. The question should require application of knowledge or critical thinking.

Full Syllabus Context:
--- START OF SYLLABUS ---
{full_syllabus_text}
--- END OF SYLLABUS ---

Based on the sampled key concepts, their session(s), and the full syllabus context, please generate one clear and concise homework question.
The question should be challenging yet solvable for a student at the '{subject_name}' level.
"""

# --- Main Script Logic ---
if __name__ == "__main__":
    syllabus_details_dir = "../syllabus_generation/data/processed/"
    raw_syllabus_dir = "../syllabus_generation/data/raw/" # For full syllabus context
    
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_questions_file = os.path.join(output_dir, "questions.jsonl")

    syllabus_files_pattern = os.path.join(syllabus_details_dir, "*_syllabus_details.json")
    syllabus_files = glob.glob(syllabus_files_pattern)

    if not syllabus_files:
        print(f"No processed syllabus files found at '{syllabus_files_pattern}'. Please ensure previous steps ran successfully.")
        # Create dummy syllabus files for pipeline demonstration
        print("Creating dummy syllabus files for demonstration...")
        os.makedirs(syllabus_details_dir, exist_ok=True)
        os.makedirs(raw_syllabus_dir, exist_ok=True)
        
        dummy_syllabi = {
            "classical_mechanics_kinematics": {
                "details": [
                    {"class_session_name": "Intro to Kinematics", "key_concepts_list": ["Displacement", "Velocity", "Acceleration"]},
                    {"class_session_name": "Uniform Motion", "key_concepts_list": ["Constant velocity", "x-t graphs", "v-t graphs"]}
                ],
                "raw_text": "Session 1: Intro to Kinematics (Displacement, Velocity, Acceleration). Session 2: Uniform Motion (Constant velocity, x-t graphs, v-t graphs)."
            },
            "organic_chemistry_structure-and-bonding": {
                "details": [
                    {"class_session_name": "Atomic Structure", "key_concepts_list": ["Orbitals", "Quantum numbers"]},
                    {"class_session_name": "Covalent Bonds", "key_concepts_list": ["Lewis structures", "Formal charge", "Resonance"]}
                ],
                "raw_text": "Session 1: Atomic Structure (Orbitals, Quantum numbers). Session 2: Covalent Bonds (Lewis structures, Formal charge, Resonance)."
            }
        }
        for key, data in dummy_syllabi.items():
            details_path = os.path.join(syllabus_details_dir, f"{key}_syllabus_details.json")
            raw_path = os.path.join(raw_syllabus_dir, f"{key}_raw_syllabus.txt")
            with open(details_path, 'w') as f_details: json.dump(data["details"], f_details, indent=4)
            with open(raw_path, 'w') as f_raw: f_raw.write(data["raw_text"])
            syllabus_files.append(details_path)
        print(f"Created {len(dummy_syllabi)} dummy syllabus sets.")


    all_generated_questions = []
    questions_to_generate_per_syllabus = 5 # For demonstration

    for syllabus_detail_filepath in syllabus_files:
        filename = os.path.basename(syllabus_detail_filepath)
        parts = filename.replace("_syllabus_details.json", "").split("_", 1)
        if len(parts) == 2:
            discipline_slug, subject_slug = parts
            discipline_name = discipline_slug.replace("-", " ").title()
            subject_name = subject_slug.replace("-", " ").title()
        else:
            print(f"Warning: Could not parse discipline/subject from filename '{filename}'. Using placeholders.")
            discipline_slug, subject_slug = filename.replace("_syllabus_details.json",""), "unknown_subject"
            discipline_name, subject_name = "Unknown Discipline", "Unknown Subject"

        print(f"\n--- Processing Syllabus for: Discipline '{discipline_name}', Subject '{subject_name}' ---")
        
        class_sessions_details = load_processed_syllabus(syllabus_detail_filepath)
        if not class_sessions_details:
            print(f"  No class session details found or loaded for {filename}. Skipping.")
            continue

        raw_syllabus_filepath = os.path.join(raw_syllabus_dir, f"{discipline_slug}_{subject_slug}_raw_syllabus.txt")
        full_syllabus_text = load_raw_syllabus_text(raw_syllabus_filepath)
        if not full_syllabus_text:
            print(f"  Warning: Raw syllabus text not found for {discipline_slug}_{subject_slug}. Question context might be limited.")
            # Fallback: use a stringified version of the structured details if raw is missing
            full_syllabus_text = json.dumps(class_sessions_details, indent=2)


        for i in range(questions_to_generate_per_syllabus):
            sampled_session_names, sampled_concepts = sample_concepts_for_question(class_sessions_details)
            
            if not sampled_concepts: # If no concepts could be sampled (e.g. empty lists)
                print(f"  Skipping question {i+1} for '{subject_name}' as no concepts were sampled.")
                continue

            print(f"  Generating question {i+1}/{questions_to_generate_per_syllabus} for '{subject_name}', focusing on concepts: {sampled_concepts} from session(s): {sampled_session_names}")
            
            question_prompt = get_question_generation_prompt(
                sampled_session_names, sampled_concepts, full_syllabus_text, subject_name, discipline_name
            )
            
            generated_question_text = call_openai_api(
                prompt=question_prompt,
                model_name="gpt-4", # As per GLAN paper
                temperature=1.0,   # As per GLAN paper
                top_p=0.95         # As per GLAN paper
            )

            question_data = {
                "discipline": discipline_name,
                "subject": subject_name,
                "sampled_class_sessions": sampled_session_names,
                "sampled_key_concepts": sampled_concepts,
                "question_text": generated_question_text,
                "source_syllabus_file": filename 
            }
            all_generated_questions.append(question_data)

    # Save all generated questions to a single JSONL file
    if all_generated_questions:
        with open(output_questions_file, 'w') as f:
            for item in all_generated_questions:
                f.write(json.dumps(item) + "\n")
        print(f"\nSuccessfully generated {len(all_generated_questions)} questions and saved to: {output_questions_file}")
    else:
        print("\nNo questions were generated in this run.")

    print("\nInstruction generation process completed.")
