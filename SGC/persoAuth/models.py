from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.db import transaction


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    print('\n\nCREATE_AUTH_TOKE')
    if created:
        print('Creando token\n')
        try:
            with transaction.atomic():
                Token.objects.create(user=instance)
            print('Token creado\n')
        except Exception:
            print('Excepcion tratando de crear el token\n')

# Create your models here.
