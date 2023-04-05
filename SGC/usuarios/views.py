from datetime import date
import io
from django.http import FileResponse
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
from materias.models import Asignan, Materias, Carreras
from reportes.models import Reportes, Generan
from fpdf import FPDF
import matplotlib.pyplot as plt
import matplotlib
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
def p2MaestrosCarrera(request,query):
    '''
    Filtro que corresponde al filtro: Maestros por carrera
    (ADMIN)
    '''
    try:
        asignan = Asignan.objects.filter(ID_Materia__Carrera__Nombre_Carrera__startswith=query)
    except Asignan.DoesNotExist:
        return Response({'Error':'Asignan no existe'},status=status.HTTP_404_NOT_FOUND)
    
    try:
        lista = []
        for i in asignan:
            usuario = Usuarios.objects.get(ID_Usuario=i.ID_Usuario.ID_Usuario)
            lista.append(usuario)
        usuarios = set(lista) 
    except Usuarios.DoesNotExist:
        return Response({'Error':'Usuario no existe'},status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        lista = []
        serializer = list(usuarios)
        for i in serializer:
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
def p2MaestrosHora(request, query):
    '''
    View que pertenece al filtro: Maestros(as) que laboran en cierta hora.
    (ADMIN)
    '''
    try:
        asignan = Asignan.objects.filter(Hora__startswith=query)
    except Asignan.DoesNotExist:
        return Response({'Error':'Asignan no existe'},status=status.HTTP_404_NOT_FOUND)
    
    try:
        lista = []
        for i in asignan:
            usuario = Usuarios.objects.get(ID_Usuario=i.ID_Usuario.ID_Usuario)
            lista.append(usuario)
        usuarios = set(lista)
    except Usuarios.DoesNotExist:
        return Response({'Error':'Usuario no existe'},status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        lista = []
        serializer = list(usuarios)
        for i in serializer:
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
def p2MaestrosIndice(request):
    '''
    View que pertenece al filtro: Maestros(as) con el mas alto/bajo indice de reprobacion.
    (ADMIN)
    '''

    usuarios = Usuarios.objects.filter(Tipo_Usuario='Docente')

    auxL = []
    aux = {}
    for i in usuarios:
        auxL = []
        generan = Generan.objects.filter(ID_Asignan__ID_Usuario = i, ID_Reporte__Unidad = True)
        auxL.append(generan)
        aux.update({i.Nombre_Usuario:auxL})

    lista = []
    for x in aux.keys():
        rep = 0
        for i in aux[x]:
            tam = len(i)
            for o in i:
                if o.Reprobados >= 0:
                    rep = rep + o.Reprobados
                else:
                    tam = tam - 1
            rep = rep / tam
            mai = Usuarios.objects.get(Nombre_Usuario=x)
            auxU = {
                'PK':mai.PK,
                'ID_Usuario':{'username':mai.ID_Usuario.username,'password':mai.ID_Usuario.password},
                'Nombre_Usuario':f'{mai.Nombre_Usuario} - {str(round(rep))}%',
                'Tipo_Usuario':mai.Tipo_Usuario,
                'CorreoE':mai.CorreoE,
                'Permiso':mai.Permiso,
                'Indice':round(rep)
            }
            lista.append(auxU)

    if request.method == 'GET':
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
def p2MaestrosCarreraPDF(request, query):
    '''
    View que corresponde al PDF: Maestros por carrera.
    (ADMIN)
    '''
    try:
        asignan = Asignan.objects.filter(ID_Materia__Carrera__Nombre_Carrera__startswith = query)
    except Materias.DoesNotExist:
        return Response({'Error':'Materias no existen'},status=status.HTTP_404_NOT_FOUND)

    if asignan:
        buffer = io.BytesIO()

        global titulo
        titulo = 'Maestros por carrera\n'

        pdf = PDF(format='Letter')
        pdf.add_page()
        pdf.set_font("helvetica",size=12)
        pdf.set_title('Maestros por carrera')

        aux = set()
        for i in asignan:
            aux.add(i.ID_Materia.Carrera.Nombre_Carrera)
        
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
        names = []
        for a in aux:
            data.append([a])
            data.append(['Nombre','Correo electronico'])
            for i in asignan:
                if i.ID_Materia.Carrera.Nombre_Carrera == a:
                    if i.ID_Usuario.Nombre_Usuario not in names:
                        data.append([i.ID_Usuario.Nombre_Usuario,i.ID_Usuario.CorreoE])
                        names.append(i.ID_Usuario.Nombre_Usuario)
            names = []

        tamL = pdf.font_size_pt * 0.7
        tamC = pdf.epw
        f = False
        for i in data:
            if len(i) > 1:
                pdf.set_font('Helvetica',size=12)
                for u in i:
                    if u == 'Nombre' or u == 'Correo electronico':
                        pdf.set_font('Helvetica','B',size=12)
                        pdf.cell(w=tamC/2,h=tamL,txt=u,border=1,align='C')
                    else:
                        pdf.set_font('Helvetica',size=12)
                        pdf.cell(w=tamC/2,h=tamL,txt=u,border=1,align='L')
                pdf.ln(tamL)
            else:
                pdf.set_font('Helvetica','B',size=12)
                pdf.ln(tamL)
                pdf.cell(w=0,h=tamL,txt=i[0],border=1,ln=2,align='C')

        pdf.output(buffer)

        buffer.seek(0)

        if request.method == 'GET':
            return FileResponse(buffer, filename='Maestros.pdf', as_attachment=False)
    else:
        if request.method == 'GET':
            return Response({'Error','No hay información para poblar el pdf'},status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MaestrosHoraPDF(request, query):
    '''
    View que pertenece al filtro: Maestros(as) que laboran en cierta hora.
    (ADMIN)
    '''
    try:
        asignan = Asignan.objects.filter(Hora__startswith=query)
    except Asignan.DoesNotExist:
        return Response({'Error':'Asignan no existe'},status=status.HTTP_404_NOT_FOUND)
    
    try:
        lista = []
        for i in asignan:
            usuario = Usuarios.objects.get(ID_Usuario=i.ID_Usuario.ID_Usuario)
            lista.append(usuario)
        usuarios = set(lista)
    except Usuarios.DoesNotExist:
        return Response({'Error':'Usuario no existe'},status=status.HTTP_404_NOT_FOUND)
    
    if asignan:
        buffer = io.BytesIO()

        global titulo
        titulo = 'Maestros(as) que laboran en cierta hora\n'

        pdf = PDF(format='Letter')
        pdf.add_page()
        pdf.set_font("helvetica",size=12)
        pdf.set_title('Maestros(as) que laboran en cierta hora')

        pdf.set_left_margin(55) # MARGEN REAL
        pdf.set_right_margin(55)

        pdf.multi_cell(w=0,txt=f'Los siguientes maestros(as) imparten en la hora: {query}',border=0,ln=1,align='C')
        
        pdf.set_left_margin(10) # MARGEN REAL
        pdf.set_right_margin(10)

        pdf.set_draw_color(192, 194, 196)
        
        pdf.set_left_margin(10) # MARGEN REAL
        pdf.set_right_margin(10)

        data = []
        for i in usuarios:
            data.append([i.Nombre_Usuario])
            data.append(['Materia','Semestre','Grupo','Dia','Aula','Hora'])
            auxAs = Asignan.objects.filter(ID_Usuario = i, Hora__startswith = query)
            for a in auxAs:
                data.append([a.ID_Materia.Nombre_Materia,str(a.Semestre),a.Grupo,a.Dia,a.Aula,a.Hora])

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
                pdf.set_font('helvetica',size=12)
                for u in i:
                    if len(u) > 23:
                        cx = pdf.get_x()
                        cy = pdf.get_y()
                        tam = True
                        ax = u.replace(' ','\n')
                        sal = ax.count('\n')
                        factor_Mul = sal + 1
                        pdf.multi_cell(w=tamC/6,txt=ax,border=1,ln=0,align='L')
                        ex = pdf.get_x()
                        ey = pdf.get_y()
                        pdf.set_x(ex)
                    elif tam:
                        cx = pdf.get_x()
                        pdf.set_xy(cx,cy)
                        pdf.multi_cell(w=tamC/6,h=tamL*(factor_Mul/1.99),txt=u,border=1,ln=0,align='L')
                        ex = cx + (tamC/6)
                        pdf.set_x(ex)
                    else:
                        pdf.cell(w=tamC/6,h=tamL,txt=u,border=1,ln=0,align='L') 
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

        pdf.output(buffer)

        buffer.seek(0)

        if request.method == 'GET':
            return FileResponse(buffer, filename='Maestros.pdf', as_attachment=False)
    else:
        if request.method == 'GET':
            return Response({'Error','No hay información para poblar el pdf'},status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MaestrosIndiceAltoPDF(request):
    '''
    View que pertenece al filtro: Maestros(as) con el mas alto/bajo indice de reprobacion.
    (ADMIN)
    '''

    usuarios = Usuarios.objects.filter(Tipo_Usuario='Docente')

    auxL = []
    aux = {}
    for i in usuarios:
        auxL = []
        generan = Generan.objects.filter(ID_Asignan__ID_Usuario = i, ID_Reporte__Unidad = True)
        auxL.append(generan)
        aux.update({i.Nombre_Usuario:auxL})

    nombresIndices = {}
    for x in aux.keys():
        rep = 0
        for i in aux[x]:
            tam = len(i)
            for o in i:
                if o.Reprobados >= 0:
                    rep = rep + o.Reprobados
                else:
                    tam = tam - 1
            rep = rep / tam
            mai = Usuarios.objects.get(Nombre_Usuario=x)
            nombresIndices[f'{mai.Nombre_Usuario}'] = round(rep)
    
    if usuarios:
        buffer = io.BytesIO()

        global titulo
        titulo = 'Maestros(as) con el mas alto indice de reprobación\n'

        pdf = PDF(format='Letter')
        pdf.add_page()
        pdf.set_font("helvetica",size=12)
        pdf.set_title('Maestros(as) con el mas alto indice de reprobación')

        pdf.set_left_margin(55) # MARGEN REAL
        pdf.set_right_margin(55)

        pdf.multi_cell(w=0,txt=f'Se presentan todos los maestros ordenados de mayor a menor, por indice de reprobación',border=0,ln=1,align='C')
        
        pdf.set_left_margin(10) # MARGEN REAL
        pdf.set_right_margin(10)

        pdf.set_draw_color(192, 194, 196)
        
        pdf.set_left_margin(10) # MARGEN REAL
        pdf.set_right_margin(10)
    
        maestrosordenIn = sorted(nombresIndices.items(),key=lambda x:x[1],reverse=True)
        
        data = []
        data.append(['Maestros(as) por indice de reprobación'])
        data.append(['Maestro(a)','Indice de reprobacion','Correo'])
        for i in maestrosordenIn:
            data.append(i)
                
        tamL = pdf.font_size_pt * 0.7
        tamC = pdf.epw
        correo = ''
        for i in data:
            if len(i) == 1:
                pdf.set_font('helvetica','B',size=12)
                pdf.ln(tamL)
                pdf.cell(w=0,h=tamL,txt=i[0],border=1,ln=2,align='C')
            elif len(i) == 2:
                pdf.set_font('helvetica',size=12)
                for u in i:
                    if isinstance(u,int):
                        pdf.cell(w=tamC/3,h=tamL,txt=str(u),border=1,ln=0,align='L')
                        pdf.cell(w=tamC/3,h=tamL,txt=correo,border=1,ln=0,align='L')
                    else:
                        pdf.cell(w=tamC/3,h=tamL,txt=u,border=1,ln=0,align='L')
                        auxN = Usuarios.objects.get(Nombre_Usuario=u)
                        correo = auxN.CorreoE
                pdf.ln(tamL)
            else:
                for u in i:
                    pdf.cell(w=tamC/3,h=tamL,txt=u,border=1,ln=0,align='C')
                pdf.ln(tamL)
        
        pdf.ln(tamL)
        pdf.cell(w=0,txt=f'A continuación se presenta la información de manera grafica: ',ln=2,align='C')

        heights=[] #valores Y
        bar_labels=[] #valores X
        for i in maestrosordenIn:
                for u in i:
                    if isinstance(u, int):
                        heights.append(u)
                    else:
                        bar_labels.append(u)

        matplotlib.use('agg')
        plt.bar(bar_labels,heights,width=0.2,color='#6B809B')
        plt.xlabel('Maestros(as)')
        plt.ylabel('Indices de reprobación')
        plt.title("Grafica de indices de reprobación")

        img_buf = io.BytesIO()
        plt.savefig(img_buf, dpi=200)

        pdf.image(img_buf, w=pdf.epw)

        pdf.output(buffer)
        img_buf.close()
        buffer.seek(0)

        if request.method == 'GET':
            return FileResponse(buffer, filename='Maestros.pdf', as_attachment=False)
    else:
        if request.method == 'GET':
            return Response({'Error','No hay información para poblar el pdf'},status=status.HTTP_204_NO_CONTENT)
        
@api_view(['GET'])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated, AdminDocentePermission])
def p2MaestrosIndiceBajoPDF(request):
    '''
    View que pertenece al filtro: Maestros(as) con el mas bajo indice de reprobacion.
    (ADMIN)
    '''

    usuarios = Usuarios.objects.filter(Tipo_Usuario='Docente')

    auxL = []
    aux = {}
    for i in usuarios:
        auxL = []
        generan = Generan.objects.filter(ID_Asignan__ID_Usuario = i, ID_Reporte__Unidad = True)
        auxL.append(generan)
        aux.update({i.Nombre_Usuario:auxL})
        
    nombresIndices = {}
    for x in aux.keys():
        rep = 0
        for i in aux[x]:
            tam = len(i)
            for o in i:
                if o.Reprobados >= 0:
                    rep = rep + o.Reprobados
                else:
                    tam = tam - 1
            rep = rep / tam
            mai = Usuarios.objects.get(Nombre_Usuario=x)
            nombresIndices[f'{mai.Nombre_Usuario}'] = round(rep)
    
    if usuarios:
        buffer = io.BytesIO()

        global titulo
        titulo = 'Maestros(as) con el mas bajo indice de reprobación\n'

        pdf = PDF(format='Letter')
        pdf.add_page()
        pdf.set_font("helvetica",size=12)
        pdf.set_title('Maestros(as) con el mas bajo indice de reprobación')

        pdf.set_left_margin(55) # MARGEN REAL
        pdf.set_right_margin(55)

        pdf.multi_cell(w=0,txt=f'Se presentan todos los maestros ordenados de menor a mayor, por indice de reprobación',border=0,ln=1,align='C')
        
        pdf.set_left_margin(10) # MARGEN REAL
        pdf.set_right_margin(10)

        pdf.set_draw_color(192, 194, 196)
        
        pdf.set_left_margin(10) # MARGEN REAL
        pdf.set_right_margin(10)
    
        maestrosordenIn = sorted(nombresIndices.items(),key=lambda x:x[1])
        
        data = []
        data.append(['Maestros(as) por indice de reprobación'])
        data.append(['Maestro(a)','Indice de reprobacion','Correo'])
        for i in maestrosordenIn:
            data.append(i)
                
        tamL = pdf.font_size_pt * 0.7
        tamC = pdf.epw
        correo = ''
        for i in data:
            if len(i) == 1:
                pdf.set_font('helvetica','B',size=12)
                pdf.ln(tamL)
                pdf.cell(w=0,h=tamL,txt=i[0],border=1,ln=2,align='C')
            elif len(i) == 2:
                pdf.set_font('helvetica',size=12)
                for u in i:
                    if isinstance(u,int):
                        pdf.cell(w=tamC/3,h=tamL,txt=str(u),border=1,ln=0,align='L')
                        pdf.cell(w=tamC/3,h=tamL,txt=correo,border=1,ln=0,align='L')
                    else:
                        pdf.cell(w=tamC/3,h=tamL,txt=u,border=1,ln=0,align='L')
                        auxN = Usuarios.objects.get(Nombre_Usuario=u)
                        correo = auxN.CorreoE
                pdf.ln(tamL)
            else:
                for u in i:
                    pdf.cell(w=tamC/3,h=tamL,txt=u,border=1,ln=0,align='C')
                pdf.ln(tamL)
        
        pdf.ln(tamL)
        pdf.cell(w=0,txt=f'A continuación se presenta la información de manera grafica: ',ln=2,align='C')

        heights=[] #valores Y
        bar_labels=[] #valores X
        for i in maestrosordenIn:
                for u in i:
                    if isinstance(u, int):
                        heights.append(u)
                    else:
                        bar_labels.append(u)

        matplotlib.use('agg')
        plt.bar(bar_labels,heights,width=0.2,color='#6B809B')
        plt.xlabel('Maestros(as)')
        plt.ylabel('Indices de reprobación')
        plt.title("Grafica de indices de reprobación")

        img_buf = io.BytesIO()
        plt.savefig(img_buf, dpi=200)

        pdf.image(img_buf, w=pdf.epw)

        pdf.output(buffer)
        img_buf.close()
        buffer.seek(0)

        if request.method == 'GET':
            return FileResponse(buffer, filename='Maestros.pdf', as_attachment=False)
    else:
        if request.method == 'GET':
            return Response({'Error','No hay información para poblar el pdf'},status=status.HTTP_204_NO_CONTENT)