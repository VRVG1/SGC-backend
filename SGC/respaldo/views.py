from django.http import HttpResponse
from django.core.management import call_command
from django.core.exceptions import ValidationError
from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from persoAuth.permissions import OnlyAdminPermission
from .forms import UploadFileForm
from .uploadHandler import handleUploadFile
from .utils import removeMediaFiles, removeDBData

from wsgiref.util import FileWrapper
from zipfile import ZipFile
from pathlib import Path

import os

backup_filename = 'BackupSGC.zip'


class MakeBackup(generics.ListAPIView):
    '''
    Vista que crea el backup tanto de la base de datos como de los archivos
    media.
    (ADMIN)
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, OnlyAdminPermission]

    def get(self, request, format=None):

        print(f'\n\n\n{os.getcwd()}\n\n\n')
        try:
            os.mkdir('./media')
            print('Se creo el directorio media/')
        except FileExistsError:
            print('Ya existe el directorio media.')
        except FileNotFoundError as e:
            raise e

        try:
            os.makedirs('./var/respaldo')
            print('Se crearon los directorios var/ y var/respaldo/')
        except FileExistsError:
            print('Ya existen los directorios var/ y var/respaldo/')

        try:
            os.mkdir('./static')
            print('Se creo el directorio static/')
        except FileExistsError:
            print('Ya existe el directorio static/')

        try:
            os.mkdir('./var/backups')
            print('Se creo el directorio var/backups/')
        except FileExistsError:
            print('Ya existe el directorio var/backups/')
        except FileNotFoundError as e:
            raise e
        print('Creando respaldo de la base de datos...')

        # Estructura del comando ejecutado
        # dumpdata --output ./var/backups/backup_notokens.json --verbosity 3 -e authtoken.token
        call_command('dumpdata',
                     format='json',
                     output='./var/backups/backup.json',
                     # verbosity='3',
                     # exclude=['authtoken.token']
                     )

        print('Respaldo de la base de datos realizado con exito.')
        print('Creando respaldo de los archivos media...')
        call_command('mediabackup', clean=True)
        print('Respaldo de los archivos media realizado con exito.')

        print('Comprimiendo archivos de respaldo...')

        with ZipFile(f'./var/respaldo/{backup_filename}', 'w') as backup_zip:
            with Path('./var/backups/') as backup_path:
                print('Respaldando los archivos en "var/backups/"...')
                for file in backup_path.iterdir():
                    if file.is_file():
                        backup_zip.write(file.__str__(), arcname=file.name)
            print('Respaldo de los archivos en "var/backups/" realizado con exito')

            # TODO: Crear un folder 'static' dentro de 'backup_zip' y guardar
            #       en el todos los archivos del directorio './static/'
            with Path('./static/') as static_files_path:
                print('Respaldando los archivos en "static/"...')
                for file in static_files_path.iterdir():
                    if file.is_file():
                        backup_zip.write(file.__str__(), arcname=file.name)
            print('Respaldo de los archivos en "static/" realizado con exito')

            print('Archivos de respaldo comprimidos con exito.')

        with open(f'./var/respaldo/{backup_filename}', 'rb') as backup_zip:
            response = HttpResponse(FileWrapper(backup_zip),
                                    content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{backup_filename}"'
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            print('Enviando archivo de respaldo...')
            return response


class RestoreData(generics.ListAPIView):
    '''
    Vista que permite restaurar la base de datos junto con sus archivos de
    media.
    (ADMIN)
    '''

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, OnlyAdminPermission]

    def post(self, request, format=None):
        print(f'\n\n{os.getcwd()}\n\n')
        form = UploadFileForm(request.POST, request.FILES)
        restore_path = './var/restauracion/'

        # Se limpia el directorio de restauración, esto para evitar la
        # acumulación de multiples archivos en este.
        if Path(restore_path).exists():
            with Path(restore_path) as to_remove_path:
                for file in to_remove_path.iterdir():
                    if file.is_file():
                        os.remove(file)

        try:
            os.mkdir(restore_path)
            print(f'Se creo el directorio {restore_path}')
        except FileExistsError:
            print(f'Ya existe el directorio {restore_path}')
        except FileNotFoundError as e:
            raise e

        if form.is_valid():
            valid_file = False
            namefiles = ''
            print('Cargando archivo de respaldo...')
            handleUploadFile(request.FILES['restorefile'])
            print('Archivo de respaldo cargado.')
            print('Verificando estructura del archivo de respaldo...')
            with ZipFile(restore_path + backup_filename) as restore_zip:
                # En caso de que los formatos de archivos del backup cambien,
                # modifica alguno de estos elementos
                file_types = ['tar', 'json']  # [0] mediabackup, [1] dbbackup
                has_mediabackup_file = False
                has_dbbackup_file = False
                namefiles = restore_zip.namelist()
                if 0 < len(namefiles) <= 2:
                    for namefile in namefiles:
                        file_type = namefile.split('.')
                        if file_type[1] == file_types[0]:  # tar
                            has_mediabackup_file = True
                        elif file_type[1] == file_types[1]:  # json
                            has_dbbackup_file = True

                    if not (has_mediabackup_file and has_dbbackup_file):
                        response = HttpResponse('Archivo no cumple con los requisitos',
                                                content_type="text/plain",
                                                status=406)
                    else:
                        # Elimina los datos en el directorio media.
                        removeMediaFiles()
                        # Elimina los datos de la base de datos con flush
                        removeDBData(True)
                        valid_file = True
                        restore_zip.extractall(path=restore_path)
                        for namefile in namefiles:
                            file_type = namefile.split('.')
                            if file_type[1] == file_types[0]:  # tar
                                print('Restaurando archivos media...')
                                call_command('mediarestore',
                                             '--noinput',
                                             input_path=restore_path+namefile
                                             )
                                print('Archivos media restaurados.')
                            elif file_type[1] == file_types[1]:  # json
                                print('Restaurando base de datos...')
                                call_command('loaddata',
                                             restore_path+namefile,
                                             format='json')
                                # call_command('dbrestore',
                                #              '--noinput',
                                #              input_path=restore_path+namefile
                                #              )
                                print('Base de datos restaurada.')

                else:
                    response = HttpResponse('Archivo de restauración vacio',
                                            content_type="text/plain",
                                            status=406)

            if valid_file:
                response = HttpResponse('Restauración exitosa',
                                        content_type="text/plain",
                                        status=200)
        else:
            error_msg = 'Error al subir el archivo'
            form_errors = form.errors.as_data()
            if len(form_errors) > 0:
                error_msg = ''
                for error in form_errors['restorefile']:
                    try:
                        raise error
                    except ValidationError as e:
                        error_msg = error_msg + e.message + '\n'

            response = HttpResponse(error_msg,
                                    content_type="text/plain",
                                    status=408)
        return response
