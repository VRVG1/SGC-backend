from django.http import HttpResponse
from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from persoAuth.permissions import AdminEspectadorPermission
from reportes.models import Generan
from .InformeReportes import InformeReportes

from wsgiref.util import FileWrapper

import os


class MakeDatasheet(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    Permission_classes = [IsAuthenticated, AdminEspectadorPermission]

    def get(self, request, format=None):

        export_path = './var/exportar/'
        filename = 'Informe_de_entrega_de_reportes_del_SGC.xlsx'

        print(f'\n\n\n{os.getcwd()}\n\n\n')

        try:
            os.makedirs(export_path)
            print('Se crearon los directorios ./var/ y ./var/respaldo/')
        except FileExistsError:
            print('Ya existen los directorios')

        # workbook = xlsxwriter.Workbook(export_path + filename)

        db_fields = ['ID_Asignan__ID_Usuario__Nombre_Usuario',
                     'ID_Asignan__ID_Materia__Nombre_Materia',
                     'ID_Asignan__Grado',
                     'ID_Asignan__Grupo',
                     'ID_Reporte__Nombre_Reporte',
                     'Estatus',
                     'ID_Reporte__Fecha_Entrega']

        data_to_export = Generan.objects.values(db_fields[0],  # Nombre_Usuario
                                                db_fields[1],  # Nombre_Materia
                                                db_fields[2],  # Grado
                                                db_fields[3],  # Grupo
                                                db_fields[4],  # Nombre_Reporte
                                                db_fields[5],  # Estatus
                                                db_fields[6])  # Fecha_Entrega

        informe = InformeReportes(export_path, filename)
        last_username = ''
        for query in data_to_export:
            row_data = []
            username = query[db_fields[0]]
            if username != last_username:
                informe.newWorksheet(username)

            for field in db_fields[1:]:
                # field_name = field.split('__')[-1]
                row_data.append(query[field])
            informe.addRow(row_data)
            last_username = username
        informe.closeWorkbook()

        excel_file_MiME_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        with open(export_path + filename, 'rb') as excel_file:
            response = HttpResponse(FileWrapper(excel_file),
                                    content_type=excel_file_MiME_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            print('Enviando hoja de datos...')
            return response
