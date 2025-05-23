# GLAN Pipeline Architecture

This document outlines the architecture of the GLAN (Generalized Instruction Tuning) pipeline, based on the research paper "Synthetic Data (Almost) from Scratch: Generalized Instruction Tuning for Language Models" (arxiv.org/html/2402.13064v1). The pipeline is designed to generate large-scale synthetic instruction data for training Large Language Models (LLMs).

The GLAN pipeline consists of five main phases:

## Phase 1: Taxonomy Creation

-   **Goal:** To establish a comprehensive and structured foundation of human knowledge and capabilities.
-   **Input:** A pre-curated taxonomy of human knowledge (e.g., existing knowledge graphs, academic classifications).
-   **Process:**
    1.  Decompose the broad pre-curated taxonomy into a hierarchy of fields, sub-fields, and finally, distinct disciplines.
    2.  This process is semi-automatic:
        *   **LLM-aided Generation (GPT-4):** Use a powerful LLM like GPT-4 to propose initial decompositions and categorizations.
        *   **Human Verification:** Human annotators review, refine, and validate the LLM-generated taxonomy to ensure correctness, completeness, and reduce redundancy. This step is crucial for the quality of the generated data.
-   **Output:** A finalized list of disciplines.
    -   *Checkpointable Data:* `disciplines.jsonl` (Each line is a JSON object representing a discipline, e.g., `{"discipline_id": "CHEM101", "name": "Chemistry"}`).

## Phase 2: Subject Generator

-   **Goal:** To identify specific subjects within each discipline that can form the basis for instruction generation.
-   **Input:** The list of disciplines from Phase 1 (e.g., `disciplines.jsonl`).
-   **Process:**
    1.  For each discipline in the input list:
        *   Instruct an LLM (specifically GPT-4 as per the paper) to act as an "education expert" for that discipline.
        *   The LLM generates a comprehensive list of subjects a student should learn within that discipline. This initial output is often unstructured text.
        *   A second LLM prompt is used to transform the unstructured list of subjects into a structured JSONL format. This includes extracting metadata for each subject.
    2.  The paper notes that querying GPT-4 multiple times (e.g., 10 times per discipline) can ensure better coverage and diversity of subjects.
-   **Output:** A collection of lists, where each list contains subjects for a specific discipline.
    -   *Checkpointable Data:* JSONL files, one for each discipline, containing its subjects and their metadata (e.g., `checkpoints/subjects/[discipline_name]_subjects.jsonl`). Each line would be a JSON object like `{"subject_name": "Organic Chemistry", "level": "Undergraduate", "subtopics": ["Alkanes", "Alkenes", "Functional Groups"]}`.

## Phase 3: Syllabus Generator

-   **Goal:** To break down each subject into a detailed, structured syllabus, outlining class sessions and key learning concepts.
-   **Input:** The list of subjects with their metadata from Phase 2 (e.g., loaded from `checkpoints/subjects/`).
-   **Process:**
    1.  For each subject:
        *   Instruct an LLM (GPT-4) to design a syllabus based on the subject's name, level, and subtopics.
        *   The LLM is prompted to break the subject into different class sessions.
        *   For each class session, the LLM should provide a description and a list of detailed key concepts that students need to master.
        *   The initial syllabus output might be unstructured text. A subsequent LLM-aided step is used to extract class session names and their corresponding key concepts into a structured format.
-   **Output:** A detailed syllabus for each subject, along with extracted lists of class sessions and key concepts.
    -   *Checkpointable Data:*
        *   Full syllabus: `checkpoints/syllabi/[subject_name]_syllabus.jsonl` (or a text file if structure is very complex).
        *   Extracted class details: `checkpoints/syllabi/[subject_name]_class_details.jsonl`, where each line could be `{"class_session_name": "Introduction to Alkanes", "key_concepts": ["Nomenclature", "Physical Properties", "Reactions"]}`.

## Phase 4: Instruction Generator

-   **Goal:** To create diverse homework questions and their corresponding answers based on the generated syllabi.
-   **Input:**
    1.  Generated syllabi from Phase 3 (e.g., loaded from `checkpoints/syllabi/[subject_name]_syllabus.jsonl`).
    2.  Extracted class sessions and key concepts from Phase 3 (e.g., loaded from `checkpoints/syllabi/[subject_name]_class_details.jsonl`).
-   **Process:**
    1.  **Question Generation:**
        *   For each subject's syllabus:
            *   Sample one or two class session names from the list of class sessions.
            *   Sample one to five key concepts from the selected class session(s).
            *   The paper describes two sampling strategies:
                1.  **Single Session Sampling:** Key concepts are sampled from just one class session (for basic questions).
                2.  **Multi-Session Sampling:** Key concepts are sampled from two different class sessions (for more complex questions requiring integration of knowledge).
            *   Prompt an LLM (GPT-4 or GPT-3.5, as per the paper) to generate a homework question. The prompt includes the selected class session(s), key concept(s), and the full syllabus (to provide context about what students have already learned).
    2.  **Answer Generation:**
        *   Send the generated homework questions to another LLM (GPT-3.5 is used in the paper for speed and sufficient quality).
        *   Collect the LLM-generated answers.
-   **Output:** A large dataset of question-answer pairs suitable for instruction tuning.
    -   *Checkpointable Data:*
        *   Intermediate questions: `checkpoints/questions/[subject_name]_questions.jsonl`.
        *   Final question-answer pairs: `checkpoints/instruction_data/[subject_name]_qa_pairs.jsonl`. Each line is a JSON object like `{"question": "What are the first five alkanes?", "answer": "Methane, Ethane, Propane, Butane, Pentane."}`.

## Phase 5: Model Training

-   **Goal:** To fine-tune a base LLM using the synthetically generated instruction data.
-   **Input:** The large dataset of question-answer pairs from Phase 4 (e.g., aggregated from `checkpoints/instruction_data/`).
-   **Process:**
    1.  Concatenate each instruction (question) and response (answer) pair into a single sequence.
    2.  Train a base LLM (Mistral 7B is used as an example in the paper) on these sequences.
    3.  During training, compute the loss function only on the response (answer) tokens to teach the model to generate correct and relevant answers.
    4.  The paper specifies training for three epochs, using a cosine learning rate schedule with a linear warm-up of 1000 steps, and a final learning rate reduced to 0.
-   **Output:** A fine-tuned LLM with improved instruction-following capabilities across a wide range of domains.
    -   *Checkpointable Data:* Model weights/checkpoints at regular intervals (e.g., end of each epoch, or more frequently). Stored in the standard format of the training framework (e.g., PyTorch `.pt` files, TensorFlow checkpoint files) in a designated `checkpoints/model_training/` directory.

## Checkpointing Strategy Summary

Checkpointing is implemented at the end of each major data generation or processing step within each phase. This allows for:
-   **Resumability:** If the pipeline is interrupted, it can be resumed from the last successful checkpoint, saving significant computation time and resources.
-   **Modularity:** Individual phases can be re-run with different parameters or inputs without affecting other completed phases.
-   **Data Integrity:** Intermediate data is saved, reducing the risk of loss due to errors in subsequent steps.

The specific checkpoint file names and locations are suggested in the output sections of each phase description above. The general idea is to save the output of each significant generation (disciplines, subjects per discipline, syllabi per subject, questions per subject, Q&A pairs per subject, and model weights per epoch/training step).
