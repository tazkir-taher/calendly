from django.urls import path
from . import views

app_name = 'profile_contact'

urlpatterns = [
    path('', views.profileContactList, name='ProfileContact-list'),
    path('detail/<int:pk>', views.profileContactDetail, name='ProfileContact-detail'),
    path('create', views.profileContactCreate, name='ProfileContact-create'),
    path('delete/<int:pk>', views.profileContactDelete, name='ProfileContact-delete'),
]