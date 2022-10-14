from django.urls import path
from .views import SGCAuthToken

urlpatterns = [
    # verificacion/token-auth/
    path('token-auth/', SGCAuthToken.as_view()),
]
