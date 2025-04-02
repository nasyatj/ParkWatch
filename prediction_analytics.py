from datetime import datetime

from database import weather_data_7days, get_tasks, get_parks, update_park, weather_data_24hours
from pydantic.v1 import BaseModel

parks_from_db = get_parks()
parks_dict = [
    {
        "id": park[0],
        "name": park[1],
        "plow_paths": park[2],
        "cut_grass": park[3],
        "water_flowers": park[4],
        "high_winds": park[5],
        "heavy_rain": park[6],
        "heavy_snow": park[7]
    }
    for park in parks_from_db
]

class Park(BaseModel):
    id : int
    name: str
    plow_paths: bool = False
    water_flowers: bool = False
    cut_grass: bool = False
    high_winds: bool = False
    heavy_rain: bool = False
    heavy_snow: bool = False

# Create a list of Park objects
parks = [Park(**park) for park in parks_dict]

# Snow plows prediction
def predict_plowing():
    weather_data = weather_data_24hours()

    if not weather_data:
        return "No weather data available."

    # Extract temperature and precipitation data
    temp_data = [data[2] for data in weather_data]
    precip_data = [data[3] for data in weather_data]

    for temperature in temp_data:
        if temperature < 0:
            if precip_data[temp_data.index(temperature)] > 20:
                for park in parks:
                    park.plow_paths = True
                    #print(f"Snow plowing required for {park.name}") #debugging
                break

def predict_watering():
    weather_data = weather_data_7days()

    if not weather_data:
        return "No weather data available."

    # Extract precipitation data
    precip_data = [data[3] for data in weather_data]

    for precipitation in precip_data:
        if precipitation < 0.25: #less than 25mm of rain
            for park in parks:
                park.water_flowers = True
                #print(f"Watering required for {park.name}") #debugging
            break

def predict_grass_cutting():
    all_parks_tasks = get_tasks()

    for park in parks:
        for task in all_parks_tasks:
            if park.id == task[3]:
                if task[1] == "Lawn Mowing":
                    if (task[2] - datetime.now().date()).days < -7:
                        park.cut_grass = True
                        #print(f"Grass cutting required for {park.name}") #debugging

def predict_wind_damage():
    weather_data = weather_data_24hours()

    if not weather_data:
        return "No weather data available."

    # Extract wind speed data
    wind_speed = [data[4] for data in weather_data]
    for wind in wind_speed:
        if wind > 19: #19m/s is considered high winds (70km/h)
            for park in parks:
                park.high_winds = True
                #print(f"High winds experienced at {park.name}") #debugging
            break

def predict_flooding():
    weather_data = weather_data_24hours()

    if not weather_data:
        return "No weather data available."

    # Extract precipitation data
    precip_data = [data[3] for data in weather_data]
    for precipitation in precip_data:
        if precipitation > 50:
            for park in parks:
                park.heavy_rain = True
                #print(f"Possible flooding at {park.name}") #debugging
            break

def predict_heavy_snow():
    weather_data = weather_data_24hours()

    if not weather_data:
        return "No weather data available."

    # Extract precipitation data
    precip_data = [data[3] for data in weather_data]
    temp_data = [data[2] for data in weather_data]

    for temperature in temp_data:
        if temperature < 0:
            if precip_data[temp_data.index(temperature)] > 50:
                for park in parks:
                    park.heavy_snow = True
                    #print(f"Heavy snowfall expected at {park.name}") #debugging
                break


def update_parks():
    for park in parks:
        update_park(
            park.id,
            park.plow_paths,
            park.water_flowers,
            park.cut_grass,
            park.high_winds,
            park.heavy_rain,
            park.heavy_snow
        )
    #print("Park data updated successfully.") #debugging


if __name__ == "__main__":
    #run updates for all parks
    predict_plowing()
    predict_watering()
    predict_grass_cutting()
    predict_wind_damage()
    predict_flooding()
    predict_heavy_snow()

    #update park data in database with new predictions
    update_parks()
