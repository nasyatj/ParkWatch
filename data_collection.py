import time

import requests
import psycopg2
from datetime import datetime

# OpenWeatherMap API Configuration
API_KEY = "7ef4fb0d4778af5be6af867af0f0fcb7"
CITY = "Toronto"
URL = f"https://api.openweathermap.org/data/3.0/onecall?lat=43.7&lon=-79.42&exclude=hourly,daily&appid={API_KEY}&units=metric"

# Database Configuration
DB_CONFIG = {
    "dbname": "weather_data",
    "user": "postgres",  # Use 'postgres' unless you created another user
    "password": "coe892",
    "host": "34.130.225.57",
    "port": "5432"
}


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
            "precipitation": data.get('minutely', [{}])[0].get('precipitation', 0)
            # First available entry or 0 if missing
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
        INSERT INTO weather_data (timestamp, temperature, precipitation)
        VALUES (%s, %s, %s)
        """

        cur.execute(query, (
            weather_data['timestamp'],
            weather_data['temperature'],
            weather_data['precipitation']
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
    #     time.sleep(60 * 60) # Fetch data every hour

