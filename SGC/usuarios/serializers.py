from rest_framework import serializers
from .models import Usuarios
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password')


class UsuarioSerializer(serializers.ModelSerializer):
    ID_Usuario = UserSerializer()

    class Meta:
        model = Usuarios
        fields = '__all__'

    def create(self, validated_data):
        UserData = validated_data.pop('ID_Usuario')
        user = User(**UserData)
        user.set_password(UserData['password'])
        user.save()
        usuario = Usuarios.objects.create(ID_Usuario=user, **validated_data)

        return usuario


class UsuarioInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuarios
        fields = ('PK', 'Nombre_Usuario', 'Tipo_Usuario', 'CorreoE', 'Permiso')


class CambioPassSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('password', 'new_password')

    password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class UpdateUsuarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Usuarios
        fields = ('Nombre_Usuario', 'Tipo_Usuario', 'CorreoE')

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
