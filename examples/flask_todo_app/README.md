# Flask Todo List API

This is a simple Todo List API built with Flask. It allows users to manage a list of tasks.

## Setup and Run

### 1. Create and Activate a Virtual Environment

It's recommended to use a virtual environment to manage project dependencies.

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 2. Install Dependencies

Install the required packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Run the Flask Application

To start the Flask development server:

```bash
export FLASK_APP=app.py # or set FLASK_APP=app.py on Windows
export FLASK_ENV=development # Optional: for development mode
python -m flask run
```

The API will typically be available at `http://127.0.0.1:5000/`.

## API Endpoints

*   `GET /todos`: Get all todos.
*   `POST /todos`: Add a new todo.
    *   Payload: `{"task": "Your task description"}`
*   `GET /todos/<id>`: Get a specific todo by its ID.
*   `PUT /todos/<id>`: Update a specific todo.
    *   Payload: `{"task": "Updated description", "completed": true/false}`
*   `DELETE /todos/<id>`: Delete a specific todo.

## Running Tests

Tests are written using `pytest`. To run the tests:

```bash
pytest
```
(Note: Test details will be fully available once `tests/test_app.py` is implemented).
