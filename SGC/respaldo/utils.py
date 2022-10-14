from pathlib import Path
from shutil import rmtree
from django.core.management import call_command

import os


def removeMediaFiles():
    """
    Funcion encargada de eliminar el contenido dentro del directorio media.
    """
    media_path = Path('./media/')
    if media_path.exists():
        print(f'Eliminando contenido del directorio {media_path}...')
        with media_path:
            for file in media_path.iterdir():
                print(f'Eliminando {file}...')
                if file.is_file():
                    os.remove(file)
                    print(f'{file} Eliminado.')
                elif file.is_dir():
                    try:
                        rmtree(file.__str__())
                        print(f'{file} Eliminado.')
                    except Exception as e:
                        print(e)


def removeDBData(useFlush=False):
    """
    Funcion encargada de eliminar los datos de la base de datos.

    Si se asigna un true a useFlush, entonces la función utilizará la funcion
    flush() de django para eliminar los datos (aplicable a cualquier base de
    datos mantenida por defecto por django), no hará falta migrar los datos
    de los modelos, pero si una tabla acaba de ser migrada no eliminará sus
    datos.
    Por defecto useFlush es false, en este caso, la función eliminará el
    archivo de la db dentro del directorio raiz. (Esto solo funcionará si la
    base de datos que se esta usando es sqlite3).
    """
    if useFlush:
        print('Ejecuntando función flush sobre la base de datos...')
        call_command('flush', '--noinput')
        print('Se eliminaron los datos de la base de datos con exito.')
    elif os.path.exists('./db.sqlite3'):
        try:
            print('Eliminando el archivo de base de datos...')
            os.remove('./db.sqlite3')
            print('Base de datos eliminada con exito.')
            print('Creando archivos de migración...')
            call_command('makemigrations')
            print('Archivos de migración creados.')
            print('Migrando modelos...')
            call_command('migrate')
            print('Modelos migrados, base de datos restaurada desde cero...')
        except Exception as e:
            print(e)
