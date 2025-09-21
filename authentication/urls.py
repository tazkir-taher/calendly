from django.urls import path

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from .views import *

# from .views import GoogleView

urlpatterns = [
    path('register', registration_view, name="register"),

    path('token', tokenObtainPair),
    path('token/refresh', tokenRefresh),
    path('token/verify', tokenVerify),
    path('test', test_view)
    

]