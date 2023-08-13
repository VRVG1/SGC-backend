from .models import Reportes
from rest_framework.response import Response
from rest_framework import status
import re


def checkPNC(pnc):
    """
    checkPNC verifica que la estructura del parametro 'pnc' cumpla con la
    estructura estandar.

    @param pnc  Dict. Se espera que su estructura sea:
        {
            "numeroPNC": int
            "folio": str
            "fechaRegistro": str
            "especIncumplida": str
            "accionImplantada": str
            "isEliminaPNC": bool
        }

    @return La funcion retorna 2 tipos de datos:
                Response: Indica que la estructura del parametro 'datos' no
                          es valida, por lo que se puede retornar la Response
                          directamente al usuario. Atributos de todos los
                          response:
                              data: Diccionario con un unico atributo 'Error'
                              status: status.HTTP_400_BAD_REQUEST

                True <Bool>: Indica que el parametro 'pnc' cumple con el
                             estandar
    """
    atributos_pnc = {
        "numeroPNC": {"dataClass": int},
        "folio": {"dataClass": str},
        "fechaRegistro": {"dataClass": str},
        "especIncumplida": {"dataClass": str},
        "accionImplantada": {"dataClass": str},
        "isEliminaPNC": {"dataClass": bool}
    }

    new_registro_pnc_keys = pnc.keys()
    if len(new_registro_pnc_keys) != 6:
        return Response(data={
            "Error": "Estructura de pnc_<ID> no valida. Elementos no concuerdan"
        },
            status=status.HTTP_400_BAD_REQUEST)

    for atributo_pnc in atributos_pnc:
        try:
            valor_atributo = pnc[atributo_pnc]
        except KeyError:
            return Response(data={
                "Error": f"Estructura de pnc_<ID> no valida. El atributo '{atributo_pnc}' no existe en el nuevo pnc"
            },
                status=status.HTTP_400_BAD_REQUEST)

        if type(valor_atributo) is not atributos_pnc[atributo_pnc]["dataClass"]:
            return Response(data={
                "Error": f"Estructura de pnc_<ID> no valida. El valor relacionado con el atributo '{valor_atributo}' no es de tipo '{atributos_pnc[atributo_pnc]['dataClass']}'"
            },
                status=status.HTTP_400_BAD_REQUEST)
    return True


def checkAddRegistro(datos):
    """
    checkAddRegistro verifica que la estructura del parametro datos cumpla con
    el estandar para agregar dicho registro al registro general pnc.

    @param datos    Dict. Se espera que su estructura sea:
        {
            "lastPNCID": int,
            "registro": {
                [
                    "reportesRegistrados": {
                        "idsReportes":  [
                                            "reporte_1",
                                            ...,
                                            "reporte_<ID>":str
                                        ]
                    },
                ]
                "reporte_<ID>": {
                    "linkedPNCs": ["pnc_<ID>":str ...]
                },
                "pnc_<ID>": {
                    "numeroPNC": int,
                    "folio": str,
                    "fechaRegistro": str,
                    "especIncumplida": str,
                    "accionImplantada": str,
                    "isEliminaPNC": bool
                }
            }
        }

        En donde:
            "reportesRegistros":    Unicamente aparecerá en el registro cuando el
                                    reporte_<ID> no exista en el registro_gral_pnc

            "reporte_<ID>": Siempre estará presente en el registro.
            "pnc_<ID>": Siempre estará presente en el registro.

    @param registro_gral_pnc    Dict. Referencia al contenido
                                de registro_gral_pnc.js

    @return La función retorna 2 tipos de datos:
                Response: Indica que la estructura del parametro 'datos' no
                          es valida, por lo que se puede retornar la Response
                          directamente al usuario. Atributos de todos los
                          response:
                              data: Diccionario con un unico atributo 'Error'
                              status: status.HTTP_400_BAD_REQUEST

                Tupla: Indica que la estructura del parametro 'datos' es
                       valida, por lo que se retornan todos los datos
                       desglozados:
                           lastPNCID: int
                           registro: dict
                           has_reportes_registrados: bool
                           reporte_id: str
                           pnc_id: str
    """
    if type(datos) is not dict:
        return Response(data={"Error": "Estructura de datos no valida."},
                        status=status.HTTP_400_BAD_REQUEST)

    datos_keys = datos.keys()
    atributos_datos = {
        "ID_reporte": {"dataClass": int},
        "new_PNC": {"dataClass": dict}
    }

    if len(datos_keys) != 2:
        return Response(data={"Error": "Estructura de datos no valida."},
                        status=status.HTTP_400_BAD_REQUEST)

    for key in datos_keys:
        if key in atributos_datos:
            atributo_dato_dataclass = atributos_datos[key]
        else:
            return Response(data={
                "Error": f"Estructura de objeto no valida. '{key}' no es un atributo de data2send"
            },
                status=status.HTTP_400_BAD_REQUEST)

        if type(datos[key]) is not atributo_dato_dataclass["dataClass"]:
            return Response(data={
                "Error": f"Estructura de objeto no valida. El contenido relacionado a '{key}' no es de tipo {atributo_dato_dataclass['dataClass']}"
            },
                status=status.HTTP_400_BAD_REQUEST)

    id_reporte = datos['ID_reporte']
    new_pnc = datos['new_PNC']

    print("\n\n\n\n")
    print(datos)
    print(f"ID Reporte: {id_reporte}")
    print(f"Type ID Reporte: {type(id_reporte)}")
    try:
        Reportes.objects.get(ID_Reporte=id_reporte)
    except Reportes.DoesNotExist:
        return Response(data={
            'Error': f'Reporte con ID "{id_reporte}" no existe'
            },
            status=status.HTTP_400_BAD_REQUEST)

    check_pnc_structure = checkPNC(new_pnc)
    if type(check_pnc_structure) is Response:
        return check_pnc_structure

    return id_reporte, new_pnc


def checkUpdateRegistro(datos, registro_gral_pnc):
    """
    checkUpdateRegistro verifica que la estructura del parametro datos cumpla
    con el estandar para modificar el registro general pnc.

    @param datos    Dict. Se espera que su estructura sea:
        {
            "lastPNCID": int,
            "registro": {
                [
                    "reportesRegistrados": {
                        "idsReportes":  [
                                            "reporte_1",
                                            ...,
                                            "reporte_<ID>":str
                                        ]
                    },
                ]|
                [
                    "reporte_<ID>": {
                        "linkedPNCs":   [
                                            "pnc_1",
                                            ...,
                                            "pnc_n"
                                            !"pnc_<ID>"
                                        ]
                    },
                ]|
                "reporte_<ID>": {
                    "linkedPNCs":   [
                                        "pnc_1",
                                        ...,
                                        "pnc_<ID>":str
                                    ]
                },
                "pnc_<ID>": {
                    "numeroPNC": int,
                    "folio": str,
                    "fechaRegistro": str,
                    "especIncumplida": str,
                    "accionImplantada": str,
                    "isEliminaPNC": bool
                }
            }
        }

        En donde:
            "reportesRegistros":    Unicamente aparecerá en el registro cuando el
                                    reporte_<ID> no exista en el registro_gral_pnc

            "reporte_<ID>": Siempre estará presente en el registro. Pero puede
                            estar presente dos veces dentro de este, en donde
                            en uno existira el 'pnc_<ID>' a modificar y en el
                            otro no.

            "pnc_<ID>": Siempre estará presente en el registro.

    @param registro_gral_pnc    Dict. Referencia al contenido
                                de registro_gral_pnc.js

    @return La función retorna 2 tipos de datos:
                Response: Indica que la estructura del parametro 'datos' no
                          es valida, por lo que se puede retornar la Response
                          directamente al usuario. Atributos de todos los
                          response:
                              data: Diccionario con un unico atributo 'Error'
                              status: status.HTTP_400_BAD_REQUEST

                Tupla: Indica que la estructura del parametro 'datos' es
                       valida, por lo que se retornan todos los datos
                       desglozados:
                           lastPNCID: int
                           registro: dict
                           has_reportes_registrados: bool
                           reporte_id: str
                           pnc_id: str
    """
    if type(datos) is not dict:
        return Response(data={"Error": "Estructura de datos no valida."},
                        status=status.HTTP_400_BAD_REQUEST)

    datos_keys = datos.keys()
    if len(datos_keys) < 3 and len(datos_keys) > 4:
        return Response(data={"Error": "Cantidad de datos inusual."})

    atributos_datos = {
        "ID_reporte": {"dataClass": int},
        "ID_pnc": {"dataClass": str},
        "new_PNC": {"dataClass": dict}
    }
    if len(datos_keys) == 4:
        atributos_datos['ID_old_reporte'] = {"dataClass": int}

    for key in datos_keys:
        if key in atributos_datos:
            atributo_dato_dataclass = atributos_datos[key]
        else:
            return Response(data={
                "Error": f"Estructura de objeto no valida. '{key}' no es un atributo de data2send"
            },
                status=status.HTTP_400_BAD_REQUEST)

        if type(datos[key]) is not atributo_dato_dataclass["dataClass"]:
            return Response(data={
                "Error": f"Estructura de objeto no valida. El contenido relacionado a '{key}' no es de tipo {atributo_dato_dataclass['dataClass']}"
            },
                status=status.HTTP_400_BAD_REQUEST)

    id_reporte = datos['ID_reporte']
    id_pnc = datos['ID_pnc']
    new_pnc = datos['new_PNC']
    if id_pnc not in registro_gral_pnc['registro']:
        return Response(data={
            "Error": "ID de PNC no valido. No existe en el registro."
            },
            status=status.HTTP_400_BAD_REQUEST)

    if len(datos_keys) == 4:
        try:
            Reportes.objects.get(ID_Reporte=datos['ID_old_reporte'])
        except Reportes.DoesNotExist:
            return Response(data={
                'Error': f'Reporte viejo con ID "{id_reporte}" no existe'
                },
                status=status.HTTP_400_BAD_REQUEST)
        formated_old_id_reporte = f"reporte_{datos['ID_old_reporte']}"
        if formated_old_id_reporte not in registro_gral_pnc['registro']['reportesRegistrados']['idsReportes']:
            return Response(data={
                "Error": "ID de reporte viejo no valido. No existe en el registro."
                },
                status=status.HTTP_400_BAD_REQUEST)

        if id_pnc not in registro_gral_pnc['registro'][formated_old_id_reporte]['linkedPNCs']:
            return Response(data={
                "Error": "ID de PNC no valido. No existe en el registro del reporte viejo."
                },
                status=status.HTTP_400_BAD_REQUEST)
    else:
        formated_id_reporte = f"reporte_{datos['ID_reporte']}"
        if formated_id_reporte not in registro_gral_pnc['registro']['reportesRegistrados']['idsReportes']:
            return Response(data={
                "Error": "ID de reporte no valido. No existe en el registro."
                },
                status=status.HTTP_400_BAD_REQUEST)

        if id_pnc not in registro_gral_pnc['registro'][formated_id_reporte]['linkedPNCs']:
            return Response(data={
                "Error": "ID de PNC no valido. No existe en el registro del reporte viejo."
                },
                status=status.HTTP_400_BAD_REQUEST)

    try:
        Reportes.objects.get(ID_Reporte=id_reporte)
    except Reportes.DoesNotExist:
        return Response(data={
            'Error': f'Reporte con ID "{id_reporte}" no existe'
            },
            status=status.HTTP_400_BAD_REQUEST)

    check_pnc_structure = checkPNC(new_pnc)
    if type(check_pnc_structure) is Response:
        return check_pnc_structure

    return len(datos_keys)


def checkDeleteRegistro(datos, registro_gral_pnc):
    """
    checkDeleteRegistro verifica que la estructura del parametro datos cumpla
    con el estandar para eliminar un PNC del registro general.

    @param datos    Dict. Se espera que su estructura sea:
        {
            "reporte_<ID>": {
                "linkedPNCs": [
                    "reporte_1",
                    ...,
                    "reporte_n"
                    !"pnc_<ID>"
                ]
            },
            "pnc_<ID>": "pnc_<ID>"
        }

        En donde:
            "reporte_<ID>": Siempre estará en el registro. Y este contendrá
                            todos los pnc_ids registrados en el a excepción
                            del que será eliminado.

            "deletePNC":    Siempre estará en el registro. Contendrá el
                            pnc_<ID> del registro PNC a eliminar.

    @param registro_gral_pnc    Dict. Referencia al contenido
                                de registro_gral_pnc.js
    """

    if type(datos) is not dict:
        return Response(data={
            "Error": "Estructura de datos no valida."
        },
            status=status.HTTP_400_BAD_REQUEST)

    datos_keys = datos.keys()

    if len(datos_keys) != 2:
        return Response(data={"Error": "Estructura de datos no valida."},
                        status=status.HTTP_400_BAD_REQUEST)

    atributos_datos = {
        "ID_reporte": {"dataClass": int},
        "ID_pnc": {"dataClass": str}
    }

    for key in datos_keys:
        if key in atributos_datos:
            atributo_dato_dataclass = atributos_datos[key]
        else:
            return Response(data={
                "Error": f"Estructura de objeto no valida. '{key}' no es un atributo de data2send"
            },
                status=status.HTTP_400_BAD_REQUEST)

        if type(datos[key]) is not atributo_dato_dataclass["dataClass"]:
            return Response(data={
                "Error": f"Estructura de objeto no valida. El contenido relacionado a '{key}' no es de tipo {atributo_dato_dataclass['dataClass']}"
            },
                status=status.HTTP_400_BAD_REQUEST)

    id_reporte = datos['ID_reporte']
    id_pnc = datos['ID_pnc']
    try:
        Reportes.objects.get(ID_Reporte=id_reporte)
    except Reportes.DoesNotExist:
        return Response(data={
            'Error': f'Reporte con ID "{id_reporte}" no existe'
            },
            status=status.HTTP_400_BAD_REQUEST)

    format_id_reporte = f"reporte_{id_reporte}"
    if format_id_reporte not in registro_gral_pnc['registro']['reportesRegistrados']['idsReportes']:
        return Response(data={
            "Error": f"ID Reporte no valido. El reporte con ID '{format_id_reporte}' no existe en el registro"
            },
            status=status.HTTP_400_BAD_REQUEST)


    if id_pnc not in registro_gral_pnc['registro'][format_id_reporte]['linkedPNCs']:
        return Response(data={
            "Error": f"ID PNC no valido. El PNC con ID '{id_pnc}' no existe en el registro del reporte."
            },
            status=status.HTTP_400_BAD_REQUEST)

    return id_reporte, id_pnc
