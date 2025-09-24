from django.urls import path, include

urlpatterns = [
    path('auth/', include('authentication.urls')),
    path('schedule/', include('schedule.urls')),
    path('meeting/', include('meeting.urls')),
]