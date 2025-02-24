import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS for cross-origin requests
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        return jsonify({"message": "Welcome to the Attendance API! Use /get-attendance with POST."})
    return "Welcome to the Attendance API! Send a POST request to /get-attendance with username and password."

@app.route('/get-attendance', methods=['POST'])
def get_attendance():
    # Extract username and password from request
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    # Validate required fields
    if not username or not password:
        return jsonify({"error": "Username and password are required!"}), 400
    
    try:
        # Create a session and login
        session = requests.Session()
        login_url = "https://sctce.etlab.in/user/login"
        login_payload = {"LoginForm[username]": username, "LoginForm[password]": password}
        
        # Add timeout to prevent hanging requests
        login_response = session.post(login_url, data=login_payload, timeout=10)
        
        # Check if login was successful
        if login_response.url == login_url:
            return jsonify({"error": "Login failed! Please check your credentials."}), 401
        
        # Get attendance data
        attendance_dict = get_daily_attendance(session)
        
        # Get subject-wise attendance
        subject_attendance = get_subject_attendance(session)
        
        # Get timetable
        timetable_dict = get_timetable(session)
        
        # Return compiled data
        return jsonify({
            "attendance": attendance_dict,
            "subject_attendance": subject_attendance,
            "timetable": timetable_dict
        })
    
    except requests.Timeout:
        return jsonify({"error": "Request timed out. Please try again later."}), 504
    except requests.ConnectionError:
        return jsonify({"error": "Could not connect to the server. Please check your internet connection."}), 503
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

def get_daily_attendance(session):
    """Extract daily attendance data from the attendance page"""
    attendance_url = "https://sctce.etlab.in/student/attendance"
    attendance_response = session.get(attendance_url, timeout=10)
    attendance_soup = BeautifulSoup(attendance_response.text, "html.parser")
    
    attendance_dict = {}
    attendance_table = attendance_soup.find("table", {"id": "itsthetable"})
    
    if attendance_table:
        rows = attendance_table.find("tbody").find_all("tr")
        for row in rows:
            date_element = row.find("th")
            if date_element:
                # Extract and format date (DD-MM-YYYY to YYYY-MM-DD)
                date_str = date_element.text.strip()
                try:
                    date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    # If date format is different, use as is
                    formatted_date = date_str
                
                # Extract attendance statuses
                periods = row.find_all("td")
                attendance_statuses = []
                for period in periods:
                    class_attr = period.get("class")
                    if class_attr:
                        status = class_attr[0].replace("span1 ", "")
                        # Map the status values to standard formats
                        if status == "present":
                            attendance_statuses.append("present")
                        elif status == "absent":
                            attendance_statuses.append("absent")
                        else:
                            attendance_statuses.append(status)
                
                # Only add non-empty attendance records
                if attendance_statuses:
                    attendance_dict[formatted_date] = attendance_statuses
    
    return attendance_dict

def get_subject_attendance(session):
    """Extract subject-wise attendance percentages"""
    # Try first URL
    subject_url = "https://sctce.etlab.in/ktuacademics/student/viewattendancesubject/81"
    subject_response = session.get(subject_url, timeout=10)
    
    # If not successful, try alternate URL
    if "Access Denied" in subject_response.text:
        subject_url = "https://sctce.etlab.in/student/attendance/subject"
        subject_response = session.get(subject_url, timeout=10)
    
    subject_soup = BeautifulSoup(subject_response.text, "html.parser")
    subject_attendance = {}
    
    # Try to find any table with attendance data
    subject_tables = subject_soup.find_all("table")
    for subject_table in subject_tables:
        if not subject_table:
            continue
        
        # Look for rows with subject data
        subject_rows = subject_table.find_all("tr")
        for row in subject_rows:
            cols = row.find_all("td")
            # Check if this row has enough columns for subject data
            if len(cols) >= 2:
                # Try different column positions for subject name and attendance
                for i in range(len(cols) - 1):
                    subject_name = cols[i].text.strip()
                    attendance_value = cols[i+1].text.strip()
                    
                    # Look for percentage pattern
                    percentage_match = re.search(r'(\d+(?:\.\d+)?)%?', attendance_value)
                    
                    if subject_name and percentage_match:
                        percentage = percentage_match.group(1)
                        # Ensure percentage has % symbol
                        if not attendance_value.endswith('%'):
                            attendance_value = f"{percentage}%"
                        subject_attendance[subject_name] = attendance_value
                        break
    
    # If no data found, check for alternate table format
    if not subject_attendance:
        for table in subject_tables:
            rows = table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 5:  # Typical format for KTU attendance
                    subject_name = cols[3].text.strip() if len(cols) > 3 else ""
                    attendance_value = cols[4].text.strip() if len(cols) > 4 else ""
                    
                    if subject_name and attendance_value:
                        # Add % if not present
                        if not attendance_value.endswith('%'):
                            attendance_value = f"{attendance_value}%"
                        subject_attendance[subject_name] = attendance_value
    
    return subject_attendance

def get_timetable(session):
    """Extract timetable data"""
    timetable_url = "https://sctce.etlab.in/student/timetable"
    timetable_response = session.get(timetable_url, timeout=10)
    timetable_soup = BeautifulSoup(timetable_response.text, "html.parser")
    
    timetable_dict = {}
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    # Find timetable
    timetable_table = timetable_soup.find("table")
    
    if timetable_table:
        timetable_rows = timetable_table.find_all("tr")
        for row in timetable_rows:
            cells = row.find_all("td")
            if not cells:
                continue
            
            # First cell might contain day name
            day = cells[0].text.strip()
            
            # If day not found, try to infer from position
            if not day and len(timetable_dict) < len(days_of_week):
                day = days_of_week[len(timetable_dict)]
            
            # Skip if no valid day found
            if not day or day not in days_of_week:
                continue
            
            # Extract periods (skip first cell which is the day name)
            periods = cells[1:] if len(cells) > 1 else []
            subjects = []
            
            for period in periods:
                subject = period.text.strip().replace("\n", " ")
                # Clean up the subject text
                subject = re.sub(r'\s+', ' ', subject)
                
                if not subject:
                    subject = "No Class"
                    
                # Try to extract just the subject name without codes
                match = re.search(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', subject)
                if match:
                    cleaned_subject = match.group(0)
                    if len(cleaned_subject) > 3:  # Ensure it's not just a short code
                        subject = cleaned_subject
                
                subjects.append(subject)
            
            # Only add days with actual periods
            if subjects:
                timetable_dict[day] = subjects
    
    # If timetable is empty, provide a default structure
    if not timetable_dict:
        for day in days_of_week:
            timetable_dict[day] = ["No Data Available"] * 6
    
    return timetable_dict

# Provide mock data for testing when real data can't be fetched
@app.route('/mock-data', methods=['GET'])
def get_mock_data():
    mock_data = {
        "attendance": {
            "2025-02-24": ["present", "absent", "present"],
            "2025-02-23": ["present", "present", "present"],
            "2025-02-22": ["absent", "absent", "present"],
            "2025-02-21": ["present", "present", "absent"],
            "2025-02-20": ["present", "absent", "present"]
        },
        "subject_attendance": {
            "Mathematics": "85%",
            "Physics": "90%",
            "Chemistry": "78%",
            "English": "92%",
            "Computer Science": "94%",
            "Biology": "72%"
        },
        "timetable": {
            "Monday": ["Mathematics", "Physics", "Computer Science"],
            "Tuesday": ["Chemistry", "English", "Biology"],
            "Wednesday": ["Physics", "Computer Science", "Mathematics"],
            "Thursday": ["English", "Biology", "Chemistry"],
            "Friday": ["Computer Science", "Mathematics", "Physics"]
        }
    }
    return jsonify(mock_data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
