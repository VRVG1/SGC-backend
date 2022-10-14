from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from .serializers import UsuarioSerializer, CambioPassSerializer, UsuarioInfoSerializer
from .models import Usuarios
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from persoAuth.permissions import AdminDocentePermission, AdminEspectadorPermission, OnlyAdminPermission, OnlyDocentePermission, AdminEspectadorDocentePermission
from rest_framework.authentication import TokenAuthentication
from .tasks import ForgotPass
# Create your views here.


class UsuarioView(generics.ListAPIView):
    '''
    Vista que permite ver todos los usuarios registrados en la BD
    (ADMIN, SUPERVISOR)
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, AdminEspectadorPermission]

    serializer_class = UsuarioSerializer
    queryset = Usuarios.objects.all()


class CreateUsuarioView(APIView):
    '''
    Vista que permite registrar un usuario en la BD
    (ADMIN)
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, OnlyAdminPermission]

    serializer_class = UsuarioSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CambiarPass(generics.UpdateAPIView):
    '''
    Vista que permite cambiar la contraseña de un usuario
    (DOCENTE) **Por concretar el como hacer el cambio de contraseña**
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, OnlyDocentePermission]

    serializer_class = CambioPassSerializer
    model = User

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # CHECAR SI AMBAS CONTRASEÑAS INGRESADAS SON LA MISMA
            if serializer.data.get('password') != serializer.data.get('new_password'):
                return Response({"password": ["Se debe ingresar la misma contraseña."]}, status=status.HTTP_400_BAD_REQUEST)
            # CIFRAR LA CONTRASEÑA CON set_password
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def borrar(request, pk=None):
    '''
    Vista que permite borrar un usuario de la BD
    (ADMIN)
    '''
    try:
        usuario = Usuarios.objects.get(PK=pk)
        user = User.objects.get(username=usuario.ID_Usuario)
    except Usuarios.DoesNotExist:
        return Response({'ERROR': 'El usuario no existe'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'DELETE':
        usuario.delete()
        user.delete()
        return Response({'Mensaje': 'Usuario eliminado correctamente'}, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def actualizar(request, pk):
    '''
    Vista que permite modificar los datos de un usuario
    (ADMIN)
    '''
    try:
        usuario = Usuarios.objects.get(PK=pk)
        user = User.objects.get(username=usuario.ID_Usuario.username)
    except Usuarios.DoesNotExist:
        return Response({'ERROR': 'El usuario no existe'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        usuario_serializer = UsuarioSerializer(usuario)
        return Response(usuario_serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        newUs = request.data['ID_Usuario']
        username = newUs['username']
        password = newUs['password']

        if bool(password) == False:
            pass
        else:
            user.set_password(password)
            user.save(update_fields=['password'])

        if bool(username) == False:
            pass
        else:
            user.username = username
            user.save(update_fields=['username'])

        try:
            usuario.PK = pk
            usuario.ID_Usuario = user
            usuario.Nombre_Usuario = request.data['Nombre_Usuario']
            usuario.Tipo_Usuario = request.data['Tipo_Usuario']
            usuario.CorreoE = request.data['CorreoE']
            print(request.data['Permiso'])
            if request.data['Permiso'] == 1:
                usuario.Permiso = True
            else:
                usuario.Permiso = False
            usuario.save()
            usuario = Usuarios.objects.get(PK=pk)
            usuario_serializer = UsuarioSerializer(usuario)
            return Response(usuario_serializer.data, status=status.HTTP_202_ACCEPTED)
        except:
            return Response(usuario_serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(['GET', 'PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def updateLoginInfo(request, pk):
    '''
    Vista que permite cambiar los datos necesarios para que el docente se loguee, (usuario y contraseña)
    (ADMIN Y DONCETE)
    '''
    try:
        usuario = Usuarios.objects.get(PK=pk)
        user = User.objects.get(username=usuario.ID_Usuario.username)
    except Usuarios.DoesNotExist:
        return Response({'ERROR': 'El usuario no existe'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        user.username = request.data['username']
        user.set_password(request.data['password'])
        try:
            user.save()
            usuario = Usuarios.objects.get(PK=pk)
            serializer = UsuarioSerializer(usuario)
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        except:
            return Response({'ERROR', 'Hubo problemas'}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def get(request, string):
    '''
    Vista que permite obtener usuario dependiendo de lo buscado (solo con lo
    ingresado que coincida con el inicio del nombre de usuario)
    (ADMIN)
    '''
    usuarios = Usuarios.objects.filter(
        Nombre_Usuario__startswith=string)
    if usuarios.exists():
        pass
    else:
        return Response({'ERROR': 'No hay usuarios con esta informacion'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        # PARA CUANDO SE OCUPA JALAR VARIOS RESULTADOS DEL QUERY EN SERIALIZER
        usuario_serializer = UsuarioSerializer(usuarios, many=True)
        return Response(usuario_serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminEspectadorDocentePermission])
def getInfoUser(request):
    '''
    Vista que recibe al user y devuelve sus datos para frontend
    (DOCENTE, ADMIN, ESPECTADOR)
    '''

    try:
        usuario = Usuarios.objects.get(ID_Usuario=request.user)
    except Usuarios.DoesNotExist:
        return Response({'Error': 'Usuario no existe'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        dic = {'username': usuario.ID_Usuario.username}
        usuario_serializer = UsuarioInfoSerializer(usuario)
        dic.update(usuario_serializer.data)
        return Response(dic, status=status.HTTP_200_OK)


@api_view(['POST'])
def OlvidoPass(request):
    '''
    Vista para cuando se le olvide la contraseña al usuario
    Generará una nueva con el formato contrasena_(username) para que al volvér a entrar
    la cambie.
    (DOCENTE)
    '''
    try:
        usuarioP = request.data['username']
        correo = request.data['email']
        usuario = Usuarios.objects.get(
            CorreoE=correo, ID_Usuario__username=usuarioP)
    except Usuarios.DoesNotExist:
        return Response({'Error', 'Usuario no existe'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        newP = 'contrasena_'+usuarioP.lower()
        msg = '''
            Hola '''+str(usuario.Nombre_Usuario)+''' Recibe este correo porque olvidó su contraseña del SGC (Sistema Gestor del Curso),
            hay que ser mas atento.

            Se ha generado una contraseña provisional para que pueda entrar. Se pide encarecidamente que en cuanto entre de nuevo
            al sistema CAMBIE la contraseña por una que no olvide.

            Contraseña provisional: '''+newP+'''

            Sistema Automatizado de correos.
            (No conteste a este correo).
        '''
        try:
            user = User.objects.get(username=usuario.ID_Usuario.username)
            user.set_password(newP)
            user.save()
            ForgotPass.delay(msg, correo)
            return Response({'ENVIADO', 'Correo enviado con exito'}, status=status.HTTP_200_OK)
        except:
            return Response({'ERROR', 'Error al enviar el correo'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def actualizarPropiosDatos(request, pk):
    '''
    Vista que permite modificar los datos basicos de un usuario por si mismo
    (DOCENTE)
    '''
    try:
        usuario = Usuarios.objects.get(PK=pk)
        user = User.objects.get(username=usuario.ID_Usuario.username)
    except Usuarios.DoesNotExist:
        return Response({'ERROR': 'El usuario no existe'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        usuario_serializer = UsuarioSerializer(usuario)
        return Response(usuario_serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        newUs = request.data['ID_Usuario']
        username = newUs['username']
        password = newUs['password']

        if bool(password) == False:
            pass
        else:
            user.set_password(password)
            user.save(update_fields=['password'])

        if bool(username) == False:
            pass
        else:
            user.username = username
            user.save(update_fields=['username'])

        try:
            usuario.PK = pk
            usuario.ID_Usuario = user
            usuario.Nombre_Usuario = request.data['Nombre_Usuario']
            usuario.CorreoE = request.data['CorreoE']
            usuario.save()
            usuario = Usuarios.objects.get(PK=pk)
            usuario_serializer = UsuarioSerializer(usuario)
            return Response(usuario_serializer.data, status=status.HTTP_202_ACCEPTED)
        except:
            return Response(usuario_serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)
