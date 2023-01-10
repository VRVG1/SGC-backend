from rest_framework import serializers
from .models import Materias, Carreras, Asignan


class CarreraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carreras
        fields = '__all__'

    def create(self, validated_data):
        carrera = Carreras.objects.create(**validated_data)
        return carrera


class MateriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materias
        fields = '__all__'

    def create(self, validated_data):
        materia = Materias.objects.create(**validated_data)
        return materia


class AsignanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asignan
        fields = '__all__'

    def create(self, validated_data):
        asign = Asignan.objects.create(**validated_data)
        return asign
