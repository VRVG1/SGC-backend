from django.db import models
from materias.models import Asignan
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.


class Reportes(models.Model):
    class Meta:
        db_table = 'Reportes'

    ID_Reporte = models.AutoField(primary_key=True, null=False)
    Nombre_Reporte = models.CharField(
        max_length=480, null=False, unique=True)
    Fecha_Entrega = models.DateField(null=False)
    Descripcion = models.TextField(max_length=1000, null=True, blank=True)
    Opcional = models.BooleanField(default=False)
    Unidad = models.BooleanField(default=False)


class Generan(models.Model):
    class Meta:
        db_table = 'Generan'

    ID_Generacion = models.AutoField(primary_key=True)
    Estatus = models.CharField(max_length=20, null=True)
    Fecha_Entrega = models.DateField(null=False)
    ID_Asignan = models.ForeignKey(Asignan, on_delete=models.CASCADE)
    ID_Reporte = models.ForeignKey(Reportes, on_delete=models.CASCADE)
    Periodo = models.CharField(max_length=24,null=False,default='X - X XXXX')
    Reprobados = models.IntegerField(null=False, validators=[MinValueValidator(0),MaxValueValidator(100)])
    Unidad = models.IntegerField(null=False,validators=[MinValueValidator(1),MaxValueValidator(6)], default=0)



class Alojan(models.Model):
    class Meta:
        db_table = 'Alojan'

    ID_Alojan = models.AutoField(primary_key=True, null=False)
    ID_Generacion = models.ForeignKey(Generan, on_delete=models.CASCADE)
    Path_PDF = models.FileField(upload_to="Generados", null=False)
