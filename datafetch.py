from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
import time

app = Flask(__name__)
CORS(app)  # Allow requests from React

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
        # Setup Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run without UI (important for deployment)
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        # Open ETLab login page
        driver.get("https://sctce.etlab.in/user/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LoginForm_username"))).send_keys(username)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LoginForm_password"))).send_keys(password)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()

        time.sleep(5)  # Wait for the page to load

        # Extract attendance data
        attendance_data = {}
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.shortcut[href='/student/attendance']"))).click()
            time.sleep(5)

            rows = driver.find_elements(By.CSS_SELECTOR, "#itsthetable tbody tr")
            for row in rows:
                date = row.find_element(By.XPATH, ".//th").text
                periods = row.find_elements(By.XPATH, ".//td")
                attendance_statuses = [period.get_attribute("class").replace("span1 ", "") for period in periods]
                attendance_data[date] = attendance_statuses
        except:
            print("❌ Attendance data extraction failed")

        # Extract timetable data
        timetable_data = {}
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/student/timetable']"))).click()
            time.sleep(5)

            timetable_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            for row in timetable_rows:
                day = row.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
                periods = row.find_elements(By.CSS_SELECTOR, "td:not(:first-child)")
                subjects = [period.text.strip().replace("\n", " ") if period.text.strip() else "No Class" for period in periods]
                timetable_data[day] = subjects
        except:
            print("❌ Timetable data extraction failed")

        driver.quit()  # Close Selenium

        return jsonify({"attendance": attendance_data, "timetable": timetable_data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
