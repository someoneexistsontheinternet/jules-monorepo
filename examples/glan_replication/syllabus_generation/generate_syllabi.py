import json
import os
import glob
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

def load_subjects_from_file(processed_subject_file_path):
    """
    Reads a .jsonl file and yields each subject object (JSON parsed).
    """
    try:
        with open(processed_subject_file_path, 'r') as f:
            for line in f:
                try:
                    yield json.loads(line.strip())
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping invalid JSON line in '{processed_subject_file_path}': {e}\nLine: '{line.strip()}'")
    except FileNotFoundError:
        print(f"Error: Subject file not found: '{processed_subject_file_path}'")

# --- Mock LLM API Call ---
def call_openai_api(prompt, model_name="gpt-4", temperature=1.0, top_p=0.95, max_tokens=2000):
    """
    Mock function to simulate a call to an LLM API.
    Returns different pre-defined strings based on prompt content.
    """
    print(f"--- Simulating LLM API Call ---")
    print(f"Model: {model_name}, Temperature: {temperature}, Top_p: {top_p if top_p else 'N/A'}")
    print(f"Prompt Snippet:\n{prompt[:250]}...\n--- End of Prompt Snippet ---")

    if "design a detailed syllabus for the subject: Kinematics" in prompt:
        return """
Class Session 1: Introduction to Kinematics
Description: Overview of kinematics, fundamental quantities (displacement, velocity, acceleration), and their vector nature. Introduction to reference frames.
Key Concepts:
- Scalar vs. Vector quantities
- Displacement, distance
- Average and instantaneous velocity
- Average and instantaneous acceleration
- Frames of reference

Class Session 2: Uniform Motion
Description: Study of motion with constant velocity (zero acceleration). Graphical representations (x-t, v-t graphs).
Key Concepts:
- Equations of uniform motion (x = x0 + vt)
- Interpretation of x-t graphs (slope = velocity)
- Interpretation of v-t graphs (slope = 0, area = displacement)

Class Session 3: Uniformly Accelerated Motion
Description: Motion with constant non-zero acceleration. Derivation and application of kinematic equations.
Key Concepts:
- Kinematic equations (v = v0 + at, x = x0 + v0t + 0.5at^2, v^2 = v0^2 + 2a(x-x0))
- Problem-solving strategies
- Free fall as an example of uniformly accelerated motion (neglecting air resistance)
        """
    elif "extract the class sessions and their key concepts" in prompt and "Kinematics" in prompt:
        return json.dumps([
            {"class_session_name": "Introduction to Kinematics", "key_concepts_list": ["Scalar vs. Vector quantities", "Displacement, distance", "Average and instantaneous velocity", "Average and instantaneous acceleration", "Frames of reference"]},
            {"class_session_name": "Uniform Motion", "key_concepts_list": ["Equations of uniform motion (x = x0 + vt)", "Interpretation of x-t graphs (slope = velocity)", "Interpretation of v-t graphs (slope = 0, area = displacement)"]},
            {"class_session_name": "Uniformly Accelerated Motion", "key_concepts_list": ["Kinematic equations (v = v0 + at, x = x0 + v0t + 0.5at^2, v^2 = v0^2 + 2a(x-x0))", "Problem-solving strategies", "Free fall as an example of uniformly accelerated motion (neglecting air resistance)"]}
        ], indent=4)
    elif "design a detailed syllabus for the subject: Structure and Bonding" in prompt:
        return """
Class Session 1: Atomic Structure and Orbitals
Description: Review of atomic structure, electron configurations, and the concept of atomic orbitals (s, p, d).
Key Concepts:
- Quantum numbers
- Aufbau principle, Hund's rule, Pauli exclusion principle
- Shapes of s and p orbitals
- Electron density

Class Session 2: Covalent Bonding
Description: Formation of covalent bonds, Lewis structures, formal charges, and octet rule.
Key Concepts:
- Electronegativity and bond polarity
- Single, double, and triple bonds
- Drawing Lewis structures
- Calculating formal charges
        """
    elif "extract the class sessions and their key concepts" in prompt and "Structure and Bonding" in prompt:
        return json.dumps([
            {"class_session_name": "Atomic Structure and Orbitals", "key_concepts_list": ["Quantum numbers", "Aufbau principle, Hund's rule, Pauli exclusion principle", "Shapes of s and p orbitals", "Electron density"]},
            {"class_session_name": "Covalent Bonding", "key_concepts_list": ["Electronegativity and bond polarity", "Single, double, and triple bonds", "Drawing Lewis structures", "Calculating formal charges"]}
        ], indent=4)
    else: # Default for other subjects
        return """
Class Session 1: Generic Introduction to Subject
Description: An overview of this subject.
Key Concepts:
- Concept Alpha
- Concept Beta

Class Session 2: Core Principles of Subject
Description: Delving into the main ideas.
Key Concepts:
- Principle Gamma
- Principle Delta
        """

# --- Prompt Generation Functions ---
def get_syllabus_generation_prompt(subject_name, subject_level, subject_introduction, subject_subtopics, discipline_name):
    """
    Generates a prompt for instructing an LLM to design a detailed syllabus for a given subject.
    """
    subtopics_str = "\n- ".join(subject_subtopics) if subject_subtopics else "N/A"
    return f"""
You are an expert curriculum designer and educator specializing in the discipline of '{discipline_name}'.
Your task is to design a detailed syllabus for the subject: '{subject_name}'.

Subject Context:
- Level: {subject_level}
- Introduction: {subject_introduction}
- Key Subtopics to Cover (from previous generation step):
- {subtopics_str}

Syllabus Requirements:
1.  Break the subject into multiple distinct class sessions (e.g., 3-10 sessions, depending on subject breadth).
2.  For each class session, provide:
    a.  A clear Class Session Name/Title.
    b.  A brief Description (1-2 sentences) of what the session covers and its objectives.
    c.  A list of detailed Key Concepts that students need to master by the end of that session. These should be specific and actionable.

The output should be a clear, well-structured text, suitable for a human to read and understand. Do not use JSON or any other specific code format for this syllabus generation.

Example for a different subject (e.g., 'Introduction to Python Programming'):
Class Session 1: Getting Started with Python
Description: Introduction to Python, setting up the environment, and writing the first program.
Key Concepts:
- What is Python? History and applications.
- Installing Python (Anaconda, python.org).
- Using the Python interpreter and IDLE.
- Basic syntax: print() function, comments, simple expressions.
- Variables and data types (integers, floats, strings).

Class Session 2: Control Flow
Description: Learning about conditional statements and loops to control program execution.
Key Concepts:
- Conditional statements: if, elif, else.
- Boolean logic: and, or, not.
- Loops: for loops (with range()), while loops.
- break and continue statements.

Now, please generate the detailed syllabus for the subject '{subject_name}'.
"""

def get_detail_extraction_prompt(raw_syllabus_text, subject_name):
    """
    Generates a prompt for instructing an LLM to parse raw syllabus text and extract structured details.
    """
    return f"""
You are an expert data extraction tool. Your task is to parse the following raw syllabus text for the subject '{subject_name}' and extract structured information about class sessions and their key concepts.
The output must be a valid JSON list of objects. Each object in the list should represent a class session and must have the following two keys:
1.  "class_session_name": A string representing the name or title of the class session.
2.  "key_concepts_list": A list of strings, where each string is a key concept for that session.

Raw Syllabus Text to Parse:
--- START OF TEXT ---
{raw_syllabus_text}
--- END OF TEXT ---

Example of a single JSON object in the output list:
{{"class_session_name": "Example Session Title", "key_concepts_list": ["Example concept 1", "Example concept 2", "Example concept 3"]}}

Ensure your entire output is a single, valid JSON list. Do not include any explanatory text before or after the JSON list.
"""

# --- Main Script Logic ---
if __name__ == "__main__":
    subject_files_dir = "../subject_generation/data/processed/"
    
    raw_output_dir = "data/raw"
    processed_output_dir = "data/processed"
    os.makedirs(raw_output_dir, exist_ok=True)
    os.makedirs(processed_output_dir, exist_ok=True)

    # Find all processed subject files
    subject_files_pattern = os.path.join(subject_files_dir, "*_subjects.jsonl")
    subject_files = glob.glob(subject_files_pattern)

    if not subject_files:
        print(f"No subject files found at '{subject_files_pattern}'. Please ensure previous steps ran successfully.")
        # Create dummy subject files for pipeline demonstration if none exist
        print("Creating dummy subject files for demonstration...")
        os.makedirs(subject_files_dir, exist_ok=True)
        dummy_disciplines = {
            "classical_mechanics": [
                {"subject_name": "Kinematics", "level": "Introductory", "introduction": "Study of motion.", "subtopics": ["Displacement", "Velocity"]},
                {"subject_name": "Dynamics", "level": "Introductory", "introduction": "Study of forces.", "subtopics": ["Newton's Laws", "Friction"]}
            ],
            "organic_chemistry": [
                {"subject_name": "Structure and Bonding", "level": "Introductory", "introduction": "Atomic and molecular structure.", "subtopics": ["Orbitals", "Covalent bonds"]},
                {"subject_name": "Alkanes", "level": "Introductory", "introduction": "Saturated hydrocarbons.", "subtopics": ["Nomenclature", "Conformations"]}
            ]
        }
        for disc_slug, subjects_list in dummy_disciplines.items():
            dummy_filepath = os.path.join(subject_files_dir, f"{disc_slug}_subjects.jsonl")
            with open(dummy_filepath, 'w') as f:
                for subj in subjects_list:
                    f.write(json.dumps(subj) + "\n")
            subject_files.append(dummy_filepath) # Add to list to process
            print(f"Created dummy file: {dummy_filepath}")


    for subject_filepath in subject_files:
        try:
            filename = os.path.basename(subject_filepath)
            # Extract discipline name (assuming format <discipline_slug>_subjects.jsonl)
            discipline_slug = filename.replace("_subjects.jsonl", "")
            discipline_name = discipline_slug.replace("_", " ").title() # Simple way to get a readable name
            print(f"\n--- Processing Discipline: {discipline_name} (from file: {filename}) ---")
        except Exception as e:
            print(f"Could not determine discipline name from filename '{filename}'. Error: {e}. Skipping file.")
            continue

        for subject_data in load_subjects_from_file(subject_filepath):
            subject_name = subject_data.get("subject_name")
            if not subject_name:
                print(f"Warning: Subject data missing 'subject_name' in {subject_filepath}. Skipping.")
                continue
            
            subject_level = subject_data.get("level", "N/A")
            subject_intro = subject_data.get("introduction", "N/A")
            subject_subtopics = subject_data.get("subtopics", [])
            subject_name_slug = slugify(subject_name)

            print(f"  Processing syllabus for subject: '{subject_name}' in discipline: '{discipline_name}'")

            # 1. Generate raw syllabus text
            syllabus_prompt = get_syllabus_generation_prompt(
                subject_name, subject_level, subject_intro, subject_subtopics, discipline_name
            )
            raw_syllabus_text = call_openai_api(
                prompt=syllabus_prompt,
                model_name="gpt-4",
                temperature=1.0, # As per GLAN paper for syllabus generation
                top_p=0.95,      # As per GLAN paper for syllabus generation
                max_tokens=3000  # Syllabi can be lengthy
            )
            
            raw_syllabus_filename = os.path.join(raw_output_dir, f"{discipline_slug}_{subject_name_slug}_raw_syllabus.txt")
            with open(raw_syllabus_filename, 'w') as f:
                f.write(raw_syllabus_text)
            print(f"    Saved raw syllabus text to: {raw_syllabus_filename}")

            # 2. Extract structured details from raw syllabus text
            extraction_prompt = get_detail_extraction_prompt(raw_syllabus_text, subject_name)
            structured_syllabus_json_str = call_openai_api(
                prompt=extraction_prompt,
                model_name="gpt-3.5-turbo", # Or "gpt-4" as per paper, 3.5-turbo for cost/speed
                temperature=0.1, # Low temperature for deterministic extraction
                max_tokens=1500
            )

            processed_syllabus_filename = os.path.join(processed_output_dir, f"{discipline_slug}_{subject_name_slug}_syllabus_details.json")
            try:
                # Validate and save the JSON output
                parsed_json_details = json.loads(structured_syllabus_json_str)
                with open(processed_syllabus_filename, 'w') as f:
                    json.dump(parsed_json_details, f, indent=4)
                print(f"    Saved structured syllabus details to: {processed_syllabus_filename}")
            except json.JSONDecodeError as e:
                print(f"    Error: LLM output for structured syllabus details was not valid JSON. {e}")
                print(f"    Problematic output: {structured_syllabus_json_str[:300]}...") # Log snippet
                # Save the problematic output as a text file for debugging
                error_filename = os.path.join(processed_output_dir, f"{discipline_slug}_{subject_name_slug}_syllabus_details_error.txt")
                with open(error_filename, 'w') as f:
                    f.write(structured_syllabus_json_str)
                print(f"    Raw problematic output saved to: {error_filename}")

    print("\nSyllabus generation and detail extraction process completed for all subjects.")

"""
Placeholder for subject_generation/data/processed/classical_mechanics_subjects.jsonl:
{"subject_name": "Kinematics", "level": "Introductory", "introduction": "The study of motion without considering its causes. Covers concepts like displacement, velocity, and acceleration.", "subtopics": ["Uniform motion", "Non-uniform motion (constant acceleration)", "Projectile motion", "Circular motion"]}
{"subject_name": "Newton's Laws of Motion", "level": "Introductory", "introduction": "Fundamental principles governing the relationship between force, mass, and motion.", "subtopics": ["Newton's First Law (Inertia)", "Newton's Second Law (F=ma)", "Newton's Third Law (Action-Reaction)", "Free body diagrams", "Applications of Newton's Laws (e.g., friction, inclined planes)"]}

Placeholder for subject_generation/data/processed/organic_chemistry_subjects.jsonl:
{"subject_name": "Structure and Bonding", "level": "Introductory", "introduction": "Understanding the fundamental principles of atomic structure, chemical bonding (ionic, covalent), and molecular geometry in organic molecules.", "subtopics": ["Atomic orbitals and hybridization (sp3, sp2, sp)", "Lewis structures and formal charges", "Resonance theory", "VSEPR theory and molecular shapes", "Polarity of bonds and molecules"]}
{"subject_name": "Alkanes and Cycloalkanes", "level": "Introductory", "introduction": "Study of saturated hydrocarbons, their nomenclature, conformational analysis, and basic reactions.", "subtopics": ["IUPAC nomenclature of alkanes and cycloalkanes", "Newman projections and conformational isomers (e.g., ethane, butane)", "Ring strain in cycloalkanes (e.g., cyclopropane, cyclohexane chair/boat)", "Introduction to radical reactions (e.g., halogenation of alkanes)"]}
"""
