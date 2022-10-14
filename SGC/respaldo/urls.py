from django.urls import path
from .views import MakeBackup, RestoreData


urlpatterns = [
    path('make-backup', MakeBackup.as_view()),
    path('upload-restore', RestoreData.as_view()),
]
