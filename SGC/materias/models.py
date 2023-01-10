from django.db import models
from usuarios.models import Usuarios
from django.core.validators import MaxValueValidator, MinValueValidator

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
    Clave_reticula = models.CharField(max_length=8, null=False, primary_key=True)
    Carrera = models.ForeignKey(Carreras, on_delete=models.CASCADE)
    Nombre_Materia = models.CharField(max_length=200, null=False, unique=False)
    horas_Teoricas = models.IntegerField(null=False, default=1, validators=[MinValueValidator(1),MaxValueValidator(10)])
    horas_Practicas = models.IntegerField(null=False, default=1, validators=[MinValueValidator(1),MaxValueValidator(10)])
    creditos = models.IntegerField(null=False, default=1, validators=[MinValueValidator(1),MaxValueValidator(20)])
    unidades = models.IntegerField(null=False, default=1, validators=[MinValueValidator(1),MaxValueValidator(10)])


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

    horas = (
        ('07:00 - 08:00','07:00 - 08:00'),
        ('08:00 - 09:00','08:00 - 09:00'),
        ('09:00 - 10:00','09:00 - 10:00'),
        ('10:00 - 11:00','10:00 - 11:00'),
        ('11:00 - 12:00','11:00 - 12:00'),
        ('12:00 - 13:00','12:00 - 13:00'),
        ('13:00 - 14:00','13:00 - 14:00'),
        ('14:00 - 15:00','14:00 - 15:00'),
        ('07:00 - 09:00','07:00 - 09:00'),
        ('09:00 - 11:00','09:00 - 11:00'),
        ('11:00 - 13:00','11:00 - 13:00'),
        ('13:00 - 15:00','13:00 - 15:00'),
    )

    dias = (
        ('Lunes','Lunes'),
        ('Martes','Martes'),
        ('Miercoles','Miercoles'),
        ('Jueves','Jueves'),
        ('Viernes','Viernes'),
    )

    class Meta:
        db_table = 'Asignan'
    ID_Asignan = models.AutoField(primary_key=True, null=False)
    ID_Usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    ID_Materia = models.ForeignKey(Materias, on_delete=models.CASCADE)
    Semestre = models.IntegerField(null=False, default=1, validators=[
                                MinValueValidator(1), MaxValueValidator(13)])
    Grupo = models.CharField(max_length=1, null=False,
                             choices=grupos, default='A')
    Hora = models.CharField(max_length=14,null=False,choices=horas,default="--:-- - --:--")
    Dia = models.CharField(max_length=10,null=False,choices=dias,default="Dia")
    Aula = models.CharField(max_length=4,null=False,default='A00')
