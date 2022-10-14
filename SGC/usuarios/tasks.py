from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

'''
Funcion que recibe usuario y correo para cambiar la contraseña del usuario en caso de que la haya olvidado
(DOCENTE)
'''


@shared_task(name='EmailPass')
def ForgotPass(msg, correo):
    to = [correo]
    de = settings.DEFAULT_FROM_EMAIL
    subject = 'Cambio de contraseña SGC'
    send_mail(subject, msg, de, to, fail_silently=False)
