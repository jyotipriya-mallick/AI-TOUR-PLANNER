from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, Destination, Hotel, Flight, 
    Activity, Booking, Review, ChatMessage
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'

class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = '__all__'

class HotelSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    
    class Meta:
        model = Hotel
        fields = '__all__'

class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = '__all__'

class ActivitySerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    
    class Meta:
        model = Activity
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    hotel_details = HotelSerializer(source='hotel', read_only=True)
    flight_details = FlightSerializer(source='flight', read_only=True)
    activity_details = ActivitySerializer(source='activity', read_only=True)
    
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ('total_price', 'status')

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'

class ChatMessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = '__all__'

# Registration Serializer
class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate(self, data):
        # Check that passwords match
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords must match")
        # Enforce unique email
        if User.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError("A user with this email already exists")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user