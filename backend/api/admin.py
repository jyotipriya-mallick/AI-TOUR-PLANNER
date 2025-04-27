from django.contrib import admin
from .models import *  # Import all models
from django.contrib.admin.sites import AlreadyRegistered

# Register all models
def register_all_models():
    for model in globals().values():
        if isinstance(model, type) and issubclass(model, models.Model):
            try:
                admin.site.register(model)
            except AlreadyRegistered:
                pass  # Skip already registered models

register_all_models()
