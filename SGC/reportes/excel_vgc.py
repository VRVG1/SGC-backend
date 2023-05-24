import xlsxwriter

SHEET_HEADER_DATA = {
    "tecnm": "T E C N O L O G I C O     N A C I O N A L    D E    M É X I C O",
    "itcg": "I N S T I T U T O    T E C N O L Ó G I C O    D E    C D.    G U Z M Á N",
    "logo": "./static/itcg.png",
    "nombre_documento": "Formato para la Verificación de la Gestión del Curso",
    "referencia_iso": "ISO 9001:2015 9.1.1, 9.1.2",
    "codigo": "ITCG-AC-PO-004-08",
    "revision": "0",
    "pagina": "Página 1 de 1",
    "encabezado": "VERIFICACIÓN DE GESTIÓN DEL CURSO"
}

ROWS_HEIGHTS = [
    #         Idx FILA
    15.75,  # [0] FILA 1
    15,     # [1] FILA 2
    14.25,  # [2] FILA 3
    15,     # [3] FILA 4
    24,     # [4] FILA 5
    36,     # [5] FILA 6
    15,     # [6] FILA 7
    15,     # [7] FILA 8
    15,     # [8] FILA 9
    120.75  # [9] FILA 10
]

COLUMNS_WIDTHS = [
    #         idx    COLUMNA
    5.43,   # [0]   COLUMNA A
    39.71,  # [1]   COLUMNA B
    15.86,  # [2]   COLUMNA C
    11.86,  # [3]   COLUMNA D
    10.71,  # [4]   COLUMNA E
    10.71,  # [5]   COLUMNA F
    11.57,  # [6]   COLUMNA G
    10.71,  # [7]   COLUMNA H
    12.14,  # [8]   COLUMNA I
    7.43,   # [9]   COLUMNA J
    7.43,   # [10]  COLUMNA K
    11.00,  # [11]  COLUMNA L
    8.29,   # [12]  COLUMNA M
    13.57,  # [13]  COLUMNA N
    10.71,  # [14]  COLUMNA O
    12.29,  # [15]  COLUMNA P
    10.71,  # [16]  COLUMNA Q
    26.43   # [17]  COLUMNA R
]


class VGCExcel:
    def __init__(self, fp, academia):
        self.row_idx = 11
        self.academia = academia
        self.workbook = xlsxwriter.Workbook(fp)
        self.worksheet = self.workbook.add_worksheet('FORMATO')

        # Ajusta la altura de todas las filas a su tamaño especificado en
        # ROWS_HEIGHTS
        for idx, height in enumerate(ROWS_HEIGHTS):
            self.worksheet.set_row(idx, height)
        # Ajusta el ancho de todas las columnas a su tamaño especificado en
        # COLUMNS_WIDTHS
        for idx, width in enumerate(COLUMNS_WIDTHS):
            self.worksheet.set_column(idx, idx, width)
        #
        #
        #                           Formatos
        #
        #
        self.cell_align_center_all = self.workbook.add_format({
            'align': 'center',
            'valign': 'vcenter'
            })
        self.bold_center_border_format = self.workbook.add_format({
            'bold': True,
            'font_size': 11,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
            })
        self.bold_left_border_format = self.workbook.add_format({
            'bold': True,
            'font_size': 11,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1
            })
        self.header_normal_center_bottom_format = self.workbook.add_format({
            'bold': False,
            'italic': False,
            'font_size': 16,
            'align': 'center',
            'valign': 'bottom'
            })
        self.normal_center_format = self.workbook.add_format({
            'bold': False,
            'italic': False,
            'font_size': 11,
            'align': 'center',
            'valign': 'vcenter',
            })
        self.normal_center_bottom_format = self.workbook.add_format({
            'bold': False,
            'italic': False,
            'font_size': 11,
            'align': 'center',
            'valign': 'bottom'
            })
        self.normal_right_bottom_format = self.workbook.add_format({
            'bold': False,
            'italic': False,
            'font_size': 11,
            'align': 'right',
            'valign': 'bottom'
            })

        self.border_bottom_format = self.workbook.add_format({
            'font_size': 11,
            'align': 'center',
            'valign': 'bottom',
            'bottom': 1
            })

        # Fuentes del encabezado tabla
        self.font_7 = self.workbook.add_format({
            'font_size': 7,
            'align': 'center',
            'valign': 'vcenter',
            'rotation': 90,
            'text_wrap': True,
            'border': 1
            })
        self.font_9 = self.workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'border': 1

            })
        self.font_10 = self.workbook.add_format({
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'border': 1

            })
        self.font_11 = self.workbook.add_format({
            'font_size': 11,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'border': 1

            })
        self.font_12 = self.workbook.add_format({
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'border': 1

            })

        # Formatos para las celdas de informacion
        self.font_11_left_bottom = self.workbook.add_format({
            "font_size": 11,
            "align": "left",
            "valign": "bottom",
            'border': 1
            })
        self.font_11_right_bottom = self.workbook.add_format({
            "font_size": 11,
            "align": "right",
            "valign": "bottom",
            'border': 1
            })
        self.font_11_center_bottom = self.workbook.add_format({
            "font_size": 11,
            "align": "center",
            "valign": "bottom",
            'border': 1
            })
        self.font_11_center_bottom_no_border = self.workbook.add_format({
            "font_size": 11,
            "align": "center",
            "valign": "bottom",
            })

    def buildSheetHeader(self):
        #
        #
        #               CONSTRUCCIÓN DEL ENCABEZADO DE LA HOJA
        #
        #
        self.worksheet.merge_range('D1:M1', SHEET_HEADER_DATA['tecnm'], self.bold_center_border_format)
        self.worksheet.write_blank('N1', None, self.bold_center_border_format)
        self.worksheet.merge_range('D2:M2', SHEET_HEADER_DATA['itcg'], self.bold_center_border_format)
        self.worksheet.write_blank('N2', None, self.bold_center_border_format)
        self.worksheet.merge_range('D3:E5', None, self.bold_center_border_format)
        self.worksheet.merge_range('B3:B5', None, None)
        self.worksheet.insert_image('D3', SHEET_HEADER_DATA['logo'], {
            'x_offset': 85,
            'y_offset': 6,
            'x_scale': 0.089,
            'y_scale': 0.089
            })
        self.worksheet.merge_range('F3:L5', None, self.bold_center_border_format)
        self.worksheet.write_rich_string('F3',
                                         self.bold_center_border_format,
                                         'Nombre del Documento: ',
                                         self.normal_center_format,
                                         f"{SHEET_HEADER_DATA['nombre_documento']}\n",
                                         self.bold_center_border_format,
                                         'Referencia de la Norma: ',
                                         self.normal_center_format,
                                         SHEET_HEADER_DATA['referencia_iso'],
                                         self.cell_align_center_all)
        self.worksheet.merge_range('M3:N3', f"Código: {SHEET_HEADER_DATA['codigo']}", self.bold_left_border_format)
        self.worksheet.merge_range('M4:N4', f"Revisión: {SHEET_HEADER_DATA['revision']}", self.bold_left_border_format)
        self.worksheet.merge_range('M5:N5', SHEET_HEADER_DATA['pagina'], self.bold_left_border_format)
        self.worksheet.merge_range('A6:R6', SHEET_HEADER_DATA['encabezado'], self.header_normal_center_bottom_format)
        self.worksheet.write('B8', "SEGUIMIENTO No.", self.normal_right_bottom_format)
        self.worksheet.write_blank('C8', None, self.border_bottom_format)
        self.worksheet.write('D8', "SEMANA DEL")
        self.worksheet.write_blank('E8', None, self.border_bottom_format)
        self.worksheet.merge_range('H8:I8', "ACADEMIA", self.normal_center_bottom_format)
        self.worksheet.merge_range('J8:L8', self.academia, self.border_bottom_format)

    def buildInfoTableHeader(self):
        #
        #
        #               CONSTRUCCIÓN DE LA TABLA DE INFORMACIÓN
        #
        #
        self.worksheet.write('A10', "No.", self.font_10)
        self.worksheet.merge_range('B10:C10', "DOCENTE", self.font_11)
        self.worksheet.merge_range('D10:F10', "ASIGNATURA", self.font_11)
        self.worksheet.write('G10', "GRADO Y GRUPO", self.font_11)
        self.worksheet.write('H10', "TEMA", self.font_11)
        self.worksheet.write('I10', "SEMANA PROGRAMADA", self.font_10)
        self.worksheet.write('J10', "VERIFICACIÓN", self.font_10)
        self.worksheet.write('K10', "REGISTRÓ CALIFICACIONES EN MINDBOX Y REALIZA LA RETROALIMENTACIÓN CORRESPONDIENTE", self.font_7)
        self.worksheet.write('L10', "% DE REPROBACIÓN", self.font_9)
        self.worksheet.write('M10', "CUMPLE CON LOS CRITERIOS DE EVALUACIÓN ESTABLECIDOS EN LA INSTRUMENTACIÓN DIDÁCTICA", self.font_7)
        self.worksheet.merge_range('N10:P10', "OBSERVACIONES", self.font_12)
        self.worksheet.merge_range('Q10:R10', "FIRMA JEFE(A) DE GRUPO", self.font_12)

    def addTableRowInfo(self, reporte):
        # Todas las filas de información mediran 45
        print(f"Row Idx: {self.row_idx}")
        self.worksheet.set_row(self.row_idx - 1, 45)

        self.worksheet.write(f'A{self.row_idx}',
                             reporte['numeroReporte'],
                             self.font_11_right_bottom)
        self.worksheet.merge_range(f'B{self.row_idx}:C{self.row_idx}',
                                   reporte["nombreProfesor"],
                                   self.font_11_center_bottom)
        self.worksheet.merge_range(f'D{self.row_idx}:F{self.row_idx}',
                                   reporte["asignatura"],
                                   self.font_11_center_bottom)
        self.worksheet.write(f'G{self.row_idx}',
                             reporte["GradoGrupo"],
                             self.font_11_left_bottom)
        self.worksheet.write(f'H{self.row_idx}',
                             reporte["tema"],
                             self.font_11_left_bottom)
        self.worksheet.write(f'I{self.row_idx}',
                             reporte["semanaProgramada"],
                             self.font_11_left_bottom)
        self.worksheet.write(f'J{self.row_idx}',
                             "SI" if reporte["verificacion"] else "NO",
                             self.font_11_left_bottom)
        self.worksheet.write(f'K{self.row_idx}',
                             "SI" if reporte["RCMRRC"] else "NO",
                             self.font_11_left_bottom)
        self.worksheet.write(f'L{self.row_idx}',
                             reporte["indReprobacion"],
                             self.font_11_left_bottom)
        self.worksheet.write(f'M{self.row_idx}',
                             "SI" if reporte["CCEEID"] else "NO",
                             self.font_11_left_bottom)
        self.worksheet.merge_range(f'N{self.row_idx}:P{self.row_idx}',
                                   reporte["observaciones"],
                                   self.font_11_left_bottom)
        self.worksheet.merge_range(f'Q{self.row_idx}:R{self.row_idx}',
                                   "",
                                   self.font_11_center_bottom)

    def buildSheetFooter(self):
        self.row_idx = self.row_idx + 2
        FOOTER_ROWS_HEIGHTS = [
            15.75,  # [0] FILA 1
            15,     # [1] FILA 2
            15      # [2] FILA 3
        ]
        # Se ajustan el alto de las filas que conformaran el pie de la hoja
        for idx in range(3):
            self.worksheet.set_row(self.row_idx + idx,
                                   FOOTER_ROWS_HEIGHTS[idx])

        self.worksheet.merge_range(f'B{self.row_idx}:C{self.row_idx}',
                                   "JEFE(A) DEPTO. ACADÉMICO",
                                   self.font_11_center_bottom_no_border)
        self.worksheet.merge_range(f'I{self.row_idx}:K{self.row_idx}',
                                   "JEFE(A) PROYECTOS DE DOCENCIA",
                                   self.font_11_center_bottom_no_border)
        self.worksheet.merge_range(f'B{self.row_idx + 2}:C{self.row_idx + 2}',
                                   None,
                                   self.border_bottom_format)
        self.worksheet.merge_range(f'H{self.row_idx + 2}:L{self.row_idx + 2}',
                                   None,
                                   self.border_bottom_format)

    def buildExcel(self, registro):
        self.buildSheetHeader()
        self.buildInfoTableHeader()
        for reporte in registro:
            self.addTableRowInfo(reporte)
            self.row_idx = self.row_idx + 1
        self.buildSheetFooter()
        self.workbook.close()


registro = [
    {
        "numeroReporte": 1,
        "nombreProfesor": "ISIC_01",
        "asignatura": "Fundamentos de Programación",
        "GradoGrupo": "X1B",
        "tema": "Fundamentos de Programación - Grupo: B - Unidad: 2 - ISIC_01",
        "semanaProgramada": "2023-04-25",
        "verificacion": True,
        "RCMRRC": True,
        "indReprobacion": 19,
        "CCEEID": False,
        "observaciones": "Segundo reporte\n\n\nModificado el segundo reporte\n\n\nPRUEBA!!!"
    }
]
# vgc_excel = VGCExcel('./vgc_prueba.xlsx',
#                      'Ingeniería en Sistemas Computacionales')
# vgc_excel.buildExcel(registro)
