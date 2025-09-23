from django.urls import path
from . import views

app_name = 'contact'

urlpatterns = [
    path('', views.meetingList, name='meeting-list'),
    path('detail/<int:pk>', views.meetingDetail, name='meeting-detail'),
    path('create', views.meetingCreate, name='meeting-create'),
    path('delete/<int:pk>', views.meetingDelete, name='meeting-delete'),
    path('toggle/<int:pk>', views.meetingToggle, name='meeting-toggle'),
]