# Replication of GLAN Paper (arXiv:2402.13064v1)

This project aims to replicate the data generation pipeline and potentially the model training/evaluation described in the paper "Synthetic Data (Almost) from Scratch: Generalized Instruction Tuning for Language Models."

## Directory Structure

-   `taxonomy_generation/`: Stores generated domain/subject taxonomies.
-   `subject_generation/`: Stores generated subjects based on the taxonomies.
-   `syllabus_generation/`: Stores generated syllabi for various subjects.
-   `instruction_generation/`: Stores generated instruction-following data (e.g., question-answer pairs) based on syllabi.
-   `training_data/`: Contains the final, curated training dataset for model fine-tuning. This includes steps like decontamination and formatting.
-   `model_training/`: Holds scripts and logs related to training language models with the generated data.
-   `evaluation_results/`: Stores scripts, data, and results from evaluating the performance of the trained models.
-   `utils/`: Contains utility scripts, such as API clients for LLMs, data processing tools, etc.
-   `requirements.txt`: Lists the Python dependencies for this project.
