from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
import logging
from django.conf import settings
from django.urls import path
import time

logger = logging.getLogger(__name__)

# Retrieve API keys from settings (ensure these are defined in your .env file)
RAPIDAPI_KEY = getattr(settings, "RAPIDAPI_KEY", "YOUR_RAPIDAPI_KEY")
RAPIDAPI_HOST = "tripadvisor-scraper.p.rapidapi.com"
WEATHER_API_KEY = getattr(settings, "WEATHER_API_KEY", "YOUR_WEATHER_API_KEY")

# Common headers for RapidAPI calls
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST
}

@api_view(["GET"])
def fetch_homepage_data(request):
    """
    Fetch real-time trending destinations, recommended hotels, restaurants,
    flights, trains, weather, and simulated activities.
    If a "location" query parameter is provided, use that location; otherwise, use a default.
    """
    try:
        # Get the user-specified location from query parameters; default to "new york" if not provided.
        user_location = request.GET.get("location", "").strip()
        base_query = user_location if user_location else "new york"

        # Fetch data using the provided query.
        trending_destinations = fetch_trending_destinations(query=base_query)
        # If trending data is empty, fallback to using the base query as destination.
        base_destination = trending_destinations[0]["destination"] if trending_destinations else base_query

        weather_data = fetch_weather(base_destination)
        hotels_data = fetch_hotels(query=base_query)
        restaurants_data = fetch_restaurants(query=base_query)
        flights_data = fetch_flights()      # (Static/demo data; replace if you have a dynamic API)
        trains_data = fetch_trains()          # (Static/demo data)
        activities_data = fetch_activities(base_destination)

        return Response({
            "trending_destinations": trending_destinations,
            "weather": weather_data,
            "hotels": hotels_data,
            "restaurants": restaurants_data,
            "flights": flights_data,
            "trains": trains_data,
            "activities": activities_data,
        })
    except Exception as e:
        logger.exception("Error fetching homepage data: %s", e)
        return Response({"error": "Failed to load homepage data."}, status=500)

def parse_response(response):
    """
    Helper function to handle responses that might be either a list or a dict.
    If the response is a dict, return the value under the "data" key (if present); 
    otherwise, return the response itself.
    """
    try:
        json_data = response.json()
    except Exception as e:
        logger.exception("Error parsing JSON: %s", e)
        return []
    if isinstance(json_data, dict):
        return json_data.get("data", [])
    elif isinstance(json_data, list):
        return json_data
    return []

def safe_api_call(url, params):
    """
    Helper to make an API call and handle 429 errors gracefully.
    If a 429 is encountered, you can either wait and retry or return an empty list.
    Here, we simply log and return an empty list.
    """
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=5)
        response.raise_for_status()
        return parse_response(response)
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            logger.error("Rate limit exceeded for URL: %s", url)
            # Optionally, implement a retry mechanism:
            # time.sleep(2)  # wait for 2 seconds before retrying
            # return safe_api_call(url, params)
            return []  # fallback: return empty list
        else:
            logger.exception("HTTP error for URL %s: %s", url, e)
            return []
    except Exception as e:
        logger.exception("Error during API call to %s: %s", url, e)
        return []

def fetch_trending_destinations(query="new york"):
    """
    Fetch trending destinations using the TripAdvisor Scraper API hotels search endpoint.
    We try to filter for items with type 'city'. If none are found, return a fallback set.
    """
    try:
        url = f"https://{RAPIDAPI_HOST}/hotels/search"
        params = {"query": query, "limit": "10"}
        items = safe_api_call(url, params)
        
        # Filter for items where type is "city"
        filtered = [item for item in items if item.get("type") == "city" and item.get("name")]
        if not filtered:
            # Fallback: use all items remapped as trending destinations
            filtered = [{
                "destination": item.get("name"),
                "image": item.get("thumbnail_url") or "",
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude")
            } for item in items if item.get("name")]
        else:
            filtered = [{
                "destination": item.get("name"),
                "image": item.get("thumbnail_url") or "",
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude")
            } for item in filtered]
        return filtered
    except Exception as e:
        logger.exception("Error fetching trending destinations: %s", e)
        return []

def fetch_weather(city):
    """
    Fetch current weather information for the given city from OpenWeather API.
    """
    try:
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric"}
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.exception("Error fetching weather information: %s", e)
        return {}

def fetch_hotels(query="new york"):
    """
    Fetch hotel recommendations using the TripAdvisor Scraper API.
    We filter for items with type 'accommodation'. If none found, return fallback data.
    """
    try:
        url = f"https://{RAPIDAPI_HOST}/hotels/search"
        params = {"query": f"{query} hotels", "limit": "5"}
        items = safe_api_call(url, params)
        
        filtered = [item for item in items if item.get("type") == "accommodation"]
        if not filtered and items:
            filtered = items
        hotels = []
        for item in filtered:
            hotels.append({
                "name": item.get("name") or "Unknown Hotel",
                "address": item.get("address") or "Not available",
                "rating": item.get("rating") or "N/A",
                "reviews": item.get("num_reviews") or 0,
                "image": (item.get("photo", {})
                          .get("images", {})
                          .get("large", {})
                          .get("url", "")) or item.get("thumbnail_url", "")
            })
        return hotels
    except Exception as e:
        logger.exception("Error fetching hotel recommendations: %s", e)
        return []

def fetch_restaurants(query="new york"):
    """
    Fetch restaurant recommendations using the TripAdvisor Scraper API.
    """
    try:
        url = f"https://{RAPIDAPI_HOST}/restaurants/search"
        params = {"query": f"{query} restaurants", "limit": "5"}
        items = safe_api_call(url, params)
        
        restaurants = []
        for item in items:
            restaurants.append({
                "name": item.get("name") or "Unknown Restaurant",
                "address": item.get("address") or "Not available",
                "rating": item.get("rating") or "N/A",
                "reviews": item.get("num_reviews") or 0,
                "image": (item.get("photo", {})
                          .get("images", {})
                          .get("large", {})
                          .get("url", "")) or item.get("thumbnail_url", "")
            })
        return restaurants
    except Exception as e:
        logger.exception("Error fetching restaurant recommendations: %s", e)
        return []

def fetch_flights():
    """
    Fetch flight recommendations. (Static demo data; replace with dynamic API if available.)
    """
    return [
        {"airline": "Air India", "route": "New Delhi to Mumbai", "price": 5000},
        {"airline": "IndiGo", "route": "Bangalore to Goa", "price": 3000}
    ]

def fetch_trains():
    """
    Simulate train recommendations. (Static demo data; replace with dynamic API if available.)
    """
    return [
        {"train_name": "Rajdhani Express", "route": "New Delhi to Mumbai", "price": 1500},
        {"train_name": "Shatabdi Express", "route": "New Delhi to Kolkata", "price": 1300}
    ]

def fetch_activities(city):
    """
    Simulate activity recommendations for a destination.
    """
    return [
        {"name": "Beach Party", "location": city, "type": "Leisure"},
        {"name": "City Tour", "location": city, "type": "Sightseeing"}
    ]

