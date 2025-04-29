from flask import Flask, request, jsonify
import joblib
import numpy as np

app = Flask(__name__)

# Load the pre-trained model (make sure the path is correct)
model = joblib.load('assignment_model.pkl')

# Function to calculate skill match count and percentage
def calculate_skill_match(skills_required, employee_skills):
    matched_skills = set(skills_required) & set(employee_skills)
    skill_match_count = len(matched_skills)
    skill_match_percentage = (skill_match_count / len(skills_required)) * 100
    return skill_match_count, skill_match_percentage

# Function to create features for prediction
def create_features_for_prediction(task_data, employee_data):
    # Task data
    task_priority = {'HIGH': 2, 'MEDIUM': 1, 'LOW': 0}  # Mapping priorities to numbers
    task_priority_value = task_priority.get(task_data['priority'], 0)
    deadline_hours = task_data['deadline_hours']
    num_skills_required = len(task_data['skills_required'])

    # For each employee, create a list of features
    features_list = []

    for employee in employee_data:
        # Employee data
        employee_skills = employee['skills']
        employee_available_bandwidth = employee['available_bandwidth']

        # Skill match calculation
        skill_match_count, skill_match_percentage = calculate_skill_match(task_data['skills_required'], employee_skills)

        # Generate features for prediction
        features = [
            task_priority_value,              # Task priority
            deadline_hours,                   # Deadline in hours
            num_skills_required,              # Number of skills required for task
            skill_match_count,                # How many skills match
            employee_available_bandwidth,     # Employee bandwidth available
            skill_match_percentage           # Skill match percentage
        ]

        features_list.append(features)

    return features_list

# API endpoint to predict assignment
@app.route('/predict-assignment', methods=['POST'])
def predict_assignment():
    try:
        data = request.get_json()  # Parse incoming JSON

        # Validate input
        if 'task_id' not in data or 'task_title' not in data or 'skills_required' not in data:
            return jsonify({"error": "Invalid input format. Missing required fields."}), 400

        task_data = {
            'task_id': data['task_id'],
            'task_title': data['task_title'],
            'skills_required': data['skills_required'],
            'priority': data.get('priority', 'LOW'),  # Default to 'LOW' if not provided
            'deadline_hours': data.get('deadline_hours', 24)  # Default to 24 hours if not provided
        }

        employee_data = data['candidate_employees']

        # Create features for prediction
        features = create_features_for_prediction(task_data, employee_data)

        # Predict using the trained model (input data needs to be an array of features)
        predictions = model.predict(features)

        # Prepare the response with the best employee ID and details
        best_employee_index = np.argmax(predictions)  # Get the index of the predicted employee
        best_employee = employee_data[best_employee_index]

        # Return the best employee details
        response = {
            'assigned_employee_id': best_employee['user_id'],
            'assigned_employee_name': f"Employee {best_employee['user_id']}",  # You can customize this as per your data
            'assigned_employee_skills': best_employee['skills'],
            'available_bandwidth': best_employee['available_bandwidth']
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
