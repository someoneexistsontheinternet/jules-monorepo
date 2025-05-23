# GLAN Pipeline Implementation TODO

This file lists the tasks required to implement the full GLAN pipeline as described in `ARCHITECTURE.md`.

## Phase 1: Taxonomy Creation
- [ ] **Develop Script for Initial Taxonomy Generation (Optional):** If a pre-curated taxonomy is not readily available, create a script to prompt an LLM (e.g., GPT-4) to generate an initial draft of human knowledge fields, sub-fields, and disciplines.
- [ ] **Establish Human Verification Process/Interface:**
    - [ ] Design a process or a simple interface for human annotators to review, edit, add, or remove entries from the LLM-generated taxonomy.
    - [ ] Define guidelines for human verification to ensure consistency and quality.
- [ ] **Implement Taxonomy Finalization Script:**
    - [ ] Script to process the human-verified data.
    - [ ] Output the final list of disciplines to `disciplines.jsonl`.
- [ ] **Implement Checkpoint for Taxonomy:**
    - [ ] Ensure `disciplines.jsonl` serves as a checkpoint.
    - [ ] Add logic to subsequent scripts to load from `disciplines.jsonl` if it exists.

## Phase 2: Subject Generator
- [ ] **Implement Subject Generation Script:**
    - [ ] Takes `disciplines.jsonl` as input.
    - [ ] For each discipline:
        - [ ] Implement LLM (GPT-4) prompting to generate a list of subjects (as an "education expert").
        - [ ] Implement a second LLM (GPT-4) prompting step to convert the unstructured subject list to JSONL format, extracting name, level, and subtopics.
        - [ ] Handle API calls, retries, and error logging.
- [ ] **Implement Checkpointing for Subject Generation:**
    - [ ] Save output for each discipline to `checkpoints/subjects/[discipline_name]_subjects.jsonl`.
    - [ ] Add logic to the script to check if a subject file for a discipline already exists and skip generation if so.

## Phase 3: Syllabus Generator
- [ ] **Implement Syllabus Generation Script:**
    - [ ] Takes subject files from `checkpoints/subjects/` as input.
    - [ ] For each subject:
        - [ ] Implement LLM (GPT-4) prompting to design a syllabus (including class sessions with descriptions and key concepts).
        - [ ] Implement LLM (GPT-4) prompting to extract class session names and key concepts into a structured format.
- [ ] **Implement Checkpointing for Syllabus Generation:**
    - [ ] Save full syllabus to `checkpoints/syllabi/[subject_name]_syllabus.jsonl` (or `.txt`).
    - [ ] Save extracted class details to `checkpoints/syllabi/[subject_name]_class_details.jsonl`.
    - [ ] Add logic to skip generation if checkpoint files for a subject exist.

## Phase 4: Instruction Generator
- [ ] **Implement Question Generation Script:**
    - [ ] Takes syllabus and class details files from `checkpoints/syllabi/` as input.
    - [ ] For each subject's syllabus:
        - [ ] Implement sampling strategies for class sessions and key concepts (single session and multi-session).
        - [ ] Implement LLM (GPT-4 or GPT-3.5) prompting to generate homework questions based on samples, syllabus context.
- [ ] **Implement Answer Generation Script:**
    - [ ] Takes generated questions (e.g., `checkpoints/questions/[subject_name]_questions.jsonl`) as input.
    - [ ] Implement LLM (GPT-3.5) prompting to generate answers for each question.
- [ ] **Implement Checkpointing for Instruction Generation:**
    - [ ] Save generated questions to `checkpoints/questions/[subject_name]_questions.jsonl`.
    - [ ] Save final question-answer pairs to `checkpoints/instruction_data/[subject_name]_qa_pairs.jsonl`.
    - [ ] Add logic to skip question/answer generation if respective checkpoint files exist.
- [ ] **Implement Data Aggregation:** Script to aggregate all `[subject_name]_qa_pairs.jsonl` files into a final training dataset.
- [ ] **Implement Data Decontamination (as per paper):** Script to remove pairs that contain questions or input prompts from test/training sets of benchmarks.

## Phase 5: Model Training
- [ ] **Set up Base LLM Environment:** Prepare the environment for training Mistral 7B (or chosen alternative).
- [ ] **Implement Training Script:**
    - [ ] Load aggregated and decontaminated instruction-response pairs.
    - [ ] Concatenate instruction and response, prepare for training.
    - [ ] Implement loss calculation (only on response tokens).
    - [ ] Configure training parameters (epochs, learning rate, schedule, warm-up) as specified in the paper.
- [ ] **Implement Model Training Checkpointing:**
    - [ ] Save model weights at regular intervals (e.g., per epoch) to `checkpoints/model_training/`.
    - [ ] Implement logic to resume training from the latest model checkpoint.

## General Tasks
- [ ] **Configuration Management:** Set up a configuration file (e.g., YAML, JSON) for API keys, model names, file paths, and other parameters.
- [ ] **Logging Framework:** Implement consistent logging across all scripts for progress tracking and debugging.
- [ ] **Error Handling and Retries:** Implement robust error handling and retry mechanisms for LLM API calls.
- [ ] **Repository Setup:** Initialize Git, create a `.gitignore` file.
- [ ] **Testing:** Develop unit/integration tests for key components (e.g., data parsing, API interaction mocks).
- [ ] **Documentation (Refinement):** Continuously update `ARCHITECTURE.md` and other documentation as implementation progresses.
