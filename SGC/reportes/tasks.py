from datetime import date
from celery import shared_task
from django.core import mail
from django.core.mail import send_mail, EmailMessage
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from .models import Generan, Reportes
from usuarios.models import Usuarios

# SE USARÀ DESPUES PARA TAREAS EN LAS QUE SE TENGA QUE VERIFICAR EL TIEMPO RESTANTE DE ENTREGA DE REPORTES


# NOTE: No es periodico, es por petición Celery -> Worker
@shared_task(name='EnviarmsgR')
def sendMensaje(msg, general, correo):

    de = settings.DEFAULT_FROM_EMAIL
    subject = 'Mensaje Importante SGC'

    if general:
        usuarios = Usuarios.objects.all()
        to = []
        for i in usuarios:
            to.append(i.CorreoE)

        for i in to:
            send_mail(subject, msg, de, [i], fail_silently=False)
    else:
        to = [correo]
        send_mail(subject, msg, de, to, fail_silently=False)

    foo()


def foo():
    print("\n\n\nHoal este es foo function")


# NOTE: Es el unico proceso que funciona con Celery -> beat
@shared_task(name='tareaconjunta')
def tareaconjunta():
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
    connection = mail.get_connection()
    connection.open()
    for reporte in Reportes.objects.filter(Opcional=False, Unidad=False):
        carreras = set()
        messages = []
        fecha_entrega = reporte.Fecha_Entrega
        # Dado que la fecha de entrega limite para el reporte todavía no
        # se vence se omite.
        if hoy > fecha_entrega:
            continue
        nombre_reporte = reporte.Nombre_Reporte
        print(f"Nombre Reporte: {nombre_reporte}")

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
                subject = f'Saludos {nombre_usuario}!'
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


def sendTestMail():
    mail_from = settings.DEFAULT_FROM_EMAIL
    mail_to = ''  # Add here the mail address where you want send test mails
    subject = 'Correo enviado via Django!'

    mensaje = """
Se precisa que envíe un mensaje a la dirección de cordinación del curso antes
 del día 24/junio/2023.
\n
Atte. Ordep Soir.
    """

    mail_2_send = _buildMIME(mail_from=mail_from,
                             mail_to=mail_to,
                             subject=subject,
                             nombre_usuario='Pedro Rios',
                             msg=mensaje)
    mail_2_send.send()


@shared_task(name='EnviarmsgGrupo')
def sendGroupMail(msg, users_info):
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


def _buildMemorandumMIME(mail_from,
                         mail_to,
                         subject,
                         fecha_hoy,
                         nombre_usuario,
                         nombre_carrera,
                         msg):
    msg = msg.replace('\n', '<br>')
    mes_format = f"0{fecha_hoy.month}" if fecha_hoy.month < 10 else fecha_hoy.month
    fecha_format = f'{fecha_hoy.day}/{mes_format}/{fecha_hoy.year}'
    mensaje = f"""
<div style='font-size: 62.5%; width: 100%;'>
  <table style='border-spacing:0; border: none; margin: 0; width: 100%; background-color: rgb(0, 58, 101);'>
    <tr>
      <td style='border-spacing: 0; border: none; width: 15%; height: 5em;'></td>
    </tr>
    <tr>
      <td style='border-spacing: 0; border: none; width: 15%;'></td>
      <td colspan="3" style='color: rgb(0, 0, 0); border-spacing: 0; border: none; font-size: 2em; text-align: center; width: 23.3%; background-color: rgb(243, 243, 243);'>
        <strong>MEMORÁNDUM</strong>
      </td>
      <td style='border-spacing: 0; border: none; width: 15%;'></td>
    </tr>
    <tr>
      <td style='border-spacing: 0; border: none; width: 15%; height: 1em;'></td>
      <td style='border-spacing: 0; border: none; width: 23.3%; background-color: rgb(243, 243, 243); vertical-align: bottom; text-align: left;'>
      </td>
      <td style='border-spacing: 0; border: none; font-size: 1.5em; text-align: center; width: 23.3%; background-color: rgb(243, 243, 243);'>
      </td>
      <td style='border-spacing: 0; border: none; width: 23.3%; background-color: rgb(243, 243, 243); vertical-align: bottom; text-align: right;'>
      </td>
      <td style='border-spacing: 0; border: none; width: 15%;'></td>
    </tr>
    <tr>
      <td style='border-spacing: 0; border: none; width: 15%; height: 1em;'></td>
      <td colspan="3" style='color: rgb(0, 0, 0); border-spacing: 0; border: none; background-color: rgb(243, 243, 243); vertical-align: bottom; text-align: right; font-size: 1.5em;'>
        <div style='padding-right: 5em;'>
          Cd. Guzmán, Jal. A <span style='background-color: rgb(0, 0, 0); color: rgb(243, 243, 243);'> {fecha_format}</span>
        </div>
      </td>
      <td style='border-spacing: 0; border: none; width: 15%;'></td>
    </tr>
    <tr>
      <td style='border-spacing: 0; border: none; width: 15%;'></td>
      <td colspan="3" style='border-spacing: 0; border: none; background-color: rgb(243, 243, 243);'>
        <div style='color: rgb(0, 0, 0); padding: 5em 5em 2em 5em; font-size: 1.5em; text-align: justify;'>
          <strong style='color: rgb(0, 0, 0);'>
            {nombre_usuario}
          </strong>
          <br>
          <strong style='color: rgb(0, 0, 0);'>
            DOCENTE DE LA CARRERA {nombre_carrera}
          </strong>
          <br>
          <strong style='color: rgb(0, 0, 0);'>
            P R E S E N T E:
          </strong>
          <br>
          <br>
          {msg}
          <br>
          <br>
          <strong style='color: rgb(0, 0, 0);'>
            A T E N T A M E N T E
          </strong>
          <br>
          <i style='color: rgb(98, 98, 98)'>Innova, Transforma y Crea para ser Grande</i>
          <br>
          <br>
          <br>
          <br>
          <strong style='color: rgb(0, 0, 0);'>
            DRA. ROSA MARÍA MICHEL NAVA
          </strong>
          <br>
          <strong style='color: rgb(0, 0, 0);'>
            JEFA DE PROYECTOS DE DOCENCIA
          </strong>
        </div>
      </td>
      <td style='border-spacing: 0; border: none; width: 15%;'></td>
    </tr>
    <tr>
      <td style='border-spacing: 0; border: none; width: 15%; height: 2em;'></td>
      <td colspan="3" style='color: rgb(255, 255, 255); font-size: 1em; border-spacing: 0; border: none; height: 2em;'>
        <br>
        Este correo fue envíado de forma automatica, favor de no responder este mensaje.
        <br>
        <br>
        <br>
      </td>
      <td style='border-spacing: 0; border: none; width: 15%; height: 2em;'></td>
    </tr>
  </table>
</div>
"""
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = subject
    msgRoot['From'] = mail_from
    msgRoot['To'] = mail_to
    msgRoot.preamble = f"Recordatorio de entrega del reporte de seguimiento del curso"
    alternativo = f"""
MEMORANDUM


Cd. Guzmán Jal. A {fecha_format}


{nombre_usuario}
DOCENTE DE LA CARRERA '{nombre_carrera}'
P R E S E N T E:



{msg}



A T E N T A M E N T E:
Innova, Transforma y Crea para ser Grande



DRA. ROSA MARÍA MICHEL NAVA
JEFA DE PROYECTOS DE DOCENCIA



"""

    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    msgText = MIMEText(alternativo)
    msgAlternative.attach(msgText)

    msgText = MIMEText(_text=mensaje, _subtype='html')
    msgAlternative.attach(msgText)

    mail_2_send = EmailMessage(subject=subject,
                               body="",
                               from_email=mail_from,
                               to=[mail_to],
                               attachments=[msgRoot])

    return mail_2_send


def _buildMIME(mail_from, mail_to, subject, nombre_usuario, msg):
    msg = msg.replace('\n', '<br>')
    mensaje = f"""
<div style='font-size: 62.5%; width: 100%;'>
<table style='border-spacing:0; border: none; margin: 0; width: 100%; background-color: rgb(0, 58, 101);'>
  <tr>
    <td style='border-spacing: 0; border: none; width: 15%; height: 5em;'></td>
  </tr>
  <tr>
    <td style='border-spacing: 0; border: none; width: 15%;'></td>
    <td colspan='3' style='border-spacing: 0; border: none; height: 1.5em; background-color: rgb(243, 243, 243);'></td>
  </tr>
  <tr>
    <td style='border-spacing: 0; border: none; width: 15%;'></td>
    <td style='border-spacing: 0; border: none; width: 28.3%; background-color: rgb(243, 243, 243); vertical-align: bottom; text-align: left;'>
      <img
          style='padding-left: 3.5em; width: 35%'
          src='cid:itcg_logo'
          alt='Logotipo del itcg'
      />
    </td>
    <td style='border-spacing: 0; border: none; width: 13.3%; background-color: rgb(243, 243, 243);'>
    </td>
    <td style='border-spacing: 0; border: none; width: 28.3%; background-color: rgb(243, 243, 243); vertical-align: bottom; text-align: right;'>
      <img
          style='padding-right: 3.5em; width: 90%'
          src='cid:tecnm_logo'
          alt='Logotipo del tecnm'
      />
      </td>
    <td style='border-spacing: 0; border: none; width: 15%;'></td>
  </tr>
  <tr>
    <td style='border-spacing: 0; border: none; width: 15%;'></td>
    <td colspan="3" style='border-spacing: 0; border: none; background-color: rgb(243, 243, 243);'>
      <div style='color: rgb(0, 0, 0); padding: 0 5em; font-size: 2em; text-align: justify;'>
        <h1 style='padding: 0.5em 0; text-align: center;'>Correo de la Administración del SGC</h1>
        <strong>
          Estimado {nombre_usuario}.
        </strong>
        <br>
        <br>
        {msg}
        <br>
        <br>
      </div>
    </td>
    <td style='border-spacing: 0; border: none; width: 15%;'></td>
  </tr>
  <tr>
    <td style='border-spacing: 0; border: none; width: 15%; height: 2em;'></td>
    <td colspan="3" style='color: rgb(255, 255, 255); font-size: 1.5em; border-spacing: 0; border: none; height: 2em;'>
      <br>
      Este correo fue envíado de forma automatica, favor de no responder este mensaje.
      <br>
      <br>
      <br>
    </td>
    <td style='border-spacing: 0; border: none; width: 15%; height: 2em;'></td>
  </tr>
</table>
  <div style='width: 100%; display: flex; justify-content: space-between;'>
    <!--
    <img
        src='cid:itcg_logo'
        alt='Logotipo del itcg'
    />
    <img
        src='cid:tecnm_logo'
        alt='Logotipo del tecnm'
    />
    -->
  </div>
</div>

"""

    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = subject
    msgRoot['From'] = mail_from
    msgRoot['To'] = mail_to
    msgRoot.preamble = "Esto es una prueba de un mensaje multiparte en formato MIME"

    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    msgText = MIMEText("Esto es un texto plano alternativo")
    msgAlternative.attach(msgText)

    msgText = MIMEText(_text=mensaje, _subtype='html')
    msgAlternative.attach(msgText)

    with open('./static/itcg.png', 'rb') as itcg_logo:
        msgImage = MIMEImage(itcg_logo.read())

    msgImage.add_header(_name='Content-ID', _value='<itcg_logo>')
    msgRoot.attach(msgImage)

    with open('./static/tecnm.png', 'rb') as tecnm_logo:
        msgImage = MIMEImage(tecnm_logo.read())

    msgImage.add_header(_name='Content-ID', _value='<tecnm_logo>')
    msgRoot.attach(msgImage)

    mail_2_send = EmailMessage(subject=subject,
                               body="",
                               from_email=mail_from,
                               to=[mail_to],
                               attachments=[msgRoot])

    return mail_2_send
