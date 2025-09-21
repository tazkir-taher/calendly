from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from .models import *

class DaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Days
        fields = '__all__'
        
class TimesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Time
        fields = '__all__'