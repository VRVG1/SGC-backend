from urllib import request
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from datetime import date, datetime
from usuarios.models import Usuarios
from .serializers import CarreraSerializer, MateriaSerializer, AsignanSerializer
from .models import Asignan, Materias, Carreras
from django.contrib.auth.models import User
from django.db.models import Q
from reportes.models import Generan, Reportes
from persoAuth.permissions import OnlyAdminPermission, AdminDocentePermission, AdminEspectadorDocentePermission, AdminEspectadorPermission

# Create your views here.


class MateriasView(generics.ListAPIView):
    '''
    Vista que muestra todas las materias registradas
    (ADMIN, DOCENTE, SUPERVISOR)
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, AdminEspectadorDocentePermission]

    serializer_class = MateriaSerializer
    queryset = Materias.objects.all()


class CarrerasView(generics.ListAPIView):
    '''
    Vista que muestra todas las carreras registradas
    (ADMIN Y DOCENTE)
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, AdminDocentePermission]

    serializer_class = CarreraSerializer
    queryset = Carreras.objects.all()


class AsignanView(generics.ListAPIView):
    '''
    Vista que muestra todos los asignan registradas
    (ADMIN y SUPERVISOR)
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, AdminEspectadorPermission]

    serializer_class = AsignanSerializer
    queryset = Asignan.objects.all()


class CreateMateriasView(APIView):
    '''
    Vista que permite crear (registrar) materias en la BD
    (ADMIN)
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, OnlyAdminPermission]

    serializer_class = MateriaSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateCarreraView(APIView):
    '''
    Vista que permite crear (registrar) carreras en la BD
    (ADMIN)
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, OnlyAdminPermission]

    serializer_class = CarreraSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AsignarMateriaView(APIView):
    '''
    Vista que permite crear (registrar) la asignacion de materia a un usuario en la BD
    Verifica si hay reportes registrados antes de la asignacion actual para registrarle al maestro
    los reportes pasados.
    (ADMIN y DOCENTE)
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, AdminDocentePermission]

    serializer_class = AsignanSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            usuario = serializer.validated_data.get('ID_Usuario')
            materia = serializer.validated_data.get('ID_Materia')
            semestre = serializer.validated_data.get('Semestre')
            grupo = serializer.validated_data.get('Grupo')
            hora = serializer.validated_data.get('Hora')
            dia = serializer.validated_data.get('Dia')
            aula = serializer.validated_data.get('Aula')

            try:
                asignan = Asignan.objects.get(
                    ID_Usuario=usuario, ID_Materia=materia, Grupo=grupo, Hora=hora, Dia=dia, Aula=aula, Semestre=semestre)
            except Asignan.DoesNotExist:
                serializer.save()

            reportes = Reportes.objects.all()
            if not reportes:
                asignan = Asignan.objects.get(
                    ID_Usuario=usuario, ID_Materia=materia, Grupo=grupo, Hora=hora, Dia=dia, Aula=aula, Semestre=semestre)
                crearReportesUnidad(asignan,usuario)
            else:
                date01 = 'Jun 20'
                fecha = date.today()
                parse01 = datetime.strptime(
                    date01, '%b %d').date().replace(year=fecha.year)

                if fecha < parse01:
                    periodo = 'Enero - Junio ' + str(fecha.year)
                else:
                    periodo = 'Agosto - Diciembre ' + str(fecha.year)

                asignan = Asignan.objects.get(
                    ID_Usuario=usuario, ID_Materia=materia, Grupo=grupo, Hora=hora, Dia=dia, Aula=aula, Semestre=semestre)
                for x in reportes:
                    if x.Unidad != True:
                        generate = Generan(
                            Estatus=None, ID_Asignan=asignan, ID_Reporte=x, Periodo=periodo, Reprobados=0, Fecha_Entrega=x.Fecha_Entrega)
                        generate.save()

                crearReportesUnidad(asignan,usuario)

            user = Usuarios.objects.get(Nombre_Usuario=usuario)
            user.Permiso = False
            user.save()

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

'''
Metodo que ayuda a realizar la asignacion de reportes de unidad a cada maestro
que se asigne materias.
'''
def crearReportesUnidad(asignan,usuario):
    user = Usuarios.objects.get(Nombre_Usuario=usuario)
    materia = Materias.objects.get(Clave_reticula=asignan.ID_Materia.Clave_reticula)

    manyAsignan = Asignan.objects.filter(Q(ID_Usuario=asignan.ID_Usuario, ID_Materia=asignan.ID_Materia, Semestre=asignan.Semestre, Grupo=asignan.Grupo) & ~Q(Hora=asignan.Hora,Dia=asignan.Dia,Aula=asignan.Aula))

    if len(manyAsignan) < 1:
        date01 = 'Jun 20'
        fecha = date.today()
        parse01 = datetime.strptime(
            date01, '%b %d').date().replace(year=fecha.year)

        if fecha < parse01:
            semestre = 'Enero - Junio ' + str(fecha.year)
        else:
            semestre = 'Agosto - Diciembre ' + str(fecha.year)

        for i in range(materia.unidades):
            report = Reportes(
                Nombre_Reporte = f'{materia.Nombre_Materia} - Grupo: {asignan.Grupo} - Unidad: {i+1} - {user.Nombre_Usuario}',
                Fecha_Entrega = date.today(),
                Descripcion = '',
                Opcional = False,
                Unidad = True
            )
            report.save()

            generate = Generan(
                Estatus = '',
                Fecha_Entrega = date.today(),
                ID_Asignan = asignan,
                ID_Reporte = report,
                Periodo = semestre,
                Reprobados = -1,
                Unidad = i+1
            )
            generate.save()

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def getAsignan(request):
    '''
    Vista que permite obtener todos los asignan de un docente
    (ADMIN Y DOCENTE)
    '''

    try:
        usuario = Usuarios.objects.get(ID_Usuario=request.user)
        asign = Asignan.objects.filter(ID_Usuario=usuario)
    except Asignan.DoesNotExist:
        return Response({'Error': 'No hay asignan'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AsignanSerializer(asign, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def getAsignanpk(request, pk):
    '''
    Vista que permite obtener todos los asignan de un docente
    (ADMIN Y DOCENTE)
    '''

    try:
        usuario = Usuarios.objects.get(PK=pk)
        asign = Asignan.objects.filter(ID_Usuario=usuario)
    except Asignan.DoesNotExist:
        return Response({'Error': 'No hay asignan'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AsignanSerializer(asign, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def borrarM(request, pk):
    '''
    Vista que permite borrar una materia de la BD
    (ADMIN)
    '''
    try:
        materia = Materias.objects.get(Clave_reticula=pk)
    except Materias.DoesNotExist:
        return Response({'Error': 'Materia no existe'}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        materia_serializer = MateriaSerializer(materia)
        return Response(materia_serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'DELETE':
        materia.delete()
        return Response({'Mensaje': 'Materia borrada'}, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def updateM(request, pk):
    '''
    Vista que permite actualizar (modificar) una materia de la BD
    (ADMIN)
    '''
    try:
        materia = Materias.objects.get(Clave_reticula=pk)
    except Materias.DoesNotExist:
        return Response({'Error': 'Materia no existe'}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        materia_serializer = MateriaSerializer(materia)
        return Response(materia_serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer_class = MateriaSerializer(materia, data=request.data)
        if serializer_class.is_valid():
            serializer_class.save()
            return Response(serializer_class.data, status=status.HTTP_200_OK)
        return Response(serializer_class.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def borrarC(request, pk):
    '''
    Vista que permite borrar una carrera de la BD
    (ADMIN)
    '''
    try:
        carrera = Carreras.objects.get(ID_Carrera=pk)
    except Carreras.DoesNotExist:
        return Response({'Error': 'Carrera no existe'}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        carrera_serializer = CarreraSerializer(carrera)
        return Response(carrera_serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'DELETE':
        carrera.delete()
        return Response({'Mensaje': 'Carrera borrada'}, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def updateC(request, pk):
    '''
    Vista que permite actualizar (modificar) una carrera de la BD
    (ADMIN)
    '''
    try:
        carrera = Carreras.objects.get(ID_Carrera=pk)
    except Carreras.DoesNotExist:
        return Response({'Error': 'Carrera no existe'}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        carrera_serializer = CarreraSerializer(carrera)
        return Response(carrera_serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer_class = CarreraSerializer(carrera, data=request.data)
        if serializer_class.is_valid():
            serializer_class.save()
            return Response(serializer_class.data, status=status.HTTP_200_OK)
        return Response(serializer_class.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def borrarAs(request, pkM):
    '''
    Vista que permite borrar una asignacion de la BD
    (ADMIN y DOCENTE)
    '''
    try:
        asign = Asignan.objects.get(ID_Asignan=pkM)
    except Carreras.DoesNotExist:
        return Response({'Error': 'Esta asignacion no existe'}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        try:
            asign = Asignan.objects.get(ID_Asignan=pkM)
        except Asignan.DoesNotExist:
            return Response({'Error': 'Esta asignacion no existe'}, status=status.HTTP_400_BAD_REQUEST)

        asig_serializer = AsignanSerializer(asign)
        return Response(asig_serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        usuario = Usuarios.objects.get(ID_Usuario=asign.ID_Usuario.ID_Usuario)
        generan = Generan.objects.filter(ID_Asignan=asign)
        for i in generan:
            report = Reportes.objects.get(ID_Reporte=i.ID_Reporte.ID_Reporte)
            report.delete()
        usuario.Permiso = False
        usuario.save()
        asign.delete()
        return Response({'Mensaje': 'Asignacion borrada'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def getAsignanEspecific(request, pk):
    '''
    Vista que permite obtener la informacion de un asignan especifico
    (DOCENTE)
    '''
    try:
        asignan = Asignan.objects.get(ID_Asignan=pk)
    except Generan.DoesNotExist:
        return Response({'Error': 'No hay asignan'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AsignanSerializer(asignan)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def AdminGetAsignan(request, pk):
    '''
    Vista que regresa todos los asignan de un docente buscado por el admin
    (ADMIN)
    '''
    try:
        usuario = Usuarios.objects.get(PK=pk)
        asignan = Asignan.objects.filter(ID_Usuario=usuario)
    except Usuarios.DoesNotExist:
        return Response({'Error': 'Usuario no existe'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AsignanSerializer(asignan, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def getMateriasXCarrera(request, id):
    '''
    Vista que regresa todas las materias de una carrera por su pk
    (ADMIN Y DOCENTE)
    '''
    try:
        carrera = Carreras.objects.get(ID_Carrera=id)
        materias = Materias.objects.filter(Carrera=carrera)
    except Carreras.DoesNotExist:
        return Response({'Error':'Carrera no existe'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = MateriaSerializer(materias, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def getAsignanCarrerapk(request, pk):
    '''
    Vista que permite obtener todos los asignan de un docente (con la carrera)
    (ADMIN Y DOCENTE)
    '''

    try:
        usuario = Usuarios.objects.get(PK=pk)
        asign = Asignan.objects.filter(ID_Usuario=usuario)
    except Asignan.DoesNotExist:
        return Response({'Error': 'No hay asignan'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        lista = []
        for i in asign:
            aux = {'ID_Asignan':i.ID_Asignan,'Semestre':i.Semestre,'Grupo':i.Grupo,'Hora':i.Hora,'Dia':i.Dia,'Aula':i.Aula,'ID_Usuario':i.ID_Usuario.PK,'Nombre_Materia':i.ID_Materia.Nombre_Materia,'Carrera':i.ID_Materia.Carrera.Nombre_Carrera}
            lista.append(aux)
        return Response(lista, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def getAsignanCarreraNamespk(request, pk):
    '''
    Vista que permite obtener todos los asignan de un docente (con la carrera con nombres y pk's)
    (ADMIN Y DOCENTE)
    '''

    try:
        usuario = Usuarios.objects.get(PK=pk)
        asign = Asignan.objects.filter(ID_Usuario=usuario)
    except Asignan.DoesNotExist:
        return Response({'Error': 'No hay asignan'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        lista = []
        for i in asign:
            aux = {
                'ID_Asignan':i.ID_Asignan,
                'ID_Carrera':i.ID_Materia.Carrera.ID_Carrera,
                'ID_Materia':i.ID_Materia.pik,
                'ID_Usuario':i.ID_Usuario.PK,
                'Nombre_Materia':i.ID_Materia.Nombre_Materia,
                'Carrera':i.ID_Materia.Carrera.Nombre_Carrera,
                'Semestre':i.Semestre,
                'Grupo':i.Grupo,
                'Hora':i.Hora,
                'Dia':i.Dia,
                'Aula':i.Aula,
            }
            lista.append(aux)
        return Response(lista, status=status.HTTP_200_OK)
    
'''
**************************************************************************************
* Aqui empiezan las views de los filtros necesarios y reportes                       *
* de la (parte 2).                                                                   *
*                                                                                    *
* La parte 2 es de Greñas                                                            *
**************************************************************************************
'''

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MateriasCarrera(request, query):
    '''
    View que corresponde al filtro: Materias por carrera.
    (ADMIN)
    '''
    try:
        materias = Materias.objects.filter(Carrera__Nombre_Carrera__startswith=query)
    except Materias.DoesNotExist:
        return Response({'Error':'Materias no existen'},status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = MateriaSerializer(materias, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MateriasMaestro(request, query):
    '''
    Vista para el filtro: Materias que imparte cada maestro, así como la carrera a la que
    pertenece la materia.

    (Puede que tenga que anexar lo ultimo, habrá que ver).
    (ADMIN)
    '''
    try: 
        asignan = Asignan.objects.filter(ID_Usuario__Nombre_Usuario__startswith=query)
    except Asignan.DoesNotExist:
        return Response({'Error':'Asignan no existe'},status=status.HTTP_404_NOT_FOUND)
    
    try:
        lista = []
        for i in asignan:
            materia = Materias.objects.get(pik=i.ID_Materia.pik)
            lista.append(materia)
        materias = set(lista)
    except Materias.DoesNotExist:
        return Response({'Error':'Materia no existe'},status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        lista = []
        serializer = list(materias)
        for i in serializer:
            aux = {
                'pik':i.pik,
                'Clave_reticula':i.Clave_reticula,
                'Carrera':i.Carrera.ID_Carrera,
                'Nombre_Materia':i.Nombre_Materia,
                'horas_Teoricas':i.horas_Teoricas,
                'horas_Practicas':i.horas_Practicas,
                'creditos':i.creditos,
                'unidades':i.unidades
            }
            lista.append(aux)
        return Response(lista,status=status.HTTP_200_OK)
    
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MateriasHora(request, query):
    '''
    Vista que pertenece al filtro: Materias que se imparten en cierta hora.
    (ADMIN)
    '''
    try:
        asignan = Asignan.objects.filter(Hora__startswith=query)
    except Asignan.DoesNotExist:
        return Response({'Error':'Asignan no existen'},status=status.HTTP_404_NOT_FOUND)
    
    try:
        lista = []
        for i in asignan:
            materia = Materias.objects.get(pik=i.ID_Materia.pik)
            lista.append(materia)
        materias = set(lista)
    except Materias.DoesNotExist:
        return Response({'Error':'Materia no existe'},status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        lista = []
        serializer = list(materias)
        for i in serializer:
            aux = {
                'pik':i.pik,
                'Clave_reticula':i.Clave_reticula,
                'Carrera':i.Carrera.ID_Carrera,
                'Nombre_Materia':i.Nombre_Materia,
                'horas_Teoricas':i.horas_Teoricas,
                'horas_Practicas':i.horas_Practicas,
                'creditos':i.creditos,
                'unidades':i.unidades
            }
            lista.append(aux)
        return Response(lista,status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MateriasAula(request, query):
    '''
    Vista que pertenece al filtro: Materias que se imparten en cierta aula.
    (ADMIN)
    '''
    try:
        asignan = Asignan.objects.filter(Aula__startswith=query)
    except Asignan.DoesNotExist:
        return Response({'Error':'Asignan no existen'},status=status.HTTP_404_NOT_FOUND)
    
    try:
        lista = []
        for i in asignan:
            materia = Materias.objects.get(pik=i.ID_Materia.pik)
            lista.append(materia)
        materias = set(lista)
    except Materias.DoesNotExist:
        return Response({'Error':'Materia no existe'},status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        lista = []
        serializer = list(materias)
        for i in serializer:
            aux = {
                'pik':i.pik,
                'Clave_reticula':i.Clave_reticula,
                'Carrera':i.Carrera.ID_Carrera,
                'Nombre_Materia':i.Nombre_Materia,
                'horas_Teoricas':i.horas_Teoricas,
                'horas_Practicas':i.horas_Practicas,
                'creditos':i.creditos,
                'unidades':i.unidades
            }
            lista.append(aux)
        return Response(lista,status=status.HTTP_200_OK)
    
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MateriasGrupo(request, query):
    '''
    Vista que pertenece al filtro: Materias que se imparten en cierto grupo.
    (ADMIN)
    '''
    try:
        asignan = Asignan.objects.filter(Grupo__startswith=query)
    except Asignan.DoesNotExist:
        return Response({'Error':'Asignan no existen'},status=status.HTTP_404_NOT_FOUND)
    
    try:
        lista = []
        for i in asignan:
            materia = Materias.objects.get(pik=i.ID_Materia.pik)
            lista.append(materia)
        materias = set(lista)
    except Materias.DoesNotExist:
        return Response({'Error':'Materia no existe'},status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        lista = []
        serializer = list(materias)
        for i in serializer:
            aux = {
                'pik':i.pik,
                'Clave_reticula':i.Clave_reticula,
                'Carrera':i.Carrera.ID_Carrera,
                'Nombre_Materia':i.Nombre_Materia,
                'horas_Teoricas':i.horas_Teoricas,
                'horas_Practicas':i.horas_Practicas,
                'creditos':i.creditos,
                'unidades':i.unidades
            }
            lista.append(aux)
        return Response(lista,status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MateriasCreditos(request, query):
    '''
    View que pertenece al filtro: Materias que tienen cierta cantidad de créditos.
    (ADMIN)
    '''
    try:
        materias = Materias.objects.filter(creditos=query)
        print(materias)
    except Materias.DoesNotExist:
        return Response({'Error':'No existen asignan'})
    
    if request.method == 'GET':
        serializer = MateriaSerializer(materias, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
        