from django.urls import path
from .views import *

urlpatterns = [
    path('daily', getDailySchedule, name="daily"),
    path('monthly', getMonthlySchedule, name="monthly"),
    path('daily/open/<int:pk>', getDailyScheduleOpen, name="daily-open"),
    path('monthly/open/<int:pk>', getMonthlyScheduleOpen, name="monthly-open"),
    path('create', createSchedule, name="create"),
    path('edit', editSchedule, name="edit"),
    path('delete', deleteSchedule, name="delete"),
]