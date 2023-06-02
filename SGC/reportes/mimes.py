from django.core.mail import EmailMessage
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart


def _buildMIME(mail_from, mail_to, subject, nombre_usuario, msg):
    u"""Construye una instancia de la clase EmailMessage la cual contiene la
    estructura estandar de correo del SGC en formato type/html.
    """
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
      Este correo fue envíado de forma automatizada, favor de no responder este mensaje.
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
    msgRoot.preamble = "Correo de la administración del SGC"
    alternativo = f"""
Estimado {nombre_usuario}.

{msg}



Este correo fue enviado de forma automatizada, favor de no responder este \
mensaje.
"""

    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    msgText = MIMEText(alternativo)
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


def _buildMemorandumMIME(mail_from,
                         mail_to,
                         subject,
                         fecha_hoy,
                         nombre_usuario,
                         nombre_carrera,
                         msg):
    u""" Construye una instancia de la clase EmailMessage la cual contiene la
    estructura estandar de un memorandum del SGC en formato type/html.
    """
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
        Este correo fue envíado de forma automatizada, favor de no responder este mensaje.
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
