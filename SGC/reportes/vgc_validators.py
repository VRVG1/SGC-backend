from rest_framework.response import Response
from rest_framework import status

REGISTRO_TYPE_ATTRIBUTES = {
    "noSeguimiento": int,
    "semanaDel": str,
    "newReporte": dict
    }

NEW_REPORTE_TYPE_ATTRIBUTES = {
    "numeroReporte": int,
    "nombreProfesor": str,
    "asignatura": str,
    "GradoGrupo": str,
    "tema": str,
    "semanaProgramada": str,
    "verificacion": bool,
    "RCMRRC": bool,
    "indReprobacion": int,
    "CCEEID": bool,
    "observaciones": str
}


def checkEstructuraAddRegistro(datos):
    if len(datos.keys()) != len(REGISTRO_TYPE_ATTRIBUTES):
        return Response(data={
            "Error": "Número de atributos no concuerda."
            },
            status=status.HTTP_400_BAD_REQUEST)

    for key in datos.keys():
        if type(datos[key]) is not REGISTRO_TYPE_ATTRIBUTES[key]:
            return Response(data={
                "Error": f"Tipo de dato no permitido para {key}"
                },
                status=status.HTTP_400_BAD_REQUEST)

    return checkEstructuraReporte(datos['newReporte'])


def checkEstructuraReporte(datos):
    if len(datos.keys()) != len(NEW_REPORTE_TYPE_ATTRIBUTES):
        return Response(data={
            "Error": "Número de atributos no concuerda."
            },
            status=status.HTTP_400_BAD_REQUEST)

    for key in datos.keys():
        if type(datos[key]) is not NEW_REPORTE_TYPE_ATTRIBUTES[key]:
            return Response(data={
                "Error": f"Tipo de dato no permitido para {key}"
                },
                status=status.HTTP_400_BAD_REQUEST)

    return True


def checkAddRegistroVGC(datos, registro_gral_vgc):
    if type(datos) is not dict:
        return Response(data={"Error": "Estructura de datos no valida."},
                        status=status.HTTP_400_BAD_REQUEST)

    check_struct_datos = checkEstructuraAddRegistro(datos)
    if type(check_struct_datos) is Response:
        return check_struct_datos

    new_reporte = datos["newReporte"]
    for reporte in registro_gral_vgc["registro"]:
        if reporte["numeroReporte"] == new_reporte["numeroReporte"]:
            return Response(data={
                "Error": "Ya existe un reporte con ese numeroReporte"
                },
                status=status.HTTP_400_BAD_REQUEST)

    return datos


def checkUpdateRegistroVGC(datos, registro_gral_vgc):
    if type(datos) is not dict:
        return Response(data={"Error": "Estructura de datos no valida."},
                        status=status.HTTP_400_BAD_REQUEST)

    check_struct_datos = checkEstructuraReporte(datos)
    if type(check_struct_datos) is Response:
        return check_struct_datos

    is_numero_reporte_found = False
    for reporte in registro_gral_vgc["registro"]:
        # Se busca que el numeroReporte del reporte recibido exista dentro
        # de los reportes del registro_gral_vgc
        if reporte["numeroReporte"] == datos["numeroReporte"]:
            # Al ser encontrado se activa la flag'is_numero_reporte_found'
            # y se hace break ya que no es necesario seguir buscando
            is_numero_reporte_found = True
            break

    # Si la flag 'is_numero_reporte_found' es False, significa que el reporte
    # que se quiere modificar no existe.
    if not is_numero_reporte_found:
        return Response(data={
            "Error": "No existe un reporte con ese numeroReporte"
            },
            status=status.HTTP_400_BAD_REQUEST)

    return datos


def checkDeleteRegistroVGC(datos, registro_gral_vgc):
    if type(datos) is not NEW_REPORTE_TYPE_ATTRIBUTES["numeroReporte"]:
        return Response(data={"Error": "Tipo de dato no valido."},
                        status=status.HTTP_400_BAD_REQUEST)

    numero_reporte_2_delete = datos
    is_numero_reporte_found = False
    for reporte in registro_gral_vgc["registro"]:
        # Se busca que exista un reporte con el ID a eliminar
        if reporte["numeroReporte"] == numero_reporte_2_delete:
            is_numero_reporte_found = True
            break

    # Si la flag 'is_numero_reporte_found' es False, significa que el reporte
    # que se quiere modificar no existe.
    if not is_numero_reporte_found:
        return Response(data={
            "Error": "No existe un reporte con ese numeroReporte"
            },
            status=status.HTTP_400_BAD_REQUEST)

    return numero_reporte_2_delete
