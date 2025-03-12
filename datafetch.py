import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

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
            
        username = data.get('username', '220011')  # Default to provided username
        password = data.get('password', 'bdb1df')  # Default to provided password
        
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
        
        # Extract Subject-wise attendance from the view attendance subject page
        # Make sure we're using the correct URL as seen in the screenshot
        subject_url = "https://sctce.etlab.in/ktuacademics/student/viewattendancesubject"
        subject_response = session.get(subject_url)
        
        if "Login" in subject_response.text and "Password" in subject_response.text:
            return jsonify({"error": "Session expired or login failed!"}), 401
        
        # For debugging - save the HTML to inspect
        with open("subject_attendance_page.html", "w", encoding="utf-8") as f:
            f.write(subject_response.text)
            
        subject_soup = BeautifulSoup(subject_response.text, "html.parser")
        subject_attendance = {}
        
        # Target the table with attendance data - based on the screenshot, it has class "table table-striped table-bordered"
        subject_table = subject_soup.find("table", {"class": "table-striped"})
        
        if not subject_table:
            # Try alternative class combinations
            subject_table = subject_soup.find("table", {"class": "items"})
            if not subject_table:
                subject_table = subject_soup.find("table", {"class": "table"})
                if not subject_table:
                    # Last resort - find any table that might contain the attendance data
                    all_tables = subject_soup.find_all("table")
                    for table in all_tables:
                        if "Roll No" in table.text and "Attendance" in table.text:
                            subject_table = table
                            break
        
        if subject_table:
            # From the screenshot, we can see that the subject codes are in the header row
            # and the student's attendance percentages are in a row with their name
            headers = subject_table.find_all("th")
            subject_codes = []
            
            # Extract subject codes from the headers
            for header in headers:
                code_text = header.text.strip()
                # Skip headers that aren't subject codes (like "UNI Reg No", "Roll No", "Name")
                if code_text and code_text not in ["UNI Reg No", "Roll No", "Name"]:
                    subject_codes.append(code_text)
            
            # Find the student's row (in the screenshot it has the name "ADITHYAN S PILLAI")
            rows = subject_table.find_all("tr")
            student_row = None
            
            for row in rows:
                # Skip the header row
                if row.find("th"):
                    continue
                    
                cells = row.find_all("td")
                if cells and len(cells) > 2:
                    # Check if this is the student's row by verifying the name or ID
                    name_cell = cells[2] if len(cells) > 2 else None
                    if name_cell and "PILLAI" in name_cell.text:
                        student_row = row
                        break
            
            # If we can't find the specific student row, try to use the first data row
            if not student_row and len(rows) > 1:
                for row in rows:
                    if row.find("td"):
                        student_row = row
                        break
            
            if student_row:
                cells = student_row.find_all("td")
                # Skip the first 3 cells (UNI Reg No, Roll No, Name)
                start_index = 3
                
                # Extract attendance data
                for i, subject in enumerate(subject_codes):
                    if i + start_index < len(cells):
                        cell = cells[i + start_index]
                        cell_text = cell.text.strip()
                        
                        # Parse the attendance value and percentage
                        # Format is typically "42/42 (100%)" from screenshot
                        attendance_pattern = r'(\d+/\d+).*?(\d+%)'
                        match = re.search(attendance_pattern, cell_text)
                        
                        if match:
                            count = match.group(1)
                            percentage = match.group(2)
                        else:
                            # Alternative parsing if regex fails
                            parts = cell_text.split()
                            count = parts[0] if parts and '/' in parts[0] else "N/A"
                            
                            # Look for percentage
                            percentage = "N/A"
                            for part in parts:
                                if '%' in part:
                                    percentage = part.strip('()')
                        
                        subject_attendance[subject] = {
                            "count": count,
                            "percentage": percentage
                        }
                
                # Add overall attendance if available (typically last or second-to-last column)
                if len(cells) > len(subject_codes) + start_index:
                    total_index = len(subject_codes) + start_index
                    if total_index < len(cells):
                        total_cell = cells[total_index].text.strip()
                        
                        # Similar parsing for the total
                        parts = total_cell.split()
                        total_count = parts[0] if parts and '/' in parts[0] else "N/A"
                        
                        subject_attendance["Total"] = {
                            "count": total_count,
                            "percentage": "N/A"
                        }
                    
                    # Overall percentage is typically in the last column
                    percentage_index = len(subject_codes) + start_index + 1
                    if percentage_index < len(cells):
                        overall_percentage = cells[percentage_index].text.strip()
                        subject_attendance["Overall"] = {
                            "count": "N/A",
                            "percentage": overall_percentage
                        }
        
        # Daily attendance extraction
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
        
        # Timetable extraction
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
