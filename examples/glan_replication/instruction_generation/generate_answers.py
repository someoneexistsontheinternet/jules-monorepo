import json
import os

# --- Helper Function to Load Questions ---
def load_questions(questions_file_path):
    """
    Reads a .jsonl file containing generated questions and yields each question object.
    """
    try:
        with open(questions_file_path, 'r') as f:
            for line in f:
                try:
                    yield json.loads(line.strip())
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping invalid JSON line in '{questions_file_path}': {e}\nLine: '{line.strip()}'")
    except FileNotFoundError:
        print(f"Error: Questions file not found: '{questions_file_path}'")

# --- Mock LLM API Call ---
def call_openai_api(prompt, model_name="gpt-3.5-turbo", temperature=0.7, top_p=0.95, max_tokens=1000):
    """
    Mock function to simulate a call to an LLM API for answer generation.
    """
    print(f"--- Simulating LLM API Call for Answer Generation ---")
    print(f"Model: {model_name}, Temperature: {temperature}, Top_p: {top_p}")
    print(f"Prompt Snippet:\n{prompt[:300]}...\n--- End of Prompt Snippet ---")

    # Simple mock logic: return a pre-defined answer based on keywords in the question (from prompt)
    if "average velocity and instantaneous velocity" in prompt:
        return """
Average velocity is the total displacement divided by the total time interval, giving a measure of motion over the entire duration. 
Instantaneous velocity is the velocity at a specific point in time, found by taking the limit of the average velocity as the time interval approaches zero (i.e., the derivative of displacement with respect to time).

Example: A car travels 100 km north in 2 hours. Its average velocity is 50 km/h north. However, if it stopped at a traffic light for 10 minutes during this trip, its instantaneous velocity at that moment was 0 km/h. If it sped up to 80 km/h on a highway segment, that was its instantaneous velocity then.
        """
    elif "action-reaction pairs of forces" in prompt and "book rests on a table" in prompt:
        return """
When a book rests on a table, the primary action-reaction pairs are:
1.  Action: The book exerts a downward force on the table (due to gravity acting on the book).
    Reaction: The table exerts an upward normal force on the book. This pair involves the book and the table.
2.  Action: The Earth exerts a downward gravitational force on the book (book's weight).
    Reaction: The book exerts an upward gravitational force on the Earth. This pair involves the book and the Earth.

If someone pushes down on the book:
- The downward force exerted by the book on the table increases. Consequently, the upward normal force exerted by the table on the book also increases by the same amount (action-reaction pair 1).
- The gravitational force pair between the book and Earth (action-reaction pair 2) remains unchanged by the push, as the masses of the Earth and book haven't changed.
        """
    elif "Lewis structure for methane (CH4)" in prompt:
        return """
Methane (CH4) has a central carbon atom bonded to four hydrogen atoms.
The Lewis structure is:
      H
      |
  H - C - H
      |
      H

Carbon has 4 valence electrons, and each hydrogen has 1 valence electron, for a total of 4 + 4(1) = 8 valence electrons.
All electrons are used in forming four single C-H bonds.

VSEPR Theory and Geometry:
Carbon is the central atom with four bonding pairs of electrons and zero lone pairs. According to VSEPR theory, these four electron pairs will arrange themselves tetrahedrally around the carbon atom to minimize repulsion. This results in a molecular geometry that is tetrahedral, with bond angles of approximately 109.5 degrees.

Hybridization:
To form four equivalent C-H sigma bonds in a tetrahedral arrangement, the carbon atom undergoes sp3 hybridization. One s orbital and three p orbitals on the carbon atom combine to form four equivalent sp3 hybrid orbitals. Each of these sp3 orbitals overlaps with a 1s orbital from a hydrogen atom to form a C-H sigma bond.
        """
    elif "free-radical halogenation of methane" in prompt:
        return """
The free-radical halogenation of methane (e.g., with chlorine, Cl2) typically proceeds in three main steps:

1.  Initiation:
    This step involves the homolytic cleavage of the halogen molecule (e.g., Cl2) to form two halogen radicals. This usually requires energy in the form of UV light or heat.
    Cl-Cl --(UV light)--> 2 Cl•

2.  Propagation:
    These steps involve the reaction of a radical with a non-radical molecule to form a new radical and a new non-radical molecule. This chain reaction continues.
    a)  A halogen radical abstracts a hydrogen atom from methane, forming a methyl radical and hydrogen halide:
        Cl• + CH4 --> HCl + •CH3 (methyl radical)
    b)  The methyl radical then reacts with another halogen molecule to form the halogenated methane product and a new halogen radical:
        •CH3 + Cl-Cl --> CH3Cl + Cl•
    This new Cl• radical can then participate in step 2a again, propagating the chain.

3.  Termination:
    These steps involve the reaction of two radicals to form a non-radical molecule, thereby ending the chain reaction. There are several possibilities:
    a)  Two halogen radicals combine:
        Cl• + Cl• --> Cl2
    b)  Two methyl radicals combine:
        •CH3 + •CH3 --> CH3CH3 (ethane)
    c)  A methyl radical and a halogen radical combine:
        •CH3 + Cl• --> CH3Cl
        """
    else:
        return "This is a detailed and insightful answer based on the provided context and concepts, demonstrating critical thinking and application of knowledge."

# --- Prompt Generation Function ---
def get_answer_generation_prompt(question_text, discipline, subject, sampled_class_sessions, sampled_key_concepts):
    """
    Generates a prompt for instructing an LLM to create a high-quality answer.
    """
    sessions_str = ", ".join(sampled_class_sessions) if sampled_class_sessions else "N/A"
    concepts_str = "\n- ".join(sampled_key_concepts) if sampled_key_concepts else "N/A"

    return f"""
You are an expert in the discipline of '{discipline}' with deep knowledge of the subject '{subject}'.
A student has been asked the following question, which focuses on the key concepts:
- {concepts_str}
These concepts were primarily covered in the class session(s): '{sessions_str}'.

Question:
"{question_text}"

Your task is to generate a comprehensive, accurate, and high-quality answer to this question.
The answer should be suitable for a student learning '{subject}'. Explain any complex terms or principles clearly.
Ensure your answer directly addresses all parts of the question.
Provide explanations and examples where appropriate to enhance understanding.
"""

# --- Main Script Logic ---
if __name__ == "__main__":
    questions_file = "data/questions.jsonl" # Path relative to current script location
    output_qa_pairs_file = "../training_data/raw_qa_pairs.jsonl" # Path relative to current script

    # Ensure output directory exists
    output_training_data_dir = os.path.dirname(output_qa_pairs_file)
    os.makedirs(output_training_data_dir, exist_ok=True)

    loaded_questions = list(load_questions(questions_file)) # Load all questions into a list

    if not loaded_questions:
        print(f"No questions found in '{questions_file}'. Creating dummy questions for demonstration.")
        # Create dummy questions if the input file is empty or not found
        dummy_questions_data = [
            {
                "discipline": "Classical Mechanics", "subject": "Kinematics",
                "sampled_class_sessions": ["Intro to Kinematics", "Uniform Motion"],
                "sampled_key_concepts": ["Displacement", "Velocity", "Acceleration", "Constant velocity"],
                "question_text": "Explain the difference between average velocity and instantaneous velocity. Provide an example scenario where they would differ.",
                "source_syllabus_file": "classical_mechanics_kinematics_syllabus_details.json"
            },
            {
                "discipline": "Organic Chemistry", "subject": "Structure and Bonding",
                "sampled_class_sessions": ["Atomic Structure", "Covalent Bonds"],
                "sampled_key_concepts": ["Orbitals", "Quantum numbers", "Lewis structures", "Formal charge"],
                "question_text": "Draw the Lewis structure for methane (CH4) and explain how its tetrahedral geometry arises from VSEPR theory. What is the hybridization of the carbon atom?",
                "source_syllabus_file": "organic_chemistry_structure-and-bonding_syllabus_details.json"
            }
        ]
        # Also ensure the input questions file exists with dummy data if it was missing.
        # This helps if running this script directly after a failed previous step or for testing.
        os.makedirs(os.path.dirname(questions_file), exist_ok=True)
        with open(questions_file, 'w') as f_dummy_q:
            for q_data in dummy_questions_data:
                f_dummy_q.write(json.dumps(q_data) + "\n")
        loaded_questions = dummy_questions_data # Use dummy data for this run


    qa_pairs = []

    for question_data in loaded_questions:
        print(f"\nGenerating answer for question related to subject: {question_data.get('subject', 'Unknown Subject')}...")
        
        question_text = question_data.get("question_text")
        if not question_text:
            print("Warning: Question data missing 'question_text'. Skipping.")
            continue

        discipline = question_data.get("discipline", "N/A")
        subject = question_data.get("subject", "N/A")
        sampled_sessions = question_data.get("sampled_class_sessions", [])
        sampled_concepts = question_data.get("sampled_key_concepts", [])

        answer_prompt = get_answer_generation_prompt(
            question_text, discipline, subject, sampled_sessions, sampled_concepts
        )
        
        generated_answer_text = call_openai_api(
            prompt=answer_prompt,
            model_name="gpt-3.5-turbo", # As per GLAN paper for answer generation
            temperature=0.7,
            top_p=0.95,
            max_tokens=1500 # Allow for detailed answers
        )

        qa_pair = {
            "question": question_text,
            "answer": generated_answer_text,
            "context": question_data # Store the original question context
        }
        qa_pairs.append(qa_pair)

    # Save all QA pairs to the output JSONL file
    if qa_pairs:
        with open(output_qa_pairs_file, 'w') as f:
            for item in qa_pairs:
                f.write(json.dumps(item) + "\n")
        print(f"\nSuccessfully generated {len(qa_pairs)} Q&A pairs and saved to: {output_qa_pairs_file}")
    else:
        print("\nNo Q&A pairs were generated in this run.")

    print("\nAnswer generation process completed.")
