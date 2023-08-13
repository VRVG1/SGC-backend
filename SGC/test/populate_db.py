# from django_setup import initWorkspace
# 
# initWorkspace()

from rest_framework.authtoken.models import Token

from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from usuarios.models import Usuarios
from materias.models import Asignan, Materias, Carreras
from reportes.models import Reportes, Generan
from datetime import date

from string import ascii_uppercase
from random import random as rd

import requests
import json


def populateCarrerasTable():
    carreras = [("IIND", "Ingeniería Industrial"),
                ("IMEC", "Ingeniería Mecanica"),
                ("IINF", "Ingeniería Informatica"),
                ("ISIC", "Ingeniería en Sistemas Computacionales")]

    print("\n\nPopulating Carreras Table...\n")
    for id, carrera in carreras:
        flag_exist = True
        try:
            Carreras.objects.get(Nombre_Carrera=carrera)
        except Carreras.DoesNotExist:
            flag_exist = False

        if(flag_exist):
            continue

        print(f"\tAdding to DB...\n\tID: { id }\n\tCarrera: { carrera }\n")
        Carreras.objects.create(ID_Carrera=id, Nombre_Carrera=carrera)


def desertCarrerasTable():
    print("\n\nDepopulating Carreras Table...\n")
    Carreras.objects.all().delete()
    print("'Carreras Table' depopulation succesful.\n\n")


def populateMateriasTable():
    carrera_ind = Carreras.objects.get(ID_Carrera='IIND')
    carrera_mec = Carreras.objects.get(ID_Carrera='IMEC')
    carrera_inf = Carreras.objects.get(ID_Carrera='IINF')
    carrera_sic = Carreras.objects.get(ID_Carrera='ISIC')

    materias_ind = [
            {
                'Clave_reticula': 'INN-1008',
                'Carrera': carrera_ind,
                'Nombre_Materia': 'Dibujo Industrial',
                'horas_Teoricas': 0,
                'horas_Practicas': 6,
                'Creditos': 6,
                'Unidades': 4
            },
            {
                'Clave_reticula': 'INC-1009',
                'Carrera': carrera_ind,
                'Nombre_Materia': 'Electricidad y Electrónica Industrial',
                'horas_Teoricas': 2,
                'horas_Practicas': 2,
                'Creditos': 4,
                'Unidades': 4
            },
            {
                'Clave_reticula': 'INU-1011',
                'Carrera': carrera_ind,
                'Nombre_Materia': 'Estudio del Trabajo I',
                'horas_Teoricas': 4,
                'horas_Practicas': 2,
                'Creditos': 6,
                'Unidades': 4
            }, ]

    materias_mec = [
            {
                'Clave_reticula': 'MEV-1006',
                'Carrera': carrera_mec,
                'Nombre_Materia': 'Dibujo Mecánico',
                'horas_Teoricas': 0,
                'horas_Practicas': 5,
                'Creditos': 5,
                'Unidades': 5
            },
            {
                'Clave_reticula': 'MEF-1013',
                'Carrera': carrera_mec,
                'Nombre_Materia': 'Ingeniería de Materiales Metálicos',
                'horas_Teoricas': 3,
                'horas_Practicas': 2,
                'Creditos': 5,
                'Unidades': 6
            },
            {
                'Clave_reticula': 'AEF-1020',
                'Carrera': carrera_mec,
                'Nombre_Materia': 'Electromagnetismo',
                'horas_Teoricas': 3,
                'horas_Practicas': 2,
                'Creditos': 5,
                'Unidades': 6
            }, ]

    materias_inf = [
            {
                'Clave_reticula': 'IFE-1004',
                'Carrera': carrera_inf,
                'Nombre_Materia': 'Administración para Informática',
                'horas_Teoricas': 3,
                'horas_Practicas': 1,
                'Creditos': 4,
                'Unidades': 5
            },
            {
                'Clave_reticula': 'IFC-1001',
                'Carrera': carrera_inf,
                'Nombre_Materia': 'Administración de los Recursos y la Función Informática',
                'horas_Teoricas': 2,
                'horas_Practicas': 2,
                'Creditos': 4,
                'Unidades': 5
            },
            {
                'Clave_reticula': 'IFE-1015',
                'Carrera': carrera_inf,
                'Nombre_Materia': 'Fundamentos de Sistemas de Información',
                'horas_Teoricas': 3,
                'horas_Practicas': 1,
                'Creditos': 4,
                'Unidades': 5
            }, ]

    materias_sic = [
            {
                'Clave_reticula': 'AED-1285',
                'Carrera': carrera_sic,
                'Nombre_Materia': 'Fundamentos de Programación',
                'horas_Teoricas': 2,
                'horas_Practicas': 3,
                'Creditos': 5,
                'Unidades': 5
            },
            {
                'Clave_reticula': 'AED-1286',
                'Carrera': carrera_sic,
                'Nombre_Materia': 'Programación Orientada a Objetos',
                'horas_Teoricas': 2,
                'horas_Practicas': 3,
                'Creditos': 5,
                'Unidades': 6
            },
            {
                'Clave_reticula': 'SCC-1013',
                'Carrera': carrera_sic,
                'Nombre_Materia': 'Investigación de Operaciones',
                'horas_Teoricas': 2,
                'horas_Practicas': 2,
                'Creditos': 4,
                'Unidades': 5
            }, ]

    def iterMateriasDicts(materias, nombre_carrera):
        print(f"\tPopulating materias of '{nombre_carrera}' career...")
        for materia in materias:
            clave_reticula = materia['Clave_reticula']
            carrera = materia['Carrera']
            try:
                # Verify if exists in db a materia recorded with his
                # composed primary key
                Materias.objects.get(Clave_reticula=clave_reticula,
                                     Carrera=carrera)
                continue  # Due to the object already exist in db
            except Materias.DoesNotExist:
                # Nothing happens here, the try-except block is just to
                # catch the "DoesNotExist" exception in case the object isn't
                # recorded in db.
                pass

            nombre_materia = materia['Nombre_Materia']
            horas_teoricas = materia['horas_Teoricas']
            horas_practicas = materia['horas_Practicas']
            creditos = materia['Creditos']
            unidades = materia['Unidades']

            print("\t\tAdding to DB...")
            print(f"\t\t\tClave Reticula: { clave_reticula }")
            print(f"\t\t\tNombre Materia: { nombre_materia }\n")
            Materias.objects.create(Clave_reticula=clave_reticula,
                                    Carrera=carrera,
                                    Nombre_Materia=nombre_materia,
                                    horas_Teoricas=horas_teoricas,
                                    horas_Practicas=horas_practicas,
                                    creditos=creditos,
                                    unidades=unidades)

    print("\n\nPopulating Materias Table...\n")
    iterMateriasDicts(materias_ind, carrera_ind.Nombre_Carrera)
    iterMateriasDicts(materias_mec, carrera_mec.Nombre_Carrera)
    iterMateriasDicts(materias_inf, carrera_inf.Nombre_Carrera)
    iterMateriasDicts(materias_sic, carrera_sic.Nombre_Carrera)


def addAdmin():
    data_file = open("./test/superuserdata.json", "r")
    superuser_data = json.load(data_file)
    username = superuser_data['username']
    first_name = superuser_data['first_name']
    last_name = superuser_data['last_name']
    email = superuser_data['email']
    password = superuser_data['password']
    password = make_password(password=password)

    try:
        admin = User.objects.get(username=username)
        print("Admin user already exists.")
    except User.DoesNotExist:
        print("Adding admin user to contrib.auth.models.User...")
        admin = User.objects.create(username=username,
                                    first_name=first_name,
                                    last_name=last_name,
                                    email=email,
                                    password=password,
                                    is_superuser=True,
                                    is_staff=True)
        admin.save()
        print(f"Admin user '{username}' added to DB.")

    try:
        Usuarios.objects.get(ID_Usuario=admin)
        print("Usuario related with admin already exists.")
    except Usuarios.DoesNotExist:
        print("Adding user related with admin user...")
        Usuarios.objects.create(ID_Usuario=admin,
                                Nombre_Usuario=f"{first_name} {last_name}",
                                Tipo_Usuario="Administrador",
                                CorreoE=email)
        print(f"Usuario '{first_name} {last_name}' added to DB.")


def populateUsuariosTable():
    flag_new_career = False
    loading_p_career = ""
    print("\n\nPopulating django.contrib.auth.User & Usuarios Tables...\n")
    for i in range(40):
        id_prof = i + 1
        last_name = (id_prof) % 10
        if last_name == 0:
            last_name = 10
        else:
            last_name = "0" + str(last_name)

        username = f"Profesor{ str(0) + str(id_prof)  if id_prof <= 9 else id_prof}"
        if i < 10:
            first_name = 'Industrial'
            email = '@ind.tecnm.com'

            loading_p_career = "Industrial"
            flag_new_career = True
        elif i < 20:
            first_name = 'Mecanico'
            email = '@mec.tecnm.com'

            loading_p_career = "Mecanica"
            flag_new_career = True
        elif i < 30:
            first_name = 'Informatico'
            email = '@inf.tecnm.com'

            loading_p_career = "Informatica"
            flag_new_career = True
        else:
            first_name = 'ISIC'
            email = '@sic.tecnm.com'

            loading_p_career = "Sistemas Computacionales"
            flag_new_career = True

        if flag_new_career:
            flag_new_career = False
            print(f'\tPopulating professors of { loading_p_career } career...')

        try:
            User.objects.get(username=username)
            continue
        except User.DoesNotExist:
            pass

        print("\t\tAdding to DB...")
        print(f"\t\t\tUsername: { username }")
        print(f"\t\t\tFirst Name: { first_name }")
        print(f"\t\t\tLast Name: { last_name }\n")
        password = "abc123"
        password = make_password(password=password)
        email = username + email
        user = User.objects.create(username=username,
                                   first_name=first_name,
                                   last_name=last_name,
                                   email=email,
                                   password=password,
                                   is_superuser=False,
                                   is_staff=False)
        user.save()

        Usuarios.objects.create(ID_Usuario=user,
                                Nombre_Usuario=f"{ first_name }_{ last_name }",
                                Tipo_Usuario="Docente",
                                CorreoE=email)


def populateAsignanTable():
    asignaciones = Asignan.objects.all().count()
    if asignaciones != 0:
        print("Ya existen asignaciones registradas en la DB.\n")
        return

    carrera_ind = Carreras.objects.get(ID_Carrera='IIND')
    carrera_mec = Carreras.objects.get(ID_Carrera='IMEC')
    carrera_inf = Carreras.objects.get(ID_Carrera='IINF')
    carrera_sic = Carreras.objects.get(ID_Carrera='ISIC')

    materias_ind = Materias.objects.filter(Carrera=carrera_ind)
    materias_mec = Materias.objects.filter(Carrera=carrera_mec)
    materias_inf = Materias.objects.filter(Carrera=carrera_inf)
    materias_sic = Materias.objects.filter(Carrera=carrera_sic)

    profes_ind = Usuarios.objects.filter(Nombre_Usuario__startswith="Industrial")
    profes_mec = Usuarios.objects.filter(Nombre_Usuario__startswith="Mecanico")
    profes_inf = Usuarios.objects.filter(Nombre_Usuario__startswith="Informatico")
    profes_sic = Usuarios.objects.filter(Nombre_Usuario__startswith="ISIC")

    print("\n\nPopulating 'Asignan' Table...\n")

    def iterCarreraQuerySet(carrera, materias, profes):
        # WARN: If no superuser recorded in DB, this function
        #       won't work properly
        superuser = User.objects.get(username="OrdepSoir")
        token = Token.objects.get(user=superuser).key

        host = "http://localhost:8000/materia/asign_materia"
        semestre = 1
        for materia in materias:
            for profesor in profes:
                for grupo in ascii_uppercase:
                    if grupo == "D":
                        break

                    header = {
                            "Content-Type": "application/json",
                            "Authorization": 'Token ' + token
                            }
                    data = {
                            "ID_Materia": materia.pik,
                            "ID_Usuario": profesor.PK,
                            "Semestre": semestre,
                            "Grupo": grupo,
                            "Hora": "07:00 - 09:00",
                            "Dia": "Lunes",
                            "Aula": "A00"
                            }

                    json_data = json.dumps(data)
                    print(f"Json data: {json_data}")

                    print(f"\t\tAdding to DB '{ carrera }' assignation...")
                    print(f"\t\t\tSemestre: { semestre }")
                    print(f"\t\t\tGrupo: { grupo }")
                    print(f"\t\t\tMateria: { materia }")
                    print(f"\t\t\tProfesor: { profesor }\n")

                    response = requests.post(url=host,
                                             json=data,
                                             headers=header)

                    print(f"Respuesta servidor: {response.reason} {response.status_code}\n")
                    print(f"\n\tContent: { response.json() }\n")

                    # Asignan.objects.create(ID_Usuario=profesor,
                    #                        ID_Materia=materia,
                    #                        Semestre=semestre,
                    #                        Grupo=grupo,
                    #                        Hora="07:00 - 09:00",
                    #                        Dia="Lunes")
            semestre = semestre + 1

    iterCarreraQuerySet(carrera_ind, materias_ind, profes_ind)
    iterCarreraQuerySet(carrera_mec, materias_mec, profes_mec)
    iterCarreraQuerySet(carrera_inf, materias_inf, profes_inf)
    iterCarreraQuerySet(carrera_sic, materias_sic, profes_sic)


def populateReportesTable():
    # ^[a-zA-Z\s\d~._-]{0,200}$
    total_registered_materias = Materias.objects.all().count()
    for i in range(0, total_registered_materias):
        nombre_reporte = ""
        for idx in range(0, 200):
            alphabet_char = chr(int(rd() * (90 - 65) + 65))
            flagToUpper = round(rd())
            if flagToUpper == 1:
                alphabet_char = alphabet_char.lower()

            nombre_reporte = nombre_reporte + alphabet_char

        fecha_entrega = date(2023, 5, 30)
        Reportes.objects.create(Nombre_Reporte=nombre_reporte,
                                Fecha_Entrega=fecha_entrega)


def populateGeneranTable():
    generaciones = Generan.objects.all()
    bd_min_val_repro = 0
    bd_max_val_repro = 100 - 60  # x - y -> x=real limit, y=personal example
    for generacion in generaciones:
        reprobados = round(rd() * (bd_max_val_repro - bd_min_val_repro) +
                           bd_min_val_repro)
        print(f"Reprobados: {reprobados}\n")
        generacion.Reprobados = reprobados
        generacion.save()


    # NOTE: The commented lines below can be use for autogenerate future
    #       generan reports.

    # asignaciones = Asignan.objects.all()
    # reportes = Reportes.objects.all()

    # ord_fecha_minima = date(2023, 5, 15).toordinal()
    # ord_fecha_entrega_def = date(2023, 5, 30).toordinal()
    # ord_fecha_max = date(2023, 6, 7).toordinal()

    # ord_fecha_entrega = round(rd() * (ord_fecha_max - ord_fecha_minima) + ord_fecha_minima)

    # if ord_fecha_entrega < ord_fecha_entrega_def:
    #     estatus = "ENTREGADO EN TIEMPO"
    # else:
    #     estatus = "ENTREGADO TARDE"

    # periodo = "Enero - Junio"
    # reprobados = round(rd() * (100 - 0) + 0)


# desertCarrerasTable()
addAdmin()
populateCarrerasTable()
populateMateriasTable()
populateUsuariosTable()
populateAsignanTable()
# populateReportesTable()
populateGeneranTable()
