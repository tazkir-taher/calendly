from django.urls import path
from .views import *

urlpatterns = [
    path('daily', getDailySchedule, name="daily"),
    path('monthly', getMonthlySchedule, name="monthly"),
    path('creare', createSchedule, name="create"),
]