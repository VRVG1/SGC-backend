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
from django.http import FileResponse
import io
from fpdf import FPDF

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
    except Materias.DoesNotExist:
        return Response({'Error':'No existen materias'})
    
    if request.method == 'GET':
        serializer = MateriaSerializer(materias, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MateriasUnidades(request, query):
    '''
    View que pertenece al filtro: Materias que tienen cierto numero de unidades.
    (ADMIN)
    '''
    try:
        materias = Materias.objects.filter(unidades=query)
    except Materias.DoesNotExist:
        return Response({'Error':'No existen materias'})
    
    if request.method == 'GET':
        serializer = MateriaSerializer(materias, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
def p2HorasTeoCarrera(query):
    '''
    Metodo de apoyo para obtener las horas totales teoricas de una carrera
    '''
    carreras = Carreras.objects.filter(Nombre_Carrera__startswith=query)

    for i in carreras:
        materias = Materias.objects.filter(Carrera=i)

    horasTeo = 0
    for i in materias:
        horasTeo = horasTeo + i.horas_Teoricas
    
    return horasTeo

def p2HorasPraCarrera(query):
    '''
    Metodo de apoyo para obtener las horas totales practicas de una carrera
    '''
    carreras = Carreras.objects.filter(Nombre_Carrera__startswith=query)

    for i in carreras:
        materias = Materias.objects.filter(Carrera=i)

    horasPra = 0
    for i in materias:
        horasPra = horasPra + i.horas_Practicas
    
    return horasPra

titulo = ''

class PDF(FPDF):
    def header(self):
        # Header ************************************************
        global titulo
        self.set_font("helvetica", 'B',size=12)
        self.image("./static/tecnm.png", 10, 10, 45, 20, "") # Carga la foto del tecnm
        self.set_left_margin(55) # Margen para separar la imagen del texto centrado
        self.image("./static/itcg.png", 185, 10, 20, 20, "") # Carga la foto del itcg
        self.set_right_margin(55) # Margen para separar la imagen del texto centrado
        self.cell(w=0,txt='Instituto Tecnológico de Ciudad Guzman',border=0,ln=2,align='C')
        self.cell(txt=' ',border=0,ln=2)
        self.set_font("helvetica", size=12)
        self.multi_cell(w=0,txt='Sistema para la gestión del curso "SGC"\n',border=0,ln=2,align='C')

        self.multi_cell(w=0,txt=f'Reporte de: {titulo}',border=0,ln=2,align='C')
        self.set_left_margin(10) # MARGEN REAL
        self.set_right_margin(10)
        # Header ************************************************

    def footer(self):
        # Footer ************************************************
        # -15 representa 1.5cm del fondo de la pagina:
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        # Poner el numero de pagina y fecha:
        hoy = date.today()
        fecha = hoy.strftime('%d/%m/%Y')
        self.multi_cell(0, 10, f"Reporte recuperado el: {fecha}. Pagina {self.page_no()}/{{nb}}", align="C")
        # Footer ************************************************

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MateriasCarreraPDF(request, query):
    '''
    View que corresponde al PDF: Materias por carrera.
    (ADMIN)
    '''
    try:
        materias = Materias.objects.filter(Carrera__Nombre_Carrera__startswith=query)
    except Materias.DoesNotExist:
        return Response({'Error':'Materias no existen'},status=status.HTTP_404_NOT_FOUND)

    if materias:
        buffer = io.BytesIO()

        global titulo
        titulo = 'Materias por carrera\n'

        pdf = PDF(format='Letter')
        pdf.add_page()
        pdf.set_font("helvetica",size=12)
        pdf.set_title('Materias por carrera')

        aux = set()
        for i in materias:
            aux.add(i.Carrera.Nombre_Carrera)
        
        # pdf.multi_cell(w=0,txt=f'Reporte de: Materias por carrera\n',border=0,ln=2,align='C')
        pdf.set_left_margin(10) # MARGEN REAL
        pdf.set_right_margin(10)
        
        pdf.cell(txt=f'De su busqueda "{query}" se obtuvo la(s) siguiente(s) relación(es):',border=0,ln=2,align='L')

        txt = ''
        for i in aux:
            txt = txt + f'- {i}\n'
        
        le = len(txt)
        
        pdf.multi_cell(w=0,txt=txt[:le-1],border=0,ln=2)
        pdf.set_draw_color(192, 194, 196)

        data = []
        for a in aux:
            data.append([a])
            data.append(['Clave reticula','Materia','Unidades','Creditos','Horas Teoricas','Horas Practicas'])
            for i in materias:
                if i.Carrera.Nombre_Carrera == a:
                    data.append([i.Carrera.ID_Carrera,i.Nombre_Materia,str(i.unidades),str(i.creditos),str(i.horas_Teoricas),str(i.horas_Practicas)])
            data.append(['Total de horas teoricas','Total de horas practicas'])
            data.append([str(p2HorasTeoCarrera(a)),str(p2HorasPraCarrera(a))])

        tamL = pdf.font_size_pt * 0.7
        tamC = pdf.epw
        f = False
        for i in data:
            if len(i) > 1:
                pdf.set_font('Helvetica',size=12)
                for u in i:
                    if 'Total de horas teoricas' in i:
                        f = True
                        pdf.cell(w=tamC/2,h=tamL,txt=u,border=1,align='C')
                    elif f == True:
                        pdf.set_font('Helvetica','B',size=12)
                        pdf.cell(w=tamC/2,h=tamL,txt=u,border=1,align='C')
                    else:
                        pdf.cell(w=tamC/6,h=tamL,txt=u,border=1)
                pdf.ln(tamL)
            else:
                f = False
                pdf.set_font('Helvetica','B',size=12)
                pdf.ln(5)
                for u in i:
                    pdf.cell(w=0,h=tamL,txt=u,border=1,ln=2,align='C')

        pdf.output(buffer)

        buffer.seek(0)

        if request.method == 'GET':
            return FileResponse(buffer, filename='Materias.pdf', as_attachment=False)
    else:
        if request.method == 'GET':
            return Response({'Error','No hay información para poblar el pdf'},status=status.HTTP_204_NO_CONTENT)
        
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MateriasMaestroPDF(request, query):
    '''
    Vista para el PDF: Materias que imparte cada maestro, así como la carrera a la que
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
    
    buffer = io.BytesIO()

    global titulo
    titulo = 'Materias que imparte cada maestro\n'

    pdf = PDF(format='Letter')
    pdf.add_page()
    pdf.set_font("helvetica",size=12)
    pdf.set_title('Materias que imparte cada maestro')

    # pdf.multi_cell(w=0,txt=f'Reporte de: Materias que imparte cada maestro\n',border=0,ln=2,align='C')
    pdf.set_left_margin(10) # MARGEN REAL
    pdf.set_right_margin(10)

    pdf.cell(txt=f'De su busqueda: "{query}" se obtuvo la(s) siguiente(s) relación(es):',border=0,ln=2,align='L')

    txt = ''
    carreras = []
    maestros = set()
    for i in asignan:
        maestros.add(i.ID_Usuario.Nombre_Usuario)
        carreras.append(i.ID_Materia.Carrera.Nombre_Carrera)

    for i in maestros:
        txt = txt + f'- {i}\n'

    le = len(txt)

    pdf.multi_cell(w=0,txt=txt[:le-1],border=0,ln=2,align='L')

    pdf.set_draw_color(192, 194, 196)

    data = []
    oldC = ''
    oldM = []
    for m in maestros:
        data.append([m])
        asign = Asignan.objects.filter(ID_Usuario__Nombre_Usuario = m).order_by('ID_Materia__Carrera')
        for x,i in enumerate(asign):
            if x == 0:
                data.append([i.ID_Materia.Carrera.Nombre_Carrera])
                data.append(['Materia','Unidades','Creditos','Hrs. Teoricas','Hrs. Practicas'])
                data.append([i.ID_Materia.Nombre_Materia,str(i.ID_Materia.unidades),str(i.ID_Materia.creditos),str(i.ID_Materia.horas_Teoricas),str(i.ID_Materia.horas_Practicas)])
                oldC = i.ID_Materia.Carrera.Nombre_Carrera
                oldM.append(i.ID_Materia.Nombre_Materia)
            else:
                if oldC == i.ID_Materia.Carrera.Nombre_Carrera:
                    if i.ID_Materia.Nombre_Materia not in oldM:
                        data.append([i.ID_Materia.Nombre_Materia,str(i.ID_Materia.unidades),str(i.ID_Materia.creditos),str(i.ID_Materia.horas_Teoricas),str(i.ID_Materia.horas_Practicas)])
                        oldM.append(i.ID_Materia.Nombre_Materia)
                else:
                    data.append([i.ID_Materia.Carrera.Nombre_Carrera])
                    data.append(['Materia','Unidades','Creditos','Hrs. Teoricas','Hrs. Practicas'])
                    data.append([i.ID_Materia.Nombre_Materia,str(i.ID_Materia.unidades),str(i.ID_Materia.creditos),str(i.ID_Materia.horas_Teoricas),str(i.ID_Materia.horas_Practicas)])
                    oldC = i.ID_Materia.Carrera.Nombre_Carrera
                    oldM.append(i.ID_Materia.Nombre_Materia)
        oldM = []
    
    tamL = pdf.font_size_pt * 0.7
    tamC = pdf.epw

    for i in data:
        if len(i) > 1:
            for u in i:
                pdf.set_font('Helvetica',size=12)
                pdf.cell(w=tamC/5,h=tamL,txt=u,border=1,ln=0)
            pdf.ln(tamL)
        else:
            if i[0] in maestros:
                pdf.ln(tamL)
                pdf.set_font('Helvetica','B',size=12)
                pdf.cell(w=0,h=tamL,txt=i[0],border=1,ln=2,align='C')
            else:
                pdf.set_font('Helvetica','B',size=12)
                pdf.cell(w=0,h=tamL,txt=i[0],border=1,ln=2,align='C')

    pdf.output(buffer)

    buffer.seek(0)
    
    if request.method == 'GET':
            return FileResponse(buffer, filename='Materias.pdf', as_attachment=False)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MateriasHoraPDF(request, query):
    '''
    Vista que pertenece al filtro: Materias que se imparten en cierta hora.
    (ADMIN)
    '''
    try:
        asignan = Asignan.objects.filter(Hora=query)
    except Asignan.DoesNotExist:
        return Response({'Error':'Asignan no existen'},status=status.HTTP_404_NOT_FOUND)
    
    try:
        lista = []
        for i in asignan:
            materia = Materias.objects.get(pik=i.ID_Materia.pik)
            lista.append(materia.Nombre_Materia)
        materias = list(set(lista))
    except Materias.DoesNotExist:
        return Response({'Error':'Materia no existe'},status=status.HTTP_404_NOT_FOUND)
    
    buffer = io.BytesIO()
    
    global titulo
    titulo = 'Materias que se imparten en cierta hora\n'

    pdf = PDF(format='Letter')
    pdf.add_page()
    pdf.set_font("helvetica",size=12)
    pdf.set_title('Materias que se imparten en cierta hora')

    # pdf.multi_cell(w=0,txt=f'Reporte de: Materias que se imparten en cierta hora\n',border=0,ln=2,align='C')

    pdf.set_left_margin(55) # MARGEN REAL
    pdf.set_right_margin(55)

    pdf.multi_cell(w=0,txt=f'Las siguientes materias se imparten durante: {query}\n',border=0,ln=1,align='C')
    
    pdf.set_left_margin(10) # MARGEN REAL
    pdf.set_right_margin(10)

    pdf.set_draw_color(192, 194, 196)

    data = []
    for i in asignan:
        data.append([i.ID_Materia.Nombre_Materia])
        data.append(['Semestre','Grupo','Dia','Aula'])
        data.append([i.Semestre,i.Grupo,i.Dia,i.Aula])
        data.append(['Maestro(a)'])
        data.append([i.ID_Usuario.Nombre_Usuario])

    tamL = pdf.font_size_pt * 0.7
    tamC = pdf.epw
    m = False

    for i in data:
        if len(i) > 1:
            pdf.set_font('helvetica',size=12)
            for u in i:
                pdf.cell(w=tamC/4,h=tamL,txt=f'{u}',border=1,ln=0,align='L')
            pdf.ln(tamL)
        if i[0] in materias:
            pdf.set_font('helvetica','B',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=2,align='C')
        if m:
            pdf.set_font('helvetica',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=2,align='C')
            m = False
            pdf.ln(tamL)
        if i[0] == 'Maestro(a)':
            m = True
            pdf.set_font('helvetica','B',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=2,align='C')


    pdf.output(buffer)

    buffer.seek(0)

    if request.method == 'GET':
        return FileResponse(buffer,filename='Materias.pdf',as_attachment=False)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MateriasAulaPDF(request, query):
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
            lista.append(materia.Nombre_Materia)
        materias = set(lista)
    except Materias.DoesNotExist:
        return Response({'Error':'Materia no existe'},status=status.HTTP_404_NOT_FOUND)

    buffer = io.BytesIO()
    
    global titulo
    titulo = 'Materias que se imparten en cierta aula\n'

    pdf = PDF(format='Letter')
    pdf.add_page()
    pdf.set_font("helvetica",size=12)
    pdf.set_title('Materias que se imparten en cierta aula')

    # pdf.multi_cell(w=0,txt=f'Reporte de: Materias que se imparten en cierta hora\n',border=0,ln=2,align='C')

    pdf.set_left_margin(55) # MARGEN REAL
    pdf.set_right_margin(55)

    pdf.multi_cell(w=0,txt=f'Las siguientes materias se imparten en el aula: {query}\n',border=0,ln=1,align='C')
    
    pdf.set_left_margin(10) # MARGEN REAL
    pdf.set_right_margin(10)

    pdf.set_draw_color(192, 194, 196)

    data = []
    for i in asignan:
        data.append([i.ID_Materia.Nombre_Materia])
        data.append(['Semestre','Grupo','Dia','Hora'])
        data.append([i.Semestre,i.Grupo,i.Dia,i.Hora])
        data.append(['Maestro(a)'])
        data.append([i.ID_Usuario.Nombre_Usuario])

    tamL = pdf.font_size_pt * 0.7
    tamC = pdf.epw
    m = False

    for i in data:
        if len(i) > 1:
            pdf.set_font('helvetica',size=12)
            for u in i:
                pdf.cell(w=tamC/4,h=tamL,txt=f'{u}',border=1,ln=0,align='L')
            pdf.ln(tamL)
        if i[0] in materias:
            pdf.set_font('helvetica','B',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=2,align='C')
        if m:
            pdf.set_font('helvetica',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=2,align='C')
            m = False
            pdf.ln(tamL)
        if i[0] == 'Maestro(a)':
            m = True
            pdf.set_font('helvetica','B',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=2,align='C')

    pdf.output(buffer)

    buffer.seek(0)

    if request.method == 'GET':
        return FileResponse(buffer,filename='Materias.pdf',as_attachment=False)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MateriasGrupoPDF(request, query):
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
            lista.append(materia.Nombre_Materia)
        materias = set(lista)
    except Materias.DoesNotExist:
        return Response({'Error':'Materia no existe'},status=status.HTTP_404_NOT_FOUND)

    buffer = io.BytesIO()
    
    global titulo
    titulo = 'Materias que se imparten en cierto grupo\n'

    pdf = PDF(format='Letter')
    pdf.add_page()
    pdf.set_font("helvetica",size=12)
    pdf.set_title('Materias que se imparten en cierto grupo')

    # pdf.multi_cell(w=0,txt=f'Reporte de: Materias que se imparten en cierta hora\n',border=0,ln=2,align='C')

    pdf.set_left_margin(55) # MARGEN REAL
    pdf.set_right_margin(55)

    pdf.multi_cell(w=0,txt=f'Las siguientes materias se imparten en el grupo: {query}\n',border=0,ln=1,align='C')
    
    pdf.set_left_margin(10) # MARGEN REAL
    pdf.set_right_margin(10)

    pdf.set_draw_color(192, 194, 196)

    data = []
    for i in asignan:
        data.append([i.ID_Materia.Nombre_Materia])
        data.append(['Semestre','Aula','Dia','Hora'])
        data.append([i.Semestre,i.Aula,i.Dia,i.Hora])
        data.append(['Maestro(a)'])
        data.append([i.ID_Usuario.Nombre_Usuario])

    tamL = pdf.font_size_pt * 0.7
    tamC = pdf.epw
    m = False

    for i in data:
        if len(i) > 1:
            pdf.set_font('helvetica',size=12)
            for u in i:
                pdf.cell(w=tamC/4,h=tamL,txt=f'{u}',border=1,ln=0,align='L')
            pdf.ln(tamL)
        if i[0] in materias:
            pdf.set_font('helvetica','B',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=2,align='C')
        if m:
            pdf.set_font('helvetica',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=2,align='C')
            m = False
            pdf.ln(tamL)
        if i[0] == 'Maestro(a)':
            m = True
            pdf.set_font('helvetica','B',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=2,align='C')

    pdf.output(buffer)

    buffer.seek(0)

    if request.method == 'GET':
        return FileResponse(buffer,filename='Materias.pdf',as_attachment=False)
    
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MateriasCreditosPDF(request, query):
    '''
    View que pertenece al filtro: Materias que tienen cierta cantidad de créditos.
    (ADMIN)
    '''
    try:
        materias = Materias.objects.filter(creditos=query)
    except Materias.DoesNotExist:
        return Response({'Error':'No existen materias'})
    
    nombres = []
    for i in materias:
        nombres.append(i.Nombre_Materia)

    buffer = io.BytesIO()
    
    global titulo
    titulo = 'Materias que tienen cierta cantidad de creditos\n'

    pdf = PDF(format='Letter')
    pdf.add_page()
    pdf.set_font("helvetica",size=12)
    pdf.set_title('Materias que tienen cierta cantidad de creditos')

    pdf.set_left_margin(55) # MARGEN REAL
    pdf.set_right_margin(55)

    if int(query) > 1:
        pdf.multi_cell(w=0,txt=f'Las siguientes materias tienen: {query} creditos\n',border=0,ln=1,align='C')
    else:
        pdf.multi_cell(w=0,txt=f'Las siguientes materias tienen: {query} credito\n',border=0,ln=1,align='C')
    
    pdf.set_left_margin(10) # MARGEN REAL
    pdf.set_right_margin(10)

    pdf.set_draw_color(192, 194, 196)

    data = []
    for i in materias:
        data.append([i.Nombre_Materia])
        data.append(['Clave reticula','Hrs. Teoricas','Hrs. Practicas','Unidades'])
        data.append([i.Clave_reticula,i.horas_Teoricas,i.horas_Practicas,i.unidades])
        data.append(['Carrera'])
        data.append([i.Carrera.Nombre_Carrera])

    tamL = pdf.font_size_pt * 0.7
    tamC = pdf.epw
    c = False

    for i in data:
        if len(i) > 1:
            pdf.set_font('helvetica',size=12)
            for u in i:
                pdf.cell(w=tamC/4,h=tamL,txt=f'{u}',border=1,ln=0,align='L')
            pdf.ln(tamL)
        if i[0] in nombres:
            pdf.set_font('helvetica','B',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=2,align='C')
        if c:
            pdf.set_font('helvetica',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=2,align='C')
            c = False
            pdf.ln(tamL)
        if i[0] == 'Carrera':
            c = True
            pdf.set_font('helvetica','B',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=2,align='C')

    pdf.output(buffer)

    buffer.seek(0)

    if request.method == 'GET':
        return FileResponse(buffer,filename='Materias.pdf',as_attachment=False)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MateriasUnidadPDF(request, query):
    '''
    View que pertenece al filtro: Materias que tienen un cierto número de unidades.
    (ADMIN)
    '''
    try:
        materias = Materias.objects.filter(creditos=query)
    except Materias.DoesNotExist:
        return Response({'Error':'No existen materias'})
    
    nombres = []
    for i in materias:
        nombres.append(i.Nombre_Materia)

    buffer = io.BytesIO()
    
    global titulo
    titulo = 'Materias que tienen cierto número de unidades\n'

    pdf = PDF(format='Letter')
    pdf.add_page()
    pdf.set_font("helvetica",size=12)
    pdf.set_title('Materias que tienen cierto número de unidades')

    pdf.set_left_margin(55) # MARGEN REAL
    pdf.set_right_margin(55)

    if int(query) > 1:
        pdf.multi_cell(w=0,txt=f'Las siguientes materias tienen: {query} unidades\n',border=0,ln=1,align='C')
    else:
        pdf.multi_cell(w=0,txt=f'Las siguientes materias tienen: {query} unidad\n',border=0,ln=1,align='C')
        

    pdf.set_left_margin(10) # MARGEN REAL
    pdf.set_right_margin(10)

    pdf.set_draw_color(192, 194, 196)

    data = []
    for i in materias:
        data.append([i.Nombre_Materia])
        data.append(['Clave reticula','Hrs. Teoricas','Hrs. Practicas','Creditos'])
        data.append([i.Clave_reticula,i.horas_Teoricas,i.horas_Practicas,i.creditos])
        data.append(['Carrera'])
        data.append([i.Carrera.Nombre_Carrera])

    tamL = pdf.font_size_pt * 0.7
    tamC = pdf.epw
    c = False

    for i in data:
        if len(i) > 1:
            pdf.set_font('helvetica',size=12)
            for u in i:
                pdf.cell(w=tamC/4,h=tamL,txt=f'{u}',border=1,ln=0,align='L')
            pdf.ln(tamL)
        if i[0] in nombres:
            pdf.set_font('helvetica','B',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=2,align='C')
        if c:
            pdf.set_font('helvetica',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=2,align='C')
            c = False
            pdf.ln(tamL)
        if i[0] == 'Carrera':
            c = True
            pdf.set_font('helvetica','B',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=2,align='C')

    pdf.output(buffer)

    buffer.seek(0)

    if request.method == 'GET':
        return FileResponse(buffer,filename='Materias.pdf',as_attachment=False)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2AllCarrerasPDF(request):
    '''
    View para el PDF de: Lista de las diferentes carreras que se tienen registradas.
    (ADMIN)
    '''
    try:
        carrerasA = Carreras.objects.all()
    except Carreras.DoesNotExist:
        return Response({'Error':'No hay carreras'})
    
    buffer = io.BytesIO()
    
    global titulo
    titulo = 'Listado de todas las carreras registradas\n'

    pdf = PDF(format='Letter')
    pdf.add_page()
    pdf.set_font("helvetica",size=12)
    pdf.set_title('Listado de todas las carreras registradas')

    pdf.set_left_margin(55) # MARGEN REAL
    pdf.set_right_margin(55)

    pdf.multi_cell(w=0,txt=f'A continuación se presentan todas las carreras registradas',border=0,ln=1,align='C')

    pdf.set_left_margin(10) # MARGEN REAL
    pdf.set_right_margin(10)

    pdf.set_draw_color(192, 194, 196)
    
    asignan = Asignan.objects.all()
    
    maestros = set()
    for i in asignan:
        maestros.add(i.ID_Usuario.Nombre_Usuario)
    
    carreras = set()
    for i in carrerasA:
        carreras.add(i.Nombre_Carrera)

    data = []
    for i in carrerasA:
        data.append([i.Nombre_Carrera])
        data.append(['Clave'])
        data.append([i.ID_Carrera])
        data.append(['Total de horas teoricas','Total de horas practicas'])
        data.append([p2HorasTeoCarrera(i.Nombre_Carrera),p2HorasPraCarrera(i.Nombre_Carrera)])
        data.append(['Algunos maestros de la carrera'])
        auxMae = set(Asignan.objects.filter(ID_Materia__Carrera = i).values_list('ID_Usuario__Nombre_Usuario','ID_Usuario__CorreoE'))
        data.append(['Nombre','Correo electronico'])
        if len(auxMae) >= 5:
            auxMae = list(auxMae)
            for n in (range(5)):
                data.append(auxMae[n])
        else:
            for a in auxMae:
                data.append(a)

    tamL = pdf.font_size_pt * 0.7
    tamC = pdf.epw
    h = False
    m = False

    for i in data:
        if len(i) > 1:
            for u in i:
                if u == 'Total de horas teoricas' or u == 'Total de horas practicas':
                    h = True
                    pdf.set_font('helvetica','B',size=12)
                    pdf.cell(w=tamC/2,h=tamL,txt=f'{u}',border=1,ln=0,align='C')
                elif h == True:
                    pdf.set_font('helvetica',size=12)
                    pdf.cell(w=tamC/2,h=tamL,txt=f'{u}',border=1,ln=0,align='C')
                elif m:
                    pdf.set_font('helvetica',size=12)
                    pdf.cell(w=tamC/2,h=tamL,txt=f'{u}',border=1,ln=0,align='C')
            pdf.ln(tamL)
        elif i[0] in carreras:
            m = False
            pdf.ln(tamL)
            pdf.set_font('helvetica','B',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=2,align='C')
        elif i[0] == 'Clave':
            pdf.set_font('helvetica',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=1,align='C')
        elif i[0] == 'Algunos maestros de la carrera':
            h = False
            m = True
            pdf.set_font('helvetica','B',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=1,align='C')
        else:
            pdf.set_font('helvetica',size=12)
            pdf.cell(w=0,h=tamL,txt=f'{i[0]}',border=1,ln=1,align='C')

    pdf.output(buffer)

    buffer.seek(0)

    if request.method == 'GET':
        return FileResponse(buffer,filename='Materias.pdf',as_attachment=False)