from django.urls import path
from .views import MakeDatasheet

urlpatterns = [
    path('make-datasheet', MakeDatasheet.as_view()),
]
