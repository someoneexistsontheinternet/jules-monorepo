# Interactive Python Learning Platform

This application is a simple, Flask-based interactive platform for learning Python. Users can browse lessons, write Python code to solve problems, and get immediate feedback based on predefined tests. It currently features 10 lessons covering fundamental Python concepts from variables and strings to functions, file I/O, and basic external library usage.

## Features

- Interactive Python coding challenges.
- 10 lessons covering topics from variables to basic external library usage.
- Instant feedback by running code against predefined tests.
- User code is automatically saved in the browser's local storage as you type.
- Simple and clean user interface with custom styling.
- Easy to add new lessons via JSON files.
- AI-powered hints: After 3 unsuccessful attempts on a lesson, a hint option appears, providing guidance from an AI tutor (powered by OpenAI's GPT model).

## Configuration

### AI Hint System (Optional)

This platform includes an AI-powered hint system that uses the OpenAI API to provide guidance after multiple failed attempts on a lesson. To enable this feature, you need to:

1.  Obtain an API key from [OpenAI](https://openai.com/apis/).
2.  Set the `OPENAI_API_KEY` environment variable in your terminal before running the Flask application:

    ```bash
    export OPENAI_API_KEY='your_openai_api_key_here'
    ```
    (On Windows, use `set OPENAI_API_KEY=your_openai_api_key_here`)

If this key is not set, the hint feature will be disabled (the button may still appear, but requests for hints will result in an error message indicating a configuration issue).

## Setup and Run

Follow these steps to get the application running locally:

### 1. Create and Activate a Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies and isolate this project from your global Python setup.

Navigate to the `examples/python_learning_app` directory:
```bash
cd examples/python_learning_app
```

Create a virtual environment:
```bash
python3 -m venv venv
```

Activate the virtual environment:
*   On macOS and Linux:
    ```bash
    source venv/bin/activate
    ```
*   On Windows (Command Prompt or PowerShell):
    ```bash
    venv\Scripts\activate
    ```

### 2. Install Dependencies

With the virtual environment activated, install the required packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Configure Flask Environment Variables (Optional but Recommended)

For a better development experience, you can set the following environment variables:

*   `FLASK_APP`: Specifies the entry point of your application.
*   `FLASK_ENV`: Sets the environment (e.g., `development` for debug mode).

On macOS and Linux:
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
```

On Windows (Command Prompt):
```bash
set FLASK_APP=app.py
set FLASK_ENV=development
```
On Windows (PowerShell):
```bash
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"
```

### 4. Run the Flask Application

Once the dependencies are installed (and environment variables optionally set), you can run the application:

```bash
flask run
```
Or, if you prefer to run it as a Python module:
```bash
python -m flask run
```

The application will typically be available at `http://127.0.0.1:5000/`.

## Adding New Lessons

To add a new lesson to the platform:

1.  Create a new JSON file (e.g., `lesson2.json`) inside the `examples/python_learning_app/lessons/` directory.
2.  Follow the structure of `lesson1.json` to define your lesson:
    ```json
    {
      "id": "unique-lesson-identifier", 
      "title": "Lesson Title",
      "description": "A brief description of what the lesson covers.",
      "problem": "The problem statement or task for the user to solve.",
      "boilerplate": "def function_name(param1, param2):\n  # Your initial code here\n  pass",
      "tests": [
        {"expression": "function_name(arg1, arg2)", "expected": "expected_output"},
        {"expression": "function_name(another_arg1, another_arg2)", "expected": "another_expected_output"}
      ]
    }
    ```
    *   `id`: A unique string identifier for the lesson (used in the URL).
    *   `title`: The display title of the lesson.
    *   `description`: A short summary of the lesson's content.
    *   `problem`: The programming challenge or question.
    *   `boilerplate`: Initial code provided to the user in the editor.
    *   `tests`: A list of test cases. Each test case should have:
        *   `expression`: A Python expression (string) that will be `eval()`uated using the user's submitted code. This typically calls the function the user is supposed to define.
        *   `expected`: The expected result of evaluating the `expression`.

The application will automatically load any new `.json` files from the `lessons/` directory upon startup. You may need to restart the Flask server to see newly added lessons.
