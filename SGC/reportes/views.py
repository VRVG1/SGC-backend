
from datetime import date, datetime
import os

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