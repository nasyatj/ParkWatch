import time
from collections import Counter

import requests
import psycopg2
from datetime import datetime

# OpenWeatherMap API Configuration
API_KEY = "7ef4fb0d4778af5be6af867af0f0fcb7"
URL = f"https://api.openweathermap.org/data/3.0/onecall?lat=43.7&lon=-79.42&exclude=hourly,daily&appid={API_KEY}&units=metric"

# Database configuration
DB_CONFIG = {
    "dbname": "neondb",
    "user": "neondb_owner",
    "password": "npg_wcnb1VdW5ELa",
    "host": "ep-square-band-a53at0wv-pooler.us-east-2.aws.neon.tech",
    "port": "5432",
    "sslmode": "require"
}

# Utility to get DB connection
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# Weather data
def get_latest_weather():
    try:
        api_key = "dd1b05ad0a13c55a14d14964ce36bed0"
        city = "Toronto"
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

        response = requests.get(url)
        data = response.json()

        if data["cod"] != 200:
            print("Weather API error:", data)
            return None

        weather = {
            "city": data["name"],
            "temperature": data["main"]["temp"],
            "precipitation": data.get("rain", {}).get("1h", 0.0),
            "timestamp": datetime.fromtimestamp(data["dt"]).strftime("%Y-%m-%d %H:%M:%S")
        }
        return weather
    except Exception as e:
        print("Error fetching real-time weather:", e)
        return None

# Get park reports
def get_reports():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM park_reports ORDER BY date DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching reports: {e}")
        return []

# Get maintenance tasks
def get_tasks():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM maintenance_tasks")
        tasks = cur.fetchall()
        cur.close()
        conn.close()
        return tasks
    except Exception as e:
        print("Error fetching tasks:", e)
        return []


def get_task_summary(tasks):
    parks = [task[0] for task in tasks]
    return Counter(parks)

#get weather for last 7 days
def weather_data_7days():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get all weather data
        cur.execute("SELECT * FROM weather_data ORDER BY timestamp DESC")
        rows = cur.fetchall()

        # Close database connection
        cur.close()
        conn.close()

        # Filter rows to only include today's data
        today = datetime.now().date()
        filtered_rows = [row for row in rows
                         if (row[1].date() - today).days <= 7 and row[1].date() >= today
                         ]

        return filtered_rows

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return []

def weather_data_24hours():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get all weather data
        cur.execute("SELECT * FROM weather_data ORDER BY timestamp DESC")
        rows = cur.fetchall()

        # Close database connection
        cur.close()
        conn.close()

        # Filter rows to only include today's data
        today = datetime.now().date()
        filtered_rows = [row for row in rows if row[1].date() == today]

        return filtered_rows

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return []


def get_parks():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM parks")
        parks = cur.fetchall()
        cur.close()
        conn.close()
        return parks
    except Exception as e:
        print("Error fetching parks:", e)
        return []

def update_park(id, plow_paths, water_flowers, cut_grass, high_winds, heavy_rain, heavy_snow):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE parks SET plow_paths = %s, water_flowers = %s, cut_grass = %s, high_winds = %s, heavy_rain = %s, heavy_snow = %s WHERE id = %s",
                    (plow_paths, water_flowers, cut_grass, high_winds, heavy_rain, heavy_snow, id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print("Error updating park:", e)
        return False
