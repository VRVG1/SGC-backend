from django.db import models
from django.contrib.auth.models import User
# Create your models here.

choices_users = (
    ("Administrador", "Administrador"),
    ("Docente", "Docente"),
    ("Supervisor", "Supervisor"),
)


class Usuarios(models.Model):
    class Meta:
        db_table = 'Usuarios'
    PK = models.AutoField(primary_key=True, null=False)
    ID_Usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    Nombre_Usuario = models.CharField(max_length=70, null=False)
    Tipo_Usuario = models.CharField(
        max_length=13, choices=choices_users, null=False)  # NECESITA MAX LENGTH
    CorreoE = models.EmailField(max_length=254, null=False)
    Permiso = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.Nombre_Usuario}"
