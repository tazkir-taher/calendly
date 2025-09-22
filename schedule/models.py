from django.db import models
from django.contrib.auth.models import User

class Days(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='days')
    day = models.DateField(null=True, blank=True)
    available_repeating_days = models.TextField(null=True, blank=True)  
    is_repeating = models.BooleanField(default=False)

class Time(models.Model):
    day = models.ForeignKey(Days, on_delete=models.CASCADE, related_name='times')
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)