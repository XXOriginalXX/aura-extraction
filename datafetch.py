import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

BASE_URL = "https://sctce.etlab.in"

@app.route('/get-attendance', methods=['POST'])
def get_attendance():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password are required!"}), 400
    
    try:
        session = requests.Session()
        login_url = f"{BASE_URL}/user/login"
        login_payload = {"LoginForm[username]": username, "LoginForm[password]": password}
        login_response = session.post(login_url, data=login_payload, timeout=10)
        
        if login_response.url == login_url:
            return jsonify({"error": "Login failed! Please check your credentials."}), 401
        
        # Fetch daily attendance
        attendance_url = f"{BASE_URL}/student/attendance"
        attendance_response = session.get(attendance_url, timeout=10)
        daily_attendance = extract_daily_attendance(attendance_response.text)

        # Fetch subject-wise attendance
        subject_attendance_url = f"{BASE_URL}/ktuacademics/student/viewattendancesubject/81"
        subject_response = session.get(subject_attendance_url, timeout=10)
        subject_attendance = extract_subject_attendance(subject_response.text)

        # Fetch timetable
        timetable_url = f"{BASE_URL}/student/timetable"
        timetable_response = session.get(timetable_url, timeout=10)
        timetable = extract_timetable(timetable_response.text)
        
        return jsonify({
            "daily_attendance": daily_attendance,
            "subject_attendance": subject_attendance,
            "timetable": timetable
        })
    
    except requests.Timeout:
        return jsonify({"error": "Request timed out. Please try again later."}), 504
    except requests.ConnectionError:
        return jsonify({"error": "Could not connect to the server. Please check your internet connection."}), 503
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


def extract_daily_attendance(html):
    """Extracts daily attendance from the attendance page."""
    soup = BeautifulSoup(html, "html.parser")
    attendance_dict = {}

    table = soup.find("table", {"id": "itsthetable"})
    if table:
        rows = table.find("tbody").find_all("tr")
        for row in rows:
            date_element = row.find("th")
            if date_element:
                date_str = date_element.text.strip()
                try:
                    date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    formatted_date = date_str
                
                periods = row.find_all("td")
                statuses = []
                
                for td in periods:
                    status = td.get("title", "").strip()  # Extracts status from title attribute
                    if status:
                        statuses.append(status)
                
                if statuses:
                    attendance_dict[formatted_date] = statuses
    
    return attendance_dict


def extract_subject_attendance(html):
    """Extracts subject-wise attendance from the attendance page."""
    soup = BeautifulSoup(html, "html.parser")
    subject_attendance = {}

    table = soup.find("table", {"class": "items table table-striped table-bordered"})
    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 5:
                subject_name = cols[3].text.strip()
                attendance_value = cols[4].text.strip()

                if subject_name and attendance_value:
                    if not attendance_value.endswith('%'):
                        attendance_value += "%"
                    subject_attendance[subject_name] = attendance_value

    return subject_attendance


def extract_timetable(html):
    """Extracts timetable details from the timetable page."""
    soup = BeautifulSoup(html, "html.parser")
    timetable_data = {}

    table = soup.find("table", {"class": "timetable"})
    if table:
        rows = table.find_all("tr")[1:]  # Skip header row
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                day = cols[0].text.strip()
                periods = [col.text.strip() for col in cols[1:]]
                timetable_data[day] = periods

    return timetable_data


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
