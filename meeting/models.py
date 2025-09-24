from django.db import models
from django.contrib.auth.models import User

class Meeting(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meetings', null=True, blank=True)
    name = models.TextField(null=True, blank=True)
    email = models.TextField(null=True, blank=True)
    subject = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True , null = True, blank = True)
    active = models.BooleanField(default=True)
    day = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)