import Flask
from flask import render_template, request, redirect, url_for, json, abort, session, jsonify
import os
import glob
from datetime import datetime
import openai # Added for hint generation

app = Flask(__name__)
app.secret_key = 'dev_secret_key_for_flask_session' # Should be changed for production

LESSONS = []

def load_lessons():
    """Loads all lesson .json files from the lessons/ directory."""
    lessons_dir = os.path.join(os.path.dirname(__file__), 'lessons')
    lesson_files = glob.glob(os.path.join(lessons_dir, '*.json'))
    loaded_lessons = []
    for file_path in lesson_files:
        with open(file_path, 'r') as f:
            try:
                lesson_data = json.load(f)
                loaded_lessons.append(lesson_data)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {file_path}: {e}")
    # Sort lessons, e.g., by title or a dedicated 'order' field if available
    # For now, let's assume an 'id' or 'title' can be used for basic ordering if needed
    # loaded_lessons.sort(key=lambda x: x.get('title', '')) # Example sorting
    return loaded_lessons

LESSONS = load_lessons()

@app.route('/')
def home():
    """Renders the home page listing all available lessons."""
    return render_template('home.html', lessons=LESSONS)

@app.route('/lesson/<lesson_id>')
def view_lesson(lesson_id):
    """Renders a specific lesson page."""
    lesson = next((l for l in LESSONS if l['id'] == lesson_id), None)
    if lesson:
        lesson_session_key = f"lesson_{lesson_id}"
        failure_count = session.get('failures', {}).get(lesson_session_key, 0)
        return render_template('lesson.html', lesson=lesson, code=lesson.get('boilerplate', ''), results=None, error_message=None, failure_count=failure_count)
    return render_template("404.html"), 404

@app.route('/lesson/<lesson_id>/submit', methods=['POST'])
def submit_lesson(lesson_id):
    """Handles submission of code for a lesson, executes it, and shows results."""
    session.setdefault('failures', {})
    session.setdefault('failure_details', {})
    lesson_session_key = f"lesson_{lesson_id}"

    lesson = next((l for l in LESSONS if l['id'] == lesson_id), None)
    if not lesson:
        abort(404)

    code = request.form.get('code', '')
    results = []
    error_message = None
    user_scope = {}
    all_tests_passed = True # Assume success initially

    try:
        # Execute the user's code
        exec(code, {}, user_scope)
    except Exception as e:
        error_message = str(e)
        all_tests_passed = False # Execution error means failure

    if not error_message:
        for test_case in lesson.get('tests', []):
            expression = test_case['expression']
            expected = test_case['expected']
            actual = None
            passed = False
            eval_error = None

            try:
                actual = eval(expression, {}, user_scope)
                passed = (actual == expected)
            except Exception as e:
                eval_error = str(e)
                passed = False # Evaluation error in a test means that test failed
            
            results.append({
                "expression": expression,
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "error": eval_error
            })
            if not passed:
                all_tests_passed = False # Any single test failure means overall failure
    else: # If there was an execution error, all_tests_passed is already False
        pass


    if all_tests_passed and not error_message:
        session['failures'][lesson_session_key] = 0
        session['failure_details'].pop(lesson_session_key, None)
    else:
        current_failures = session['failures'].get(lesson_session_key, 0)
        current_failures += 1
        session['failures'][lesson_session_key] = current_failures

        if lesson_session_key not in session['failure_details']:
            session['failure_details'][lesson_session_key] = []
        
        failure_log_entry = {
            "code": code,
            "results": results,
            "execution_error": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        session['failure_details'][lesson_session_key].append(failure_log_entry)
        session['failure_details'][lesson_session_key] = session['failure_details'][lesson_session_key][-5:] # Keep last 5
    
    # Make sure session changes are saved
    session.modified = True 

    failure_count = session['failures'].get(lesson_session_key, 0)
    return render_template('lesson.html', lesson=lesson, results=results, code=code, error_message=error_message, failure_count=failure_count)

@app.route('/lesson/<lesson_id>/get_hint', methods=['POST'])
def get_hint(lesson_id):
    # 1. Check if user is eligible for a hint (failure threshold)
    lesson_session_key = f"lesson_{lesson_id}"
    failure_count = session.get('failures', {}).get(lesson_session_key, 0)
    HINT_THRESHOLD = 3 

    if failure_count < HINT_THRESHOLD:
        return jsonify({"error": "Hint not available yet. Keep trying!"}), 403

    # 2. Retrieve lesson details and failure logs
    # LESSONS is already loaded globally
    lesson = next((l for l in LESSONS if l['id'] == lesson_id), None)
    if not lesson:
        return jsonify({"error": "Lesson not found."}), 404

    failure_details_for_lesson = session.get('failure_details', {}).get(lesson_session_key, [])
    if not failure_details_for_lesson:
        return jsonify({"error": "No failure details found to generate a hint."}), 404
    
    last_failure = failure_details_for_lesson[-1] # Get the most recent failure

    # 3. Construct the prompt for OpenAI
    prompt_parts = [
        f"Problem Description: {lesson['description']}",
        f"Problem Statement: {lesson['problem']}",
        "---",
        f"User's Last Submitted Code:\n```python\n{last_failure['code']}\n```",
        "---",
        "Recent Errors/Failed Tests:"
    ]

    # Add summary of errors from last_failure
    if last_failure.get('execution_error'):
        prompt_parts.append(f"- Execution Error: {last_failure['execution_error']}")
    
    if last_failure.get('results'):
        failed_tests_summary = []
        for test_res in last_failure['results']:
            if not test_res['passed']:
                failed_tests_summary.append(
                    f"  - Test: `{test_res['expression']}` Expected: `{test_res['expected']}`, Got: `{test_res['actual']}`"
                    f"{(' (Eval Error: ' + test_res['error'] + ')') if test_res.get('error') else ''}"
                )
        if failed_tests_summary:
            prompt_parts.append("- Failed Tests:")
            prompt_parts.extend(failed_tests_summary)
    
    prompt_parts.append("---")
    prompt_parts.append("Instruction: You are a friendly and encouraging Python programming tutor. Based on the problem, the user's code, and their recent errors, provide a concise hint (not the full solution) to help them identify their mistake or guide them towards the correct approach. Focus on the most likely issue. Do not provide the complete corrected code. Be encouraging.")
    
    full_prompt = "\n".join(prompt_parts)

    # 4. Call OpenAI API
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            # Log this server-side, don't expose key absence to client directly for security.
            print("ERROR: OPENAI_API_KEY environment variable not set.")
            return jsonify({"error": "Hint service configuration issue."}), 500
        
        client = openai.OpenAI(api_key=api_key) # Use the new client
        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful Python tutor providing hints."},
                {"role": "user", "content": full_prompt}
            ]
        )
        hint = chat_completion.choices[0].message.content
        
        # Optional: Log the hint generation for auditing/improvement
        # print(f"Generated hint for lesson {lesson_id}: {hint}")

        return jsonify({"hint": hint})

    except Exception as e:
        print(f"Error calling OpenAI API: {e}") # Log the actual error server-side
        return jsonify({"error": "Could not retrieve a hint at this time. Please try again later."}), 500

if __name__ == '__main__':
    app.run(debug=True)
