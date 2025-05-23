import argparse
import os
import glob
import hashlib
import json
import time
import random
import importlib.util
from concurrent.futures import ThreadPoolExecutor, as_completed
# Assuming llm_api_client might be used by worker scripts or this executor directly
# from .llm_api_client import LLMAPIClient # If LLM calls are made directly by executor

# --- Configuration ---
DEFAULT_SEED = 42
DEFAULT_NUM_WORKERS = 5 # For tasks managed by this executor, not necessarily LLM workers
METADATA_DIR = ".executor_metadata" # To store metadata about processed files

# --- Helper Functions ---
def get_file_hash(filepath):
    """Computes SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def get_input_item_hash(item_data):
    """Computes SHA256 hash of a JSON serializable data item (e.g., a line in JSONL)."""
    # For complex objects, ensure consistent serialization
    return hashlib.sha256(json.dumps(item_data, sort_keys=True).encode('utf-8')).hexdigest()

def ensure_dir_exists(path):
    os.makedirs(path, exist_ok=True)

# --- Main Executor Class or Functions ---

class ResumableExecutor:
    def __init__(self, worker_script_path, input_folder, output_folder, 
                 sample_size=None, seed=DEFAULT_SEED, num_workers=DEFAULT_NUM_WORKERS,
                 force_regenerate=False):
        self.worker_script_path = worker_script_path
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.sample_size = sample_size
        self.seed = seed
        self.num_workers = num_workers
        self.force_regenerate = force_regenerate

        ensure_dir_exists(self.output_folder)
        self.metadata_path = os.path.join(self.output_folder, METADATA_DIR)
        ensure_dir_exists(self.metadata_path)

        if not os.path.exists(worker_script_path):
            raise FileNotFoundError(f"Worker script not found: {worker_script_path}")
        self.worker_script_hash = get_file_hash(worker_script_path)
        
        random.seed(self.seed) # Initialize random seed

    def _load_worker_module(self):
        """Loads the worker script as a module to call its functions."""
        module_name = os.path.splitext(os.path.basename(self.worker_script_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, self.worker_script_path)
        if not spec or not spec.loader:
            raise ImportError(f"Could not load worker script {self.worker_script_path}")
        worker_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(worker_module)
        return worker_module

    def _get_input_files(self):
        """Gets list of input files, applying sampling if specified."""
        # Assuming input files are .jsonl for now, can be parameterized
        input_files = sorted(glob.glob(os.path.join(self.input_folder, "*.jsonl"))) # Or other patterns
        if not input_files and self.input_folder and os.path.exists(self.input_folder) and os.path.isfile(self.input_folder):
             input_files = [self.input_folder] # Handle single input file case

        if self.sample_size is not None and self.sample_size < len(input_files):
            input_files = random.sample(input_files, self.sample_size)
        return input_files

    def _get_processed_item_metadata_path(self, input_item_identifier_hash):
        """Path for metadata of a specific processed item."""
        return os.path.join(self.metadata_path, f"{input_item_identifier_hash}.json")

    def _is_item_processed(self, input_item_identifier_hash, current_worker_script_hash):
        """Checks if an item was already processed with the current script version."""
        if self.force_regenerate:
            return False
        metadata_file = self._get_processed_item_metadata_path(input_item_identifier_hash)
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                # Check if script hash matches. Add other checks if needed (e.g., params).
                if metadata.get('worker_script_hash') == current_worker_script_hash:
                    print(f"Skipping item (hash: {input_item_identifier_hash[:8]}...) as it was already processed with the same script version.")
                    return True
            except json.JSONDecodeError:
                print(f"Warning: Could not decode metadata for item {input_item_identifier_hash}. Reprocessing.")
            except Exception as e:
                print(f"Warning: Error reading metadata for {input_item_identifier_hash}: {e}. Reprocessing.")
        return False

    def _mark_item_processed(self, input_item_identifier_hash, current_worker_script_hash, output_files_map=None):
        """Marks an item as processed by saving its metadata."""
        metadata_file = self._get_processed_item_metadata_path(input_item_identifier_hash)
        metadata = {
            'input_item_hash': input_item_identifier_hash,
            'worker_script_hash': current_worker_script_hash,
            'processed_timestamp': time.strftime("%Y-%m-%dT%H:%M:%S%Z"),
            'output_files': output_files_map or {} # e.g. {"raw": "path/to/raw", "processed": "path/to/processed"}
        }
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=4)
        except Exception as e:
            print(f"Error: Could not write metadata for item {input_item_identifier_hash}: {e}")


    def process_item(self, worker_module, item_data_or_path, item_index=None):
        """
        Processes a single item (which could be a file path or a line from a file)
        using the provided worker_module.
        The worker_module must have a 'execute_task(item_data, output_folder, base_input_item_hash, llm_client_instance)' function.
        Or, if worker processes whole files: 'process_file(input_filepath, output_folder, worker_script_hash, llm_client_instance)'
        This needs to be standardized based on how workers are written.
        For now, let's assume worker scripts process individual JSONL lines if input is a folder of JSONL.
        If input is a single file (like taxonomy.json), the worker script handles its specific structure.
        """
        # This is a placeholder for how a worker might be called.
        # The actual contract between executor and worker needs to be well-defined.
        # For example, worker scripts might take an input string (line) and return an output string/dict.
        # Or they might take an input file path and produce output files directly.

        # Let's refine this: Assume worker scripts have a main_process(config) function
        # where config contains input_path, output_folder, hashes, etc.
        # Or a more granular `process_single_item(item, config)` if the executor handles item iteration.

        # For this generic executor, let's assume the worker script has a function:
        # `run_worker(input_data_identifier, input_payload, output_dir_for_item, current_script_hash)`
        # where input_payload could be a line from JSONL or a path to a file.
        # The worker is responsible for creating its specific output files within output_dir_for_item.

        if not hasattr(worker_module, 'execute_task'):
            print(f"Worker script {self.worker_script_path} does not have a required 'execute_task' function.")
            return None # Or raise error

        # `item_data_or_path` could be a line from a JSONL file, or a path to a whole file
        # The `input_item_hash` should be for the specific piece of data being processed.
        if isinstance(item_data_or_path, str) and os.path.isfile(item_data_or_path): # if it's a file path
            input_item_hash = get_file_hash(item_data_or_path)
            input_payload = item_data_or_path # worker handles file reading
        else: # if it's data (e.g. a line from JSONL)
            input_item_hash = get_input_item_hash(item_data_or_path)
            input_payload = item_data_or_path

        if self._is_item_processed(input_item_hash, self.worker_script_hash):
            return {"status": "skipped", "input_hash": input_item_hash}

        print(f"Processing item (hash: {input_item_hash[:8]}...): {str(input_payload)[:100]}...")
        
        # Define a specific output directory for this item to avoid filename clashes if worker saves files
        item_output_dir = os.path.join(self.output_folder, input_item_hash[:2], input_item_hash) # Store by hash
        ensure_dir_exists(item_output_dir)

        try:
            # The worker script's 'execute_task' function will perform the actual generation
            # It might use the LLMAPIClient internally if it makes LLM calls.
            # It should return a dict of output file paths it created, relative to item_output_dir, or a status.
            # For simplicity, let's assume it returns True on success, False on failure for now.
            # A more robust approach: worker returns a dict of generated file paths or an error object.
            task_result = worker_module.execute_task(
                input_payload=input_payload,
                output_dir_for_item=item_output_dir,
                worker_script_hash=self.worker_script_hash,
                # llm_client=self.llm_client_instance # If executor manages a single client instance
            )
            
            if task_result and (isinstance(task_result, bool) or task_result.get("status") == "success"):
                self._mark_item_processed(input_item_hash, self.worker_script_hash, 
                                          output_files_map=task_result.get("output_files") if isinstance(task_result, dict) else None)
                print(f"Successfully processed item (hash: {input_item_hash[:8]}...).")
                return {"status": "success", "input_hash": input_item_hash, "output_location": item_output_dir}
            else:
                print(f"Worker task failed for item (hash: {input_item_hash[:8]}...). Error: {task_result.get('error') if isinstance(task_result, dict) else 'Unknown'}")
                return {"status": "failed", "input_hash": input_item_hash, "error": task_result.get('error') if isinstance(task_result, dict) else 'Worker did not return success'}

        except Exception as e:
            print(f"Exception during worker task for item (hash: {input_item_hash[:8]}...): {e}")
            # Optionally log traceback: import traceback; traceback.print_exc()
            return {"status": "exception", "input_hash": input_item_hash, "error": str(e)}


    def run(self):
        print(f"Starting ResumableExecutor for worker: {self.worker_script_path}")
        print(f"Input folder: {self.input_folder}, Output folder: {self.output_folder}")
        print(f"Worker script hash: {self.worker_script_hash}")
        if self.sample_size:
            print(f"Sample size: {self.sample_size}, Seed: {self.seed}")
        
        worker_module = self._load_worker_module()
        input_files = self._get_input_files()

        if not input_files:
            if self.input_folder and not os.path.exists(self.input_folder): # Special case for initial taxonomy which has no input_folder
                 if hasattr(worker_module, 'execute_task'): # Taxonomy like scripts may not have an "input item"
                    print("No input files found, but worker has 'execute_task'. Assuming worker handles its own input (e.g. initial generation).")
                    self.process_item(worker_module, item_data_or_path="initial_generation_task_placeholder", item_index=0) # Special call
                 else:
                    print("No input files found to process.")
                 return
            elif not os.path.exists(self.input_folder) and self.input_folder: # if input_folder was specified but doesn't exist
                 print(f"Error: Input folder '{self.input_folder}' does not exist.")
                 return
            # If input_folder is None or empty, and worker doesn't handle initial generation, then nothing to do.
            elif not hasattr(worker_module, 'execute_task_no_input'): # A different entry point for no-input tasks
                 print("No input files found and worker does not seem to support initial generation without input items.")
                 return


        items_to_process = []
        if input_files and hasattr(worker_module, 'parse_input_file_to_items'):
            # Worker provides a function to parse its specific file format into processable items
            for input_file_path in input_files:
                print(f"Loading items from: {input_file_path}")
                items_from_file = worker_module.parse_input_file_to_items(input_file_path)
                items_to_process.extend(items_from_file)
            if self.sample_size and self.sample_size < len(items_to_process): # If sampling lines from combined files
                 items_to_process = random.sample(items_to_process, self.sample_size)

        elif input_files: # Default: treat each file as an item if worker doesn't parse lines
            items_to_process = input_files
        elif hasattr(worker_module, 'execute_task_no_input'): # For workers that don't need file inputs (e.g. taxonomy)
             items_to_process.append("initial_generation_task") # Placeholder item
        else:
            print("No input items to process based on current worker and input folder configuration.")
            return

        if not items_to_process:
            print("No items to process after loading and sampling.")
            return

        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = [executor.submit(self.process_item, worker_module, item, i) for i, item in enumerate(items_to_process)]
            
            for future in as_completed(futures):
                try:
                    result = future.result() # result is already printed in process_item
                    # Aggregate results if needed
                except Exception as e:
                    print(f"A task generated an unhandled exception: {e}")
        
        print("ResumableExecutor run finished.")

def main():
    parser = argparse.ArgumentParser(description="Resumable Executor for data generation tasks.")
    parser.add_argument("--worker-script", required=True, help="Path to the worker Python script.")
    parser.add_argument("--input-folder", default=None, help="Path to the folder containing input files (e.g., JSONL). Can be a single file for some workers.")
    parser.add_argument("--output-folder", required=True, help="Path to the folder where output will be stored.")
    parser.add_argument("--sample-size", type=int, default=None, help="Randomly sample N input items (files or lines) for processing.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed for sampling.")
    parser.add_argument("--num-workers", type=int, default=DEFAULT_NUM_WORKERS, help="Number of concurrent worker processes/threads for item processing.")
    parser.add_argument("--force-regenerate", action='store_true', help="Force regeneration even if item metadata suggests it was processed.")

    args = parser.parse_args()

    # A simple worker script example for testing the executor:
    # File: dummy_worker.py
    # def execute_task(input_payload, output_dir_for_item, worker_script_hash):
    #     print(f"Dummy worker processing: {input_payload} in {output_dir_for_item}")
    #     output_filepath = os.path.join(output_dir_for_item, "output.txt")
    #     with open(output_filepath, "w") as f:
    #         f.write(f"Processed: {input_payload}\nScript Hash: {worker_script_hash}")
    #     return {"status": "success", "output_files": {"main_output": output_filepath }}
    #
    # def parse_input_file_to_items(input_filepath): # Example if items are lines in a file
    #    items = []
    #    with open(input_filepath, 'r') as f:
    #        for line in f: items.append(line.strip())
    #    return items


    if args.worker_script == "dummy_worker.py" and not os.path.exists("dummy_worker.py"):
        print("Please create a 'dummy_worker.py' for testing the executor, or specify a real worker.")
        print("Example dummy_worker.py content:")
        print("""
import os
def execute_task(input_payload, output_dir_for_item, worker_script_hash, **kwargs): # Added **kwargs
    print(f"Dummy worker processing: {input_payload} in {output_dir_for_item}")
    output_filename = "output.txt"
    if isinstance(input_payload, str) and ".jsonl" in input_payload: # if it's a file path
        output_filename = os.path.basename(input_payload).replace(".jsonl", "_output.txt")

    output_filepath = os.path.join(output_dir_for_item, output_filename)
    ensure_dir_exists(os.path.dirname(output_filepath)) # Ensure dir exists before writing
    with open(output_filepath, "w") as f:
        f.write(f"Processed item: {input_payload}\nUsing script hash: {worker_script_hash}")
    return {"status": "success", "output_files": {"main_output": output_filepath }}

def parse_input_file_to_items(input_filepath): # Example if items are lines in a file
    items = []
    with open(input_filepath, 'r') as f:
        for i, line in enumerate(f):
            # For JSONL, each line is a JSON object
            try:
                items.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                print(f"Skipping malformed JSON line {i+1} in {input_filepath}")
    return items
    
def ensure_dir_exists(path): # Helper, as it's used here
    os.makedirs(path, exist_ok=True)
import json # For dummy worker
""")
        return

    executor = ResumableExecutor(
        worker_script_path=args.worker_script,
        input_folder=args.input_folder,
        output_folder=args.output_folder,
        sample_size=args.sample_size,
        seed=args.seed,
        num_workers=args.num_workers,
        force_regenerate=args.force_regenerate
    )
    executor.run()

if __name__ == "__main__":
    main()

```
