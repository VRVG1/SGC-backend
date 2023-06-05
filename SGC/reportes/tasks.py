from datetime import date
from celery import shared_task
from django.core import mail
from django.conf import settings
from .models import Generan, Reportes
from usuarios.models import Usuarios
from .mimes import _buildMIME, _buildMemorandumMIME

# SE USARÀ DESPUES PARA TAREAS EN LAS QUE SE TENGA QUE VERIFICAR EL TIEMPO
# RESTANTE DE ENTREGA DE REPORTES


# NOTE: No es periodico, es por petición Celery -> Worker
@shared_task(name='EnviarmsgR')
def sendMensaje(msg, general, usuario):
    u"""Envía un mensaje vía correo.

    msg -- El cuerpo del mensaje a envíar
    general -- Bandera que indica si el correo será enviado a todos los
               usuarios o a un solo individuo
    usuario -- Tupla que contiene los datos del usuario, debe ser None en caso
               de que general sea True. En caso de que general sea False, la
               tupla contendrá los datos:
                   (Nombre_Usuario, CorreoE)
    """
    print('Preparando el envio de correo...')
    messages = []
    de = settings.DEFAULT_FROM_EMAIL
    subject = 'Mensaje Importante SGC'

    if general:
        print('Enviando mensaje general')
        usuarios = Usuarios.objects.all()
        for i in usuarios:
            messages.append(_buildMIME(mail_from=de,
                                       mail_to=i.CorreoE,
                                       subject=subject,
                                       nombre_usuario=i.Nombre_Usuario,
                                       msg=msg))
    else:
        print('Enviando mensaje individual')
        messages.append(_buildMIME(mail_from=de,
                                   mail_to=usuario[1],
                                   subject=subject,
                                   nombre_usuario=usuario[0],
                                   msg=msg))

    if len(messages) != 0:
        connection = mail.get_connection()
        connection.open()
        connection.send_messages(messages)
        connection.close()


# NOTE: Es el unico proceso que funciona con Celery -> beat
@shared_task(name='tareaconjunta')
def tareaconjunta():
    u"""Envía de forma automatizada memorandums a los correos de aquellos
    profesores que no hayan entregado algun reporte obligatorio.
    """
    MESES = [
        'enero',
        'febrero',
        'marzo',
        'abril',
        'mayo',
        'junio',
        'julio',
        'agosto',
        'septiembre',
        'octubre',
        'noviembre',
        'diciembre'
    ]
    print('recibido')
    mail_from = settings.DEFAULT_FROM_EMAIL
    hoy = date.today()
    plazo = hoy.replace(day=hoy.day + 8)  # Se les da un plazo de una semana

    # Se abre la conexión con el SMTP desde antes de empezar a buscar los
    # usuarios, esto debido a que el completar la conexión es un proceso
    # lento y tardado.
    print('Abriendo conexión con SMTP mail...')
    connection = mail.get_connection()
    connection.open()
    print('Conexión con SMTP establecida.')
    for reporte in Reportes.objects.filter(Opcional=False, Unidad=False):
        nombre_reporte = reporte.Nombre_Reporte
        print(f"Nombre Reporte: {nombre_reporte}")
        carreras = set()
        messages = []
        fecha_entrega = reporte.Fecha_Entrega
        # Dado que la fecha de entrega limite para el reporte todavía no
        # se vence se omite.
        print(f"Fecha hoy: {hoy} Fecha Entrega: {fecha_entrega} mayor a: {fecha_entrega > hoy}")
        if fecha_entrega > hoy:
            continue
        print("Inicia proceso de construcción de memorandums...")
        # En cambio, si la fecha esta vencida, se busca a aquellos usuarios
        # que sean 'Docentes'
        for usuario in Usuarios.objects.filter(Tipo_Usuario='Docente'):
            # Teniendo el reporte y el usuario, se obtiene aquellas
            # generaciones relacionados a ellos.
            generacion = Generan.objects.filter(ID_Asignan__ID_Usuario=usuario,
                                                ID_Reporte=reporte)
            # si existen, significa que el usuario ya a entregado dichos
            # reportes, en cambio, si no existe...
            if len(generacion) == 0:
                generan_user = Generan.objects.filter(ID_Asignan__ID_Usuario=usuario)
                for generan in generan_user:
                    carrera = generan.ID_Asignan.ID_Materia.Carrera.Nombre_Carrera
                    carreras.add(carrera)

                nombre_carrera = list(carreras)[0]
                # Se obtiene el nombre y el correo del usuario para llenar
                # los datos del cuerpo del correo
                nombre_usuario = usuario.Nombre_Usuario
                mail_to = usuario.CorreoE
                subject = f'Recordatorio de entrega del reporte "{nombre_reporte}"!'
                recordatorio = f"""\
Por este medio me dirijo a Usted para saludarlo y a la vez recordarle que por \
la forma en que se ha venido trabajando en este ciclo escolar, es de vital \
importancia el envío del reporte '{nombre_reporte}' en el sistema SGC, que a \
la fecha Usted no ha cumplido con esta actividad, dado que se debe tener \
entregado dicho reporte y su información correspondiente desde el día \
'{fecha_entrega}'.\
\n
Motivo por el cual solicito de su valioso apoyo para que sea atendida esta \
necesidad a más tardar el día {plazo.day} de {MESES[plazo.month - 1]} del \
{plazo.year}.
\n
Sin más por el momento y esperando una respuesta favorable de su parte, quedo \
de Usted.
"""

                messages.append(_buildMemorandumMIME(mail_from=mail_from,
                                                     mail_to=mail_to,
                                                     subject=subject,
                                                     fecha_hoy=hoy,
                                                     nombre_usuario=nombre_usuario.upper(),
                                                     nombre_carrera=nombre_carrera.upper(),
                                                     msg=recordatorio))

        # Una vez que se obtuvieron todos los usuarios que van atrasados en
        # la entrega, se procede a envíar el correo
        connection.send_messages(messages)
    # Una vez el ciclo termina se cierra el enlace con el SMTP
    connection.close()
    print('Conexión con SMTP cerrada.')


@shared_task(name='EnviarmsgGrupo')
def sendGroupMail(msg, users_info):
    u"""Envia un mensaje vía correo a todos los usuarios de un grupo de
    correos.

    msg -- Cuerpo del mensaje a envíar.
    users_info -- Lista de tuplas que contendrán el nombre del usuario y su
                  correo.
    """
    print('Enviando correos para grupos')
    messages = []
    for user in users_info:
        nombre_usuario = user[0]    # [0] nombre usuario
        correo = user[1]            # [1] mensaje

        mail_from = settings.DEFAULT_FROM_EMAIL
        mail_to = correo
        subject = f'Saludos {nombre_usuario}!'

        messages.append(_buildMIME(mail_from=mail_from,
                                   mail_to=mail_to,
                                   subject=subject,
                                   nombre_usuario=nombre_usuario,
                                   msg=msg))

    connection = mail.get_connection()
    connection.open()
    connection.send_messages(messages)
    connection.close()
