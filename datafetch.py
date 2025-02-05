import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/get-attendance', methods=['POST'])
def get_attendance():
    # Get username and password from the request body
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required!"}), 400

    # Create session and login
    session = requests.Session()
    login_url = "https://sctce.etlab.in/user/login"
    login_payload = {
        "LoginForm[username]": username,
        "LoginForm[password]": password,
    }

    login_response = session.post(login_url, data=login_payload)

    if login_response.url == login_url:
        return jsonify({"error": "Login failed!"}), 401

    # After successful login, fetch attendance page
    attendance_url = "https://sctce.etlab.in/student/attendance"
    attendance_response = session.get(attendance_url)
    attendance_soup = BeautifulSoup(attendance_response.text, "html.parser")

    attendance_dict = {}
    attendance_table = attendance_soup.find("table", {"id": "itsthetable"})
    if attendance_table:
        rows = attendance_table.find("tbody").find_all("tr")
        for row in rows:
            date = row.find("th").text.strip()
            periods = row.find_all("td")
            attendance_statuses = []
            for period in periods:
                status = period.get("class")[0].replace("span1 ", "")
                attendance_statuses.append(status)
            attendance_dict[date] = attendance_statuses
    else:
        return jsonify({"error": "Could not extract attendance data!"}), 500

    # Fetch subject-wise attendance page
    subject_url = "https://sctce.etlab.in/ktuacademics/student/viewattendancesubject/81"
    subject_response = session.get(subject_url)
    subject_soup = BeautifulSoup(subject_response.text, "html.parser")

    subject_attendance = {}
    subject_table = subject_soup.find("table")
    if subject_table:
        subject_rows = subject_table.find("tbody").find_all("tr")
        for row in subject_rows:
            cols = row.find_all("td")
            if len(cols) > 2:
                subject_names = [col.text.strip() for col in cols[3:-2]]
                attendance_values = [col.text.strip() for col in cols[4:]]
                for subject, attendance in zip(subject_names, attendance_values):
                    if attendance:
                        subject_attendance[subject] = attendance
    else:
        return jsonify({"error": "Could not extract subject-wise attendance!"}), 500

    # Fetch timetable page
    timetable_url = "https://sctce.etlab.in/student/timetable"
    timetable_response = session.get(timetable_url)
    timetable_soup = BeautifulSoup(timetable_response.text, "html.parser")

    timetable_dict = {}
    timetable_table = timetable_soup.find("table")
    if timetable_table:
        timetable_rows = timetable_table.find("tbody").find_all("tr")
        for row in timetable_rows:
            day = row.find("td").text.strip()
            periods = row.find_all("td")[1:]
            subjects = [period.text.strip().replace("\n", " ") if period.text.strip() else "No Class" for period in periods]
            timetable_dict[day] = subjects
    else:
        return jsonify({"error": "Could not extract timetable data!"}), 500

    # Return the integrated data as a JSON response
    return jsonify({
        "attendance": attendance_dict,
        "subject_attendance": subject_attendance,
        "timetable": timetable_dict
    })

if __name__ == '__main__':
    # Get the port from the environment variable, or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
