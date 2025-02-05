import requests
from bs4 import BeautifulSoup
import re

# Ask for username and password (this could be entered manually or obtained through a config)
username = input("Enter your username: ")
password = input("Enter your password: ")

# Create session and login (Simulating a login using POST request)
session = requests.Session()

# Define login URL and payload
login_url = "https://sctce.etlab.in/user/login"
login_payload = {
    "LoginForm[username]": username,
    "LoginForm[password]": password,
}

# Perform login
login_response = session.post(login_url, data=login_payload)

# Check if login was successful (you can modify this based on the actual response from the site)
if login_response.url == login_url:  # If redirected to the login page again, login failed
    print("❌ Login failed!")
    exit()

# After successful login, fetch the attendance page
attendance_url = "https://sctce.etlab.in/student/attendance"
attendance_response = session.get(attendance_url)
attendance_soup = BeautifulSoup(attendance_response.text, "html.parser")

# Extract attendance data
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
    print("❌ Could not extract attendance data!")

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
    print("❌ Could not extract subject-wise attendance!")

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
    print("❌ Could not extract timetable data!")

# Display integrated attendance and timetable
print("\n📊 **Integrated Attendance & Timetable:**\n")

days_mapping = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

for date, attendance in attendance_dict.items():
    clean_date = re.sub(r'(st|nd|rd|th)', '', date).strip()
    try:
        date_int = int(clean_date)
        day_name = days_mapping[(date_int - 1) % 7]
    except ValueError:
        day_name = "Unknown"
    
    subjects = timetable_dict.get(day_name, ["No Data Available"])

    print(f"\n📅 {day_name}, {date}:")
    for i, (status, subject) in enumerate(zip(attendance, subjects)):
        status_text = {
            "present": "✅ Present",
            "absent": "❌ Absent",
            "holiday": "🎉 Holiday",
            "n-a": "No Class"
        }.get(status, status)

        print(f"  🕘 Period {i+1}: {subject} -> {status_text}")

print("\n📊 **Subject-wise Attendance:**\n")
for subject, data in subject_attendance.items():
    print(f"📖 {subject}: {data}")
