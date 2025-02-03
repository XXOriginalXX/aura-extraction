from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

app = Flask(__name__)

@app.route('/')
def home():
    # Serve the login form HTML
    return render_template('login.html')

@app.route('/fetch_data', methods=['POST'])
def fetch_data():
    # Get the username and password from the user input
    username = request.form['username']
    password = request.form['password']

    # Selenium WebDriver setup
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run headless to avoid opening a browser window
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # ETlab login URL
    url = "https://sctce.etlab.in/user/login"
    driver.get(url)

    try:
        # Wait for the login form and submit the credentials
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LoginForm_username"))).send_keys(username)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LoginForm_password"))).send_keys(password)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()
    except Exception as e:
        return jsonify({"error": f"Login failed: {e}"}), 400

    # Wait for login to complete
    time.sleep(5)

    # Extract attendance data
    attendance_dict = {}
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.shortcut[href='/student/attendance']"))).click()
        time.sleep(5)
        rows = driver.find_elements(By.CSS_SELECTOR, "#itsthetable tbody tr")
        for row in rows:
            date = row.find_element(By.XPATH, ".//th").text
            periods = row.find_elements(By.XPATH, ".//td")
            attendance_statuses = []
            for period in periods:
                status = period.get_attribute("class").replace("span1 ", "")
                attendance_statuses.append(status)
            attendance_dict[date] = attendance_statuses
    except Exception as e:
        print("❌ Could not extract attendance data:", e)

    # Extract timetable data
    timetable_dict = {}
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/student/timetable']"))).click()
        time.sleep(5)
        timetable_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in timetable_rows:
            day = row.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
            periods = row.find_elements(By.CSS_SELECTOR, "td:not(:first-child)")
            subjects = [period.text.strip().replace("\n", " ") if period.text.strip() else "No Class" for period in periods]
            timetable_dict[day] = subjects
    except Exception as e:
        print("❌ Could not extract timetable data:", e)

    driver.quit()

    # Return the scraped data as JSON response
    return jsonify({
        "attendance": attendance_dict,
        "timetable": timetable_dict
    })

if __name__ == '__main__':
    app.run(debug=True)
