import json
import os

# Placeholder for the actual API call function from utils.llm_api_client
# from ..utils.llm_api_client import call_openai_api 
# For now, we'll define a mock function here.
def call_openai_api(prompt, model_name="gpt-4", temperature=0.7, max_tokens=2000):
    """
    Mock function to simulate a call to an LLM API.
    In a real scenario, this would interact with an actual LLM (e.g., OpenAI).
    """
    print(f"--- Simulating LLM API Call ---")
    print(f"Model: {model_name}, Temperature: {temperature}")
    print(f"Prompt:\n{prompt[:300]}...\n--- End of Prompt Snippet ---") # Print a snippet
    
    # Simulated raw JSON output structure based on the prompt
    # This is a simplified and truncated example. A real output would be much larger.
    simulated_output = [
        {
            "field": "Natural Sciences",
            "sub_fields": [
                {
                    "sub_field_name": "Physics",
                    "disciplines": [
                        "Classical Mechanics", 
                        "Quantum Mechanics", 
                        "Thermodynamics", 
                        "Electromagnetism",
                        "Optics",
                        "Acoustics",
                        "Astrophysics",
                        "Condensed Matter Physics"
                    ]
                },
                {
                    "sub_field_name": "Chemistry",
                    "disciplines": [
                        "Organic Chemistry", 
                        "Inorganic Chemistry", 
                        "Physical Chemistry", 
                        "Analytical Chemistry",
                        "Biochemistry"
                    ]
                },
                {
                    "sub_field_name": "Biology",
                    "disciplines": [
                        "Molecular Biology",
                        "Cellular Biology",
                        "Genetics",
                        "Physiology",
                        "Ecology",
                        "Evolutionary Biology",
                        "Microbiology",
                        "Botany",
                        "Zoology"
                    ]
                }
            ]
        },
        {
            "field": "Humanities",
            "sub_fields": [
                {
                    "sub_field_name": "History",
                    "disciplines": ["Ancient History", "Medieval History", "Modern History", "Art History"]
                },
                {
                    "sub_field_name": "Literature",
                    "disciplines": ["Poetry", "Prose", "Drama", "Literary Criticism"]
                }
            ]
        },
        # ... (More fields like Social Sciences, Applied Sciences, Formal Sciences, Services/Vocational Training would follow)
    ]
    return json.dumps(simulated_output, indent=4)


def get_taxonomy_generation_prompt():
    """
    Returns the prompt for instructing an LLM to generate a hierarchical taxonomy
    of human knowledge and capabilities.
    """
    return """
Your task is to generate a comprehensive hierarchical taxonomy of human knowledge and capabilities.
The hierarchy should be structured as follows:
1. Top-level: Broad Fields (e.g., Natural Sciences, Humanities, Social Sciences, Applied Sciences, Formal Sciences, Services/Vocational Training).
2. Mid-level: Sub-fields within each Field (e.g., under Natural Sciences: Physics, Chemistry, Biology).
3. Lowest-level: Distinct Disciplines within each Sub-field (e.g., under Physics: Classical Mechanics, Quantum Mechanics, Thermodynamics, Electromagnetism).

Aim for a broad coverage. The output should be structured in a nested JSON format.
Ensure that each level is clearly defined:
- "field": Name of the broad field.
- "sub_fields": A list of objects, where each object has:
    - "sub_field_name": Name of the sub-field.
    - "disciplines": A list of strings, where each string is a distinct discipline.

Example of desired output structure (JSON):
[
    {
        "field": "Field Name 1",
        "sub_fields": [
            {
                "sub_field_name": "Sub-field Name 1.1",
                "disciplines": ["Discipline 1.1.1", "Discipline 1.1.2"]
            },
            // ... more sub-fields for Field Name 1
        ]
    },
    {
        "field": "Field Name 2",
        "sub_fields": [
            {
                "sub_field_name": "Sub-field Name 2.1",
                "disciplines": ["Discipline 2.1.1", "Discipline 2.1.2"]
            }
            // ... more sub-fields for Field Name 2
        ]
    }
    // ... more fields
]

Please generate a comprehensive list.
"""

if __name__ == "__main__":
    # 1. Get the prompt
    taxonomy_prompt = get_taxonomy_generation_prompt()

    # 2. Make a simulated or actual call to the LLM API
    # The paper uses GPT-4 for this.
    print("Generating raw taxonomy using LLM (simulated)...")
    raw_taxonomy_output_json = call_openai_api(
        prompt=taxonomy_prompt, 
        model_name="gpt-4",  # As per GLAN paper
        temperature=0.7,     # As per GLAN paper (though they might use different T for different stages)
        max_tokens=4096      # Requesting a larger token limit for comprehensive taxonomy
    )

    # 3. Print the raw output for inspection
    print("\n--- Raw LLM Output (Simulated) ---")
    print(raw_taxonomy_output_json)
    print("--- End of Raw LLM Output ---\n")

    # 4. Save the raw LLM output
    output_dir = "examples/glan_replication/taxonomy_generation/data"
    output_filename = "raw_taxonomy_output.json" # Saving as JSON due to prompt structure
    
    # Ensure the data directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    output_filepath = os.path.join(output_dir, output_filename)
    
    try:
        # Attempt to parse the JSON to ensure it's valid before saving
        # In a real scenario, more robust error handling for LLM output might be needed
        parsed_json = json.loads(raw_taxonomy_output_json)
        with open(output_filepath, 'w') as f:
            json.dump(parsed_json, f, indent=4)
        print(f"Successfully saved raw taxonomy output to: {output_filepath}")
    except json.JSONDecodeError as e:
        print(f"Error: LLM output was not valid JSON. {e}")
        print("Saving raw output as .txt instead.")
        output_filepath_txt = os.path.join(output_dir, "raw_taxonomy_output_error.txt")
        with open(output_filepath_txt, 'w') as f:
            f.write(raw_taxonomy_output_json)
        print(f"Raw output saved to: {output_filepath_txt}")

    # 5. Note on next steps
    # Human verification and post-editing of this raw output would be the next step,
    # as per the GLAN paper, to ensure correctness and completeness,
    # and to curate the final list of disciplines.
    # For this automated script, we are saving the raw output.
    print("\nNote: Human verification and post-editing of this raw output would be the next step.")
    print("For this automated script, we are saving the raw output.")
