from django.urls import path
from .views import MateriasView, CreateMateriasView, borrarM, borrarAs, CreateCarreraView, AsignarMateriaView, CarrerasView, borrarC
from .views import getGrupos,\
        updateM,\
        updateC,\
        AsignanView,\
        getAsignan,\
        getAsignanEspecific,\
        AdminGetAsignan,\
        getAsignanpk,\
        getMateriasXCarrera,\
        getAsignanCarrerapk
from .views import getAsignanCarreraNamespk, p2MateriasCarrera, p2MateriasMaestro, p2MateriasHora, p2MateriasAula, p2MateriasGrupo, p2MateriasCreditos, p2MateriasUnidades
from .views import p2MateriasCarreraPDF, p2MateriasMaestroPDF, p2MateriasHoraPDF, p2MateriasAulaPDF, p2MateriasGrupoPDF, p2MateriasCreditosPDF, p2MateriasUnidadPDF, p2AllCarrerasPDF
urlpatterns = [
    path('materias', MateriasView.as_view()),
    path('create_materia', CreateMateriasView.as_view()),
    path('create_carrera', CreateCarreraView.as_view()),
    path('asign_materia', AsignarMateriaView.as_view()),
    path('carreras', CarrerasView.as_view()),
    path('asignan', AsignanView.as_view()),
    path('delete-materia/<pk>', borrarM),
    path('delete-carrera/<pk>', borrarC),
    path('delete-asign/<int:pkM>', borrarAs),
    path('update-materia/<pk>', updateM),
    path('update-carrera/<pk>', updateC),
    path('getAsignan', getAsignan),
    path('get-asignan/<pk>', getAsignanEspecific),
    path('adminGet-asign/<pk>', AdminGetAsignan),
    path('asignan-allpk/<pk>', getAsignanpk),
    path('materiaXcarrera/<id>', getMateriasXCarrera),
    path('asignanC-allpk/<pk>',getAsignanCarrerapk),
    path('asignanCNames-allpk/<pk>',getAsignanCarreraNamespk),

    path('p2MatXC/<query>',p2MateriasCarrera),
    path('p2MatXM/<query>',p2MateriasMaestro),
    path('p2MatXH/<query>',p2MateriasHora),
    path('p2MatXA/<query>',p2MateriasAula),
    path('p2MatXG/<query>',p2MateriasGrupo),
    path('p2MatXCred/<query>',p2MateriasCreditos),
    path('p2MatXU/<query>',p2MateriasUnidades),
    path('p2MatXCPDF/<query>',p2MateriasCarreraPDF),
    path('p2MatXMPDF/<query>',p2MateriasMaestroPDF),
    path('p2MatXHPDF/<query>',p2MateriasHoraPDF),
    path('p2MatXAPDF/<query>',p2MateriasAulaPDF),
    path('p2MatXGPDF/<query>',p2MateriasGrupoPDF),
    path('p2MatXCredPDF/<query>',p2MateriasCreditosPDF),
    path('p2MatXUPDF/<query>',p2MateriasUnidadPDF),
    path('p2AllCarrerasPDF',p2AllCarrerasPDF),

    path('getGrupos/<query>', getGrupos),
]
