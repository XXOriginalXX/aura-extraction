import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

# Fetch username and password from environment variables
username = os.getenv("ETLAB_USERNAME")
password = os.getenv("ETLAB_PASSWORD")

if not username or not password:
    raise ValueError("Username and password must be provided as environment variables.")

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

url = "https://sctce.etlab.in/user/login"
driver.get(url)

try:
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LoginForm_username"))).send_keys(username)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LoginForm_password"))).send_keys(password)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()
except Exception as e:
    print("❌ Login failed:", e)

time.sleep(5)

try:
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.shortcut[href='/student/attendance']"))).click()
except:
    print("❌ Attendance link not found!")

time.sleep(5)

attendance_dict = {}

try:
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

try:
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/ktuacademics/student/viewattendancesubject/81']"))).click()
except:
    print("❌ Attendance By Subject link not found!")

time.sleep(5)

subject_attendance = {}

try:
    subject_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in subject_rows:
        cols = row.find_elements(By.CSS_SELECTOR, "td")
        if len(cols) > 2:
            subject_names = [col.text.strip() for col in cols[3:-2]]
            attendance_values = [col.text.strip() for col in cols[4:]]
            for subject, attendance in zip(subject_names, attendance_values):
                if attendance:
                    subject_attendance[subject] = attendance
except Exception as e:
    print("❌ Could not extract subject-wise attendance:", e)

try:
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/student/timetable']"))).click()
except:
    print("❌ Timetable link not found!")

time.sleep(5)

timetable_dict = {}

try:
    timetable_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in timetable_rows:
        day = row.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
        periods = row.find_elements(By.CSS_SELECTOR, "td:not(:first-child)")
        subjects = [period.text.strip().replace("\n", " ") if period.text.strip() else "No Class" for period in periods]
        timetable_dict[day] = subjects
except Exception as e:
    print("❌ Could not extract timetable data:", e)

driver.quit()

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
