import logging
import os
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

        # Headers to mimic a real browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": login_url,
        }

        # Login data (Adjust based on actual form fields)
        payload = {
            'LoginForm[username]': username,
            'LoginForm[password]': password,
        }

        # Send POST request to login
        response = session.post(login_url, data=payload, headers=headers)

        # Check if login was successful
        if "Dashboard" not in response.text:  
            return jsonify({"error": "Login failed"}), 400

        # Parse the response using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # DEBUGGING: Print the response HTML to check structure
        with open("response.html", "w", encoding="utf-8") as file:
            file.write(soup.prettify())  # Save HTML to check structure

        # Scrape attendance data
        attendance_data = {}
        attendance_table = soup.find("table", {"id": "itsthetable"})
        if attendance_table:
            rows = attendance_table.find_all("tr")
            for row in rows:
                date = row.find("th")
                if date:
                    date = date.text.strip()
                    periods = row.find_all("td")
                    attendance_statuses = [period["class"][0] if "class" in period.attrs else "No Class" for period in periods]
                    attendance_data[date] = attendance_statuses
        else:
            logging.error("Attendance table not found")
            return jsonify({"error": "Attendance data not found"}), 500

        # Scrape timetable data
        timetable_data = {}
        timetable_table = soup.find("table", {"id": "timetable"})
        if timetable_table:
            timetable_rows = timetable_table.find_all("tr")
            for row in timetable_rows:
                day = row.find("td", {"class": "day"})
                if day:
                    day = day.text.strip()
                    subjects = [period.text.strip() for period in row.find_all("td")[1:]]
                    timetable_data[day] = subjects
        else:
            logging.error("Timetable table not found")
            return jsonify({"error": "Timetable data not found"}), 500

        return jsonify({"attendance": attendance_data, "timetable": timetable_data})

    except Exception as e:
        logging.error(f"Login failed for {username}: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
