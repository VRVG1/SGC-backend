import sys
sys.path.append("/home/ordep/programas/desarrollo_web/residencias/SGC/SGC-backend/SGC/")
print(sys.path)
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()

from django.db import models
from django.contrib.auth.models import User
from usuarios.models import Usuarios
import json

superuser_data = json.load(open("./superuserdata.json", "r"))

super_usuario = User.objects.get(username=superuser_data['username'])
usuario = Usuarios.objects.create(ID_Usuario=super_usuario,
                                  Nombre_Usuario=f"{superuser_data['first_name']} {superuser_data['last_name']}",
                                  Tipo_Usuario=superuser_data['tipo_usuario'],
                                  CorreoE=superuser_data['email'])
