# server.py

from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import random
import json
import csv
from pathlib import Path
from pydantic import BaseModel
from typing import Dict
from datetime import datetime, timezone
from geopy.geocoders import Nominatim
import io
import numpy as np

# -----------------------------------------
# 1️⃣ Load environment variables from .env
# -----------------------------------------
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "weather_app")
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

# -----------------------------------------
# 2️⃣ Connect to MongoDB
# -----------------------------------------
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# -----------------------------------------
# 3️⃣ Create FastAPI app
# -----------------------------------------
app = FastAPI(title="Will It Rain on My Parade?")

# Use a router with /api prefix
api_router = APIRouter(prefix="/api")

# Allow React frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# -----------------------------------------
# 4️⃣ Geocoder (to get latitude/longitude)
# -----------------------------------------
geolocator = Nominatim(user_agent="will-it-rain-parade")

# -----------------------------------------
# 5️⃣ Define Data Models
# -----------------------------------------
class WeatherRequest(BaseModel):
    location: str
    date: str  # ISO format: "YYYY-MM-DDTHH:MM:SSZ"

class WeatherProbabilities(BaseModel):
    very_hot: float
    very_cold: float
    very_wet: float
    very_windy: float
    very_uncomfortable: float

class WeatherResponse(BaseModel):
    location: str
    date: str
    coordinates: Dict[str, float] = None
    probabilities: WeatherProbabilities

# -----------------------------------------
# 6️⃣ Helper Functions
# -----------------------------------------
def get_coordinates(location: str) -> Dict[str, float]:
    """Get latitude and longitude from a location string"""
    try:
        loc = geolocator.geocode(location)
        if loc:
            return {"latitude": loc.latitude, "longitude": loc.longitude}
    except:
        pass
    return {"latitude": 0.0, "longitude": 0.0}

def generate_realistic_probabilities(location: str, date: str) -> WeatherProbabilities:
    """
    Generate realistic weather probabilities for a given location and date
    """
    try:
        date_obj = datetime.fromisoformat(date.replace("Z", "+00:00"))
        month = date_obj.month
    except:
        month = 6  # Default to summer

    np.random.seed(hash(location + date) % 1000)

    # Seasonal adjustments
    if month in [6, 7, 8]:
        hot_factor, cold_factor, wet_factor = 1.8, 0.2, 1.2
    elif month in [12, 1, 2]:
        hot_factor, cold_factor, wet_factor = 0.1, 2.0, 1.0
    else:
        hot_factor, cold_factor, wet_factor = 0.8, 0.8, 1.4

    very_hot = min(85, max(5, np.random.normal(25 * hot_factor, 15)))
    very_cold = min(85, max(5, np.random.normal(25 * cold_factor, 15)))
    very_wet = min(85, max(10, np.random.normal(35 * wet_factor, 20)))
    very_windy = min(60, max(5, np.random.normal(20, 12)))
    very_uncomfortable = min(
        90, max(10, (very_hot * 0.4 + very_cold * 0.3 + very_wet * 0.2 + very_windy * 0.1))
    )

    return WeatherProbabilities(
        very_hot=round(very_hot, 1),
        very_cold=round(very_cold, 1),
        very_wet=round(very_wet, 1),
        very_windy=round(very_windy, 1),
        very_uncomfortable=round(very_uncomfortable, 1)
    )

# -----------------------------------------
# 7️⃣ API Endpoints
# -----------------------------------------

@api_router.get("/")
async def api_root():
    return {"message": "Will It Rain on My Parade? API running!"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "weather-probability-api"}

@api_router.post("/weather", response_model=WeatherResponse)
async def get_weather(request: WeatherRequest):
    """Return weather probabilities for a location and date"""
    coordinates = get_coordinates(request.location)
    probabilities = generate_realistic_probabilities(request.location, request.date)
    return WeatherResponse(
        location=request.location,
        date=request.date,
        coordinates=coordinates,
        probabilities=probabilities
    )

@api_router.post("/download/csv")
async def download_csv(request: WeatherRequest):
    """Download weather data as a CSV file"""
    coordinates = get_coordinates(request.location)
    probabilities = generate_realistic_probabilities(request.location, request.date)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Location", "Date", "Latitude", "Longitude", 
        "Very Hot", "Very Cold", "Very Wet", "Very Windy", "Very Uncomfortable"
    ])
    writer.writerow([
        request.location, request.date, 
        coordinates["latitude"], coordinates["longitude"],
        probabilities.very_hot, probabilities.very_cold,
        probabilities.very_wet, probabilities.very_windy,
        probabilities.very_uncomfortable
    ])
    output.seek(0)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=weather_{request.location}_{request.date}.csv"}
    )

@api_router.post("/download/json")
async def download_json(request: WeatherRequest):
    """Download weather data as JSON file"""
    coordinates = get_coordinates(request.location)
    probabilities = generate_realistic_probabilities(request.location, request.date)

    data = {
        "location": request.location,
        "date": request.date,
        "coordinates": coordinates,
        "probabilities": probabilities.dict(),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

    json_string = json.dumps(data, indent=2)
    return StreamingResponse(
        io.BytesIO(json_string.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=weather_{request.location}_{request.date}.json"}
    )

# -----------------------------------------
# 8️⃣ Include Router
# -----------------------------------------
app.include_router(api_router)

# -----------------------------------------
# 9️⃣ Close DB connection on shutdown
# -----------------------------------------
@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# -----------------------------------------
# 10️⃣ Logging
# -----------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Weather Probability API is running...")