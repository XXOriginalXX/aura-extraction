import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        return jsonify({"message": "Welcome to the Attendance API! Use /get-attendance with POST."})
    return "Welcome to the Attendance API!"

@app.route('/get-attendance', methods=['POST'])
def get_attendance():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Username and password are required!"}), 400
            
        # Create session with headers to mimic a browser
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,/;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        })
        
        # First get the login page to capture any CSRF tokens
        login_url = "https://sctce.etlab.in/user/login"
        initial_response = session.get(login_url)
        
        # Check if the initial request succeeded
        if initial_response.status_code != 200:
            return jsonify({"error": f"Initial request failed with status code {initial_response.status_code}"}), 500
            
        # Parse the login page for CSRF token
        login_soup = BeautifulSoup(initial_response.text, "html.parser")
        csrf_token = login_soup.find('input', {'name': '_csrf'})
        
        # Prepare login payload with CSRF token if found
        login_payload = {
            "LoginForm[username]": username, 
            "LoginForm[password]": password
        }
        
        if csrf_token:
            login_payload['_csrf'] = csrf_token.get('value', '')
            
        # Log in to the system
        login_response = session.post(login_url, data=login_payload, allow_redirects=True)
        
        # Better login verification
        if login_response.url == login_url or "Invalid username or password" in login_response.text:
            return jsonify({"error": "Login failed! Invalid username or password."}), 401
        
        # Extract Subject-wise attendance directly from the main attendance page
        subject_url = "https://sctce.etlab.in/ktuacademics/student/viewattendancesubject"
        subject_response = session.get(subject_url)
        
        if "Login" in subject_response.text and "Password" in subject_response.text:
            return jsonify({"error": "Session expired or login failed!"}), 401
        
        subject_soup = BeautifulSoup(subject_response.text, "html.parser")
        subject_attendance = {}
        
        # Target the table with class "items table table-striped table-bordered"
        subject_table = subject_soup.find("table", {"class": "items table table-striped table-bordered"})
        
        if subject_table:
            # Extract headers to get subject codes
            headers = subject_table.find("thead").find_all("th")
            subject_codes = []
            
            # Skip the first 3 columns (UNi Reg No, Roll No, Name) and the last 2 (Total, Percentage)
            for header in headers[3:-2]:
                subject_code = header.text.strip()
                if subject_code:
                    subject_codes.append(subject_code)
            
            # Extract the attendance data from the first row (assuming it's the student's row)
            rows = subject_table.find("tbody").find_all("tr")
            if rows:
                first_row = rows[0]
                cells = first_row.find_all("td")
                
                # Skip the first 3 cells (UNi Reg No, Roll No, Name)
                for i, subject_code in enumerate(subject_codes):
                    cell_index = i + 3  # Offset for the first 3 columns
                    if cell_index < len(cells):
                        attendance_value = cells[cell_index].text.strip()
                        subject_attendance[subject_code] = attendance_value
                
                # Add total and percentage if available
                if len(cells) >= len(subject_codes) + 4:  # +4 for UNi Reg No, Roll No, Name, and ensure Total exists
                    total_index = len(subject_codes) + 3
                    subject_attendance["Total"] = cells[total_index].text.strip()
                
                if len(cells) >= len(subject_codes) + 5:  # +5 to ensure Percentage exists
                    percentage_index = len(subject_codes) + 4
                    subject_attendance["Percentage"] = cells[percentage_index].text.strip()
        
        # Daily attendance extraction (keeping this part as is)
        attendance_url = "https://sctce.etlab.in/student/attendance"
        attendance_response = session.get(attendance_url)
        
        # Check if we can access attendance page
        if "Login" in attendance_response.text and "Password" in attendance_response.text:
            return jsonify({"error": "Session expired or login failed!"}), 401
            
        attendance_soup = BeautifulSoup(attendance_response.text, "html.parser")
        attendance_dict = {}
        attendance_table = attendance_soup.find("table", {"id": "itsthetable"})
        
        if attendance_table:
            rows = attendance_table.find("tbody").find_all("tr") if attendance_table.find("tbody") else []
            for row in rows:
                date_element = row.find("th")
                if date_element:
                    date = date_element.text.strip()
                    periods = row.find_all("td")
                    attendance_statuses = [period.text.strip() for period in periods]  # Extract actual text
                    attendance_dict[date] = attendance_statuses
        
        # Timetable extraction (keeping this part as is)
        timetable_url = "https://sctce.etlab.in/student/timetable"
        timetable_response = session.get(timetable_url)
        timetable_soup = BeautifulSoup(timetable_response.text, "html.parser")
        timetable_dict = {}
        timetable_table = timetable_soup.find("table")
        
        if timetable_table and timetable_table.find("tbody"):
            timetable_rows = timetable_table.find("tbody").find_all("tr")
            for row in timetable_rows:
                cells = row.find_all("td")
                if cells:
                    day = cells[0].text.strip()
                    periods = cells[1:]
                    subjects = [period.text.strip().replace("\n", " ") if period.text.strip() else "No Class" for period in periods]
                    timetable_dict[day] = subjects
        
        return jsonify({
            "daily_attendance": attendance_dict,
            "subject_attendance": subject_attendance,
            "timetable": timetable_dict
        })
        
    except Exception as e:
        # Log the detailed error but return a generic message
        print(f"Error: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
