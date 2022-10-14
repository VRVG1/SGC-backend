from django import forms
from .validators import isZipFile


class UploadFileForm(forms.Form):
    restorefile = forms.FileField(validators=[isZipFile])
