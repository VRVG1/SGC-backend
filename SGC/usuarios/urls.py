from django.urls import path
from .views import UsuarioView, CreateUsuarioView, borrar, actualizar, get, CambiarPass, getInfoUser, updateLoginInfo, OlvidoPass, actualizarPropiosDatos
from .views import p2MaestrosCarrera, p2MaestrosHora
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
]
