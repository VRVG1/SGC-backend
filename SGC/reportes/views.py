
from datetime import date, datetime
import io
import os

from django.http import FileResponse

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
from .tasks import sendMensaje
from django.db.models import Q
from fpdf import FPDF
import matplotlib.pyplot as plt
import matplotlib

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
                sendMensaje.delay(msg, False, usuario.CorreoE)
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
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated, AdminDocentePermission])
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
    pdf.cell(w=0,txt=f'A continuación se presenta la información de manera grafica: ',ln=2,align='C')

    heights=[atiempoC,tardeC] #valores Y
    bar_labels=['A tiempo','Tarde'] #valores X
    matplotlib.use('agg')
    plt.bar(bar_labels,heights,width=0.2,color='#6B809B')
    plt.xlabel('Entregas') 
    plt.ylabel('Cantidad de incidencia')
    plt.title(f"Grafica de entregas de: {query}")

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

@api_view(['GET'])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated, AdminDocentePermission])
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
    pdf.cell(w=0,txt=f'A continuación se presenta la información de manera grafica: ',ln=2,align='C')

    heights=[atiempoC,tardeC] #valores Y
    bar_labels=['A tiempo','Tarde'] #valores X
    matplotlib.use('agg')
    plt.bar(bar_labels,heights,width=0.2,color='#6B809B')
    plt.xlabel('Entregas')
    plt.ylabel('Cantidad de incidencia')
    plt.title(f"Grafica de entregas de: {query}")

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
