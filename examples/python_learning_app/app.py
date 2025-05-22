import Flask
from flask import render_template, request, redirect, url_for, json, abort
import os
import glob

app = Flask(__name__)

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
        return render_template('lesson.html', lesson=lesson, code=lesson.get('boilerplate', ''))
    return render_template("404.html"), 404

@app.route('/lesson/<lesson_id>/submit', methods=['POST'])
def submit_lesson(lesson_id):
    """Handles submission of code for a lesson, executes it, and shows results."""
    lesson = next((l for l in LESSONS if l['id'] == lesson_id), None)
    if not lesson:
        abort(404)

    code = request.form.get('code', '')
    results = []
    error_message = None
    user_scope = {}

    try:
        # Execute the user's code
        exec(code, {}, user_scope)
    except Exception as e:
        error_message = str(e)

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
            
            results.append({
                "expression": expression,
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "error": eval_error
            })

    return render_template('lesson.html', lesson=lesson, results=results, code=code, error_message=error_message)

if __name__ == '__main__':
    app.run(debug=True)
