import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        return jsonify({"message": "Welcome to the Attendance API! Use /get-attendance with POST."})
    return "Welcome to the Attendance API!"

@app.route('/get-attendance', methods=['POST'])
def get_attendance():
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required!"}), 400

    session = requests.Session()
    login_url = "https://sctce.etlab.in/user/login"
    login_payload = {"LoginForm[username]": username, "LoginForm[password]": password}

    login_response = session.post(login_url, data=login_payload)
    if login_response.url == login_url:
        return jsonify({"error": "Login failed!"}), 401

    # Attendance extraction
    attendance_url = "https://sctce.etlab.in/student/attendance"
    attendance_response = session.get(attendance_url)
    attendance_soup = BeautifulSoup(attendance_response.text, "html.parser")

    attendance_dict = {}
    attendance_table = attendance_soup.find("table", {"id": "itsthetable"})
    if attendance_table:
        rows = attendance_table.find("tbody").find_all("tr")
        for row in rows:
            date_element = row.find("th")
            if date_element:
                date = date_element.text.strip()
                periods = row.find_all("td")
                attendance_statuses = [period.text.strip() for period in periods]  # Extract actual text
                attendance_dict[date] = attendance_statuses
    else:
        return jsonify({"error": "Could not extract attendance data!"}), 500

    # Subject-wise attendance extraction
    subject_url = "https://sctce.etlab.in/ktuacademics/student/viewattendancesubject/81"
    subject_response = session.get(subject_url)
    subject_soup = BeautifulSoup(subject_response.text, "html.parser")

    subject_attendance = {}
    subject_table = subject_soup.find("table")
    if subject_table:
        subject_rows = subject_table.find("tbody").find_all("tr")
        for row in subject_rows:
            cols = row.find_all("td")
            if len(cols) >= 5:
                subject_name = cols[3].text.strip()
                attendance_value = cols[4].text.strip()
                if subject_name and attendance_value:
                    subject_attendance[subject_name] = attendance_value
    else:
        return jsonify({"error": "Could not extract subject-wise attendance!"}), 500

    # Timetable extraction
    timetable_url = "https://sctce.etlab.in/student/timetable"
    timetable_response = session.get(timetable_url)
    timetable_soup = BeautifulSoup(timetable_response.text, "html.parser")

    timetable_dict = {}
    timetable_table = timetable_soup.find("table")
    if timetable_table:
        timetable_rows = timetable_table.find("tbody").find_all("tr")
        for row in timetable_rows:
            day_element = row.find("td")
            if day_element:
                day = day_element.text.strip()
                periods = row.find_all("td")[1:]
                subjects = [period.text.strip().replace("\n", " ") if period.text.strip() else "No Class" for period in periods]
                timetable_dict[day] = subjects
    else:
        return jsonify({"error": "Could not extract timetable data!"}), 500

    return jsonify({
        "daily_attendance": attendance_dict,
        "subject_attendance": subject_attendance,
        "timetable": timetable_dict
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
