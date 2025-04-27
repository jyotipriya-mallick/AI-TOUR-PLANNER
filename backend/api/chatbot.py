import json
import logging
import requests
from forex_python.converter import CurrencyRates
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Configure logger
logger = logging.getLogger(__name__)

# Retrieve API keys securely from settings
MAPPLES_API_KEY = settings.MAPPLES_API_KEY
WEATHER_API_KEY = settings.WEATHER_API_KEY
RAPIDAPI_KEY = settings.RAPIDAPI_KEY
HOTEL_API_KEY = settings.HOTEL_API_KEY  # if used
OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_BASE_URL = settings.OPENAI_BASE_URL

CURRENCY_CONVERTER = CurrencyRates()

class Chatbot:
    """
    Advanced stateful chatbot that collects user inputs step-by-step,
    integrates with multiple external APIs in real time, and generates
    a personalized trip plan. Falls back to OpenAI if primary sources fail.
    """
    def __init__(self, state="greeting", data=None):
        self.state = state
        self.data = data or {}

    def to_dict(self):
        return {"state": self.state, "data": self.data}

    @classmethod
    def from_dict(cls, data_dict):
        return cls(state=data_dict.get("state", "greeting"), data=data_dict.get("data", {}))

    def reset(self):
        self.state = "greeting"
        self.data = {}

    def handle_input(self, user_input):
        logger.info("State: %s | User Input: %s", self.state, user_input)
        user_input = user_input.strip()
        response = ""
        try:
            if self.state == "greeting":
                response = ("Hello! I'm your AI-powered tour planner. Would you like to plan a trip? (Yes/No)")
                self.state = "confirm_trip"

            elif self.state == "confirm_trip":
                if user_input.lower() in ["yes", "y"]:
                    response = ("Great! Please tell me your budget. Enter a numeric value (in INR) or type a category (low/medium/high).")
                    self.state = "get_budget"
                else:
                    response = "Alright, feel free to ask me anytime when you want to plan a trip!"
                    self.reset()

            elif self.state == "get_budget":
                try:
                    budget = float(user_input)
                    self.data["budget"] = budget
                except ValueError:
                    budget_categories = {"low": 5000, "medium": 15000, "high": 30000}
                    self.data["budget"] = budget_categories.get(user_input.lower(), 10000)
                response = "Which destination (city/place) in India would you like to visit? (e.g., Goa, Delhi, Jaipur)"
                self.state = "get_destination"

            elif self.state == "get_destination":
                self.data["destination"] = user_input
                response = "For how many days would you like the trip? (Enter a number)"
                self.state = "get_days"

            elif self.state == "get_days":
                if user_input.isdigit():
                    self.data["days"] = int(user_input)
                    response = ("What mode of transportation do you prefer? Options: flight, train, car, bus or type 'any'.")
                    self.state = "get_transportation"
                else:
                    response = "Please enter a valid number for the trip duration."

            elif self.state == "get_transportation":
                valid_options = ["flight", "train", "car", "bus", "any"]
                if user_input.lower() in valid_options:
                    self.data["transportation"] = user_input.lower()
                    response = "Do you have any hotel preferences? (e.g., luxury, budget, boutique, any)"
                    self.state = "get_hotel_preference"
                else:
                    response = "Please choose a valid transportation option: flight, train, car, bus, or 'any'."

            elif self.state == "get_hotel_preference":
                self.data["hotel_preference"] = user_input.lower()
                response = "Any particular food preference or cuisine? (e.g., North Indian, South Indian, continental, any)"
                self.state = "get_food_preference"

            elif self.state == "get_food_preference":
                self.data["food_preference"] = user_input.lower()
                response = ("Lastly, do you have any specific activity interests? For example: adventure, sightseeing, culture, shopping, or type 'none'.")
                self.state = "get_activities"

            elif self.state == "get_activities":
                if user_input.lower() == "none":
                    self.data["activities"] = []
                else:
                    activities = [act.strip() for act in user_input.split(",") if act.strip()]
                    self.data["activities"] = activities
                response = "Thanks! Generating your personalized trip plan..."
                self.state = "generating_plan"
                trip_plan = self.generate_trip_plan(self.data)
                response += "\n\n" + trip_plan
                self.reset()

            else:
                response = "I'm sorry, I didn't understand that. Could you please repeat?"
        except Exception as e:
            logger.exception("Error in handle_input: %s", e)
            response = "An error occurred while processing your input. Please try again later."
        return response

    def generate_trip_plan(self, data):
        """
        Generate a detailed day-wise trip plan including suggestions for morning attractions,
        lunch at recommended restaurants, and hotel check-in with dinner & leisure in the evening.
        Uses real-time data from multiple APIs.
        """
        try:
            destination = data.get("destination", "Unknown").title()
            budget = float(data.get("budget", 10000))
            days = int(data.get("days", 3))
            transportation = data.get("transportation", "any")
            hotel_pref = data.get("hotel_preference", "any")
            food_pref = data.get("food_preference", "any")
            user_activities = data.get("activities", [])
            
            # Fetch dynamic recommendations
            attractions = self.fetch_attractions(destination)       # e.g. returns list of attraction names
            weather_info = self.fetch_weather(destination)           # e.g. returns string summary like "28°C, Clear sky"
            hotels = self.fetch_hotels(destination, hotel_pref)      # e.g. list of hotel names
            restaurants = self.fetch_restaurants(destination, food_pref)  # e.g. list of restaurant names
            cost_breakdown = self.calculate_costs(budget, days, transportation, hotel_pref)
            
            # Build a detailed day-wise itinerary
            itinerary_lines = []
            for day in range(1, days + 1):
                itinerary_lines.append(f"Day {day}:")
                # Morning: Suggest an attraction or activity
                if attractions:
                    morning_plan = attractions[(day - 1) % len(attractions)]
                else:
                    morning_plan = f"Explore popular landmarks in {destination}"
                itinerary_lines.append(f"  Morning: Visit {morning_plan}.")
                
                # Afternoon: Suggest lunch at a recommended restaurant and an activity (or user-specified activity)
                if restaurants:
                    lunch_spot = restaurants[(day - 1) % len(restaurants)]
                else:
                    lunch_spot = f"Local cuisine spot in {destination}"
                # Optionally, include user activities if provided
                if user_activities:
                    extra = ", ".join(user_activities)
                    afternoon_plan = f"Enjoy lunch at {lunch_spot} and then experience: {extra}."
                else:
                    afternoon_plan = f"Enjoy lunch at {lunch_spot} and visit a local market or museum."
                itinerary_lines.append(f"  Afternoon: {afternoon_plan}")
                
                # Evening: Recommend hotel check-in and leisure/dinner
                if hotels:
                    hotel_choice = hotels[0]
                else:
                    hotel_choice = f"your chosen hotel in {destination}"
                itinerary_lines.append(f"  Evening: Check in at {hotel_choice}, have dinner at a nearby restaurant, and relax.")
                itinerary_lines.append("")  # Blank line for spacing
            
            itinerary_str = "\n".join(itinerary_lines)
            
            trip_plan = (
                f"Trip Plan for {destination} (Duration: {days} days, Budget: INR {budget:.0f}):\n\n"
                f"Weather Info: {weather_info}\n\n"
                f"Transportation: {transportation.capitalize()}\n"
                f"Estimated Cost Breakdown:\n{cost_breakdown}\n\n"
                f"Detailed Itinerary:\n{itinerary_str}\n"
                f"Recommended Hotels: {', '.join(hotels[:3]) if hotels else 'No hotel data available'}\n"
                f"Recommended Restaurants: {', '.join(restaurants[:3]) if restaurants else 'No restaurant data available'}\n\n"
                "Enjoy your trip!"
            )
            return trip_plan
        except Exception as e:
            logger.exception("Error generating trip plan: %s", e)
            return "An error occurred while generating the trip plan."

    def fallback_openai_trip_plan(self, data):
        try:
            # Using OpenAI as a fallback to generate itinerary
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
            prompt = (
                f"Plan a detailed trip itinerary for a traveler with these details:\n"
                f"Destination: {data.get('destination', 'Unknown')}\n"
                f"Budget (INR): {data.get('budget', 10000)}\n"
                f"Days: {data.get('days', 3)}\n"
                f"Transportation: {data.get('transportation', 'any')}\n"
                f"Hotel Preference: {data.get('hotel_preference', 'any')}\n"
                f"Food Preference: {data.get('food_preference', 'any')}\n"
                f"Activities: {', '.join(data.get('activities', [])) if data.get('activities') else 'none'}\n\n"
                f"Return a well-structured itinerary including daily schedule, estimated costs, weather, "
                f"and recommendations for hotels and restaurants."
            )
            completion = client.chat.completions.create(
                model="gpt-4o-2024-05-13",
                messages=[{"role": "user", "content": prompt}]
            )
            answer = completion.choices[0].message.content
            return answer
        except Exception as e:
            logger.exception("OpenAI fallback failed: %s", e)
            return "An error occurred while generating a fallback trip plan."

    def fetch_attractions(self, destination):
        try:
            url = f"https://api.mapples.com/v1/places/search?query={destination}&apikey={MAPPLES_API_KEY}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            attractions = [place.get("name") for place in data.get("results", []) if place.get("name")]
            if not attractions:
                attractions = [f"Popular attraction in {destination}"]
        except Exception:
            logger.exception("Error fetching attractions from Mapples API")
            attractions = [f"Famous landmark in {destination}"]
        return attractions

    def fetch_weather(self, destination):
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={destination}&appid={WEATHER_API_KEY}&units=metric"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if "main" in data:
                temp = data["main"]["temp"]
                description = data["weather"][0]["description"].capitalize()
                return f"Current weather in {destination}: {temp}°C, {description}."
            else:
                return "Weather information is unavailable."
        except Exception:
            logger.exception("Error fetching weather information")
            return "Weather information is unavailable."

    def fetch_hotels(self, destination, hotel_pref):
        try:
            if hotel_pref in ["luxury", "boutique"]:
                hotels = [f"{destination} Grand Palace", f"{destination} Royal Residency", f"{destination} Elite Suites"]
            elif hotel_pref == "budget":
                hotels = [f"{destination} Comfort Inn", f"{destination} Budget Stay", f"{destination} City Lodge"]
            else:
                hotels = [f"{destination} Central Hotel", f"{destination} Heritage Inn", f"{destination} Traveller's Rest"]
        except Exception:
            logger.exception("Error fetching hotel information")
            hotels = [f"Standard hotel in {destination}"]
        return hotels

    def fetch_restaurants(self, destination, food_pref):
        try:
            if food_pref in ["north indian", "south indian", "continental"]:
                restaurants = [
                    f"{destination} {food_pref.title()} Delight",
                    f"{destination} {food_pref.title()} Bistro",
                    f"{destination} {food_pref.title()} Corner"
                ]
            else:
                restaurants = [f"{destination} Food Plaza", f"{destination} Diner", f"{destination} Culinary Hub"]
        except Exception:
            logger.exception("Error fetching restaurant information")
            restaurants = [f"Popular restaurant in {destination}"]
        return restaurants

    def calculate_costs(self, budget, days, transportation, hotel_pref):
        try:
            trans_cost = 0.2 * budget if transportation != "any" else 0.15 * budget
            hotel_cost = 0.5 * budget if hotel_pref in ["luxury", "boutique"] else 0.3 * budget
            food_cost = 0.1 * budget
            activity_cost = 0.1 * budget
            total = trans_cost + hotel_cost + food_cost + activity_cost
            breakdown = (
                f"Transportation: INR {trans_cost:.0f}\n"
                f"Accommodation: INR {hotel_cost:.0f}\n"
                f"Food: INR {food_cost:.0f}\n"
                f"Activities: INR {activity_cost:.0f}\n"
                f"Total: INR {total:.0f}"
            )
        except Exception:
            logger.exception("Error calculating cost breakdown")
            breakdown = "Cost breakdown unavailable."
        return breakdown

    def create_itinerary(self, days, attractions, activities):
        itinerary_lines = []
        for day in range(1, days + 1):
            attraction = attractions[(day - 1) % len(attractions)]
            day_activities = f"Explore {attraction}"
            if activities:
                additional = ", ".join(activities)
                day_activities += f"; also enjoy: {additional}"
            itinerary_lines.append(f"Day {day}: {day_activities}.")
        return "\n".join(itinerary_lines)
