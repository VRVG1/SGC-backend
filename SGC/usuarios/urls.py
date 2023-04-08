from django.urls import path
from .views import UsuarioView, CreateUsuarioView, borrar, actualizar, get, CambiarPass, getInfoUser, updateLoginInfo, OlvidoPass, actualizarPropiosDatos
from .views import p2MaestrosCarrera, p2MaestrosHora, p2MaestrosIndiceAlto, p2MaestrosIndiceBajo
from .views import p2MaestrosCarreraPDF, p2MaestrosHoraPDF, p2MaestrosIndiceAltoPDF, p2MaestrosIndiceBajoPDF, p2AllMaestrosPDF
urlpatterns = [
    path('users', UsuarioView.as_view()),
    path('create_user', CreateUsuarioView.as_view()),
    path('change_pass/', CambiarPass.as_view()),
    path('delete-user/<pk>', borrar),
    path('update-user/<pk>', actualizar),
    path('user/<string>', get),
    path('getInfo', getInfoUser),
    path('update-login/<pk>', updateLoginInfo),
    path('forgotPass', OlvidoPass),
    path('update-Ownuser/<pk>', actualizarPropiosDatos),

    path('p2MaeXC/<query>',p2MaestrosCarrera),
    path('p2MaeXH/<query>',p2MaestrosHora),
    path('p2MaeXIA',p2MaestrosIndiceAlto),
    path('p2MaeXIB',p2MaestrosIndiceBajo),
    path('p2MaeXCPDF/<query>',p2MaestrosCarreraPDF),
    path('p2MaeXHPDF/<query>',p2MaestrosHoraPDF),
    path('p2MaeXIAPDF',p2MaestrosIndiceAltoPDF),
    path('p2MaeXIBPDF',p2MaestrosIndiceBajoPDF),
    path('p2AllMaePDF',p2AllMaestrosPDF),
]
