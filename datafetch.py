from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import os
import time

app = Flask(__name__)

# ✅ Configure Selenium for Railway Deployment
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# 📌 Route to Fetch Timetable
@app.route('/api/timetable', methods=['GET'])
def fetch_timetable():
    username = request.args.get('username')
    password = request.args.get('password')

    if not username or not password:
        return jsonify({"error": "Username and Password are required"}), 400

    driver = init_driver()
    
    try:
        driver.get("https://etlab.ktu.edu/login")
        time.sleep(2)

        # Login process
        driver.find_element("id", "username").send_keys(username)
        driver.find_element("id", "password").send_keys(password)
        driver.find_element("id", "login-btn").click()
        time.sleep(3)

        # Extract timetable (Modify selectors as needed)
        timetable = driver.find_element("id", "timetable").text

        driver.quit()
        return jsonify({"timetable": timetable})
    
    except Exception as e:
        driver.quit()
        return jsonify({"error": str(e)}), 500

# 📌 Route to Fetch Attendance
@app.route('/api/attendance', methods=['GET'])
def fetch_attendance():
    username = request.args.get('username')
    password = request.args.get('password')

    if not username or not password:
        return jsonify({"error": "Username and Password are required"}), 400

    driver = init_driver()
    
    try:
        driver.get("https://etlab.ktu.edu/login")
        time.sleep(2)

        # Login process
        driver.find_element("id", "username").send_keys(username)
        driver.find_element("id", "password").send_keys(password)
        driver.find_element("id", "login-btn").click()
        time.sleep(3)

        # Extract attendance (Modify selectors as needed)
        attendance = driver.find_element("id", "attendance").text

        driver.quit()
        return jsonify({"attendance": attendance})
    
    except Exception as e:
        driver.quit()
        return jsonify({"error": str(e)}), 500

# ✅ Run Flask on Railway's dynamic port
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
