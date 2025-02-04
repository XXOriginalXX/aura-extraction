import logging
import os  # Import os module
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Allow requests from React

# Set up logging
logging.basicConfig(level=logging.INFO)

@app.route("/")
def home():
    return jsonify({"message": "AURA backend is running!"})

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    try:
        login_url = "https://sctce.etlab.in/user/login"
        
        # Start a session to maintain cookies
        session = requests.Session()

        # Login data (You might need to inspect the actual POST parameters)
        payload = {
            'LoginForm[username]': username,
            'LoginForm[password]': password,
        }

        # Send POST request to login
        response = session.post(login_url, data=payload)

        # Check if login was successful (You may need to adjust this logic)
        if "Dashboard" not in response.text:  # Just an example condition
            return jsonify({"error": "Login failed"}), 400

        # Once logged in, scrape attendance and timetable data
        soup = BeautifulSoup(response.text, 'html.parser')

        # Scrape attendance data
        attendance_data = {}
        attendance_table = soup.find("table", {"id": "itsthetable"})
        if attendance_table:
            rows = attendance_table.find_all("tr")
            for row in rows:
                date = row.find("th")
                if date:
                    date = date.text
                    periods = row.find_all("td")
                    attendance_statuses = [period["class"][0] if "class" in period.attrs else "No Class" for period in periods]
                    attendance_data[date] = attendance_statuses
        else:
            logging.error("Attendance table not found")

        # Scrape timetable data
        timetable_data = {}
        timetable_table = soup.find("table", {"id": "timetable"})  # Modify with the actual ID or class
        if timetable_table:
            timetable_rows = timetable_table.find_all("tr")
            for row in timetable_rows:
                day = row.find("td", {"class": "day"})  # Adjust with actual class or selector
                if day:
                    day = day.text.strip()
                    subjects = [period.text.strip() for period in row.find_all("td")[1:]]
                    timetable_data[day] = subjects
        else:
            logging.error("Timetable table not found")

        return jsonify({"attendance": attendance_data, "timetable": timetable_data})

    except Exception as e:
        logging.error(f"Login failed for {username}: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
