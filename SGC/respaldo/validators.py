import os
from django.core.exceptions import ValidationError


def isZipFile(value):
    ext = os.path.splitext(value.name)[1]
    if not ext.lower() == '.zip':
        raise ValidationError('Extensión de archivo no valida')
