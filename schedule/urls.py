from django.urls import path
from .views import *

urlpatterns = [
    path('daily', getDailySchedule, name="daily"),
    path('monthly', getMonthlySchedule, name="monthly"),
    path('create', createSchedule, name="create"),
    path('edit', editSchedule, name="edit"),
    path('delete', deleteSchedule, name="delete"),
]