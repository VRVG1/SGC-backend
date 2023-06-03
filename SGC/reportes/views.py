
from datetime import date, datetime
import io
import os

from django.http import FileResponse

from materias.models import Carreras, Materias
from usuarios.models import Usuarios
from .models import Reportes, Generan, Alojan
from .serializers import AlojanSerializer, ReportesSerializer, GeneranSerializer
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from materias.models import Asignan
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from persoAuth.permissions import AdminDocentePermission, OnlyAdminPermission, OnlyDocentePermission, AdminEspectadorPermission, AdminEspectadorDocentePermission
from .tasks import sendMensaje, sendGroupMail
from .pnc_validators import checkAddRegistro,\
        checkUpdateRegistro,\
        checkDeleteRegistro
from .vgc_validators import checkAddRegistroVGC,\
        checkUpdateRegistroVGC,\
        checkDeleteRegistroVGC
from django.db.models import Q
from fpdf import FPDF
import matplotlib.pyplot as plt
import matplotlib

from pathlib import Path
import json
from .pdf_pnc import PncPDF
from .excel_vgc import VGCExcel

# Create your views here.


class ReportesView(generics.ListAPIView):
    '''
    Vista que permite ver todos los reportes registrados en la BD
    (ADMIN y SUPERVISOR)
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, AdminEspectadorPermission]

    serializer_class = ReportesSerializer
    queryset = Reportes.objects.filter(Unidad=False)


class GeneranView(generics.ListAPIView):
    '''
    Vista que permite ver todos los generan registrados en la BD
    (ADMIN y SUPERVISOR)
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, AdminEspectadorPermission]

    serializer_class = GeneranSerializer
    queryset = Generan.objects.all()


class AlojanView(generics.ListAPIView):
    '''
    Vista que permite ver todos los alojan registrados en la BD
    (ADMIN y SUPERVISOR)
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, AdminEspectadorPermission]

    serializer_class = AlojanSerializer
    queryset = Alojan.objects.all()


class CreateReportesView(APIView):
    '''
    Vista que permite registrar un reporte en la BD
    (ADMIN)
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, OnlyAdminPermission]

    serializer_class = ReportesSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            name = serializer.validated_data.get('Nombre_Reporte')
            serializer.save()
            ID_Reporte = Reportes.objects.get(Nombre_Reporte=name)
            asignan = Asignan.objects.all()
            if not asignan:
                pass
            else:
                date01 = 'Jun 20'
                fecha = date.today()
                parse01 = datetime.strptime(
                    date01, '%b %d').date().replace(year=fecha.year)

                if fecha < parse01:
                    semestre = 'Enero - Junio ' + str(fecha.year)
                else:
                    semestre = 'Agosto - Diciembre ' + str(fecha.year)
                
                lista = []
                olds = []
                for x,i in enumerate(asignan):
                    if x == 0:
                        manyAsignan = Asignan.objects.filter(Q(ID_Materia=i.ID_Materia, Semestre=i.Semestre, Grupo=i.Grupo) & ~Q(Hora=i.Hora,Dia=i.Dia,Aula=i.Aula))
                        if manyAsignan:
                            for o in manyAsignan:
                                olds.append(o)
                        lista.append(i)
                    else:
                        if i not in olds:
                            manyAsignan = Asignan.objects.filter(Q(ID_Materia=i.ID_Materia, Semestre=i.Semestre, Grupo=i.Grupo) & ~Q(Hora=i.Hora,Dia=i.Dia,Aula=i.Aula))
                            if manyAsignan:
                                for o in manyAsignan:
                                    olds.append(o)
                            lista.append(i)
                for i in lista:
                    generate = Generan(
                        Estatus=None, Periodo=semestre, Fecha_Entrega=fecha, ID_Asignan=i, ID_Reporte=ID_Reporte, Reprobados=0)
                    generate.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnlySaveReportesView(APIView):
    '''
    Vista que permite guardar pero no "enviar" un reporte
    (ADMIN)
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, OnlyAdminPermission]
    serializer_class = ReportesSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


class CreateAlojanView(APIView):
    '''
    Vista que permite guardar los archivos PDF que se necesiten subir para el reporte
    (DOCENTE)
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, AdminDocentePermission]

    serializer_class = AlojanSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminEspectadorDocentePermission])
def alojanFromView(request, fk):
    '''
    Vista que permite ver todos los alojan de una cierta generacion
    (DOCENTE, ADMIN, SUPERVISOR)
    '''
    if request.method == 'GET':
        try:
            ID_Generacion = Generan.objects.get(ID_Generacion=fk)
        except Generan.DoesNotExist:
            return Response({'Error': ' Generado no existe'}, status=status.HTTP_404_NOT_FOUND)

        AlojanX = Alojan.objects.filter(ID_Generacion=ID_Generacion)
        lista = []
        for i in AlojanX:
            pdf = str(i.Path_PDF)
            lista.append(pdf[pdf.index('/')+1:])
        dic = {}
        aux = 0
        for i in lista:
            pdf = {aux: i}
            dic.update(pdf)
            aux = aux + 1
        return Response(dic, status=status.HTTP_200_OK)


@api_view(['GET', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def borrarReporte(request, pk):
    '''
    Vista que permite borrar un reporte de la BD
    (ADMIN)
    '''
    try:
        reporte = Reportes.objects.get(ID_Reporte=pk)
    except Reportes.DoesNotExist:
        return Response({'Error': 'Reporte no existe'}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        reporte_serializer = ReportesSerializer(reporte)
        return Response(reporte_serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'DELETE':
        reporte.delete()
        return Response({'Mensaje': 'Reporte Borrado'}, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def updateReporte(request, pk):
    '''
    Vista que permite actualizar (modificar) un reporte de la BD
    (ADMIN)
    '''
    try:
        reporte = Reportes.objects.get(ID_Reporte=pk)
    except Reportes.DoesNotExist:
        return Response({'Error': 'Reporte no existe'}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        reporte_serializer = ReportesSerializer(reporte)
        return Response(reporte_serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer_class = ReportesSerializer(reporte, data=request.data)
        if serializer_class.is_valid():
            serializer_class.save()
            return Response(serializer_class.data, status=status.HTTP_200_OK)
        return Response(serializer_class.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def EnviarGeneran(request, pk):
    '''
    Vista que permite crear o "enviar" un generan de un reporte que solo fue guardado
    (ADMIN)
    '''

    try:
        reporte = Reportes.objects.get(ID_Reporte=pk)
    except Reportes.DoesNotExist:
        return Response({'Error': 'Reporte no existe'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        try:
            asignan = Asignan.objects.all()
        except Asignan.DoesNotExist:
            return Response({'Error': 'No hay asignan'}, status=status.HTTP_404_NOT_FOUND)

        try:
            date01 = 'Jun 20'
            fecha = date.today()
            parse01 = datetime.strptime(
                date01, '%b %d').date().replace(year=fecha.year)

            if fecha < parse01:
                semestre = 'Enero - Junio ' + str(fecha.year)
            else:
                semestre = 'Agosto - Diciembre ' + str(fecha.year)

            lista = []
            olds = []
            for x,i in enumerate(asignan):
                if x == 0:
                    manyAsignan = Asignan.objects.filter(Q(ID_Materia=i.ID_Materia, Semestre=i.Semestre, Grupo=i.Grupo) & ~Q(Hora=i.Hora,Dia=i.Dia,Aula=i.Aula))
                    if manyAsignan:
                        for o in manyAsignan:
                            olds.append(o)
                    lista.append(i)
                else:
                    if i not in olds:
                        manyAsignan = Asignan.objects.filter(Q(ID_Materia=i.ID_Materia, Semestre=i.Semestre, Grupo=i.Grupo) & ~Q(Hora=i.Hora,Dia=i.Dia,Aula=i.Aula))
                        if manyAsignan:
                            for o in manyAsignan:
                                olds.append(o)
                        lista.append(i)
            for i in lista:
                generate = Generan(
                    Estatus=None, Periodo=semestre, Fecha_Entrega=fecha, ID_Asignan=i, ID_Reporte=reporte, Reprobados=0)
                generate.save()

            return Response({'Success': 'Generan creado'}, status=status.HTTP_201_CREATED)
        except:
            return Response({'Error': 'Error al crear un generan'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def GetGeneranUser(request):
    '''
    Vista que permite obtener todos los reportes que el usuario debe entregar
    (DOCENTE)
    '''
    try:
        usuario = Usuarios.objects.get(ID_Usuario=request.user)
        generan = Generan.objects.filter(ID_Asignan__ID_Usuario=usuario, ID_Reporte__Unidad=False)
    except Generan.DoesNotExist:
        return Response({'Error': 'No hay registros'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = GeneranSerializer(generan, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def GetReporte(request, pk):
    '''
    Vista que permite obtener la informacion de un reporte especifico
    (DOCENTE)
    '''
    try:
        reporte = Reportes.objects.get(ID_Reporte=pk)
    except Generan.DoesNotExist:
        return Response({'Error': 'No hay reporte'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ReportesSerializer(reporte)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyDocentePermission])
def CrearGeneran(request, pk):
    '''
    Vista que permite crear un generan (en si no crea nada ya que el espacio ya
    fue creado, solo se modifica con los datos de estatus y el pdf)
    (DOCENTE)
    '''
    try:
        generan = Generan.objects.get(ID_Generacion=pk)
        reporte = Reportes.objects.get(
            ID_Reporte=generan.ID_Reporte.ID_Reporte)
    except Generan.DoesNotExist:
        return Response({'Error': 'Generado no existe'}, status=status.HTTP_404_NOT_FOUND)

    fechaE = reporte.Fecha_Entrega
    fechaH = date.today()

    if fechaH > fechaE:
        estatus = 'Entrega tarde'
    else:
        estatus = 'Entrega a tiempo'

    if request.method == 'GET':
        generan_serializer = GeneranSerializer(generan)
        return Response(generan_serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        data = {
            'Estatus': estatus,
            'Periodo': generan.Periodo,
            'Fecha_Entrega':generan.Fecha_Entrega,
            'ID_Asignan': generan.ID_Asignan.ID_Asignan,
            'ID_Reporte': generan.ID_Reporte.ID_Reporte,
            'Reprobados': generan.Reprobados,
        }
        serializer_class = GeneranSerializer(generan, data=data)
        if serializer_class.is_valid():
            serializer_class.save()
            return Response(serializer_class.data, status=status.HTTP_202_ACCEPTED)
        print(serializer_class.errors)
        return Response(serializer_class.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def AdminSendMail(request):
    if request.method == 'POST':
        pk = request.data['pk']
        if pk == str(0):
            try:
                msg = request.data['msg']
                sendMensaje.delay(msg, True, None)
                return Response({'Exito': 'Mensaje enviado'}, status=status.HTTP_202_ACCEPTED)
            except:
                return Response({'Error': 'Error al enviar el mensaje'}, status=status.HTTP_400_BAD_REQUEST)

        else:
            try:
                usuario = Usuarios.objects.get(PK=pk)
            except Usuarios.DoesNotExist:
                return Response({'Error': 'Usuario no existe'}, status=status.HTTP_404_NOT_FOUND)

            try:
                msg = request.data['msg']
                sendMensaje.delay(msg, False, usuario)
                return Response({'Exito': 'Mensaje enviado'}, status=status.HTTP_202_ACCEPTED)
            except:
                return Response({'Error': 'Error al enviar el mensaje'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def IniciarNuevoSem(request):

    if request.method == 'GET':
        try:
            os.chdir('./media/Generados')
            pdfs = os.listdir()
            if pdfs:
                for i in pdfs:
                    os.remove(i)
                Asignan.objects.all().delete()
            usuarios = Usuarios.objects.all()
            for i in usuarios:
                i.Permiso = True
                i.save()
            return Response({'Exito': 'Datos borrados'}, status=status.HTTP_200_OK)
        except:
            return Response({'Error': 'Error al borrar los datos'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def borrarEntrega(request, pk):

    if request.method == 'DELETE':

        alojan = Alojan.objects.filter(ID_Generacion=pk)
        generan = Generan.objects.get(pk=pk)
        if not alojan:
            return Response({'Error': 'Alojan no existe'}, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                path = './media/Generados'
                lista = []
                for i in alojan:
                    pdf = str(i.Path_PDF)
                    lista.append(pdf[pdf.index('/')+1:])

                for i in lista:
                    aux = path + '/' + str(i)
                    if os.path.exists(aux):
                        os.remove(aux)

                for i in alojan:
                    i.delete()

                generan.Estatus = None
                generan.save()

            except:
                return Response({'Error': 'Error al eliminar pdf y alojan'})
            return Response({'Exito': 'PDFs borrados con exito'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def getResportesUnidad(request, pk):
    '''
    Vista que permite obtener los reportes de unidad de un usuario
    (Por el momento solo para la vista del usuario)
    (ADMIN Y DOCENTE)
    '''
    try:
        user = Usuarios.objects.get(ID_Usuario=pk)
    except Usuarios.DoesNotExist:
        return Response({'Error':'Usuario no existe'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            RepUnidades = Generan.objects.filter(ID_Asignan__ID_Usuario=user, ID_Reporte__Unidad=True)
            
            lista = []
            for x,i in enumerate(RepUnidades):
                if x == 0:
                    asignacion = Asignan.objects.get(ID_Asignan=i.ID_Asignan.ID_Asignan)
                    aux = {
                        'Nombre_Materia':asignacion.ID_Materia.Nombre_Materia,
                        'Semestre':asignacion.Semestre,
                        'Grupo':asignacion.Grupo,
                        'Aula':asignacion.Aula,
                        'Unidades':asignacion.ID_Materia.unidades
                    }
                    lista.append(aux)
                    aux = {
                        'ID_Generacion':i.ID_Generacion,
                        'Fecha_Entrega':i.Fecha_Entrega,
                        'Reprobados':i.Reprobados,
                        'Unidad':i.Unidad
                    }
                    lista.append(aux)
                    oldAs = i.ID_Asignan.ID_Asignan

                elif i.ID_Asignan.ID_Asignan != oldAs:
                    asignacion = Asignan.objects.get(ID_Asignan=i.ID_Asignan.ID_Asignan)
                    aux = {
                        'Nombre_Materia':asignacion.ID_Materia.Nombre_Materia,
                        'Semestre':asignacion.Semestre,
                        'Grupo':asignacion.Grupo,
                        'Aula':asignacion.Aula,
                        'Unidades':asignacion.ID_Materia.unidades
                    }
                    lista.append(aux)
                    aux = {
                        'ID_Generacion':i.ID_Generacion,
                        'Fecha_Entrega':i.Fecha_Entrega,
                        'Reprobados':i.Reprobados,
                        'Unidad':i.Unidad
                    }
                    lista.append(aux)
                    oldAs = i.ID_Asignan.ID_Asignan
                else:
                    aux = {
                        'ID_Generacion':i.ID_Generacion,
                        'Fecha_Entrega':i.Fecha_Entrega,
                        'Reprobados':i.Reprobados,
                        'Unidad':i.Unidad
                    }
                    lista.append(aux)

            return Response(lista, status=status.HTTP_200_OK)
        except Generan.DoesNotExist:
            return Response({'Error':'No hay generan'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET','PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def entregarUnidad(request, pk):

    try:
        generanU = Generan.objects.get(ID_Generacion=pk)
    except Generan.DoesNotExist:
        return Response({'Error':'Generan no existe'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = GeneranSerializer(generanU)
        return Response(serializer.data, status=status.HTTP_200_OK)
    if request.method == 'PUT':
        date01 = 'Jun 20'
        fecha = date.today()
        parse01 = datetime.strptime(
            date01, '%b %d').date().replace(year=fecha.year)

        if fecha < parse01:
            semestre = 'Enero - Junio ' + str(fecha.year)
        else:
            semestre = 'Agosto - Diciembre ' + str(fecha.year)

        data = {
            'ID_Generacion':generanU,
            'Estatus':'Entregado Unidad',
            'Fecha_Entrega':request.data['Fecha_Entrega'],
            'ID_Asignan':generanU.ID_Asignan.ID_Asignan,
            'ID_Reporte':generanU.ID_Reporte.ID_Reporte,
            'Periodo':semestre,
            'Reprobados':request.data['Reprobados'],
            'Unidad':generanU.Unidad,
        }
        generan_serializer = GeneranSerializer(generanU, data=data)
        if generan_serializer.is_valid():
            generan_serializer.save()
            return Response(generan_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(generan_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def getReportesUnidadAdmin(request):
    '''
    Vista que permite obtener los reportes de unidad de todos los maestros
    (separados como victor pidió)
    (ADMIN)
    '''

    try:
        usuarios = Usuarios.objects.filter(Tipo_Usuario='Docente')
    except Usuarios.DoesNotExist:
        return Response({'Error':'No hay usuarios'},status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try: 
            RepUnidades = Generan.objects.filter(ID_Reporte__Unidad=True)

            lista = []
            listagen = []
            for u in usuarios:
                oldAs = None
                for x,i in enumerate(RepUnidades):
                    if x == 0:
                        try:
                            asignacion = Asignan.objects.get(ID_Usuario=u, ID_Asignan=i.ID_Asignan.ID_Asignan)
                            aux = {
                                'Nombre_Usuario':u.Nombre_Usuario
                            }
                            aux.update({
                                'Nombre_Materia':asignacion.ID_Materia.Nombre_Materia,
                                'Semestre':asignacion.Semestre,
                                'Grupo':asignacion.Grupo,
                                'Aula':asignacion.Aula,
                                'Unidades':asignacion.ID_Materia.unidades
                            })
                            listagen.append({
                                    'ID_Generacion':i.ID_Generacion,
                                    'Fecha_Entrega':i.Fecha_Entrega,
                                    'Reprobados':i.Reprobados,
                                    'Unidad':i.Unidad
                            })
                            aux.update({'Generan':listagen})
                            oldAs = i.ID_Asignan.ID_Asignan
                        except Asignan.DoesNotExist:
                            pass

                    elif i.ID_Asignan.ID_Asignan != oldAs:
                        try:
                            asignacion = Asignan.objects.get(ID_Usuario=u, ID_Asignan=i.ID_Asignan.ID_Asignan)
                            listagen = []
                            lista.append(aux)
                            aux = {
                                'Nombre_Usuario':u.Nombre_Usuario
                            }
                            aux.update({
                                'Nombre_Materia':asignacion.ID_Materia.Nombre_Materia,
                                'Semestre':asignacion.Semestre,
                                'Grupo':asignacion.Grupo,
                                'Aula':asignacion.Aula,
                                'Unidades':asignacion.ID_Materia.unidades
                            })
                            listagen.append({
                                    'ID_Generacion':i.ID_Generacion,
                                    'Fecha_Entrega':i.Fecha_Entrega,
                                    'Reprobados':i.Reprobados,
                                    'Unidad':i.Unidad
                            })
                            aux.update({'Generan':listagen})
                            oldAs = i.ID_Asignan.ID_Asignan
                        except Asignan.DoesNotExist:
                            pass
                    else:
                        if oldAs != None:
                            listagen.append({
                                'ID_Generacion':i.ID_Generacion,
                                'Fecha_Entrega':i.Fecha_Entrega,
                                'Reprobados':i.Reprobados,
                                'Unidad':i.Unidad
                            })
                            aux.update({'Generan':listagen})
                listagen = []
            lista.append(aux)
            return Response(lista,status=status.HTTP_200_OK)
        except Generan.DoesNotExist:
            return Response({'Error':'No hay generan'},status=status.HTTP_404_NOT_FOUND)

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
def p2MaestrosPuntual(request, query):

    try:
        reporte = Reportes.objects.get(Nombre_Reporte=query)
    except Reportes.DoesNotExist:
        return Response({'Error':'Reporte no existe'},status=status.HTTP_404_NOT_FOUND)
    

    if request.method == 'GET':
        generan = Generan.objects.filter(ID_Reporte = reporte, Estatus='Entrega a tiempo')

        aux = []
        for i in generan:
            aux.append(i.ID_Asignan.ID_Usuario)
        aux = set(aux)
        
        lista = []
        for i in list(aux):
            aux = {
                    'PK':i.PK,
                    'ID_Usuario':{'username':i.ID_Usuario.username,'password':i.ID_Usuario.password},
                    'Nombre_Usuario':i.Nombre_Usuario,
                    'Tipo_Usuario':i.Tipo_Usuario,
                    'CorreoE':i.CorreoE,
                    'Permiso':i.Permiso
                }
            lista.append(aux)
        return Response(lista,status=status.HTTP_200_OK)
    
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MaestrosTarde(request, query):

    try:
        reporte = Reportes.objects.get(Nombre_Reporte=query)
    except Reportes.DoesNotExist:
        return Response({'Error':'Reporte no existe'},status=status.HTTP_404_NOT_FOUND)
    

    if request.method == 'GET':
        generan = Generan.objects.filter(ID_Reporte = reporte, Estatus='Entrega tarde')

        aux = []
        for i in generan:
            aux.append(i.ID_Asignan.ID_Usuario)
        aux = set(aux)
        
        lista = []
        for i in list(aux):
            aux = {
                    'PK':i.PK,
                    'ID_Usuario':{'username':i.ID_Usuario.username,'password':i.ID_Usuario.password},
                    'Nombre_Usuario':i.Nombre_Usuario,
                    'Tipo_Usuario':i.Tipo_Usuario,
                    'CorreoE':i.CorreoE,
                    'Permiso':i.Permiso
                }
            lista.append(aux)
        return Response(lista,status=status.HTTP_200_OK)


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
        date01 = 'Jun 20'
        fecha = date.today()
        parse01 = datetime.strptime(
            date01, '%b %d').date().replace(year=fecha.year)

        if fecha < parse01:
            semestre = 'Enero - Junio ' + str(fecha.year)
        else:
            semestre = 'Agosto - Diciembre ' + str(fecha.year)
        self.cell(w=0,txt=semestre,border=0,ln=2,align='C')
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
def p2MaestrosPuntualPDF(request, query):

    try:
        reporte = Reportes.objects.get(Nombre_Reporte=query)
    except Reportes.DoesNotExist:
        return Response({'Error':'Reporte no existe'},status=status.HTTP_404_NOT_FOUND)
    
    generan = Generan.objects.filter(ID_Reporte = reporte, Estatus='Entrega a tiempo')

    aux = []
    for i in generan:
        aux.append(i.ID_Asignan.ID_Usuario)
    aux = set(aux)
    
    lista = []
    for i in list(aux):
        aux = {
                'Nombre_Usuario':i.Nombre_Usuario,
                'CorreoE':i.CorreoE,
            }
        lista.append(aux)
    
    if generan:
        buffer = io.BytesIO()

        global titulo
        titulo = 'Maestros(as) que entregaron puntual sus avances\n'

        pdf = PDF(format='Letter')
        pdf.add_page()
        pdf.set_font("helvetica",size=12)
        pdf.set_title('Maestros(as) que entregaron puntual sus avances')

        pdf.set_left_margin(55) # MARGEN REAL
        pdf.set_right_margin(55)

        # pdf.set_font("helvetica",'B',size=12)
        pdf.multi_cell(w=0,txt=f'Se presentan todos los maestros que han entregado a tiempo el reporte: ',border=0,ln=1,align='C')
        pdf.set_font("helvetica",'B',size=12)
        pdf.multi_cell(w=0,txt=f'{query}',border=0,ln=1,align='C')
        pdf.set_font("helvetica",size=12)
        
        pdf.set_left_margin(10) # MARGEN REAL
        pdf.set_right_margin(10)

        pdf.set_draw_color(192, 194, 196)
        
        pdf.set_left_margin(10) # MARGEN REAL
        pdf.set_right_margin(10)

        data = []
        laux = []
        materia = ''
        data.append([f'Entregaron a tiempo: {query}'])
        for i in lista:
            data.append([i['Nombre_Usuario'],i['CorreoE']])
            data.append(['Materia','Grupo','Semestre','Fecha programada','Entregado'])
            genera = Generan.objects.filter(ID_Reporte = reporte, Estatus='Entrega a tiempo',ID_Asignan__ID_Usuario__Nombre_Usuario = i['Nombre_Usuario']).values_list('ID_Asignan__ID_Materia__Nombre_Materia','ID_Asignan__Grupo','ID_Asignan__Semestre','ID_Reporte__Fecha_Entrega','Fecha_Entrega')
            for u in genera:
                for o in u:
                        laux.append(str(o))
                data.append(laux)
                laux = []

        tamL = pdf.font_size_pt * 0.7
        tamC = pdf.epw
        tam = False
        cy = 0
        ex = 0
        cx = 0
        ey = 0
        sal = 0
        factor_Mul = 0
        for i in data:
            if len(i) > 1:
                for u in i:
                    pdf.set_font('helvetica',size=12)
                    if len(i) == 2:
                        pdf.set_font('helvetica','B',size=12)
                        pdf.cell(w=tamC/2,h=tamL,txt=u,border=1,ln=0,align='C')
                    elif len(u) > 23:
                        cx = pdf.get_x()
                        cy = pdf.get_y()
                        tam = True
                        ax = u.replace(' ','\n')
                        sal = ax.count('\n')
                        factor_Mul = sal + 1
                        pdf.multi_cell(w=tamC/5,txt=ax,border=1,ln=0,align='L')
                        ex = pdf.get_x()
                        ey = pdf.get_y()
                        pdf.set_x(ex)
                    elif tam:
                        cx = pdf.get_x()
                        pdf.set_xy(cx,cy)
                        pdf.multi_cell(w=tamC/5,h=tamL*(factor_Mul/1.99),txt=u,border=1,ln=0,align='L')
                        ex = cx + (tamC/5)
                        pdf.set_x(ex)
                    else:
                        pdf.cell(w=tamC/5,h=tamL,txt=u,border=1,ln=0,align='L')
                if tam:
                    ey = cy + (tamL*(factor_Mul/1.99))
                    pdf.set_y(ey)
                    tam = False
                else:
                    tam = False
                    pdf.ln(tamL)
            else:
                tam = False
                pdf.ln(tamL)
                pdf.set_font('helvetica','B',size=12)
                pdf.cell(w=0,h=tamL,txt=i[0],border=1,ln=2,align='C')
                ey = pdf.get_y()

        tardeC = Generan.objects.filter(ID_Reporte = reporte, Estatus='Entrega tarde').count()
        atiempoC = Generan.objects.filter(ID_Reporte = reporte, Estatus='Entrega a tiempo').count()

        pdf.ln(tamL)
        pdf.cell(w=0,txt=f'A continuación se presenta la información de manera gráfica: ',ln=2,align='C')

        heights=[atiempoC,tardeC] #valores Y
        bar_labels=['A tiempo','Tarde'] #valores X
        matplotlib.use('agg')
        plt.bar(bar_labels,heights,width=0.2,color='#6B809B')
        plt.xlabel('Entregas') 
        plt.ylabel('Cantidad de incidencia')
        plt.title(f"Gráfica de entregas de: {query}")

        img_buf = io.BytesIO()
        plt.savefig(img_buf, dpi=200)
        plt.close()

        pdf.image(img_buf, w=pdf.epw,h=pdf.eph/2)
        pdf.ln(tamL)

        if tardeC > atiempoC:
            pdf.multi_cell(w=0,txt=f'Se observa que el: {query} se entregó (o se está entregando) después de la fecha acordada.\nPara enviar un recordatorio o memo a algún maestro lo puede hacer desde el SGC mismo.',align='C')
        else:
            pdf.multi_cell(w=0,txt=f'Se observa que el: {query} se entregó (o se está entregando) antes o en la fecha acordada, nada mal.\nPara enviar un recordatorio o memo a algún maestro lo puede hacer desde el SGC mismo.',align='C')

        pdf.output(buffer)
        img_buf.close()
        buffer.seek(0)

        if request.method == 'GET':
            return FileResponse(buffer,filename='Avances.pdf',as_attachment=False)
    else:
        if request.method == 'GET':
            return Response({'Error':'No hay suficiente informacion para poblar el pdf'},status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MaestrosTardePDF(request, query):

    try:
        reporte = Reportes.objects.get(Nombre_Reporte=query)
    except Reportes.DoesNotExist:
        return Response({'Error':'Reporte no existe'},status=status.HTTP_404_NOT_FOUND)
    
    generan = Generan.objects.filter(ID_Reporte = reporte, Estatus='Entrega tarde')

    aux = []
    for i in generan:
        aux.append(i.ID_Asignan.ID_Usuario)
    aux = set(aux)
    
    lista = []
    for i in list(aux):
        aux = {
                'Nombre_Usuario':i.Nombre_Usuario,
                'CorreoE':i.CorreoE,
            }
        lista.append(aux)
    
    if generan:
        buffer = io.BytesIO()

        global titulo
        titulo = 'Maestros(as) que se retrasaron en la entrega de los avances\n'

        pdf = PDF(format='Letter')
        pdf.add_page()
        pdf.set_font("helvetica",size=12)
        pdf.set_title('Maestros(as) que se retrasaron en la entrega de los avances')

        pdf.set_left_margin(55) # MARGEN REAL
        pdf.set_right_margin(55)

        # pdf.set_font("helvetica",'B',size=12)
        pdf.multi_cell(w=0,txt=f'Se presentan todos los maestros que han entregado tarde el reporte: ',border=0,ln=1,align='C')
        pdf.set_font("helvetica",'B',size=12)
        pdf.multi_cell(w=0,txt=f'{query}',border=0,ln=1,align='C')
        pdf.set_font("helvetica",size=12)
        
        pdf.set_left_margin(10) # MARGEN REAL
        pdf.set_right_margin(10)

        pdf.set_draw_color(192, 194, 196)
        
        pdf.set_left_margin(10) # MARGEN REAL
        pdf.set_right_margin(10)

        data = []
        laux = []
        materia = ''
        data.append([f'Entregaron tarde: {query}'])
        for i in lista:
            data.append([i['Nombre_Usuario'],i['CorreoE']])
            data.append(['Materia','Grupo','Semestre','Fecha programada','Entregado'])
            genera = Generan.objects.filter(ID_Reporte = reporte, Estatus='Entrega tarde',ID_Asignan__ID_Usuario__Nombre_Usuario = i['Nombre_Usuario']).values_list('ID_Asignan__ID_Materia__Nombre_Materia','ID_Asignan__Grupo','ID_Asignan__Semestre','ID_Reporte__Fecha_Entrega','Fecha_Entrega')
            for u in genera:
                for o in u:
                        laux.append(str(o))
                data.append(laux)
                laux = []

        tamL = pdf.font_size_pt * 0.7
        tamC = pdf.epw
        tam = False
        cy = 0
        ex = 0
        cx = 0
        ey = 0
        sal = 0
        factor_Mul = 0
        for i in data:
            if len(i) > 1:
                for u in i:
                    pdf.set_font('helvetica',size=12)
                    if len(i) == 2:
                        pdf.set_font('helvetica','B',size=12)
                        pdf.cell(w=tamC/2,h=tamL,txt=u,border=1,ln=0,align='C')
                    elif len(u) > 23:
                        cx = pdf.get_x()
                        cy = pdf.get_y()
                        tam = True
                        ax = u.replace(' ','\n')
                        sal = ax.count('\n')
                        factor_Mul = sal + 1
                        pdf.multi_cell(w=tamC/5,txt=ax,border=1,ln=0,align='L')
                        ex = pdf.get_x()
                        ey = pdf.get_y()
                        pdf.set_x(ex)
                    elif tam:
                        cx = pdf.get_x()
                        pdf.set_xy(cx,cy)
                        pdf.multi_cell(w=tamC/5,h=tamL*(factor_Mul/1.99),txt=u,border=1,ln=0,align='L')
                        ex = cx + (tamC/5)
                        pdf.set_x(ex)
                    else:
                        pdf.cell(w=tamC/5,h=tamL,txt=u,border=1,ln=0,align='L')
                if tam:
                    ey = cy + (tamL*(factor_Mul/1.99))
                    pdf.set_y(ey)
                    tam = False
                else:
                    tam = False
                    pdf.ln(tamL)
            else:
                tam = False
                pdf.ln(tamL)
                pdf.set_font('helvetica','B',size=12)
                pdf.cell(w=0,h=tamL,txt=i[0],border=1,ln=2,align='C')
                ey = pdf.get_y()

        tardeC = Generan.objects.filter(ID_Reporte = reporte, Estatus='Entrega tarde').count()
        atiempoC = Generan.objects.filter(ID_Reporte = reporte, Estatus='Entrega a tiempo').count()

        pdf.ln(tamL)
        pdf.cell(w=0,txt=f'A continuación se presenta la información de manera gráfica: ',ln=2,align='C')

        heights=[atiempoC,tardeC] #valores Y
        bar_labels=['A tiempo','Tarde'] #valores X
        matplotlib.use('agg')
        plt.bar(bar_labels,heights,width=0.2,color='#6B809B')
        plt.xlabel('Entregas')
        plt.ylabel('Cantidad de incidencia')
        plt.title(f"Gráfica de entregas de: {query}")

        img_buf = io.BytesIO()
        plt.savefig(img_buf, dpi=200)
        plt.close()

        pdf.image(img_buf, w=pdf.epw,h=pdf.eph/2)
        pdf.ln(tamL)

        if tardeC > atiempoC:
            pdf.multi_cell(w=0,txt=f'Se observa que el: {query} se entregó (o se está entregando) después de la fecha acordada.\nPara enviar un recordatorio o memo a algún maestro lo puede hacer desde el SGC mismo.',align='C')
        else:
            pdf.multi_cell(w=0,txt=f'Se observa que el: {query} se entregó (o se está entregando) antes o en la fecha acordada, nada mal.\nPara enviar un recordatorio o memo a algún maestro lo puede hacer desde el SGC mismo.',align='C')

        pdf.output(buffer)
        img_buf.close()
        buffer.seek(0)

        if request.method == 'GET':
            return FileResponse(buffer,filename='Avances.pdf',as_attachment=False)
    else:
        if request.method == 'GET':
            return Response({'Error':'No hay suficiente informacion para poblar el pdf'},status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p3ReprobacionMaestro(request, query):
    u"""View filtro que retorna el indice de reprobación por maestro de una
    carrera e información relacionada.
    (ADMIN)

    query -- String que conteine dos valores divididos por un '-':
        [0] -> Nombre del Maestro
        [1] -> Nombre de la Carrera
    """
    splitted = query.split("-")
    try:
        generan = Generan.objects.filter(Q(ID_Asignan__ID_Usuario__Nombre_Usuario=splitted[0]),
                                         Q(ID_Asignan__ID_Materia__Carrera__Nombre_Carrera=splitted[1])
                                         )
    except Generan.DoesNotExist:
        return Response({'Error': "Generan no existe"},
                        status=status.HTTP_404_NOT_FOUND)
    print(f"\n\nGeneran: {generan}")
    if request.method == 'GET':
        lista = []
        for generacion in generan:
            formato = {
                'Nombre_Usuario': generacion.ID_Asignan.ID_Usuario.Nombre_Usuario,
                'Nombre_Materia': generacion.ID_Asignan.ID_Materia.Nombre_Materia,
                'Nombre_Carrera': generacion.ID_Asignan.ID_Materia.Carrera.Nombre_Carrera,
                'Semestre': generacion.ID_Asignan.Semestre,
                'Grupo': generacion.ID_Asignan.Grupo,
                'Unidad': generacion.Unidad,
                'aprobados': 100 - generacion.Reprobados,
                'reprobados': generacion.Reprobados,
            }
            lista.append(formato)
        return Response(data=lista, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p3ReprobacionMateria(request, query):
    u"""View filtro que retorna el indice de reprobación por materia de una
    carrera e información relacionada.
    (ADMIN)

    query -- String que contiene dos valores divididos por un '-':
        [0] -> Nombre de la Materia
        [1] -> Nombre de la Carrera
    """
    splitted = query.split("-")
    try:
        generan = Generan.objects.filter(Q(ID_Asignan__ID_Materia__Nombre_Materia=splitted[0]),
                                         Q(ID_Asignan__ID_Materia__Carrera__Nombre_Carrera=splitted[1]))
    except Generan.DoesNotExist:
        return Response({'Error': "Generan no existe"},
                        status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        lista = []
        for generacion in generan:
            formato = {
                'Nombre_Usuario': generacion.ID_Asignan.ID_Usuario.Nombre_Usuario,
                'Nombre_Materia': generacion.ID_Asignan.ID_Materia.Nombre_Materia,
                'Nombre_Carrera': generacion.ID_Asignan.ID_Materia.Carrera.Nombre_Carrera,
                'Semestre': generacion.ID_Asignan.Semestre,
                'Grupo': generacion.ID_Asignan.Grupo,
                'Unidad': generacion.Unidad,
                'aprobados': 100 - generacion.Reprobados,
                'reprobados': generacion.Reprobados,
            }
            lista.append(formato)
        return Response(data=lista, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p3ReprobacionGrupo(request, query):
    u"""View filtro que retorna el indice de reprobación por grupo de una
    carrera e información relacionada.
    (ADMIN)

    query -- String que contiene dos valores divididos por un '-':
        [0] -> Grupo
        [1] -> Nombre de la Carrera
    """
    splitted = query.split("-")
    try:
        generan = Generan.objects.filter(Q(ID_Asignan__Grupo=splitted[0]),
                                         Q(ID_Asignan__ID_Materia__Carrera__Nombre_Carrera=splitted[1]))
    except Generan.DoesNotExist:
        return Response({'Error': "Generan no existe"},
                        status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        lista = []
        for generacion in generan:
            formato = {
                'Nombre_Usuario': generacion.ID_Asignan.ID_Usuario.Nombre_Usuario,
                'Nombre_Materia': generacion.ID_Asignan.ID_Materia.Nombre_Materia,
                'Nombre_Carrera': generacion.ID_Asignan.ID_Materia.Carrera.Nombre_Carrera,
                'Semestre': generacion.ID_Asignan.Semestre,
                'Grupo': generacion.ID_Asignan.Grupo,
                'Unidad': generacion.Unidad,
                'aprobados': 100 - generacion.Reprobados,
                'reprobados': generacion.Reprobados,
            }
            lista.append(formato)
        return Response(data=lista, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p3IndiceEntregaReportesCarrera(request, nombre_reporte, nombre_carrera):
    u"""View filtro que retorna, además del indice de entrega de reportes, la
    información relacionada a los argumentos de la misma.
    (ADMIN)

    nombre_reporte -- Nombre del reporte del cual se esta buscando sus indices
                      de entrega.
    nombre_carrera -- Nombre de la carrera de la cual se esta filtrando el
                      indice de entrega de reportes.
    """
    if request.method == 'GET':
        if nombre_reporte == "" or nombre_carrera == "":
            return Response({'Error': "Argumento vacio"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            reporte = Reportes.objects.get(Nombre_Reporte=nombre_reporte)
            carrera = Carreras.objects.get(Nombre_Carrera=nombre_carrera)

            generan = Generan.objects.filter(Q(ID_Reporte=reporte) &
                                             Q(ID_Asignan__ID_Materia__Carrera=carrera))
            count_puntual = generan.filter(Estatus="Entrega a tiempo").count()
            count_inpuntual = generan.filter(Estatus="Entrega tarde").count()

        except Reportes.DoesNotExist:
            return Response({'Error': "Reporte no existe"},
                            status=status.HTTP_404_NOT_FOUND)
        except Carreras.DoesNotExist:
            return Response({'Error': "Carrera no existe"},
                            status=status.HTTP_404_NOT_FOUND)
        except Generan.DoesNotExist:
            return Response({'Error': "Generan no existe"},
                            status=status.HTTP_404_NOT_FOUND)
        formato = {
                "Nombre_Reporte": reporte.Nombre_Reporte,
                "Nombre_Carrera": carrera.Nombre_Carrera,
                "Entrega_Limite": reporte.Fecha_Entrega,
                "Count_Puntuales": count_puntual,
                "Count_Inpuntuales": count_inpuntual
                }
    return Response(data=formato, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def getRegistroPNC(request):
    u"""View que retorna el registro general de PNCs. En caso de no existir, el
    sistema lo crea.
    (ADMIN)
    """
    cwd = os.getcwd()
    filename_registro_pnc = "registro_pnc.json"
    registro_pnc_path = Path(f'{cwd}/static/{filename_registro_pnc}')
    registro_pnc = {
        "lastPNCID": 1,
        "registro": {
            "reportesRegistrados": {
                "idsReportes": []
            }
        }
    }
    if (registro_pnc_path.exists() and registro_pnc_path.is_file()):
        # Si existe el archivo registro_pnc.json se deberá leer y transformar
        # de formato json a python.
        data_file = open(registro_pnc_path, "r")
        registro_pnc = json.load(data_file)
    else:
        print(f"Creando '{registro_pnc_path}'...")
        data_file = open(registro_pnc_path, "w")
        json.dump(registro_pnc, data_file)

    print(registro_pnc)
    return Response(data=registro_pnc, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def addRegistroPNC(request):
    u"""View que permite agregar un nuevo reporte PNC al registro general de
    PNC.
    (ADMIN)

    request -- Objeto de la libreria rest_framework que representa el cuerpo
               de un request HTTP
    request.data -- Diccionario que contiene los atributos:
        'ID_reporte': int,
        'new_PNC': {
            'numeroPNC': int,
            'folio': str,
            'fechaRegistro': str,
            'especIncumplida': str,
            'accionImplantada': str,
            'isEliminaPNC': bool
        }
    """
    cwd = os.getcwd()
    filename_registro_pnc = "registro_pnc.json"
    registro_pnc_path = Path(f'{cwd}/static/{filename_registro_pnc}')
    with open(registro_pnc_path, "r") as data_file:
        registro_pnc = json.load(data_file)

    eval_res = checkAddRegistro(request.data)
    if type(eval_res) is Response:
        return eval_res

    (id_reporte, new_pnc) = eval_res

    # Se da formato a los IDs de los registros (reporte y nuevo pnc)
    # Se da formato al id de reporte recibido
    formated_id_reporte = f"reporte_{id_reporte}"
    # Se toma el ultimo valor de lastPNCID en el registro_pnc para dar valor
    # al nuevo ID del pnc a agregar
    new_id_pnc = f"pnc_{registro_pnc['lastPNCID']}"

    # Se busca el id del reporte recibido dentro de
    # registro_pnc ==> registro -> reportesRegistrados -> idsReportes
    if formated_id_reporte not in registro_pnc["registro"]["reportesRegistrados"]["idsReportes"]:
        # Si no existe el ID de reporte en el registro general, se agrega
        # al final del arreglo 'idsReportes'
        registro_pnc["registro"]["reportesRegistrados"]["idsReportes"].append(formated_id_reporte)
        # Se procede a agregar el nuevo id de reporte en el registro con
        # su unico pnc registrado (new_id_pnc)
        registro_pnc["registro"][formated_id_reporte] = {
                "linkedPNCs": [new_id_pnc]
                }
    else:
        # Si el ID de reporte existe en el registro general, solo se agrega
        # el nuevo id pnc a su arreglo 'linkedPNCs'
        registro_pnc["registro"][formated_id_reporte]["linkedPNCs"].append(new_id_pnc)

    # Se asigna el diccionario recibido con los datos del PNC al new_id_pnc
    registro_pnc["registro"][new_id_pnc] = new_pnc

    # Dado que se esta agregando un nuevo registro PNC se incrementa lastPNCID
    registro_pnc["lastPNCID"] = registro_pnc["lastPNCID"] + 1

    with open(registro_pnc_path, "w") as data_file:
        json.dump(registro_pnc, data_file)

    print(request.data)

    return Response(data=registro_pnc, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def updateRegistroPNC(request):
    u"""View que permite actualizar un reporte PNC del registro general de PNC.
    (ADMIN)

    request -- Objeto de la libreria rest_framework que representa el cuerpo
               de un request HTTP
    request.data -- Diccionario que contiene los atributos:
        'ID_reporte': int
        'ID_pnc': str
        'new_PNC': {
                'numeroPNC': int,
                'folio': str,
                'fechaRegistro': str,
                'especIncumplida': str,
                'accionImplantada': str,
                'isEliminaPNC': bool
        }

        puede contener el atributo:
        'ID_old_reporte': int
    """
    cwd = os.getcwd()
    filename_registro_pnc = "registro_pnc.json"
    registro_pnc_path = Path(f'{cwd}/static/{filename_registro_pnc}')
    with open(registro_pnc_path, "r") as data_file:
        registro_pnc = json.load(data_file)

    eval_res = checkUpdateRegistro(request.data, registro_pnc)
    if type(eval_res) is Response:
        return eval_res

    id_reporte = request.data['ID_reporte']
    id_pnc = request.data['ID_pnc']
    new_pnc = request.data['new_PNC']

    formated_id_reporte = f"reporte_{id_reporte}"

    if eval_res == 4:
        id_old_reporte = request.data['ID_old_reporte']
        # Se da formato al id del reporte viejo
        formated_id_old_reporte = f"reporte_{id_old_reporte}"
        linkedPNCs = registro_pnc['registro'][formated_id_old_reporte]['linkedPNCs']
        # se busca el indice en el que se encuentra el PNC
        idx_id_pnc_in_old_reporte = linkedPNCs.index(id_pnc)

        for idx, iter_id_pnc in enumerate(linkedPNCs):
            if idx > idx_id_pnc_in_old_reporte:
                # Se procede a reducir en 1 el numeroPNC de aquellos registros
                # PNC's agregados despues de aquel que se esta cambiando
                numero_pnc = registro_pnc['registro'][iter_id_pnc]['numeroPNC']
                registro_pnc['registro'][iter_id_pnc]['numeroPNC'] = numero_pnc - 1
        # se elimina el PNC de la lista 'linkedPNCs' en el reporte viejo
        registro_pnc['registro'][formated_id_old_reporte]['linkedPNCs'].pop(idx_id_pnc_in_old_reporte)

        # Si no existe el id de reporte en el registro de reportes, es
        # agregado
        if formated_id_reporte not in registro_pnc['registro']['reportesRegistrados']['idsReportes']:
            registro_pnc['registro']['reportesRegistrados']['idsReportes'].append(formated_id_reporte)
            registro_pnc['registro'][formated_id_reporte] = {
                    'linkedPNCs': [id_pnc]
                }
        else:
            registro_pnc['registro'][formated_id_reporte]['linkedPNCs'].append(id_pnc)

    # Si eval_res == 3 quiere decir que se esta modificando el registro PNC
    # de un reporte con presencia en el registro_pnc. Por lo que no se
    # tiene que efectuar ningún cambio en los 'linkedPNCs' de dicho reporte,
    # Solo se cambiará el contenido del PNC.
    registro_pnc['registro'][id_pnc] = new_pnc

    with open(registro_pnc_path, "w") as data_file:
        json.dump(registro_pnc, data_file)

    return Response(data=registro_pnc, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def deleteRegistroPNC(request):
    u"""View que permite eliminar un reporte PNC del registro general de PNC.
    (ADMIN)

    request -- Objeto de la libreria rest_framework que representa el cuerpo
               de un request HTTP
    request.data -- Diccionario que contiene los atributos:
        'ID_reporte': int
        'ID_pnc': str
    """
    cwd = os.getcwd()
    filename_registro_pnc = "registro_pnc.json"
    registro_pnc_path = Path(f'{cwd}/static/{filename_registro_pnc}')
    with open(registro_pnc_path, "r") as data_file:
        registro_pnc = json.load(data_file)

    eval_res = checkDeleteRegistro(request.data, registro_pnc)
    if type(eval_res) is Response:
        return eval_res

    (id_reporte, id_pnc) = eval_res
    formated_id_reporte = f"reporte_{id_reporte}"

    # Se toma la lista de PNCs relacionados con el id_reporte
    linkedPNC = registro_pnc['registro'][formated_id_reporte]['linkedPNCs']
    # Se obtiene el idx en linkedPNC del PNC a eliminar
    idx_of_id_pnc_in_linkedPNC = linkedPNC.index(id_pnc)
    for idx, iter_id_pnc in enumerate(linkedPNC):
        # Se procede a iterar la lista de PNCs relacionados con el reporte
        if idx > idx_of_id_pnc_in_linkedPNC:
            # Si el idx iterado es mayor al idx del PNC a eliminar significa
            # que idx esta sobre aquellos PNC's registrados despues de quel
            # que será eliminado por lo que...
            # Se procede a copiar su numeroPNC
            numeroPNC = registro_pnc['registro'][iter_id_pnc]['numeroPNC']
            # Y a reducir en 1 este mismo.
            registro_pnc['registro'][iter_id_pnc]['numeroPNC'] = numeroPNC - 1

    # Terminado el ciclo, se procede a eliminar de la lista 'linkedPNC' del
    # id_reporte el PNC a eliminar.
    registro_pnc['registro'][formated_id_reporte]['linkedPNCs'].pop(idx_of_id_pnc_in_linkedPNC)
    # Por ultimo, se elimina el registro PNC del registro_pnc
    registro_pnc['registro'].pop(id_pnc)

    with open(registro_pnc_path, "w") as data_file:
        json.dump(registro_pnc, data_file)

    return Response(data=registro_pnc, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def downloadRegistroPNC(request):
    u"""View encargada de convertir el registro PNC a formato PDF.
    (ADMIN)
    """
    cwd = os.getcwd()
    filename_registro_pnc = "registro_pnc.json"
    registro_pnc_path = Path(f'{cwd}/static/{filename_registro_pnc}')
    with open(registro_pnc_path, "r") as data_file:
        registro_pnc = json.load(data_file)

    has_pncs = False
    # Se verifica que existan reportes dentro del registro general.
    if len(registro_pnc["registro"]["reportesRegistrados"]["idsReportes"]) == 0:
        return Response(data={
            "Error": "No existen reportes registrados por el momento."
            },
            status=status.HTTP_400_BAD_REQUEST)

    # Si hay reportes, se procede a iterar la lista de ids de reportes
    # registrados
    for id_reporte in registro_pnc["registro"]["reportesRegistrados"]["idsReportes"]:
        # Si existe por lo menos un elemento dentro de los PNCs relacionados
        # a un reporte se activa la flag 'has_pncs' y se rompe el ciclo
        if len(registro_pnc["registro"][id_reporte]["linkedPNCs"]) != 0:
            has_pncs = True
            break

    # Se evalua si se tiene PNCs registrados
    if has_pncs:
        # Si se tiene, se procede a construir el archivo PDF
        registro = registro_pnc["registro"]
        ids_reportes = registro["reportesRegistrados"]["idsReportes"]
        nombre_reporte = ""
        fecha_reporte = ""
        pdf = PncPDF()
        pdf.set_title("Registro y Control de Productos No Conformes")
        buffer = io.BytesIO()
        for id_reporte in ids_reportes:
            no_id_repo = id_reporte.split('_')[1]
            try:
                reporte = Reportes.objects.get(ID_Reporte=no_id_repo)
            except Reportes.DoesNotExist:
                return Response(data={ "Error": "No existe el reporte." },
                                status=status.HTTP_400_BAD_REQUEST)

            nombre_reporte = reporte.Nombre_Reporte
            fecha_reporte = reporte.Fecha_Entrega
            linked_pncs = registro[id_reporte]["linkedPNCs"]
            if len(linked_pncs) != 0:
                pdf.printReporte(registro,
                                 linked_pncs,
                                 nombre_reporte,
                                 fecha_reporte)
        pdf.output(buffer)
        buffer.seek(0)
        return FileResponse(buffer,
                            filename='Registro y Control de Productos No Conformes.pdf',
                            as_attachment=False)
    else:
        return Response(data={"Error": "No hay registros guardados"},
                        status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def p3RepUXCXMaeXMatXGraXGrp(request,
                             id_carrera,
                             nombre_maestro,
                             id_materia,
                             grado,
                             grupo):
    u"""View filtro que retorna la información relacionada a los argumentos de
    la misma.
         p3ReporteUnidad X Carrera X Maestro X Materia X Grado X Grupo

        id_carrera -- ID de la Carrera de la que se va a consultar
        nombre_maestro -- Nombre de un profesor
        id_materia -- ID de la Materia que se encuentra relacionada a
                      id_carrera
        grado -- Semestre del cual se busca la asignación de materia al
                 profesor
        grupo -- Grupo al cual se esta asignada dicha materia del profesor
    """
    try:
        carrera = Carreras.objects.get(ID_Carrera=id_carrera)
        maestro = Usuarios.objects.get(Nombre_Usuario=nombre_maestro)
        materia = Materias.objects.get(Q(pik=id_materia) & Q(Carrera=carrera))

        asignan = Asignan.objects.filter(Q(ID_Materia=materia) &
                                         Q(ID_Usuario=maestro) &
                                         Q(Semestre=grado) &
                                         Q(Grupo=grupo))
    except Carreras.DoesNotExist:
        return Response({'Error': "Carrera no existe"},
                        status=status.HTTP_404_NOT_FOUND)
    except Usuarios.DoesNotExist:
        return Response({'Error': "Usuario no existe"},
                        status=status.HTTP_404_NOT_FOUND)
    except Asignan.DoesNotExist:
        return Response({'Error': "Asignan no existe"},
                        status=status.HTTP_404_NOT_FOUND)
    data_2_send = []
    try:
        for asignacion in asignan:
            generan = Generan.objects.filter(Q(ID_Asignan=asignacion))
            for generacion in generan:
                data_2_send.append({
                    "ID_Asignan": generacion.ID_Asignan.ID_Asignan,
                    "ID_Reporte": generacion.ID_Reporte.ID_Reporte,
                    "Nombre_Profesor": generacion.ID_Asignan.ID_Usuario.Nombre_Usuario,
                    "Nombre_Materia:": generacion.ID_Asignan.ID_Materia.Nombre_Materia,
                    "Nombre_Reporte": generacion.ID_Reporte.Nombre_Reporte,
                    "Fecha_Entregado": generacion.Fecha_Entrega,
                    "Fecha_Especificada_Entrega": generacion.ID_Reporte.Fecha_Entrega,
                    "Carrera": generacion.ID_Asignan.ID_Materia.Carrera.Nombre_Carrera,
                    "Semestre": generacion.ID_Asignan.Semestre,
                    "Grupo": generacion.ID_Asignan.Grupo,
                    "Reprobados": generacion.Reprobados
                    })
    except Generan.DoesNotExist:
        return Response({'Error': "Generan no existe"},
                        status=status.HTTP_404_NOT_FOUND)

    if len(data_2_send) == 0:
        return Response(data={
            "Error": "Temas no encontrados"
            },
            status=status.HTTP_404_NOT_FOUND)
    return Response(data_2_send, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def getRegistroVGC(request, id_carrera, seguimiento_no, semana):
    u"""View que retorna el registro VGC especificado. En caso de no existir el
    registro que se busca, lo crea.
    (ADMIN)

    id_carrera -- ID de la Carrera a la cual pertenece el registro
    seguimiento_no -- Valor númerico que representa el número de seguimiento
                      del registro
    semana -- Semana a la cual pertenece el seguimiento del registro
    """
    try:
        Carreras.objects.get(ID_Carrera=id_carrera)
    except Carreras.DoesNotExist:
        return Response(data={
            "Error": "Carrera no existe"
            },
            status=status.HTTP_400_BAD_REQUEST)

    cwd = os.getcwd()
    filename_registro_vgc = "registro_vgc_{}_seg-no_{}_sem_{}.json".format(id_carrera,
                                                                           seguimiento_no,
                                                                           semana)
    registro_vgc_path = Path(f'{cwd}/static/{filename_registro_vgc}')
    # Por defecto la fecha de semanaDel será el día actual en el que se genera
    # el registro
    registro_vgc = {
        'lastReporteID': 1,
        'registro': []
    }

    if (registro_vgc_path.exists() and registro_vgc_path.is_file()):
        data_file = open(registro_vgc_path, "r")
        registro_vgc = json.load(data_file)
    else:
        print(f"Creando {registro_vgc_path}...")
        data_file = open(registro_vgc_path, "w")
        json.dump(registro_vgc, data_file)

    print(registro_vgc)
    return Response(data=registro_vgc, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def addRegistroVGC(request, id_carrera, seguimiento_no, semana):
    u"""View que permite agregar un nuevo reporte VGC en un registro especifico
    de VGC.
    (ADMIN)

    request -- Objeto de la libreria rest_framework que representa el cuerpo
               de un request HTTP
    request.data -- Diccionario que contiene los atributos:
        'numeroReporte': int
        'nombreProfesor': str
        'asignatura': str
        'GradoGrupo': str
        'tema': str
        'semanaProgramada': str
        'verificacion': bool
        'RCMRRC': bool
        'indReprobacion': int
        'CCEEID': bool
        'observaciones': str
    id_carrera -- ID de la Carrera a la cual pertenece el registro
    seguimiento_no -- Valor númerico que representa el número de seguimiento
                      del registro
    semana -- Semana a la cual pertenece el seguimiento del registro
    """
    try:
        Carreras.objects.get(ID_Carrera=id_carrera)
    except Carreras.DoesNotExist:
        return Response(data={
            "Error": "Carrera no existe"
            },
            status=status.HTTP_400_BAD_REQUEST)

    cwd = os.getcwd()
    filename_registro_vgc = "registro_vgc_{}_seg-no_{}_sem_{}.json".format(id_carrera,
                                                                           seguimiento_no,
                                                                           semana)
    registro_vgc_path = Path(f'{cwd}/static/{filename_registro_vgc}')
    with open(registro_vgc_path, "r") as data_file:
        registro_vgc = json.load(data_file)

    eval_res = checkAddRegistroVGC(request.data, registro_vgc)
    if type(eval_res) is Response:
        return eval_res

    # Se reasigna a una nueva variable solo para dar contexto del resultado
    newReporte = eval_res['newReporte']

    # Se incrementa el lastReporteID ya que se esta agregando un nuevo
    # elemento
    registro_vgc["lastReporteID"] = registro_vgc["lastReporteID"] + 1
    registro_vgc["registro"].append(newReporte)

    with open(registro_vgc_path, "w") as data_file:
        json.dump(registro_vgc, data_file)

    print(request.data)

    return Response(data=registro_vgc, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def updateRegistroVGC(request, id_carrera, seguimiento_no, semana):
    u"""View que permite actualizar un reporte VGC en un registro especifico de
    VGC.
    (ADMIN)

    request -- Objeto de la libreria rest_framework que representa el cuerpo
               de un request HTTP
    request.data -- Diccionario que contiene el atributo:
        'newReporte': {
            'numeroReporte': int
            'nombreProfesor': str
            'asignatura': str
            'GradoGrupo': str
            'tema': str
            'semanaProgramada': str
            'verificacion': bool
            'RCMRRC': bool
            'indReprobacion': int
            'CCEEID': bool
            'observaciones': str
        }
    id_carrera -- ID de la Carrera a la cual pertenece el registro
    seguimiento_no -- Valor númerico que representa el número de seguimiento
                      del registro
    semana -- Semana a la cual pertenece el seguimiento del registro
    """
    try:
        Carreras.objects.get(ID_Carrera=id_carrera)
    except Carreras.DoesNotExist:
        return Response(data={
            "Error": "Carrera no existe"
            },
            status=status.HTTP_400_BAD_REQUEST)

    cwd = os.getcwd()
    filename_registro_vgc = "registro_vgc_{}_seg-no_{}_sem_{}.json".format(id_carrera,
                                                                           seguimiento_no,
                                                                           semana)
    registro_vgc_path = Path(f'{cwd}/static/{filename_registro_vgc}')
    with open(registro_vgc_path, "r") as data_file:
        registro_vgc = json.load(data_file)

    eval_res = checkUpdateRegistroVGC(request.data, registro_vgc)
    if type(eval_res) is Response:
        return eval_res

    # Se reasigna a una nueva variable solo para dar contexto del resultado
    updatedRegistro = eval_res

    for idx, reporte in enumerate(registro_vgc["registro"]):
        if reporte["numeroReporte"] == updatedRegistro["numeroReporte"]:
            registro_vgc["registro"][idx] = updatedRegistro
            break

    with open(registro_vgc_path, "w") as data_file:
        json.dump(registro_vgc, data_file)

    return Response(data=registro_vgc, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def deleteRegistroVGC(request, id_carrera, seguimiento_no, semana):
    u"""View que permite eliminar un reporte VGC de un registro especifico de
    VGC.
    (ADMIN)

    request -- Objeto de la libreria rest_framework que representa el cuerpo
               de un request HTTP
    request.data -- Diccionario que contiene un unico atributo: 'numeroReporte'
    id_carrera -- ID de la Carrera a la cual pertenece el registro
    seguimiento_no -- Valor númerico que representa el número de seguimiento
                      del registro
    semana -- Semana a la cual pertenece el seguimiento del registro
    """
    try:
        Carreras.objects.get(ID_Carrera=id_carrera)
    except Carreras.DoesNotExist:
        return Response(data={
            "Error": "Carrera no existe"
            },
            status=status.HTTP_400_BAD_REQUEST)

    cwd = os.getcwd()
    filename_registro_vgc = "registro_vgc_{}_seg-no_{}_sem_{}.json".format(id_carrera,
                                                                           seguimiento_no,
                                                                           semana)
    registro_vgc_path = Path(f'{cwd}/static/{filename_registro_vgc}')
    with open(registro_vgc_path, "r") as data_file:
        registro_vgc = json.load(data_file)

    eval_res = checkDeleteRegistroVGC(request.data, registro_vgc)
    if type(eval_res) is Response:
        return eval_res

    no_reporte_2_delete = eval_res

    idx_reporte_2_delete = -1
    is_reporte_2_delete_found = False
    for idx, reporte in enumerate(registro_vgc["registro"]):
        if is_reporte_2_delete_found:
            # Se debe actualizar el numeroReporte de todos los reportes que se
            # encuentran despues del que fue eliminado
            registro_vgc["registro"][idx]["numeroReporte"] = registro_vgc["registro"][idx]["numeroReporte"] - 1
        elif reporte["numeroReporte"] == no_reporte_2_delete:
            # Se toma el idx de aquel reporte cuyo atributo 'numeroReporte' es
            # igual al recibido
            idx_reporte_2_delete = idx
            # Ya que fue encontrado el registro a eliminar, se activa la flag
            # 'is_reporte_2_delete_found' que será usado para las demás
            # iteraciones del for
            is_reporte_2_delete_found = True

    # Se reduce el lastReporteID en 1 ya que fue eliminado un reporte
    registro_vgc["lastReporteID"] = registro_vgc["lastReporteID"] - 1
    # Se elimina el reporte que se encuentra en el idx_reporte_2_delete
    registro_vgc["registro"].pop(idx_reporte_2_delete)

    with open(registro_vgc_path, "w") as data_file:
        json.dump(registro_vgc, data_file)

    return Response(data=registro_vgc, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, AdminDocentePermission])
def vgcExcel(request, id_carrera, seguimiento_no, semana):
    u"""View encargada de convertir un registro especifico de VGC a formato
    xlsx.
    (ADMIN)

    id_carrera -- ID de la Carrera a la cual pertenece el registro
    seguimiento_no -- Valor númerico que representa el número de seguimiento
                      del registro
    semana -- Semana a la cual pertenece el seguimiento del registro
    """
    try:
        carrera = Carreras.objects.get(ID_Carrera=id_carrera)
    except Carreras.DoesNotExist:
        return Response(data={
            "Error": "Carrera no existe"
            },
            status=status.HTTP_400_BAD_REQUEST)

    cwd = os.getcwd()
    filename_registro_vgc = "registro_vgc_{}_seg-no_{}_sem_{}.json".format(id_carrera,
                                                                           seguimiento_no,
                                                                           semana)
    registro_vgc_path = Path(f'{cwd}/static/{filename_registro_vgc}')
    with open(registro_vgc_path, "r") as data_file:
        registro_vgc = json.load(data_file)

    if registro_vgc['lastReporteID'] < 1:
        return Response(data={"Error": "No hay registros guardados"},
                        status=status.HTTP_404_NOT_FOUND)

    registro = registro_vgc["registro"]
    buffer = io.BytesIO()
    vgc_excel = VGCExcel(buffer,
                         carrera.Nombre_Carrera,
                         seguimiento_no,
                         semana)
    vgc_excel.buildExcel(registro)
    buffer.seek(0)
    return FileResponse(buffer,
                        filename='Formato para la Verificación de la Gestión del Curso.xlsx',
                        as_attachment=True)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def getMailGroups(request):
    u"""View que retorna el registro de grupos de correos. En caso de no existir
    crea desde cero el registro.
    (ADMIN)
    """
    cwd = os.getcwd()
    filename = "registro_mail_groups.json"
    registro_mail_groups_path = Path(f'{cwd}/static/{filename}')

    registro_mail_groups = []

    if registro_mail_groups_path.exists() and registro_mail_groups_path.is_file():
        data_file = open(registro_mail_groups_path, "r")
        registro_mail_groups = json.load(data_file)
    else:
        print(f"Creando {registro_mail_groups_path}...")
        data_file = open(registro_mail_groups_path, "w")
        json.dump(registro_mail_groups, data_file)

    print("\n\n")
    print(registro_mail_groups)
    return Response(data=registro_mail_groups, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def addMailGroup(request):
    u"""View que permite agregar un grupo de correos al registro.
    (ADMIN)

    request -- Objeto de la libreria rest_framework que representa el cuerpo
               de un request HTTP
    request.data -- Diccionario que contiene dos atributos: 'groupName' y
                    'suscritos'
    """
    print(request.data)

    # TODO: validar los datos recibidos
    new_mail_group = request.data

    cwd = os.getcwd()
    filename = "registro_mail_groups.json"
    registro_mail_groups_path = Path(f'{cwd}/static/{filename}')

    with open(registro_mail_groups_path) as data_file:
        registro_mail_groups = json.load(data_file)

    registro_mail_groups.append(new_mail_group)
    print('\n\n\n\n\t\tNuevo Grupo agregado')
    print('\n\tGrupo Agregado:')
    print(new_mail_group)
    print('\n\tRegistro de Grupos:')
    print(registro_mail_groups)
    print('\n\n\n')

    with open(registro_mail_groups_path, "w") as data_file:
        json.dump(registro_mail_groups, data_file)

    return Response(data={
        "status": "OK"
        },
        status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def updateMailGroup(request):
    u"""View que permite actualizar un grupo de correos del registro.
    (ADMIN)

    request -- Objeto de la libreria rest_framework que representa el cuerpo
               de un request HTTP
    request.data -- Diccionario que contiene dos atributos: 'groupName' y
                    'suscritos'
    """
    print('\n\n\n\t\tGrupo a modificar:')
    print(request.data)

    mail_group_name = request.data['groupName']
    group_suscribers = request.data['suscritos']

    cwd = os.getcwd()
    filename = "registro_mail_groups.json"
    registro_mail_groups_path = Path(f'{cwd}/static/{filename}')

    with open(registro_mail_groups_path) as data_file:
        registro_mail_groups = json.load(data_file)

    for idx, grupo in enumerate(registro_mail_groups):
        if grupo['groupName'] == mail_group_name:
            registro_mail_groups[idx]['suscritos'] = group_suscribers
            break

    print('\n\n\n\tRegistro de grupos despues de modificar:')
    print(registro_mail_groups)
    print('\n\n\n\n')

    with open(registro_mail_groups_path, "w") as data_file:
        json.dump(registro_mail_groups, data_file)

    return Response(data={
        "status": "OK"
        },
        status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def deleteMailGroup(request):
    u"""View que permite eliminar un grupo de correos del registro.
    (ADMIN)

    request -- Objeto de la libreria rest_framework que representa el cuerpo
               de un request HTTP
    request.data -- Diccionario que contiene un unico atributo: 'groupName'
    """
    print('\n\n\n\t\tGrupo a eliminar:')
    print(request.data)

    mail_group_name = request.data['groupName']
    idx_of_group = -1

    cwd = os.getcwd()
    filename = "registro_mail_groups.json"
    registro_mail_groups_path = Path(f'{cwd}/static/{filename}')

    with open(registro_mail_groups_path) as data_file:
        registro_mail_groups = json.load(data_file)

    for idx, grupo in enumerate(registro_mail_groups):
        if grupo['groupName'] == mail_group_name:
            idx_of_group = idx
            break

    if idx_of_group != -1:
        registro_mail_groups.pop(idx_of_group)

    print('\n\n\n\tRegistro de grupos despues de eliminar:')
    print(registro_mail_groups)
    print('\n\n\n\n')

    with open(registro_mail_groups_path, "w") as data_file:
        json.dump(registro_mail_groups, data_file)

    return Response(data={
        "status": "OK"
        },
        status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, OnlyAdminPermission])
def sendMailToGroup(request):
    u"""View cuya funcion es envíar correos a todos aquellos usuarios que forman
    parte de un grupo de correos.
    (ADMIN)

    request -- Objeto de la libreria rest_framework que representa el cuerpo
               de un request HTTP
    request.data -- Lista de strings que representan el atributo 'groupName' de
                    un un grupo de correos registrado.
    """
    # TODO: Validar los datos recibidos
    print('\n\n\nHoal')
    msg = request.data['msg']
    groups = request.data['grupos']

    cwd = os.getcwd()
    filename = "registro_mail_groups.json"
    registro_mail_groups_path = Path(f'{cwd}/static/{filename}')

    with open(registro_mail_groups_path, 'r') as data_file:
        registro_mail_groups = json.load(data_file)

    mail_groups = []
    print(f'Grupos: {groups}')
    for mail_group in registro_mail_groups:
        print(mail_group)
        if mail_group in groups:
            mail_groups.append(mail_group)

    users_info = []
    print(mail_groups)
    try:
        for mail_group in mail_groups:
            for suscrito in mail_group['suscritos']:
                # suscrito -> dict:
                #   id: int
                #   nombre: str
                usuario = Usuarios.objects.get(ID_Usuario=suscrito['id'],
                                               Nombre_Usuario=suscrito['nombre'])
                nombre = usuario.Nombre_Usuario
                correo = usuario.CorreoE
                user_info = (nombre, correo)
                users_info.append(user_info)
            print('Cargando en celery...')
            sendGroupMail.delay(msg, users_info)
            print('Carga en celery completada')
    except Usuarios.DoesNotExist:
        return Response(data={
            "Error": "Usuario no existe."
            },
            status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response(data={
            "Error": "Error al enviar el mensaje"
            },
            status=status.HTTP_400_BAD_REQUEST)

    return Response(data={
        "status": "OK"
        },
        status=status.HTTP_200_OK)
