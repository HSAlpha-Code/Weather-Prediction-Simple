import requests
import statistics
from collections import Counter
from datetime import datetime

try:
    from config import WEATHERAPI_API_KEY
except:
    print ("Couldn't access config.py")
    print ("Please read instructions README.txt")
    quit()
    
def normalize_condition(condition_text):
    condition_text = condition_text.lower()
    if any(word in condition_text for word in ["rain", "drizzle", "shower"]):
        return "Rain"
    if any(word in condition_text for word in ["snow", "sleet", "ice", "blizzard"]):
        return "Snow"
    if "thunder" in condition_text or "storm" in condition_text:
        return "Thunderstorm"
    if any(word in condition_text for word in ["cloud", "overcast"]):
        return "Clouds"
    if any(word in condition_text for word in ["clear", "sunny", "fair"]):
        return "Clear"
    if any(word in condition_text for word in ["mist", "fog", "haze"]):
        return "Fog"
    return "Other"

def get_coordinates(city):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
    try:
        response = requests.get(url)
        if response.status_code >= 400:
            print("Error: Unable to retrieve data")
        data = response.json()    
        #checks if the data is a non empty list
        if not data.get('results'):
            return None, None
        location = data['results'][0]
        return location['latitude'], location['longitude']
    except:
        print("Error")
        
def get_weatherapi_forecast(lat, lon):
    print("Fetching data from WeatherAPI.com...")
    latlon = f"{lat},{lon}"
    url = (f"http://api.weatherapi.com/v1/forecast.json?key={WEATHERAPI_API_KEY}"
           f"&q={latlon}&days=3&aqi=no&alerts=no")
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json().get('forecast', {}).get('forecastday', [])
        
        forecast = []
        for day_data in data:
            forecast.append({
                'date': day_data['date'],
                'max_temp': day_data['day']['maxtemp_c'],
                'min_temp': day_data['day']['mintemp_c'],
                'precip_mm': day_data['day']['totalprecip_mm'],
                'condition': normalize_condition(day_data['day']['condition']['text'])
            })
        return forecast
    except (requests.exceptions.RequestException, KeyError) as e:
        print("Could not fetch from WeatherAPI.com")
        return None
def aggregate_forecasts(all_forecasts):
    valid_forecasts = [f for f in all_forecasts if f is not None]
    if not valid_forecasts:
        return None

    final_forecast = []
    for i in range(3):
        day_temps_max = []
        day_temps_min = []
        day_precip = []
        day_conditions = []
        
        for forecast_source in valid_forecasts:
            try:
                day_data = forecast_source[i]
                day_temps_max.append(day_data['max_temp'])
                day_temps_min.append(day_data['min_temp'])
                day_precip.append(day_data['precip_mm'])
                day_conditions.append(day_data['condition'])
            except (IndexError, TypeError):
                continue
        
        if not day_temps_max: continue

        agg_date = valid_forecasts[0][i]['date']
        agg_max_temp = round(statistics.mean(day_temps_max), 1)
        agg_min_temp = round(statistics.mean(day_temps_min), 1)
        agg_precip = round(statistics.mean(day_precip), 1)
        
        if day_conditions:
            agg_condition = Counter(day_conditions).most_common(1)[0][0]
        else:
            agg_condition = "Unknown"

        final_forecast.append({
            'date': agg_date,
            'max_temp': agg_max_temp,
            'min_temp': agg_min_temp,
            'precip_mm': agg_precip,
            'condition': agg_condition
        })
        
    return final_forecast
def display_forecast(forecast, city):
    print("\n" + "="*40)
    print(f"Probabilistic Weather Forecast for {city.title()}")
    print("="*40)
    
    if not forecast:
        print("Could not generate a forecast. Please check the errors above.")
        return

    for day in forecast:
        date_obj = datetime.strptime(day['date'], '%Y-%m-%d')
        print(f"\n--- {date_obj.strftime('%A, %B %d')} ---")
        print(f"  Condition: {day['condition']}")
        print(f"  Temperature: {day['min_temp']}°C to {day['max_temp']}°C")
        print(f"  Precipitation: {day['precip_mm']} mm")
    
    print("\n" + "="*40)
    print("Forecast based on consensus from WeatherAPI.com")

if __name__ == "__main__":
    city = input("Enter a city name to get the weather forecast: ")
    if not city:
        print("City name cannot be empty.")
    else:
        lat, lon = get_coordinates(city)
        if lat is None or lon is None:
            print(f"Could not find coordinates for '{city}' Please check your internet connection")
        else:
            #Fetching!
            weatherapi_data = get_weatherapi_forecast(lat, lon)
            
            all_data = [weatherapi_data]
            final_forecast = aggregate_forecasts(all_data)
            display_forecast(final_forecast, city)
