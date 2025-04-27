# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views,dynamic_homepage

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'profiles', views.UserProfileViewSet)
router.register(r'destinations', views.DestinationViewSet)
router.register(r'hotels', views.HotelViewSet)
router.register(r'flights', views.FlightViewSet)
router.register(r'activities', views.ActivityViewSet)
router.register(r'bookings', views.BookingViewSet, basename='booking')
router.register(r'reviews', views.ReviewViewSet)
router.register(r'chat', views.ChatMessageViewSet, basename='chat')

urlpatterns = [
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.register_user, name='register'),
    path('login/', views.login, name='login'),
    
    # Custom endpoints
    path('trending-destinations/', views.DestinationViewSet.trending_destinations, name='trending-destinations'),
    path('user-bookings/', views.user_bookings, name='user-bookings'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel-booking'),
    
    # Chatbot and Real-Time Data Endpoints
    path('chatbot/', views.chatbot_api, name='chatbot_api'),  # Session-based chatbot endpoint
    path('recommend_trip/', views.advanced_recommend_trip, name='advanced_recommend_trip'),
    path('get_weather/', views.get_weather, name='get_weather'),
    path('generate_itinerary/', views.generate_itinerary, name='generate_itinerary'),

    #path('', include(dynamic_homepage.urlpatterns)),
    path('fetch_homepage_data/', dynamic_homepage.fetch_homepage_data, name='fetch_homepage_data'),
]
