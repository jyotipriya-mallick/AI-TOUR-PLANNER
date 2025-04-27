# api/views.py

from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db.models import Q
from datetime import datetime
from forex_python.converter import CurrencyRates
import requests
import logging
#import openai
from openai import OpenAI # Use OpenAI class from the new SDK
from .models import (
    UserProfile, Destination, Hotel, Flight,
    Activity, Booking, Review, ChatMessage
)
from .serializers import (
    UserSerializer, UserProfileSerializer, DestinationSerializer,
    HotelSerializer, FlightSerializer, ActivitySerializer,
    BookingSerializer, ReviewSerializer, ChatMessageSerializer,
    UserRegistrationSerializer
)

# -------------------------------
# Production-Level Logging Setup
# -------------------------------
logger = logging.getLogger('chatbot')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# -------------------------------
# API Keys and Global Variables
# -------------------------------
from django.conf import settings
WEATHER_API_KEY = getattr(settings, "WEATHER_API_KEY", "YOUR_WEATHER_API_KEY")
RAPIDAPI_KEY = getattr(settings, "RAPIDAPI_KEY", "YOUR_RAPIDAPI_KEY")
RAPIDAPI_HOST = "tripadvisor-scraper.p.rapidapi.com"
CURRENCY_CONVERTER = CurrencyRates()

# Common headers for RapidAPI calls
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST
}

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
# -------------------------------
# Advanced Chatbot Class & Functions
# -------------------------------
class Chatbot:
    """
    Advanced stateful chatbot that collects user inputs step-by-step,
    integrates with external APIs in real time, and generates a personalized trip plan.
    Falls back to OpenAI if primary sources fail.
    """
    def __init__(self, state="greeting", data=None):
        self.state = state
        self.data = data or {}

    def to_dict(self):
        """Serialize chatbot state for session storage."""
        return {"state": self.state, "data": self.data}

    @classmethod
    def from_dict(cls, data_dict):
        """Reconstruct Chatbot instance from session data."""
        return cls(state=data_dict.get("state", "greeting"), data=data_dict.get("data", {}))

    def reset(self):
        self.state = "greeting"
        self.data = {}

    def handle_input(self, user_input):
        logger.info("Handling input. Current state: %s, User input: %s", self.state, user_input)
        user_input = user_input.strip()
        response = ""
        try:
            if self.state == "greeting":
                response = "Hello! I'm your AI-powered tour planner. Would you like to plan a trip? (Yes/No)"
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
        Production-level trip plan generation using real-time API data.
        Falls back to GPT-4 if external API calls fail or return insufficient data.
        """
        try:
            destination = data.get("destination", "Unknown").title()
            # Convert budget to a numeric value
            try:
                budget = float(data.get("budget"))
            except (ValueError, TypeError):
                budget_categories = {"low": 5000, "medium": 15000, "high": 30000}
                budget = budget_categories.get(data.get("budget", "").lower(), 10000)
            days = int(data.get("days", 3))
            transportation = data.get("transportation", "any")
            hotel_pref = data.get("hotel_preference", "any")
            food_pref = data.get("food_preference", "any")
            activities = data.get("activities", [])

            # Call external API methods
            attractions = self.fetch_attractions(destination)
            weather_info = self.fetch_weather(destination)
            hotels = self.fetch_hotels(destination, hotel_pref)
            restaurants = self.fetch_restaurants(destination, food_pref)
            cost_breakdown = self.calculate_costs(budget, days, transportation, hotel_pref)
            itinerary = self.create_itinerary(days, attractions, activities)

            # If critical data is missing, trigger fallback
            if not attractions or not hotels or not restaurants:
                raise Exception("Insufficient data from external APIs.")

            trip_plan = (
                f"Trip Plan for {destination} (Duration: {days} days, Budget: INR {budget:.0f}):\n\n"
                f"Weather Info: {weather_info}\n\n"
                f"Transportation: {transportation.capitalize()}\n"
                f"Estimated Cost Breakdown:\n{cost_breakdown}\n\n"
                f"Detailed Itinerary:\n{itinerary}\n\n"
                f"Recommended Hotels: {', '.join(hotels[:3])}\n"
                f"Recommended Restaurants: {', '.join(restaurants[:3])}\n\n"
                "Enjoy your trip!"
            )
            return trip_plan
        except Exception as e:
            logger.exception("Error generating trip plan using external APIs: %s", e)
            return self.fallback_generate_trip_plan(data)


    def fallback_generate_trip_plan(self, data):
        """
        Fallback mechanism using OpenAI's GPT-4 to generate a detailed day-wise itinerary.
        This method is used if external API calls fail or return insufficient data.
        """
        try:
            api_key = getattr(settings, "OPENAI_API_KEY", None)
            if not api_key:
                raise Exception("OpenAI API key not configured.")

            client = OpenAI(api_key=api_key)  # Create a client instance

            prompt = (
                f"Generate a detailed day-wise itinerary for a trip with these details:\n"
                f"- Destination: {data.get('destination', 'Unknown')}\n"
                f"- Duration: {data.get('days', 3)} days\n"
                f"- Budget: {data.get('budget', 'N/A')} INR\n"
                f"- Transportation: {data.get('transportation', 'any')}\n"
                f"- Hotel Preference: {data.get('hotel_preference', 'any')}\n"
                f"- Food Preference: {data.get('food_preference', 'any')}\n"
                f"- Specific Activities/Interests: {', '.join(data.get('activities', [])) or 'None'}\n\n"
                "Provide a detailed, numbered, day-wise itinerary including suggestions for morning, afternoon, "
                "and evening (attractions, dining, hotel check-ins, and leisure activities)."
            )

            response = client.chat.completions.create(
                model="gpt-4o-2024-05-13",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,

            )

            trip_plan = response.choices[0].message.content.strip()
            return trip_plan

        except Exception as fallback_exception:
            logger.exception("Fallback generate trip plan error: %s", fallback_exception)
            return "An error occurred while generating the trip plan."


    def fetch_attractions(self, destination):
        """
        Fetch attractions using the Mapples API. Falls back to a default if the call fails.
        """
        try:
            MAPPLES_API_KEY = getattr(settings, "MAPPLES_API_KEY", None)
            if not MAPPLES_API_KEY:
                raise Exception("Mapples API key not configured.")
            url = f"https://api.mapples.com/v1/places/search?query={destination}&apikey={MAPPLES_API_KEY}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            attractions = [place.get("name") for place in data.get("results", []) if place.get("name")]
            if not attractions:
                attractions = [f"Famous landmark in {destination}"]
            return attractions
        except Exception as e:
            logger.exception("Error fetching attractions: %s", e)
            return []

    def fetch_weather(self, destination):
        """
        Fetch current weather information for the destination from OpenWeather.
        """
        try:
            WEATHER_API_KEY = getattr(settings, "WEATHER_API_KEY", None)
            if not WEATHER_API_KEY:
                raise Exception("Weather API key not configured.")
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
        except Exception as e:
            logger.exception("Error fetching weather: %s", e)
            return "Weather information is unavailable."

    def fetch_hotels(self, destination, hotel_pref):
        """
        Fetch hotel recommendations based on destination and preference.
        In production, replace simulated data with a real API call.
        """
        try:
            if hotel_pref.lower() in ["luxury", "boutique"]:
                return [f"{destination} Grand Palace", f"{destination} Royal Residency", f"{destination} Elite Suites"]
            elif hotel_pref.lower() == "budget":
                return [f"{destination} Comfort Inn", f"{destination} Budget Stay", f"{destination} City Lodge"]
            else:
                return [f"{destination} Central Hotel", f"{destination} Heritage Inn", f"{destination} Traveller's Rest"]
        except Exception as e:
            logger.exception("Error fetching hotels: %s", e)
            return []

    def fetch_restaurants(self, destination, food_pref):
        """
        Fetch restaurant recommendations based on destination and cuisine preference.
        In production, replace simulated data with a real API call.
        """
        try:
            if food_pref.lower() in ["north indian", "south indian", "continental"]:
                return [f"{destination} {food_pref.title()} Delight", f"{destination} {food_pref.title()} Bistro", f"{destination} {food_pref.title()} Corner"]
            else:
                return [f"{destination} Food Plaza", f"{destination} Diner", f"{destination} Culinary Hub"]
        except Exception as e:
            logger.exception("Error fetching restaurants: %s", e)
            return []

    def calculate_costs(self, budget, days, transportation, hotel_pref):
        """
        Calculate a cost breakdown based on budget, days, transportation, and hotel preference.
        """
        try:
            trans_cost = 0.2 * budget if transportation.lower() != "any" else 0.15 * budget
            hotel_cost = 0.5 * budget if hotel_pref.lower() in ["luxury", "boutique"] else 0.3 * budget
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
            return breakdown
        except Exception as e:
            logger.exception("Error calculating costs: %s", e)
            return "Cost breakdown unavailable."

    def create_itinerary(self, days, attractions, activities):
        """
        Create a detailed day-wise itinerary including morning, afternoon, and evening plans.
        """
        itinerary_lines = []
        for day in range(1, days + 1):
            itinerary_lines.append(f"Day {day}:")
            # Morning plan: rotate through attractions or use default text
            morning = attractions[(day - 1) % len(attractions)] if attractions else f"Explore landmarks in {self.data.get('destination', 'your destination')}"
            itinerary_lines.append(f"  Morning: Visit {morning}.")
            # Afternoon plan: suggest a lunch spot and include user activities if provided
            lunch = f"{self.data.get('destination', 'Local')} Food Plaza" if self.data.get("food_preference") else "a local restaurant"
            if activities:
                extra = ", ".join(activities)
                afternoon = f"Enjoy lunch at {lunch} and then experience: {extra}."
            else:
                afternoon = f"Enjoy lunch at {lunch} and visit local attractions."
            itinerary_lines.append(f"  Afternoon: {afternoon}")
            # Evening plan: suggest hotel check-in and dinner
            hotel = f"{self.data.get('destination', 'Local')} Central Hotel" if self.data.get("hotel_preference") else "your chosen hotel"
            itinerary_lines.append(f"  Evening: Check in at {hotel}, have dinner at a nearby restaurant, and relax.")
            itinerary_lines.append("")  # Blank line for spacing
        return "\n".join(itinerary_lines)


# -------------------------------
# End of Chatbot class and helper functions
# -------------------------------

@api_view(["POST"])
def advanced_recommend_trip(request):
    try:
        data = request.data
        bot = Chatbot()
        trip_plan = bot.generate_trip_plan(data)
        return Response({"recommendation": trip_plan})
    except Exception:
        logger.exception("Error in advanced_recommend_trip endpoint")
        return Response({"error": "An error occurred while generating the trip plan."}, status=500)

@api_view(["GET"])
def get_weather(request):
    city = request.GET.get("city", "Delhi")
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return Response(response.json())
    except Exception as e:
        logger.exception("Error in get_weather: %s", e)
        return Response({"error": "Unable to fetch weather information."}, status=500)

@api_view(["POST"])
def generate_itinerary(request):
    try:
        destination = request.data.get("destination", "Goa")
        days = int(request.data.get("days", 3))
    except Exception as e:
        logger.exception("Error parsing itinerary data: %s", e)
        return Response({"error": "Invalid input for itinerary."}, status=400)
    
    bot = Chatbot()
    attractions = bot.fetch_attractions(destination)
    itinerary = {}
    for day in range(1, days + 1):
        attraction = attractions[(day - 1) % len(attractions)]
        itinerary[f"Day {day}"] = [
            f"Morning: Visit {attraction}",
            "Afternoon: Enjoy local cuisine",
            "Evening: Explore local markets and culture"
        ]
    return Response({"itinerary": itinerary})

@api_view(["POST"])
def chatbot_api(request):
    try:
        user_message = request.data.get("message", "")
        session_data = request.session.get("chatbot_state")
        logger.info("Session data before processing: %s", session_data)
        if session_data:
            bot = Chatbot.from_dict(session_data)
        else:
            bot = Chatbot()
        response_text = bot.handle_input(user_message)
        request.session["chatbot_state"] = bot.to_dict()
        logger.info("Session data after processing: %s", bot.to_dict())
        return Response({"message": response_text, "type": "text"})
    except Exception as e:
        logger.exception("Error in chatbot_api: %s", e)
        return Response({"error": "An error occurred while processing your request."}, status=500)

# # api/views.py
# from django.shortcuts import render
# from rest_framework import viewsets, status, filters
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from django.contrib.auth.models import User
# from django.contrib.auth import authenticate
# from django.db.models import Q
# from datetime import datetime
# from forex_python.converter import CurrencyRates
# import requests
# import logging

# from .models import (
#     UserProfile, Destination, Hotel, Flight,
#     Activity, Booking, Review, ChatMessage
# )
# from .serializers import (
#     UserSerializer, UserProfileSerializer, DestinationSerializer,
#     HotelSerializer, FlightSerializer, ActivitySerializer,
#     BookingSerializer, ReviewSerializer, ChatMessageSerializer,
#     UserRegistrationSerializer
# )

# # -------------------------------
# # Production-Level Logging Setup
# # -------------------------------
# logger = logging.getLogger('chatbot')
# logger.setLevel(logging.INFO)
# if not logger.handlers:
#     handler = logging.StreamHandler()
#     formatter = logging.Formatter(
#         '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#     )
#     handler.setFormatter(formatter)
#     logger.addHandler(handler)

# # -------------------------------
# # API Keys and Global Variables
# # -------------------------------
# from django.conf import settings
# #MAPPLES_API_KEY = getattr(settings, "MAPPLES_API_KEY", "YOUR_MAPPLES_API_KEY")
# WEATHER_API_KEY = getattr(settings, "WEATHER_API_KEY", "YOUR_WEATHER_API_KEY")
# RAPIDAPI_KEY = getattr(settings, "RAPIDAPI_KEY", "YOUR_RAPIDAPI_KEY")
# RAPIDAPI_HOST = "tripadvisor-scraper.p.rapidapi.com"
# #HOTEL_API_KEY = getattr(settings, "HOTEL_API_KEY", "YOUR_HOTEL_API_KEY")
# CURRENCY_CONVERTER = CurrencyRates()

# # Common headers for RapidAPI calls
# HEADERS = {
#     "X-RapidAPI-Key": RAPIDAPI_KEY,
#     "X-RapidAPI-Host": RAPIDAPI_HOST
# }
# # -------------------------------
# # Advanced Chatbot Class & Functions
# # -------------------------------
# class Chatbot:
#     """
#     Advanced stateful chatbot that collects user inputs step-by-step,
#     integrates with external APIs in real time, and generates a personalized trip plan.
#     """
#     def __init__(self, state="greeting", data=None):
#         self.state = state
#         self.data = data or {}

#     def to_dict(self):
#         """Serialize chatbot state for session storage."""
#         return {"state": self.state, "data": self.data}

#     @classmethod
#     def from_dict(cls, data_dict):
#         """Reconstruct Chatbot instance from session data."""
#         return cls(state=data_dict.get("state", "greeting"), data=data_dict.get("data", {}))

#     def reset(self):
#         self.state = "greeting"
#         self.data = {}

#     def handle_input(self, user_input):
#         logger.info("Handling input. Current state: %s, User input: %s", self.state, user_input)
#         user_input = user_input.strip()
#         response = ""
#         try:
#             if self.state == "greeting":
#                 response = "Hello! I'm your AI-powered tour planner. Would you like to plan a trip? (Yes/No)"
#                 self.state = "confirm_trip"

#             elif self.state == "confirm_trip":
#                 if user_input.lower() in ["yes", "y"]:
#                     response = ("Great! Please tell me your budget. "
#                                 "Enter a numeric value (in INR) or type a category (low/medium/high).")
#                     self.state = "get_budget"
#                 else:
#                     response = "Alright, feel free to ask me anytime when you want to plan a trip!"
#                     self.reset()

#             elif self.state == "get_budget":
#                 try:
#                     budget = float(user_input)
#                     self.data["budget"] = budget
#                 except ValueError:
#                     budget_categories = {"low": 5000, "medium": 15000, "high": 30000}
#                     self.data["budget"] = budget_categories.get(user_input.lower(), 10000)
#                 response = "Which destination (city/place) in India would you like to visit? (e.g., Goa, Delhi, Jaipur)"
#                 self.state = "get_destination"

#             elif self.state == "get_destination":
#                 self.data["destination"] = user_input
#                 response = "For how many days would you like the trip? (Enter a number)"
#                 self.state = "get_days"

#             elif self.state == "get_days":
#                 if user_input.isdigit():
#                     self.data["days"] = int(user_input)
#                     response = ("What mode of transportation do you prefer? "
#                                 "Options: flight, train, car, bus or type 'any'.")
#                     self.state = "get_transportation"
#                 else:
#                     response = "Please enter a valid number for the trip duration."

#             elif self.state == "get_transportation":
#                 valid_options = ["flight", "train", "car", "bus", "any"]
#                 if user_input.lower() in valid_options:
#                     self.data["transportation"] = user_input.lower()
#                     response = "Do you have any hotel preferences? (e.g., luxury, budget, boutique, any)"
#                     self.state = "get_hotel_preference"
#                 else:
#                     response = "Please choose a valid transportation option: flight, train, car, bus, or 'any'."

#             elif self.state == "get_hotel_preference":
#                 self.data["hotel_preference"] = user_input.lower()
#                 response = "Any particular food preference or cuisine? (e.g., North Indian, South Indian, continental, any)"
#                 self.state = "get_food_preference"

#             elif self.state == "get_food_preference":
#                 self.data["food_preference"] = user_input.lower()
#                 response = ("Lastly, do you have any specific activity interests? "
#                             "For example: adventure, sightseeing, culture, shopping, or type 'none'.")
#                 self.state = "get_activities"

#             elif self.state == "get_activities":
#                 if user_input.lower() == "none":
#                     self.data["activities"] = []
#                 else:
#                     activities = [act.strip() for act in user_input.split(",") if act.strip()]
#                     self.data["activities"] = activities
#                 response = "Thanks! Generating your personalized trip plan..."
#                 self.state = "generating_plan"
#                 trip_plan = self.generate_trip_plan(self.data)
#                 response += "\n\n" + trip_plan
#                 self.reset()

#             else:
#                 response = "I'm sorry, I didn't understand that. Could you please repeat?"
#         except Exception as e:
#             logger.exception("Exception in handle_input: %s", e)
#             response = "An error occurred while processing your input. Please try again later."
#         return response

#     def generate_trip_plan(self, data):
#         try:
#             destination = data.get("destination", "Unknown")
#             budget = data.get("budget", 10000)
#             days = data.get("days", 3)
#             transportation = data.get("transportation", "any")
#             hotel_pref = data.get("hotel_preference", "any")
#             food_pref = data.get("food_preference", "any")
#             activities = data.get("activities", [])

#             attractions = self.fetch_attractions(destination)
#             weather_info = self.fetch_weather(destination)
#             hotels = self.fetch_hotels(destination, hotel_pref)
#             restaurants = self.fetch_restaurants(destination, food_pref)
#             cost_breakdown = self.calculate_costs(budget, days, transportation, hotel_pref)
#             itinerary = self.create_itinerary(days, attractions, activities)

#             trip_plan = (
#                 f"Trip Plan for {destination} (Duration: {days} days, Budget: INR {budget}):\n\n"
#                 f"{weather_info}\n\n"
#                 f"Transportation: {transportation.capitalize()}\n"
#                 f"Estimated Cost Breakdown:\n{cost_breakdown}\n\n"
#                 f"Itinerary:\n{itinerary}\n\n"
#                 f"Recommended Hotels: {', '.join(hotels[:3])}\n\n"
#                 f"Recommended Restaurants: {', '.join(restaurants[:3])}\n\n"
#                 "Enjoy your trip!"
#             )
#             return trip_plan
#         except Exception as e:
#             logger.exception("Exception in generate_trip_plan: %s", e)
#             return "An error occurred while generating the trip plan."

#     def fetch_attractions(self, destination):
#         try:
#             url = f"https://api.mapples.com/v1/places/search?query={destination}&apikey={MAPPLES_API_KEY}"
#             response = requests.get(url, timeout=5)
#             response.raise_for_status()
#             data = response.json()
#             attractions = [place.get("name") for place in data.get("results", []) if place.get("name")]
#             if not attractions:
#                 attractions = [f"Popular attraction in {destination}"]
#         except Exception as e:
#             logger.exception("Error fetching attractions: %s", e)
#             attractions = [f"Famous landmark in {destination}"]
#         return attractions

   

#     def calculate_costs(self, budget, days, transportation, hotel_pref):
#         try:
#             trans_cost = 0.2 * budget if transportation != "any" else 0.15 * budget
#             hotel_cost = 0.5 * budget if hotel_pref in ["luxury", "boutique"] else 0.3 * budget
#             food_cost = 0.1 * budget
#             activity_cost = 0.1 * budget
#             breakdown = (
#                 f"Transportation: INR {trans_cost:.0f}\n"
#                 f"Accommodation: INR {hotel_cost:.0f}\n"
#                 f"Food: INR {food_cost:.0f}\n"
#                 f"Activities: INR {activity_cost:.0f}\n"
#                 f"Total: INR {trans_cost + hotel_cost + food_cost + activity_cost:.0f}"
#             )
#         except Exception as e:
#             logger.exception("Error calculating costs: %s", e)
#             breakdown = "Cost breakdown unavailable."
#         return breakdown

#     def create_itinerary(self, days, attractions, activities):
#         itinerary_lines = []
#         for day in range(1, days + 1):
#             attraction = attractions[(day - 1) % len(attractions)]
#             day_activities = f"Explore {attraction}"
#             if activities:
#                 day_activities += f"; also enjoy: {', '.join(activities)}"
#             itinerary_lines.append(f"Day {day}: {day_activities}.")
#         return "\n".join(itinerary_lines)

# # -------------------------------
# # Existing Endpoints (Users, Destinations, etc.)
# # -------------------------------

@api_view(['GET'])
def api_overview(request):
    api_urls = {
        'Users': '/users/',
        'User Detail': '/users/<str:pk>/',
        'Chatbot': '/api/chatbot/',  # Advanced chatbot endpoint
        # ... Other endpoints ...
    }
    return Response(api_urls)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'location']

    @api_view(['GET'])
    def trending_destinations(request):
        destinations = Destination.objects.filter(is_trending=True)
        serializer = DestinationSerializer(destinations, many=True)
        return Response(serializer.data)

class HotelViewSet(viewsets.ModelViewSet):
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'destination__name']

    def get_queryset(self):
        queryset = Hotel.objects.all()
        destination = self.request.query_params.get('destination', None)
        if destination:
            queryset = queryset.filter(destination__name__icontains=destination)
        return queryset

class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer

    def get_queryset(self):
        queryset = Flight.objects.all()
        source = self.request.query_params.get('source', None)
        destination = self.request.query_params.get('destination', None)
        date = self.request.query_params.get('date', None)
        if source:
            queryset = queryset.filter(source__icontains=source)
        if destination:
            queryset = queryset.filter(destination__icontains=destination)
        if date:
            try:
                search_date = datetime.strptime(date, '%Y-%m-%d').date()
                queryset = queryset.filter(departure_time__date=search_date)
            except ValueError:
                pass
        return queryset

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'destination__name']

    def get_queryset(self):
        queryset = Activity.objects.all()
        destination = self.request.query_params.get('destination', None)
        if destination:
            queryset = queryset.filter(destination__name__icontains=destination)
        return queryset

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        booking_type = self.request.data.get('booking_type')
        if booking_type == 'hotel':
            hotel_id = self.request.data.get('hotel')
            hotel = Hotel.objects.get(id=hotel_id)
            total_price = hotel.price_per_night * (
                datetime.strptime(self.request.data.get('end_date'), '%Y-%m-%d').date() -
                datetime.strptime(self.request.data.get('start_date'), '%Y-%m-%d').date()
            ).days
        elif booking_type == 'flight':
            flight_id = self.request.data.get('flight')
            flight = Flight.objects.get(id=flight_id)
            total_price = flight.price
        else:  # activity
            activity_id = self.request.data.get('activity')
            activity = Activity.objects.get(id=activity_id)
            total_price = activity.price

        serializer.save(user=self.request.user, total_price=total_price)

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatMessage.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # For each chat message, use the session-based chatbot endpoint to generate a reply.
        ai_response = chatbot_api(self.request).data.get("message", "")
        serializer.save(user=self.request.user, response=ai_response)

# # -------------------------------
# # Authentication & Registration Endpoints
# # -------------------------------
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def register_user(request):
    """
    Endpoint to register a new user.
    Expected JSON payload:
      {
         "username": "<username>",         // optional if you want to derive from email
         "email": "<user_email>",
         "password": "<password>",
         "password2": "<password_confirmation>",
         "first_name": "<first_name>",       // optional
         "last_name": "<last_name>"          // optional
      }
    Returns:
      On success, returns created user data and JWT tokens.
    """
    logger.info("Received registration request.")
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            # Optionally, if you want to create a UserProfile here,
            # you can do so after saving the user.
            refresh = RefreshToken.for_user(user)
            response_data = {
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
            logger.info(f"User '{user.username}' registered successfully.")
            return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception("Exception during user registration: %s", e)
            return Response({"detail": "Error creating user."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        logger.error("Registration data invalid: %s", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_bookings(request):
    bookings = Booking.objects.filter(user=request.user)
    serializer = BookingSerializer(bookings, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)
        booking.status = 'cancelled'
        booking.save()
        return Response({"message": "Booking cancelled successfully"})
    except Booking.DoesNotExist:
        return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def login(request):
    """
    Custom login endpoint.
    Expected JSON payload:
      {
         "email": "<user_email>",
         "password": "<password>"
      }
    Returns:
      On success, returns user data and JWT tokens.
    """
    logger.info("Received login request.")
    data = request.data
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        logger.warning("Login attempt with missing email or password.")
        return Response({"detail": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Use filter to get all users with this email.
        users = User.objects.filter(email=email)
        if not users.exists():
            logger.warning("Login attempt with non-existent email: %s", email)
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        if users.count() > 1:
            logger.warning("Multiple users found with email: %s. Using the first one.", email)
        user = users.first()
        
        # Now, authenticate using username (since Django's default backend uses username)
        user = authenticate(request, username=user.username, password=password)
        if user is None:
            logger.warning("Invalid credentials for user: %s", email)
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        
        refresh = RefreshToken.for_user(user)
        response_data = {
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
        logger.info("User '%s' logged in successfully.", user.username)
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.exception("Exception during login: %s", e)
        return Response({"detail": "An error occurred during login."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# # -------------------------------
# # Advanced Chatbot Endpoints
# # -------------------------------

# @api_view(["POST"])
# def chatbot_api(request):
#     """
#     Session-based dynamic chatbot endpoint.
#     """
#     try:
#         user_message = request.data.get("message", "")
#         session_data = request.session.get("chatbot_state")
#         logger.info("Session data before processing: %s", session_data)
#         if session_data:
#             bot = Chatbot.from_dict(session_data)
#         else:
#             bot = Chatbot()
#         response_text = bot.handle_input(user_message)
#         request.session["chatbot_state"] = bot.to_dict()
#         logger.info("Session data after processing: %s", bot.to_dict())
#         return Response({"message": response_text, "type": "text"})
#     except Exception as e:
#         logger.exception("Error in chatbot_api: %s", e)
#         return Response({"error": "An error occurred while processing your request."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# @api_view(["POST"])
# def advanced_recommend_trip(request):
#     return chatbot_api(request)

# @api_view(["GET"])
# def get_weather(request):
#     city = request.GET.get("city", "Delhi")
#     try:
#         url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
#         response = requests.get(url, timeout=5)
#         response.raise_for_status()
#         return Response(response.json())
#     except Exception as e:
#         logger.exception("Error in get_weather: %s", e)
#         return Response({"error": "Unable to fetch weather information."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# @api_view(["POST"])
# def generate_itinerary(request):
#     try:
#         destination = request.data.get("destination", "Goa")
#         days = int(request.data.get("days", 3))
#     except Exception as e:
#         logger.exception("Error parsing itinerary data: %s", e)
#         return Response({"error": "Invalid input for itinerary."}, status=status.HTTP_400_BAD_REQUEST)
    
#     bot = Chatbot()
#     attractions = bot.fetch_attractions(destination)
#     itinerary = {}
#     for day in range(1, days + 1):
#         attraction = attractions[(day - 1) % len(attractions)]
#         itinerary[f"Day {day}"] = [
#             f"Morning: Visit {attraction}",
#             "Afternoon: Enjoy local cuisine",
#             "Evening: Explore local markets and culture"
#         ]
#     return Response({"itinerary": itinerary})


# #*****************************************************************************************************************************

# #*************************************************************************************************************************************

