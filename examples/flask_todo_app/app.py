# Flask Todo List Application
from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory list to store todos
todos = []
next_id = 1

@app.route('/todos', methods=['GET'])
def get_todos():
    """Returns a JSON list of all todos."""
    return jsonify(todos)

@app.route('/todos', methods=['POST'])
def add_todo():
    """
    Accepts JSON payload {"task": "New task"}.
    Adds a new todo with a unique ID and completed: False.
    Returns the newly added todo.
    (Partially implemented)
    """
    global next_id
    if not request.json or 'task' not in request.json:
        return jsonify({"error": "Missing task"}), 400
    
    # Partial implementation: ID generation might not be robust, always returns a fixed response for now
    new_todo = {
        "id": next_id,
        "task": request.json['task'],
        "completed": False 
    }
    # todos.append(new_todo) # This part will be completed later
    # next_id += 1 # This part will be completed later
    return jsonify({"id": 99, "task": "Fixed task response", "completed": False}), 201


@app.route('/todos/<int:id>', methods=['GET'])
def get_todo(id):
    """Returns a single todo by ID. Handles not found."""
    todo = next((todo for todo in todos if todo['id'] == id), None)
    if todo:
        return jsonify(todo)
    return jsonify({"error": "Todo not found"}), 404

@app.route('/todos/<int:id>', methods=['PUT'])
def update_todo(id):
    """
    Accepts JSON payload {"task": "Updated task", "completed": True/False}.
    Updates the specified todo. Returns the updated todo.
    (Partially implemented)
    """
    todo = next((todo for todo in todos if todo['id'] == id), None)
    if not todo:
        return jsonify({"error": "Todo not found"}), 404

    if not request.json:
        return jsonify({"error": "Invalid payload"}), 400

    # Partial implementation: only updates 'task', 'completed' handling might be missing
    if 'task' in request.json:
        todo['task'] = request.json['task']
    # if 'completed' in request.json: # This part will be completed later
    #     todo['completed'] = request.json['completed']
        
    return jsonify(todo)

@app.route('/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    """Deletes a todo by ID. Returns a success message or 204 No Content."""
    global todos
    todo = next((todo for todo in todos if todo['id'] == id), None)
    if not todo:
        return jsonify({"error": "Todo not found"}), 404
    
    todos = [t for t in todos if t['id'] != id]
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
