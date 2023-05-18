from rest_framework.response import Response
from rest_framework import status
import re


def checkReceivedData(datos):
    if type(datos) is not dict:
        return Response(data={"Error": "Estructura de datos no valida."},
                        status=status.HTTP_400_BAD_REQUEST)

    datos_keys = datos.keys()
    atributos_datos = {
        "lastPNCID": {"dataClass": int},
        "registro": {"dataClass": dict}
    }

    if len(datos_keys) != 2:
        return Response(data={"Error": "Estructura de datos no valida."},
                        status=status.HTTP_400_BAD_REQUEST)

    for key in datos_keys:
        try:
            atributo_dato_dataclass = atributos_datos[key]
        except KeyError:
            return Response(data={
                "Error": f"Estructura de objeto no valida. '{key}' no es un atributo de data2send"
                },
                status=status.HTTP_400_BAD_REQUEST)

        if type(datos[key]) is not atributo_dato_dataclass["dataClass"]:
            return Response(data={
                "Error": f"Estructura de objeto no valida. El contenido relacionado a '{key}' no es de tipo {atributo_dato_dataclass['dataClass']}"
                },
                status=status.HTTP_400_BAD_REQUEST)

    # Se crean las variables solo para dar contexto de lo que retornan
    lastPNCID = datos["lastPNCID"]
    registro = datos["registro"]
    return (lastPNCID, registro)


def checkReportesRegistrados(reportes_ids,
                             reportes_registrados,
                             registro_gral_idsReportes):
    keys = reportes_registrados.keys()
    if len(keys) != 1:
        return Response(data={
            "Error": "Estructura de reportesRegistrados no valida. Más elementos de los esperados"
            },
            status=status.HTTP_400_BAD_REQUEST)

    if "idsReportes" not in keys:
        return Response(data={
            "Error": "Estructura de reportesRegistrados no valida. No existe el elemento 'idsReportes'"
            },
            status=status.HTTP_400_BAD_REQUEST)

    new_ids_reportes = reportes_registrados["idsReportes"]
    if type(new_ids_reportes) is not list:
        return Response(data={
            "Error": "Estructura de reportesRegistrados no valida. Valor relacionado a 'idsReportes' no es de tipo 'arreglo'"
            },
            status=status.HTTP_400_BAD_REQUEST)

    # El ultimo id agregado en idsReportes debe ser el del nuevo reporte
    if new_ids_reportes[-1] not in reportes_ids:
        return Response(data={
            "Error": "Estructura de reportesRegistrados no valida. Id del nuevo reporte no concuerda"
            },
            status=status.HTTP_400_BAD_REQUEST)

    # Todos los ids dentro de idsReportes menos el ultimo son de reportes
    # existentes
    new_ids_reportes = new_ids_reportes[:-1]
    # Comprobando si los ids pasados por parametro realmente existen en el registro
    for id_reporte in new_ids_reportes:
        if id_reporte in registro_gral_idsReportes:
            return Response(data={
                "Error": f"Estructura de reportesRegistrados no valida. Id '{id_reporte}' no existe en el servidor"
                },
                status=status.HTTP_400_BAD_REQUEST)

    return True


def checkReporte(pnc_id, reporte, registro_gral):
    new_registro_reporte_key = reporte.keys()
    if len(new_registro_reporte_key) != 1:
        return Response(data={
            "Error": "Estructura de reporte_<ID> no valida. Más elementos de los esperados"
            },
            status=status.HTTP_400_BAD_REQUEST)

    if "linkedPNCs" not in new_registro_reporte_key:
        return Response(data={
            "Error": "Estructura de reporte_<ID> no valida. No existe el elemento 'linkedPNCs'"
            },
            status=status.HTTP_400_BAD_REQUEST)

    new_linked_pncs = reporte["linkedPNCs"]
    if type(new_linked_pncs) is not list:
        return Response(data={
            "Error": "Estructura de reporte_<ID> no valida. Valor relacionado a 'linkedPNCs' no es de tipo 'arreglo'"
            },
            status=status.HTTP_400_BAD_REQUEST)

    # El último id agregado en linkedPNCs debe ser el nuevo pnc
    if pnc_id != new_linked_pncs[-1]:
        return Response(data={
            "Error": "Estructura de reporte_<ID> no valida. Id del nuevo PNC no concuerda"
            },
            status=status.HTTP_400_BAD_REQUEST)

    # Todos los ids dentro de linkedPNCs menos el ultimo son de pncs existentes
    new_linked_pncs = new_linked_pncs[:-1]
    # Comprobando si los ids pasados por parametro realmente existen en el registro
    for id_pnc in new_linked_pncs:
        if id_pnc in registro_gral:
            return Response(data={
                "Error": f"Estructura de reporte_<ID> no valida. Id '{id_pnc}' no existe en el servidor"
                },
                status=status.HTTP_400_BAD_REQUEST)

    return True


def checkPNC(pnc):
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


def validarDatos(datos, registro_gral_pnc):
    check_datos = checkReceivedData(datos)
    if type(check_datos) is Response:
        return check_datos

    lastPNCID, registro = check_datos
    registro_keys = registro.keys()
    rgx_id_reporte = r"(?:^reporte_[0-9]+$)"
    rgx_id_pnc = r"(?:^pnc_[0-9]+$)"

    if len(registro_keys) < 2 or len(registro_keys) > 3:
        return Response(data={
            "Error": "Estructura de registro no valida. Más elementos de los esperados"
            },
            status=status.HTTP_400_BAD_REQUEST)

    # TODO: Cambiar las variables has_ por contadores
    # TODO: Cambiar los registro_..._id por arreglos y hacer que agregue los
    #       matches de los rgx_id_...correspondientes
    has_reportes_registrados = False
    has_reporte_id = False
    has_pnc_id = False
    registro_reporte_id = ""
    registro_pnc_id = ""
    for key in registro_keys:
        if len(registro_keys) == 3 and key == "reportesRegistrados":
            if has_reportes_registrados:
                return Response(data={
                    "Error": "Estructura de registro no valida. Elemento reportesRegistrados repetido"
                    },
                    status=status.HTTP_400_BAD_REQUEST)
            has_reportes_registrados = True

        if re.match(rgx_id_reporte, key) is not None:
            if has_reporte_id:
                return Response(data={
                    "Error": "Estructura de registro no valida. Elemento reporte_<ID> repetido"
                    },
                    status=status.HTTP_400_BAD_REQUEST)
            has_reporte_id = True
            registro_reporte_id = key
        elif re.match(rgx_id_pnc, key) is not None:
            if has_pnc_id:
                return Response(data={
                    "Error": "Estructura de registro no valida. Elemento pnc_<ID> repetido"
                    },
                    status=status.HTTP_400_BAD_REQUEST)
            has_pnc_id = True
            registro_pnc_id = key
        else:
            if len(registro_keys) == 3 and key == "reportesRegistrados":
                continue

            return Response(data={
                "Error": "Estructura de registro no valida. Elemento no tiene un formato valido"
                },
                status=status.HTTP_400_BAD_REQUEST)

    or_registro_len_3 = len(registro_keys) == 3 or has_reportes_registrados
    and_registro_len_3 = len(registro_keys) == 3 and has_reportes_registrados
    xor_registro_len_3 = or_registro_len_3 and not and_registro_len_3
    # El xor evalua si el registro_keys tiene un length de 3 y
    # has_reportes_registrados es falso retornará el response 400
    # o
    # Si el registro_keys tiene un length distinto a 3 (2) y
    # has_reportes_registrados es verdadero retornará el response 400
    if xor_registro_len_3 or not has_reporte_id or not has_pnc_id:
        return Response(data={
            "Error": "Estructura de registro no valida. Faltan elementos"
            },
            status=status.HTTP_400_BAD_REQUEST)

    if len(registro_keys) == 3:
        new_reportes_registrados = registro["reportesRegistrados"]
        check_repo_registro = checkReportesRegistrados(registro_reporte_id,
                                                       new_reportes_registrados,
                                                       registro_gral_pnc["registro"]["reportesRegistrados"]["idsReportes"])
        if type(check_repo_registro) is Response:
            return check_repo_registro

    # Si unicamente se reciben 2 elementos (reporte_<ID> y pnc_<ID>) significa
    # que existe ya una referencia a dicho reporte en el registro general
    if len(registro_keys) == 2:
        print(f"\n\n\n\tRegistro Reporte ID: {registro_reporte_id}")
        print(f"\n\n\n\tRegistro General: {registro_gral_pnc}")
        if registro_reporte_id in registro_gral_pnc["registro"]:
            return Response(data={
                "Error": "Estructura de reporte_<ID> no valida. El reporte que se esta actualizando no existe en el registro general"
                },
                status=status.HTTP_400_BAD_REQUEST)

    registro_reporte = registro[registro_reporte_id]
    check_reporte = checkReporte(registro_pnc_id,
                                 registro_reporte,
                                 registro_gral_pnc["registro"])
    if type(check_reporte) is Response:
        return check_reporte

    new_registro_pnc = registro[registro_pnc_id]
    check_pnc = checkPNC(new_registro_pnc)
    if type(check_pnc) is Response:
        return check_pnc

    return (lastPNCID,
            registro,
            has_reportes_registrados,
            registro_reporte_id,
            registro_pnc_id)