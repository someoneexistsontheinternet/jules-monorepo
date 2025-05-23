import argparse
import asyncio

# Import the main async functions from the respective scripts
# These imports assume the scripts are in the same directory or accessible via PYTHONPATH
try:
    from taxonomy_generator import main as taxonomy_main
except ImportError:
    print("Warning: Could not import taxonomy_generator.py. 'taxonomy' stage will not be available.")
    taxonomy_main = None

try:
    from finalize_taxonomy import main as finalize_taxonomy_main
except ImportError:
    print("Warning: Could not import finalize_taxonomy.py. 'finalize_taxonomy' stage will not be available.")
    finalize_taxonomy_main = None

try:
    from subject_generator import main as subject_main
except ImportError:
    print("Warning: Could not import subject_generator.py. 'subjects' stage will not be available.")
    subject_main = None

try:
    from syllabus_generator import main as syllabus_main
except ImportError:
    print("Warning: Could not import syllabus_generator.py. 'syllabi' stage will not be available.")
    syllabus_main = None

async def run_stage(stage_name):
    """Helper to run an async main function from an imported module."""
    print(f"--- Attempting to run stage: {stage_name} ---")
    if stage_name == "taxonomy" and taxonomy_main:
        await taxonomy_main()
    elif stage_name == "finalize_taxonomy" and finalize_taxonomy_main:
        # finalize_taxonomy.main is synchronous, so no await needed directly here,
        # but if it were async, it would be: await finalize_taxonomy_main()
        # For now, assuming it's simple enough not to need full async conversion itself.
        # If it involves heavy I/O, it should also be made async or run in a thread.
        # For this iteration, we'll call its current main directly.
        # If finalize_taxonomy.main was made async:
        # await finalize_taxonomy_main() 
        # else:
        finalize_taxonomy_main() # Assuming it's still synchronous
    elif stage_name == "subjects" and subject_main:
        await subject_main()
    elif stage_name == "syllabi" and syllabus_main:
        await syllabus_main()
    else:
        print(f"Error: Stage '{stage_name}' is not defined, not imported correctly, or its main function is missing.")
        if stage_name == "taxonomy" and not taxonomy_main:
             print("taxonomy_generator.py might be missing or has import errors.")
        elif stage_name == "finalize_taxonomy" and not finalize_taxonomy_main:
             print("finalize_taxonomy.py might be missing or has import errors.")
        # ... add similar checks for other stages
        return False
    print(f"--- Stage '{stage_name}' completed ---")
    return True

def main():
    parser = argparse.ArgumentParser(description="Unified entry script for the GLAN pipeline.")
    parser.add_argument(
        "stage",
        choices=["taxonomy", "finalize_taxonomy", "subjects", "syllabi", "all"],
        help="The pipeline stage to run. 'all' runs them in sequence (taxonomy -> finalize_taxonomy -> subjects -> syllabi)."
    )
    # Add other arguments here if needed, e.g., --force for specific stages,
    # or --discipline_name for subject-specific operations if we extend that.

    args = parser.parse_args()

    stages_to_run = []
    if args.stage == "all":
        stages_to_run = ["taxonomy", "finalize_taxonomy", "subjects", "syllabi"]
    else:
        stages_to_run = [args.stage]

    # For stages that are async, they need to be run within an asyncio event loop.
    # Synchronous stages can be called directly.
    # This script's main function itself is synchronous, but it calls asyncio.run for async stages.

    for stage_name in stages_to_run:
        print(f"\n>>> Preparing to run stage: {stage_name} <<<")
        # finalize_taxonomy.main is currently synchronous.
        # Other mains (taxonomy_main, subject_main, syllabus_main) are async.
        if stage_name == "finalize_taxonomy":
            if finalize_taxonomy_main:
                print(f"--- Running synchronous stage: {stage_name} ---")
                finalize_taxonomy_main() # Direct call
                print(f"--- Stage '{stage_name}' completed ---")
            else:
                print(f"Error: Stage '{stage_name}' not available (finalize_taxonomy.main missing).")
                break # Stop processing if a stage in 'all' is missing
        else:
            # Run async stages using asyncio.run()
            # We need to get the specific async function for the stage
            async_stage_func = None
            if stage_name == "taxonomy" and taxonomy_main:
                async_stage_func = taxonomy_main
            elif stage_name == "subjects" and subject_main:
                async_stage_func = subject_main
            elif stage_name == "syllabi" and syllabus_main:
                async_stage_func = syllabus_main
            
            if async_stage_func:
                try:
                    print(f"--- Running asynchronous stage: {stage_name} ---")
                    asyncio.run(async_stage_func())
                    print(f"--- Stage '{stage_name}' completed ---")
                except Exception as e:
                    print(f"Error running async stage {stage_name}: {e}")
                    break # Stop processing if an error occurs
            else:
                print(f"Error: Async stage '{stage_name}' not available or its main function is missing.")
                if stage_name == "taxonomy" and not taxonomy_main:
                     print("taxonomy_generator.py might be missing or has import errors.")
                elif stage_name == "subjects" and not subject_main:
                     print("subject_generator.py might be missing or has import errors.")
                elif stage_name == "syllabi" and not syllabus_main:
                     print("syllabus_generator.py might be missing or has import errors.")
                break # Stop processing

        print(f">>> Stage {stage_name} finished processing. <<<")
    
    print("\nPipeline execution finished.")


if __name__ == "__main__":
    print("--- GLAN Pipeline Runner ---")
    # Check if finalize_taxonomy.main is synchronous and adjust run_stage or main logic if it's made async later.
    # Currently, finalize_taxonomy.py's main is synchronous.
    # The other generator scripts have async main functions.
    
    # A small check to ensure the user understands that finalize_taxonomy.main is synchronous.
    if finalize_taxonomy_main and not asyncio.iscoroutinefunction(finalize_taxonomy_main):
        print("Note: 'finalize_taxonomy' stage is currently synchronous.")
    
    main()
```
