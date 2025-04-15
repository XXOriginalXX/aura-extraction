# Attendance Scraper API

AURA Smart Board is a Flask-based API that scrapes and returns student attendance data, subject-wise and date-wise, from the [ETLab portal](https://sctce.etlab.in). It also extracts the class timetable.

## 🌐 Features

- ✅ Student Login using ETLab credentials
- 📊 Subject-wise attendance with counts and percentages
- 📅 Daily attendance (period-wise per day)
- 📆 Timetable extraction
- 🔒 Secure CSRF handling
- 🧠 Intelligent parsing of HTML tables
- 🔁 CORS enabled for integration with frontend apps

---

## 🛠️ Tech Stack

- Python 3.x
- Flask
- BeautifulSoup (for web scraping)
- Requests (session handling)
- Flask-CORS (CORS support)

-

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/aura-smartboard-api.git
cd aura-smartboard-api
```
### 2. Install Dependencies

```bash
pip install flask requests beautifulsoup4 flask-cors

```
### 3. Run the Flask Server

```bash
python app.py

