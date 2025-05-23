import json
import os

# --- Mock LLM API Call ---
def call_openai_api(prompt, model_name="gpt-4", temperature=1.0, top_p=0.95, max_tokens=1500):
    """
    Mock function to simulate a call to an LLM API.
    Returns different pre-defined strings based on prompt content.
    """
    print(f"--- Simulating LLM API Call ---")
    print(f"Model: {model_name}, Temperature: {temperature}, Top_p: {top_p}")
    print(f"Prompt Snippet:\n{prompt[:200]}...\n--- End of Prompt Snippet ---")

    if "generate a comprehensive list of subjects" in prompt and "Classical Mechanics" in prompt:
        return """
Subject 1: Kinematics
Level: Introductory
Introduction: The study of motion without considering its causes. Covers concepts like displacement, velocity, and acceleration.
Subtopics:
- Uniform motion
- Non-uniform motion (constant acceleration)
- Projectile motion
- Circular motion

Subject 2: Newton's Laws of Motion
Level: Introductory
Introduction: Fundamental principles governing the relationship between force, mass, and motion.
Subtopics:
- Newton's First Law (Inertia)
- Newton's Second Law (F=ma)
- Newton's Third Law (Action-Reaction)
- Free body diagrams
- Applications of Newton's Laws (e.g., friction, inclined planes)
        """
    elif "generate a comprehensive list of subjects" in prompt and "Organic Chemistry" in prompt:
        return """
Subject 1: Structure and Bonding
Level: Introductory
Introduction: Understanding the fundamental principles of atomic structure, chemical bonding (ionic, covalent), and molecular geometry in organic molecules.
Subtopics:
- Atomic orbitals and hybridization (sp3, sp2, sp)
- Lewis structures and formal charges
- Resonance theory
- VSEPR theory and molecular shapes
- Polarity of bonds and molecules

Subject 2: Alkanes and Cycloalkanes
Level: Introductory
Introduction: Study of saturated hydrocarbons, their nomenclature, conformational analysis, and basic reactions.
Subtopics:
- IUPAC nomenclature of alkanes and cycloalkanes
- Newman projections and conformational isomers (e.g., ethane, butane)
- Ring strain in cycloalkanes (e.g., cyclopropane, cyclohexane chair/boat)
- Introduction to radical reactions (e.g., halogenation of alkanes)
        """
    elif "convert the following unstructured subject list into a JSONL format" in prompt and "Kinematics" in prompt:
        # Simulating JSONL for Classical Mechanics
        return (
            '{"subject_name": "Kinematics", "level": "Introductory", "introduction": "The study of motion without considering its causes. Covers concepts like displacement, velocity, and acceleration.", "subtopics": ["Uniform motion", "Non-uniform motion (constant acceleration)", "Projectile motion", "Circular motion"]}\n'
            '{"subject_name": "Newton\'s Laws of Motion", "level": "Introductory", "introduction": "Fundamental principles governing the relationship between force, mass, and motion.", "subtopics": ["Newton\'s First Law (Inertia)", "Newton\'s Second Law (F=ma)", "Newton\'s Third Law (Action-Reaction)", "Free body diagrams", "Applications of Newton\'s Laws (e.g., friction, inclined planes)"]}'
        )
    elif "convert the following unstructured subject list into a JSONL format" in prompt and "Structure and Bonding" in prompt:
        # Simulating JSONL for Organic Chemistry
        return (
            '{"subject_name": "Structure and Bonding", "level": "Introductory", "introduction": "Understanding the fundamental principles of atomic structure, chemical bonding (ionic, covalent), and molecular geometry in organic molecules.", "subtopics": ["Atomic orbitals and hybridization (sp3, sp2, sp)", "Lewis structures and formal charges", "Resonance theory", "VSEPR theory and molecular shapes", "Polarity of bonds and molecules"]}\n'
            '{"subject_name": "Alkanes and Cycloalkanes", "level": "Introductory", "introduction": "Study of saturated hydrocarbons, their nomenclature, conformational analysis, and basic reactions.", "subtopics": ["IUPAC nomenclature of alkanes and cycloalkanes", "Newman projections and conformational isomers (e.g., ethane, butane)", "Ring strain in cycloalkanes (e.g., cyclopropane, cyclohexane chair/boat)", "Introduction to radical reactions (e.g., halogenation of alkanes)"]}'
        )
    else:
        # Default fallback for other disciplines or unexpected prompts
        return """
Subject 1: Generic Subject A for this Discipline
Level: Introductory
Introduction: An introduction to Generic Subject A.
Subtopics:
- Topic X
- Topic Y
        """
        
# --- Helper Functions ---
def load_disciplines_from_taxonomy(taxonomy_file_path):
    """
    Reads raw_taxonomy_output.json, parses it, and extracts a list of all discipline names.
    Returns a placeholder list if the file is not found or parsing fails.
    """
    disciplines = []
    try:
        with open(taxonomy_file_path, 'r') as f:
            taxonomy_data = json.load(f)
        
        for field_obj in taxonomy_data:
            if "sub_fields" in field_obj and isinstance(field_obj["sub_fields"], list):
                for sub_field_obj in field_obj["sub_fields"]:
                    if "disciplines" in sub_field_obj and isinstance(sub_field_obj["disciplines"], list):
                        disciplines.extend(sub_field_obj["disciplines"])
        
        if not disciplines: # If parsing succeeded but no disciplines found
            raise ValueError("No disciplines found in taxonomy file.")
        return list(set(disciplines)) # Return unique disciplines
    except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError) as e:
        print(f"Warning: Could not load or parse taxonomy file '{taxonomy_file_path}'. Error: {e}")
        print("Using placeholder disciplines for development.")
        return ["Classical Mechanics", "Organic Chemistry", "Quantum Mechanics"] # Placeholder

def get_subject_generation_prompt(discipline_name):
    """
    Returns a prompt for instructing an LLM to generate a list of subjects for a given discipline.
    """
    return f"""
You are an education expert specializing in the discipline of '{discipline_name}'.
Your task is to design a comprehensive list of subjects that a student should learn to master this discipline.
For each subject, please provide the following details:
1.  Subject Name: A clear and concise name for the subject.
2.  Level: The typical educational level (e.g., Introductory, Intermediate, Advanced, Foundational, Specialized).
3.  Introduction: A brief (1-2 sentences) introduction to what the subject covers.
4.  Subtopics: A list of key subtopics or concepts covered within this subject.

Please provide this information as a clear, well-structured text. Do not use JSON or any other specific code format for this initial list.
Ensure the list is comprehensive and covers the core areas of '{discipline_name}'.

Example for a different discipline (e.g., 'Data Structures and Algorithms'):
Subject 1: Basic Data Structures
Level: Introductory
Introduction: Covers fundamental data structures used in computer science.
Subtopics:
- Arrays and Lists
- Stacks and Queues
- Linked Lists (Singly, Doubly)
- Hash Tables

Subject 2: Trees and Graphs
Level: Intermediate
Introduction: Explores hierarchical and networked data structures.
Subtopics:
- Binary Trees, Binary Search Trees
- Balanced Trees (AVL, Red-Black)
- Heaps
- Graph representations (Adjacency Matrix, Adjacency List)
- Graph traversal algorithms (BFS, DFS)

Now, please generate a comprehensive list of subjects for the discipline: '{discipline_name}'.
"""

def get_jsonl_conversion_prompt(raw_subject_list_text, discipline_name):
    """
    Returns a prompt for instructing an LLM to convert an unstructured subject list
    into a JSONL format.
    """
    return f"""
You are an expert data formatter. Your task is to convert the following unstructured text, which describes a list of subjects for the discipline '{discipline_name}', into a JSONL format.
Each line in the output must be a valid JSON object representing one subject.
Each JSON object should have the following keys: "subject_name", "level", "introduction", "subtopics" (where "subtopics" is a list of strings).

Here is the unstructured text to convert:
--- START OF TEXT ---
{raw_subject_list_text}
--- END OF TEXT ---

Ensure that every line in your output is a distinct, valid JSON object.
Example of a single line in the expected JSONL output:
{{"subject_name": "Example Subject Name", "level": "Example Level", "introduction": "Example introduction.", "subtopics": ["Example subtopic 1", "Example subtopic 2"]}}

Now, please convert the provided text for '{discipline_name}' into JSONL format.
"""

# --- Main Script Logic ---
if __name__ == "__main__":
    taxonomy_file = "../taxonomy_generation/data/raw_taxonomy_output.json" # Relative path
    
    # Ensure output directories exist
    raw_output_dir = "data/raw"
    processed_output_dir = "data/processed"
    os.makedirs(raw_output_dir, exist_ok=True)
    os.makedirs(processed_output_dir, exist_ok=True)

    disciplines_to_process = load_disciplines_from_taxonomy(taxonomy_file)
    
    print(f"Found {len(disciplines_to_process)} disciplines to process.")
    # The paper mentions querying GPT-4 10 times for each discipline for subject generation.
    # For this implementation, we will do it once to build the pipeline.
    print("Note: GLAN paper queries GPT-4 10x per discipline for diversity; this script does it 1x for pipeline demonstration.")

    for discipline in disciplines_to_process:
        print(f"\nProcessing discipline: {discipline}...")

        # 1. Generate raw subject list text
        subject_gen_prompt = get_subject_generation_prompt(discipline)
        raw_subjects_text_output = call_openai_api(
            prompt=subject_gen_prompt,
            model_name="gpt-4", # As per GLAN paper for subject generation
            temperature=1.0,    # As per GLAN paper for diversity
            top_p=0.95,         # As per GLAN paper for diversity
            max_tokens=2000     # Increased tokens for comprehensive subject list
        )
        
        # Save raw subject text
        raw_subjects_filename = os.path.join(raw_output_dir, f"{discipline.replace(' ', '_').lower()}_raw_subjects.txt")
        with open(raw_subjects_filename, 'w') as f:
            f.write(raw_subjects_text_output)
        print(f"Saved raw subjects text to: {raw_subjects_filename}")

        # 2. Convert raw text to JSONL
        jsonl_conversion_prompt = get_jsonl_conversion_prompt(raw_subjects_text_output, discipline)
        subjects_jsonl_output = call_openai_api(
            prompt=jsonl_conversion_prompt,
            model_name="gpt-3.5-turbo", # Can use a cheaper/faster model for formatting
            temperature=0.2, # Lower temperature for more deterministic formatting
            max_tokens=1000
        )

        # Save processed JSONL
        processed_subjects_filename = os.path.join(processed_output_dir, f"{discipline.replace(' ', '_').lower()}_subjects.jsonl")
        # Basic validation: ensure it's somewhat like JSONL (multiple lines, each seems like JSON)
        lines = subjects_jsonl_output.strip().split('\n')
        all_lines_valid_json = True
        processed_lines = []

        for line_num, line_content in enumerate(lines):
            try:
                json.loads(line_content) # Try to parse each line
                processed_lines.append(line_content)
            except json.JSONDecodeError as e:
                all_lines_valid_json = False
                print(f"Warning: Line {line_num+1} in JSONL output for '{discipline}' is not valid JSON: {e}")
                print(f"Problematic line: {line_content}")
        
        if not processed_lines: # If all lines failed or output was empty
             print(f"Error: No valid JSONL lines produced for '{discipline}'. Saving raw converter output as error file.")
             error_filename = os.path.join(processed_output_dir, f"{discipline.replace(' ', '_').lower()}_subjects_conversion_error.txt")
             with open(error_filename, 'w') as f:
                f.write(subjects_jsonl_output)
        else:
            with open(processed_subjects_filename, 'w') as f:
                f.write("\n".join(processed_lines)) # Write only valid/processed lines
            print(f"Saved processed subjects JSONL to: {processed_subjects_filename}")
            if not all_lines_valid_json:
                print(f"Note: Some lines were invalid JSON for '{discipline}' and were potentially skipped. Check logs.")

    print("\nSubject generation process completed for all disciplines.")

"""
Example of how raw_taxonomy_output.json might look (ensure this file exists at the specified path for testing):
[
    {
        "field": "Natural Sciences",
        "sub_fields": [
            {
                "sub_field_name": "Physics",
                "disciplines": [
                    "Classical Mechanics", 
                    "Quantum Mechanics"
                ]
            },
            {
                "sub_field_name": "Chemistry",
                "disciplines": [
                    "Organic Chemistry"
                ]
            }
        ]
    },
    {
        "field": "Humanities",
        "sub_fields": [
            {
                "sub_field_name": "History",
                "disciplines": ["Ancient History"]
            }
        ]
    }
]
"""
