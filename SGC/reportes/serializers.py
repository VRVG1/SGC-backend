from re import A
from rest_framework import serializers

from materias.models import Asignan
from .models import Reportes, Generan, Alojan


class ReportesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reportes
        fields = '__all__'


class GeneranSerializer(serializers.ModelSerializer):
    class Meta:
        model = Generan
        fields = '__all__'


class AlojanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alojan
        fields = '__all__'


class UpdateGeneranSerializer(serializers.ModelSerializer):
    class Meta:
        model = Generan
        fields = ('Estatus', 'Path_PDF')
