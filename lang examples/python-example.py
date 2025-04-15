# app.py
import os
import json
from datetime import datetime

import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/api/weather')
def get_weather():
    api_key = os.getenv('WEATHER_API_KEY')
    city = request.args.get('city', 'London')
    
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
    response = requests.get(url)
    
    return response.json()

if __name__ == '__main__':
    app.run(debug=True)