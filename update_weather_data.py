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

# Function to fetch weather data
def fetch_weather():
    try:
        response = requests.get(URL)
        response.raise_for_status()
        data = response.json()

        # Extract temperature and precipitation data
        weather_info = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "temperature": data['current']['temp'],  # Current temperature
            "precipitation": data.get('minutely', [{}])[0].get('precipitation', 0),
            "wind speed": data['current']['wind_speed']
        }

        return weather_info

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None


# Function to store data in Cloud SQL
def store_weather_data():
    weather_data = fetch_weather()

    if not weather_data:
        print("No data to store.")
        return

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        query = """
        INSERT INTO weather_data (timestamp, temperature, precipitation, wind_speed)
        VALUES (%s, %s, %s, %s)
        """

        cur.execute(query, (
            weather_data['timestamp'],
            weather_data['temperature'],
            weather_data['precipitation'],
            weather_data['wind speed']
        ))

        conn.commit()
        cur.close()
        conn.close()

        print("Weather data stored successfully!")

    except Exception as e:
        print(f"Database error: {e}")


if __name__ == "__main__":
    store_weather_data()
    print(fetch_weather())

    # while True:
    #     store_weather_data()
    #     print(fetch_weather())
    #     time.sleep(60 * 60 * 24) # Fetch data once per day