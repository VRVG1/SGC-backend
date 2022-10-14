from pyexpat import model
from django.db import models
from usuarios.models import Usuarios
from django.core.validators import MaxValueValidator, MinValueValidator
# Create your models here.


class Carreras(models.Model):
    class Meta:
        db_table = 'Carreras'
    ID_Carrera = models.CharField(max_length=8, null=False, primary_key=True)
    Nombre_Carrera = models.CharField(max_length=80, null=False, unique=True)

    def __str__(self):
        return f"{self.Nombre_Carrera}"


class Materias(models.Model):
    class Meta:
        db_table = 'Materias'
    ID_Materia = models.CharField(max_length=8, null=False, primary_key=True)
    Nombre_Materia = models.CharField(max_length=200, null=False, unique=True)
    Carrera = models.CharField(null=True, max_length=1)

    def __str__(self) -> str:
        return f"{self.Nombre_Materia}"


class Asignan(models.Model):
    grupos = (
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E'),
        ('F', 'F'),
        ('G', 'G'),
        ('H', 'H'),
        ('I', 'I'),
        ('J', 'J'),
    )

    class Meta:
        db_table = 'Asignan'
    ID_Asignan = models.AutoField(primary_key=True, null=False)
    ID_Materia = models.ForeignKey(Materias, on_delete=models.CASCADE)
    ID_Usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    ID_Carrera = models.ForeignKey(Carreras, on_delete=models.CASCADE)
    Grado = models.IntegerField(null=False, default=1, validators=[
                                MinValueValidator(1), MaxValueValidator(13)])
    Grupo = models.CharField(max_length=1, null=False,
                             choices=grupos, default='A')
