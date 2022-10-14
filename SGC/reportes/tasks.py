from datetime import date
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Generan, Reportes
from usuarios.models import Usuarios

# SE USARÀ DESPUES PARA TAREAS EN LAS QUE SE TENGA QUE VERIFICAR EL TIEMPO RESTANTE DE ENTREGA DE REPORTES


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


@shared_task(name='tareaconjunta')
def tareaconjunta():
    print('recibido')
    generan = Generan.objects.all()
    reportes = Reportes.objects.filter(Opcional=False)
    hoy = date.today()
    From = settings.DEFAULT_FROM_EMAIL
    users = []
    for i in generan:
        if i.Estatus:
            pass
        else:
            users.append(i.ID_Asignan.ID_Usuario.CorreoE)

    for t in users:
        for i in reportes:
            print('Mensaje para: '+t+' Por el reporte: '+i.Nombre_Reporte +
                  ' Con fecha: '+str(i.Fecha_Entrega))
            diferencia = i.Fecha_Entrega.day - hoy.day
            if diferencia <= 5:
                subject = 'Mensaje de recordatorio SGC: '+i.Nombre_Reporte
                message = 'Se le recuerda que solo quedan '+str(diferencia)+' dia(s) para realizar la entrega del reporte: '+i.Nombre_Reporte+' cuya fecha limite de entrega es el dia: '+str(i.Fecha_Entrega) + \
                    '.\n\nSe recomienda atender a las indicaciones solicitadas y entregar lo antes posible.\n\nSi ya realizó la entrega del reporte: ' + \
                    i.Nombre_Reporte+' haga caso omiso de este mensaje.'
                send_mail(subject, message, From, [t], fail_silently=False)
