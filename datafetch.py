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

    print(f"🔍 Received Login Request | Username: {username}")

    if not username or not password:
        print("❌ Missing username or password")
        return jsonify({"error": "Username and password required"}), 400

    try:
        # Setup Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run without UI (important for deployment)
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        print("✅ WebDriver initialized, opening ETLab login page...")
        driver.get("https://sctce.etlab.in/user/login")

        # Find and enter username
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LoginForm_username"))).send_keys(username)
        # Find and enter password
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LoginForm_password"))).send_keys(password)
        # Click login button
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()

        print("🕒 Waiting for login to process...")
        time.sleep(5)  # Allow page to load

        # Check if login failed
        if "user/login" in driver.current_url:
            print("❌ Login failed - Incorrect credentials")
            driver.quit()
            return jsonify({"error": "Invalid credentials"}), 401

        print("✅ Login successful!")

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
        except Exception as e:
            print("❌ Attendance data extraction failed:", str(e))

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
        except Exception as e:
            print("❌ Timetable data extraction failed:", str(e))

        driver.quit()  # Close Selenium
        print("✅ Successfully extracted data!")

        return jsonify({"attendance": attendance_data, "timetable": timetable_data})

    except Exception as e:
        print("🔥 Internal Server Error:", str(e))
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500
