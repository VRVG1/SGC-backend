from rest_framework import permissions
from usuarios.models import Usuarios


class OnlyAdminPermission(permissions.BasePermission):
    """
    OnlyAdminPermission
    Permite el acceso a toda interfaz visible para un usuario de tipo
    administrador.
    """

    def has_permission(self, request, view):
        user = Usuarios.objects.get(ID_Usuario=request.user)

        return user.Tipo_Usuario == 'Administrador'


class OnlyDocentePermission(permissions.BasePermission):
    """
    OnlyDocentePermission
    Permite el acceso a toda interfaz visible para un usuario de tipo
    docente.
    """

    def has_permission(self, request, view):
        user = Usuarios.objects.get(ID_Usuario=request.user)

        return user.Tipo_Usuario == 'Docente'


class OnlyEspectadorPermission(permissions.BasePermission):
    """
    DocentePermission
    Permite el acceso a toda interfaz visible para un usuario de tipo
    espectador.
    """

    def has_permission(self, request, view):
        user = Usuarios.objects.get(ID_Usuario=request.user)

        return user.Tipo_Usuario == 'Supervisor'


class AdminDocentePermission(permissions.BasePermission):
    """
    AdminDocentePermission
    Permite el acceso a toda interfaz visible para un usuario de tipo
    administrador o docente.
    """

    def has_permission(self, request, view):
        user = Usuarios.objects.get(ID_Usuario=request.user)

        return user.Tipo_Usuario in ['Administrador', 'Docente']


class AdminEspectadorPermission(permissions.BasePermission):
    """
    AdminEspectadorPermission
    Permite el acceso a toda interfaz visible para un usuario de tipo
    administrador o espectador.
    """

    def has_permission(self, request, view):
        user = Usuarios.objects.get(ID_Usuario=request.user)

        return user.Tipo_Usuario in ['Administrador', 'Supervisor']


class DocenteEspectadorPermission(permissions.BasePermission):
    """
    DocenteEspectadorPermission
    Permite el acceso a toda interfaz visible para un usuario de tipo
    docente o espectador.
    """

    def has_permission(self, request, view):
        user = Usuarios.objects.get(ID_Usuario=request.user)

        return user.Tipo_Usuario in ['Docente', 'Supervisor']


class AdminEspectadorDocentePermission(permissions.BasePermission):
    """
    AdminEspectadorDocentePermission
    Permite el acceso a toda interfaz visible para un usuario de tipo
    administrador o espectador o docente.
    """

    def has_permission(self, request, view):
        user = Usuarios.objects.get(ID_Usuario=request.user)
        return user.Tipo_Usuario in ['Administrador', 'Supervisor', 'Docente']
