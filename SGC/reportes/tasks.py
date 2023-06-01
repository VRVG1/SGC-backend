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


# NOTE: Es el unico proceso que funciona con Celery -> beat
@shared_task(name='tareaconjunta')
def tareaconjunta():
    print('recibido')
    # TODO: Tomar todos los generan que son de reportes cuya Unidad = False
    # TODO: Tomar todos los que generan que son de reportes cuya
    #       Opcional = False

    generan = Generan.objects.filter(ID_Reporte__Unidad=False,
                                     ID_Reporte__Opcional=False)

    # generan = Generan.objects.all()
    reportes = Reportes.objects.filter(Opcional=False)  # <-- Cambiar

    hoy = date.today()
    From = settings.DEFAULT_FROM_EMAIL
    users = []
    for reporte in generan:
        if reporte.Estatus:
            pass
        else:
            users.append(reporte.ID_Asignan.ID_Usuario.CorreoE)

    for usuario in users:
        for reporte in reportes:
            print('Mensaje para: {} Por el reporte: {} Con fecha: {}'.
                  format(usuario,
                         reporte.Nombre_Reporte,
                         str(reporte.Fecha_Entrega)))
            diferencia = reporte.Fecha_Entrega.day - hoy.day
            if diferencia <= 5:
                subject = 'Mensaje de recordatorio SGC: {}'.format(reporte.Nombre_Reporte)
                message = f'''\
Se le recuerda que solo quedan {str(diferencia)} dia(s) para realizar la\
 entrega del reporte: {reporte.Nombre_Reporte} cuya fecha limite de entrega\
 es el dia: {str(reporte.Fecha_Entrega)}.\
 \n\nSe recomienda atender a las indicaciones solicitadas y entregar lo antes\
 posible.\
 \n\nSi ya realizó la entrega del reporte: {reporte.Nombre_Reporte} haga caso
 omiso de este mensaje.
 '''
                send_mail(subject,
                          message,
                          From,
                          [usuario],
                          fail_silently=False)


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


# @shared_task(name='EnviarmsgGrupo')
def sendGroupMail(msg, users_info):
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
