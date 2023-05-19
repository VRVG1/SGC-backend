from rest_framework.response import Response
from rest_framework import status
import re


def checkRegistroKeys(registro_keys):
    """
    checkRegistroKeys verifica que cada uno de los elementos que contiene
    el parametro 'registro_keys' cumple con una expresión permitida.

    @param registro_keys    List<str>. Lista de strings que contendrá todas
                            las keys dentro del registro recibido por el
                            usuario.

    @return La función retorna 2 tipos de datos:
                Response:   Indica que la estructura del parametro
                            'reportes_registrados' no es valida, por lo que se
                            puede retornar la Response directamente al usuario.
                            Atributos de todos los response:
                                data: Diccionario con un unico atributo 'Error'
                                status: status.HTTP_400_BAD_REQUEST

                Tupla:  Indica que la estructura del parametro 'registro_keys'
                        es valida, por lo que se retornan todos los datos
                        desglozados:
                            has_reportes_registrados:   bool. Indica si existe el
                                                        atributo reportesRegistrados
                                                        en el registro.
                            count_match_rgx_reporte:    int. Contador que especifica
                                                        cuantos keys hicieron match
                                                        con la expresión regular de reporte.
                            count_match_rgx_pnc:        int. Contador que especifica
                                                        cuantos keys hicieron match
                                                        con la expresión regular de pnc.
                            reportes_ids:               List<str>. Lista que contiene
                                                        todos los strings que hicieron
                                                        match con la expresión regular de
                                                        reporte.
                            pncs_ids:                   List<str>. Lista que contiene
                                                        todos los strings  que hicieron
                                                        match con la expresión regular de
                                                        pnc.
    """
    rgx_id_reporte = r"(?:^reporte_[0-9]+$)"
    rgx_id_pnc = r"(?:^pnc_[0-9]+$)"

    has_reportes_registrados = False
    count_match_rgx_reporte = 0
    count_match_rgx_pnc = 0
    reportes_ids = []
    pncs_ids = []
    for key in registro_keys:
        if key == "reportesRegistrados":
            if has_reportes_registrados:
                return Response(data={
                    "Error": "Estructura de registro no valida. Elemento reportesRegistrados repetido"
                    },
                    status=status.HTTP_400_BAD_REQUEST)
            has_reportes_registrados = True
        elif re.match(rgx_id_reporte, key) is not None:
            # if count_match_rgx_reporte:
            #     return Response(data={
            #         "Error": "Estructura de registro no valida. Elemento reporte_<ID> repetido"
            #         },
            #         status=status.HTTP_400_BAD_REQUEST)
            count_match_rgx_reporte = count_match_rgx_reporte + 1
            reportes_ids.append(key)
        elif re.match(rgx_id_pnc, key) is not None:
            # if count_match_rgx_pnc:
            #     return Response(data={
            #         "Error": "Estructura de registro no valida. Elemento pnc_<ID> repetido"
            #         },
            #         status=status.HTTP_400_BAD_REQUEST)
            count_match_rgx_pnc = count_match_rgx_pnc + 1
            pncs_ids.append(key)
        else:
            return Response(data={
                "Error": "Estructura de registro no valida. Elemento no tiene un formato valido"
                },
                status=status.HTTP_400_BAD_REQUEST)

    return (has_reportes_registrados,
            count_match_rgx_reporte,
            count_match_rgx_pnc,
            reportes_ids,
            pncs_ids)
    pass


def checkReceivedData(datos):
    """
    checkReceivedData verifica que la estructura del parametro datos cumpla
    con la estructura estandar de un registro.
    @param datos    Dict. Se espera que su estructura sea:
        {
            "lastPNCID": int,
            "registro": Dict
        }

    @return La funcion retorna 2 tipos de datos:
                Response: Indica que la estructura del parametro 'datos' no
                          es valida, por lo que se puede retornar la Response
                          directamente al usuario. Atributos de todos los
                          response:
                              data: Diccionario con un unico atributo 'Error'
                              status: status.HTTP_400_BAD_REQUEST

                Tupla:  Indica que la estructura del parametro 'datos' es
                        valida, por lo que se retornan todos los datos
                        desglozados:
                            lastPNCID: int
                            registro: dict
    """
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

    # Se crean las variables solo para dar contexto de lo que retornan
    lastPNCID = datos["lastPNCID"]
    registro = datos["registro"]
    return (lastPNCID, registro)


def checkReportesRegistrados(reportes_ids,
                             reportes_registrados,
                             registro_gral_idsReportes):
    """
    checkReportesRegistrados verifica que la estructura del parametro
    'reportes_registrados' cumpla con la estructura estandar
    'reportesRegistrados'.

    @param reportes_ids     List<str>. Lista de strings que contendrá todos los
                            reporte_<ID> presentes en el registro.

    @param reportes_registrados     Dict. Se espera que su estructura sea:
        {
            "idsReportes":  [
                                "reporte_1",
                                ...,
                                "reporte_<ID>":str
                            ]
        }
    @param registro_gral_idsReportes    Dict. Referencia al contenido de
                                        'idsReportes' en 'registro' de
                                        registro_gral_pnc.js

    @return La función retorna 2 tipos de datos:
                Response:   Indica que la estructura del parametro
                            'reportes_registrados' no es valida, por lo que se
                            puede retornar la Response directamente al usuario.
                            Atributos de todos los response:
                                data: Diccionario con un unico atributo 'Error'
                                status: status.HTTP_400_BAD_REQUEST

                True <Bool>:    Indica que el parametro 'reportes_registrados'
                                cumple con el estandar
    """
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
        # NOTE: No hace falta el parametro mode en esta función, ya que solo
        #       se evalua si el último ID agregado en reportesRegistrados esta
        #       dentro de los reportes declarados en el registro entrante
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


def checkReporte(pnc_id, reporte, registro_gral, mode):
    """
    checkReporte verifica que la estructura del parametro 'reporte' cumpla con
    la estructura estandar.

    @param pnc_id   str. El id pnc que se esta agregando/modificando.
    @param reporte  Dict. Se espera que su estructura sea:
        {
            "linkedPNCs": [
                    "pnc_1",
                    ...,
                    pnc_<ID>
            ]
        }

    @param registro_gral    Dict. Referencia al contenido del atributo
                            'registro' de registro_gral_pnc.js

    @param mode int. Valor entero que define desde que función se esta llamando
                a esta función:
                    -> 1: checkAddRegistro
                    -> 2: checkUpdateRegistro

    @return La función retorna 2 tipos de datos:
                Response: Indica que la estructura del parametro 'datos' no
                          es valida, por lo que se puede retornar la Response
                          directamente al usuario. Atributos de todos los
                          response:
                              data: Diccionario con un unico atributo 'Error'
                              status: status.HTTP_400_BAD_REQUEST

                <Bool>: El valor booleano cambiará según el modo. De forma que:

                    mode=1:
                            True:   Indica que el parametro 'reporte' cumple
                                    con el estandar.

                    mode=2:
                            True:   Indica que el parametro 'reporte' cumple
                                    con el estandar pero este no contiene el
                                    nuevo pnc en linkedPNCs (oldReporte).
                            False:  Indica que el parametro 'reporte' cumple
                                    con el estandar pero este si contiene el
                                    nuevo pnc en linkedPNCs (newReporte).
    """
    new_registro_reporte_key = reporte.keys()
    # Cambiará de estado cuando se detecte un registro cuyo linkedPNCs no
    # contenga el parametro pnc_id
    update_mode_flag = False
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
        if mode == 2:
            update_mode_flag = True
        else:
            return Response(data={
                "Error": "Estructura de reporte_<ID> no valida. Id del nuevo PNC no concuerda"
                },
                status=status.HTTP_400_BAD_REQUEST)

    # Todos los ids dentro de linkedPNCs menos el ultimo son de pncs existentes
    # a menos que update_mode_flag sea True, ya que este no contiene el nuevo
    # pnc
    if not update_mode_flag:
        new_linked_pncs = new_linked_pncs[:-1]

    # Comprobando si los ids pasados por parametro realmente existen en el
    # registro
    for id_pnc in new_linked_pncs:
        if id_pnc not in registro_gral:
            return Response(data={
                "Error": f"Estructura de reporte_<ID> no valida. Id '{id_pnc}' no existe en el servidor"
                },
                status=status.HTTP_400_BAD_REQUEST)

    # Retornará True si el reporte evaluado no contiene el pnc_id (oldReporte)
    # pero retornará False si el reporte evaluado contiene el pnc_id
    # (newReporte)
    if mode == 2:
        return update_mode_flag

    # Retorno para checkAddRegistro
    return True


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


def checkAddRegistro(datos, registro_gral_pnc):
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
    check_datos = checkReceivedData(datos)
    if type(check_datos) is Response:
        return check_datos

    lastPNCID, registro = check_datos
    registro_keys = registro.keys()

    if len(registro_keys) < 2 or len(registro_keys) > 3:
        return Response(data={
            "Error": "Estructura de registro no valida. Más elementos de los esperados"
            },
            status=status.HTTP_400_BAD_REQUEST)

    check_registro_keys = checkRegistroKeys(registro_keys)
    if type(check_registro_keys) is Response:
        return check_registro_keys

    (has_reportes_registrados,
     count_match_rgx_reporte,
     count_match_rgx_pnc,
     reportes_ids,
     pncs_ids) = check_registro_keys

    invalid_reportes_registrados = validacionReportesRegistros(registro_keys,
                                                               has_reportes_registrados,
                                                               3)
    # El registro recibido siempre tendrá un único atributo del tipo
    # reporte_<ID>

    # El registro recibido siempre tendrá un único atributo del tipo
    # pnc_<ID>
    invalid_amount_reportes_pncs = validacionCantidadReportesPNCs(count_match_rgx_reporte,
                                                                  count_match_rgx_pnc,
                                                                  1,
                                                                  1)

    if invalid_reportes_registrados or invalid_amount_reportes_pncs:
        return Response(data={
            "Error": "Estructura de registro no valida. Faltan elementos"
            },
            status=status.HTTP_400_BAD_REQUEST)

    # Si existe reportesRegistrados en el registro recibido
    # (len(registro_keys) == 3) se procede a evaluar su estructura
    if has_reportes_registrados:
        new_reportes_registrados = registro["reportesRegistrados"]
        check_repo_registro = checkReportesRegistrados(reportes_ids,
                                                       new_reportes_registrados,
                                                       registro_gral_pnc["registro"]["reportesRegistrados"]["idsReportes"])
        if type(check_repo_registro) is Response:
            return check_repo_registro

    # Si unicamente se reciben 2 elementos (reporte_<ID> y pnc_<ID>) significa
    # que existe ya una referencia a dicho reporte en el registro general
    if len(registro_keys) == 2:
        print(f"\n\n\n\tRegistro Reporte ID: {reportes_ids[0]}")
        print(f"\n\n\n\tRegistro General: {registro_gral_pnc}")
        if reportes_ids[0] not in registro_gral_pnc["registro"]:
            return Response(data={
                "Error": "Estructura de reporte_<ID> no valida. El reporte que se esta actualizando no existe en el registro general"
                },
                status=status.HTTP_400_BAD_REQUEST)

    registro_reporte = registro[reportes_ids[0]]
    check_reporte = checkReporte(pncs_ids[0],
                                 registro_reporte,
                                 registro_gral_pnc["registro"],
                                 mode=1)
    if type(check_reporte) is Response:
        return check_reporte

    new_registro_pnc = registro[pncs_ids[0]]
    check_pnc = checkPNC(new_registro_pnc)
    if type(check_pnc) is Response:
        return check_pnc

    return (lastPNCID,
            registro,
            has_reportes_registrados,
            reportes_ids[0],
            pncs_ids[0])


def validacionReportesRegistros(registro_keys,
                                has_reportes_registrados,
                                valid_number_keys):
    # Dado que el registro recibido unicamente puede tener el atributo
    # reportesRegistrados cuando el número de llaves es igual a 3, se considera
    # un error en la estructura cuando una de estas reglas no se cumple, por
    # lo tanto...
    or_registro_len = len(registro_keys) == valid_number_keys or has_reportes_registrados
    and_registro_len = len(registro_keys) == valid_number_keys and has_reportes_registrados
    xor_registro_len = or_registro_len and not and_registro_len
    # El xor evalua si el registro_keys tiene un length de 3 y
    # has_reportes_registrados es falso retornará el response 400
    # ó
    # Si el registro_keys tiene un length distinto a 3 (2) y
    # has_reportes_registrados es verdadero retornará el response 400
    return xor_registro_len


def validacionCantidadReportesPNCs(count_match_rgx_reporte,
                                   count_match_rgx_pnc,
                                   valid_number_reportes,
                                   valid_number_pncs):
    invalid_amount_reportes = count_match_rgx_reporte != valid_number_reportes
    invalid_amount_pncs = count_match_rgx_pnc != valid_number_pncs
    return invalid_amount_reportes or invalid_amount_pncs


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
    check_datos = checkReceivedData(datos)
    if type(check_datos) is Response:
        return check_datos

    lastPNCID, registro = check_datos
    registro_keys = registro.keys()

    if len(registro_keys) < 2 or len(registro_keys) > 4:
        return Response(data={
            "Error": "Estructura de registro no valida. Más elementos de los esperados"
            },
            status=status.HTTP_400_BAD_REQUEST)

    check_registro_keys = checkRegistroKeys(registro_keys)
    if type(check_registro_keys) is Response:
        return check_registro_keys

    (has_reportes_registrados,
     count_match_rgx_reporte,
     count_match_rgx_pnc,
     reportes_ids,
     pncs_ids) = check_registro_keys

    invalid_reportes_registrados = validacionReportesRegistros(registro_keys,
                                                               has_reportes_registrados,
                                                               4)

    valid_number_reportes = 1
    if len(registro_keys) == 4 or len(registro_keys) == 3:
        valid_number_reportes = 2

    invalid_amount_reportes_pncs = validacionCantidadReportesPNCs(count_match_rgx_reporte,
                                                                  count_match_rgx_pnc,
                                                                  valid_number_reportes,
                                                                  1)
    if invalid_reportes_registrados or invalid_amount_reportes_pncs:
        return Response(data={
            "Error": "Estructura de registro no valida. Faltan elementos"
            },
            status=status.HTTP_400_BAD_REQUEST)

    # Si existe reortesRegistrados en el registro recibido
    # (len(registro_keys) == 4) se procede a evaluar su estructura
    if has_reportes_registrados:
        new_reportes_registrados = registro["reportesRegistrados"]
        # TODO: Revisar la funcion checkReporteRegistrados, evaluar que pasa
        #       cuando reportes_ids tiene un ID ya registrado y otro que no.
        check_repo_registro = checkReportesRegistrados(reportes_ids,
                                                       new_reportes_registrados,
                                                       registro_gral_pnc["registro"]["reportesRegistrados"])
        if type(check_repo_registro) is Response:
            return check_repo_registro

    # Si unicamente se reciben 3 elementos (reporte_<ID>, reporte_<ID> y
    # pnc_<ID>) significa que existe ya una referencia para ambos reportes en
    # el registro general
    if len(registro_keys) == 3:
        for reporte_id in reportes_ids:
            if reporte_id not in registro_gral_pnc["registro"]:
                return Response(data={
                    "Error": "Estructura de reporte_<ID> no valida. El reporte que se esta actualizando no existe en el registro general"
                    },
                    status=status.HTTP_400_BAD_REQUEST)
    elif len(registro_keys) == 2:
        # Si unicamente se reciben 2 elementos (reporte_<ID> y pnc_<ID>)
        # significa que existe ya una referencia a dicho reporte en el registro
        # general, y como tal no se modifica el reporte_id
        if reportes_ids[0] not in registro_gral_pnc["registro"]:
            return Response(data={
                "Error": "Estructura de reporte_<ID> no valida. El reporte que se esta actualizando no existe en el registro general"
                },
                status=status.HTTP_400_BAD_REQUEST)

    found_old_reporte = False
    for reporte_id in reportes_ids:
        reporte = registro[reporte_id]
        # TODO: Revisar la funcion checkReporte, evaluar que pasa cuando
        #       reporte no tiene el pnc_id y cuando si lo tiene
        check_reporte = checkReporte(pncs_ids[0],
                                     reporte,
                                     registro_gral_pnc["registro"],
                                     mode=2)
        if type(check_reporte) is Response:
            return check_reporte

        if len(reportes_ids) == 2:
            if check_reporte and found_old_reporte:
                return Response(data={
                    "Error": "Estructura de reporte_<ID> no valida. Ambos reportes tienen el ID del PNC en su linkedPNC"
                    },
                    status=status.HTTP_400_BAD_REQUEST)
            elif check_reporte and not found_old_reporte:
                found_old_reporte = True

    if len(reportes_ids) == 2 and not found_old_reporte:
        return Response(data={
            "Error": "Estructura de reporte_<ID> no valida. Ningun reporte contiene el ID del nuevo PNC"
            },
            status=status.HTTP_400_BAD_REQUEST)
    elif len(reportes_ids) == 1 and found_old_reporte:
        return Response(data={
            "Error": "Estructura de reporte_<ID> no valida. El reporte no tiene registrado el ID del PNC en su linkedPNC"
            },
            status=status.HTTP_400_BAD_REQUEST)

    pnc = registro[pncs_ids[0]]
    check_pnc = checkPNC(pnc)
    if type(check_pnc) is Response:
        return check_pnc

    return (lastPNCID,
            registro,
            has_reportes_registrados,
            reportes_ids,
            pncs_ids[0])
