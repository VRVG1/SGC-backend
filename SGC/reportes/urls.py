from django.urls import path, re_path
from .views import ReportesView,\
        CreateReportesView,\
        GeneranView,\
        CrearGeneran,\
        borrarReporte,\
        updateReporte,\
        CreateAlojanView,\
        alojanFromView,\
        OnlySaveReportesView,\
        EnviarGeneran,\
        GetGeneranUser
from .views import GetReporte,\
        AlojanView,\
        AdminSendMail,\
        IniciarNuevoSem,\
        borrarEntrega,\
        getResportesUnidad,\
        entregarUnidad,\
        getReportesUnidadAdmin
from .views import p2MaestrosPuntual,\
        p2MaestrosTarde,\
        p2MaestrosPuntualPDF,\
        p2MaestrosTardePDF,\
        p3ReprobacionMaestro,\
        p3ReprobacionMateria,\
        p3ReprobacionGrupo,\
        p3IndiceEntregaReportesCarrera,\
        getRegistroPNC,\
        addRegistroPNC,\
        updateRegistroPNC,\
        deleteRegistroPNC,\
        downloadRegistroPNC,\
        p3RepUXCXMaeXMatXGraXGrp,\
        getRegistroVGC,\
        addRegistroVGC,\
        updateRegistroVGC,\
        deleteRegistroVGC,\
        vgcExcel

urlpatterns = [
    path('reportes', ReportesView.as_view()),
    path('create-reporte', CreateReportesView.as_view()),
    path('generaciones', GeneranView.as_view()),
    path('alojan', AlojanView.as_view()),
    path('create-alojan', CreateAlojanView.as_view()),
    path('create-gen/<int:pk>', CrearGeneran),
    path('delete-reporte/<int:pk>', borrarReporte),
    path('update-reporte/<int:pk>', updateReporte),
    path('get-alojanFrom/<fk>', alojanFromView),
    path('save-reporte', OnlySaveReportesView.as_view()),
    path('send-genera/<pk>', EnviarGeneran),
    path('get-generan', GetGeneranUser),
    path('get-reporte/<pk>', GetReporte),
    path('admin-mail', AdminSendMail),
    path('startNew', IniciarNuevoSem),
    path('delete-Alojan/<pk>', borrarEntrega),
    path('getRUnidades/<pk>',getResportesUnidad),
    path('entregaUnidad/<pk>',entregarUnidad),
    path('getRUnidadesAdmin',getReportesUnidadAdmin),
    
    path('p2MaeXPunt/<query>',p2MaestrosPuntual),
    path('p2MaeXTard/<query>',p2MaestrosTarde),
    path('p2MaeXPuntPDF/<query>',p2MaestrosPuntualPDF),
    path('p2MaeXTardPDF/<query>',p2MaestrosTardePDF),

    # end-points Estadisticas
    path('p3IndXMae/<query>', p3ReprobacionMaestro),
    path('p3IndXMat/<query>', p3ReprobacionMateria),
    path('p3IndXGrp/<query>', p3ReprobacionGrupo),
    re_path(
        r"^p3IndEntRepoXC/(?:Nombre_Reporte=(?P<nombre_reporte>[a-zA-Z0-9ñáéíóú\s]{0,480})&Nombre_Carrera=(?P<nombre_carrera>[a-zA-Zñáéíóú\s]{0,80}))$",
        p3IndiceEntregaReportesCarrera),

    # end-points Productos No Conformes
    path('getPNC', getRegistroPNC),
    path('addPNC', addRegistroPNC),
    path('updatePNC', updateRegistroPNC),
    path('deletePNC', deleteRegistroPNC),
    path('PncPDF', downloadRegistroPNC),

    # end-points Verificacion de Gestion del Curso
    re_path(r"^p3RepUXCXMaeXMatXGraXGrp/(?:ID_Carrera=(?P<id_carrera>[a-zA-Záéíóúñ]{,8})&Nombre_Maestro=(?P<nombre_maestro>[a-zA-Z_0-9ñáéíóú\s]{1,70})&ID_Materia=(?P<id_materia>[0-9]+)&Grado=(?P<grado>[0-9]{1,2})&Grupo=(?P<grupo>[A-Z]{1}))$",
            p3RepUXCXMaeXMatXGraXGrp),
    re_path(r"^getVGC/(?:ID_Carrera=(?P<id_carrera>[a-zA-Záéíóúñ]{,8})&Seguimiento_No=(?P<seguimiento_no>[1-9]+[0-9]*)&Semana=(?P<semana>4|8|12|16))$",
            getRegistroVGC),
    re_path(r"^addVGC/(?:ID_Carrera=(?P<id_carrera>[a-zA-Záéíóúñ]{,8})&Seguimiento_No=(?P<seguimiento_no>[1-9]+[0-9]*)&Semana=(?P<semana>4|8|12|16))$",
            addRegistroVGC),
    re_path(r"^updateVGC/(?:ID_Carrera=(?P<id_carrera>[a-zA-Záéíóúñ]{,8})&Seguimiento_No=(?P<seguimiento_no>[1-9]+[0-9]*)&Semana=(?P<semana>4|8|12|16))$",
            updateRegistroVGC),
    re_path(r"^deleteVGC/(?:ID_Carrera=(?P<id_carrera>[a-zA-Záéíóúñ]{,8})&Seguimiento_No=(?P<seguimiento_no>[1-9]+[0-9]*)&Semana=(?P<semana>4|8|12|16))$",
            deleteRegistroVGC),
    re_path(r"^VGC-Excel/(?:ID_Carrera=(?P<id_carrera>[a-zA-Záéíóúñ]{,8})&Seguimiento_No=(?P<seguimiento_no>[1-9]+[0-9]*)&Semana=(?P<semana>4|8|12|16))$",
            vgcExcel),
]
