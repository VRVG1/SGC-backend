import django
from django.contrib import admin
from .models import Materias, Carreras, Asignan
# Register your models here.

admin.site.register(Materias)
admin.site.register(Carreras)
admin.site.register(Asignan)
