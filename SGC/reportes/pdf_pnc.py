from fpdf import FPDF

PNC_EJEMPLO = {
    "numeroPNC": 1,
    "folio": "INF001",
    "fechaRegistro": "2023-05-20",
    "especIncumplida": """\
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent ultricies feugiat leo, sit amet porta diam luctus id. Sed aliquam bibendum velit, id scelerisque diam faucibus a. Integer dignissim risus eget accumsan lacinia. Fusce ullamcorper sollicitudin bibendum. Nam ut risus id ante pulvinar volutpat vel quis nisi. Suspendisse ac felis justo. Aenean venenatis laoreet ex, a lacinia leo ultricies non.
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent ultricies feugiat leo
""",
    "accionImplantada": "Adios",
    "isEliminaPNC": True
}

# Texto que va dentro del encabezado de cada página
PAGE_HEADER_DATA = {
        "tecnm": "TECNOLÓGICO NACIONAL DE MÉXICO",
        "itcg": "INSTITUTO TECNOLÓGICO DE CD. GUZMÁN",
        "logo_path": "./static/itcg.png",
        "nombre_del_documento": "Formato para identificación, registro y control de producto no conforme",
        "referencia_de_la_norma": "ISO 9001:2015   8.7",
        "codigo": "ITCG-CA-PG-004-01",
        "revision": '7'
}

# Dict:
# key   ->  Encabezado de columna
# value ->  Key dentro del registro PNC
COLUM_HEADERS = {
        "No.": "numeroPNC",
        "Folio": "folio",
        "Fecha": "fechaRegistro",
        "Especificación Incumplida": "especIncumplida",
        "Acción Implantada": "accionImplantada",
        "No. de RAC": "numeroRAC",
        "Si": "isEliminaPNC",
        "No": "isEliminaPNC",
        "Verifica": "verifica",
        "Libera": "libera"
    }

# Porcentaje del ancho de la hoja que ocupa cada columna
CONTENT_TABLE_COL_WIDTHS = (5,      # 0 No.
                            9,      # 1 Folio
                            9,      # 2 Fecha Entrega
                            18,     # 3 Especificación Incumplida
                            18,     # 4 Acción Implantada
                            9,      # 5 No. de RAC
                            7,      # 6 Elimina PNC: Si
                            7,      # 7 Elimina PNC: No
                            9,      # 8 Verifica
                            9       # 9 Libera
                            )

# Alineación de cada una de las columnas de datos (NO INCLUYE A LOS ENCABEZADOS
# DE ESTAS, TODOS LOS ENCABEZADOS VAN CENTRADOS 'CENTER')
CONTENT_TABLE_TEXT_ALIGN = ("CENTER",   # 0 No.
                            "CENTER",   # 1 Folio
                            "CENTER",   # 2 Fecha Entrega
                            "LEFT",     # 3 Especificación Incumplida
                            "LEFT",     # 4 Acción Implantada
                            "CENTER",   # 5 No. de RAC
                            "CENTER",   # 6 Elimina PNC: Si
                            "CENTER",   # 7 Elimina PNC: No
                            "CENTER",   # 8 Verifica
                            "CENTER"    # 9 Libera
                            )




class PncPDF(FPDF):

    def __init__(self,
                 orientation="landscape",
                 unit="mm",
                 format="letter",
                 font_cache_dir="DEPRECATED"):
        super().__init__(orientation, unit, format, font_cache_dir)
        self.nombre_reporte = ""
        self.fecha_reporte = ""
        self.is_render_table_over = False

    def getCellsData(self):
        table_width = self.epw
        cells_data = {
            "numeroPNC": {
                "w": table_width * CONTENT_TABLE_COL_WIDTHS[0] / 100,
                "align": CONTENT_TABLE_TEXT_ALIGN[0]
            },
            "folio": {
                "w": table_width * CONTENT_TABLE_COL_WIDTHS[1] / 100,
                "align": CONTENT_TABLE_TEXT_ALIGN[1]
            },
            "fechaRegistro": {
                "w": table_width * CONTENT_TABLE_COL_WIDTHS[2] / 100,
                "align": CONTENT_TABLE_TEXT_ALIGN[2]
            },
            "especIncumplida": {
                "w": table_width * CONTENT_TABLE_COL_WIDTHS[3] / 100,
                "align": CONTENT_TABLE_TEXT_ALIGN[3]
            },
            "accionImplantada": {
                "w": table_width * CONTENT_TABLE_COL_WIDTHS[4] / 100,
                "align": CONTENT_TABLE_TEXT_ALIGN[4]
            },
            "numeroRAC": {
                "w": table_width * CONTENT_TABLE_COL_WIDTHS[5] / 100,
                "align": CONTENT_TABLE_TEXT_ALIGN[5]
            },
            "isEliminaPNC": {
                "w": table_width * CONTENT_TABLE_COL_WIDTHS[6] / 100,
                "align": CONTENT_TABLE_TEXT_ALIGN[6]
            },
            "verifica": {
                "w": table_width * CONTENT_TABLE_COL_WIDTHS[8] / 100,
                "align": CONTENT_TABLE_TEXT_ALIGN[8]
            },
            "libera": {
                "w": table_width * CONTENT_TABLE_COL_WIDTHS[9] / 100,
                "align": CONTENT_TABLE_TEXT_ALIGN[9]
            },
        }
        return cells_data

    def header(self):
        self.set_font(family='Helvetica', style='B', size=11)
        row_height_gral = self.font_size * 2
        row_height = row_height_gral
        # ENCABEZADO
        self.cell(w=0,
                  h=row_height,
                  txt=PAGE_HEADER_DATA['tecnm'],
                  border="LTR",
                  align='CENTER')
        self.ln(row_height)
        self.set_font(family='Helvetica', style='', size=11)
        self.cell(w=0,
                  h=row_height,
                  txt=PAGE_HEADER_DATA['itcg'],
                  border="LBR",
                  align='CENTER')
        self.ln(row_height)
    # INFORMACION REPORTE
        # LOGO
        rect_logo_dimensions = 10, row_height * 3.3, 25.01, 23.3
        self.rect(*rect_logo_dimensions)
        self.image(PAGE_HEADER_DATA['logo_path'],
                   *rect_logo_dimensions,
                   keep_aspect_ratio=True)
        # FILA 1
        # row_height = row_height_gral * 1.2

        self.cell(w=rect_logo_dimensions[3],
                  h=row_height,
                  txt="",
                  border=0)
        self.set_font(family='Helvetica', style='B', size=10)
        self.cell(w=52.42,
                  h=row_height,
                  txt="Nombre del documento:",
                  border="",
                  align="RIGHT")
        self.set_font(family='Helvetica', style='', size=10)
        self.cell(w=120,
                  h=row_height,
                  txt=PAGE_HEADER_DATA['nombre_del_documento'],
                  border="R",
                  align="LEFT")
        self.set_font(family='Helvetica', style='B', size=10)
        self.cell(w=17.02,
                  h=row_height,
                  txt="Código: ",
                  border="B",
                  align="RIGHT")
        self.cell(w=0,
                  h=row_height,
                  txt=PAGE_HEADER_DATA['codigo'],
                  border="BR",
                  align="LEFT")
        self.ln(row_height)
        # FILA 2
        self.cell(w=rect_logo_dimensions[3],
                  h=row_height,
                  txt="",
                  border=0)
        self.set_font(family='Helvetica', style='B', size=10)
        self.cell(w=92.42,
                  h=row_height,
                  txt="Referencia de la norma:",
                  border="",
                  align="RIGHT")
        self.set_font(family='Helvetica', style='', size=10)
        self.cell(w=80,
                  h=row_height,
                  txt=PAGE_HEADER_DATA['referencia_de_la_norma'],
                  border="R",
                  align="LEFT")
        self.set_font(family='Helvetica', style='B', size=10)
        self.cell(w=19.52,
                  h=row_height,
                  txt="Revisión: ",
                  border="B",
                  align="RIGHT")
        self.set_font(family='Helvetica', style='', size=10)
        self.cell(w=0,
                  h=row_height,
                  txt=PAGE_HEADER_DATA['revision'],
                  border="BR",
                  align="LEFT")
        self.ln(row_height)
        # FILA 3
        self.cell(w=rect_logo_dimensions[3],
                  h=row_height,
                  txt="",
                  border=0)
        self.cell(w=172.42,
                  h=row_height,
                  txt="",
                  border="BR",
                  align="RIGHT")
        self.cell(w=0,
                  h=row_height,
                  txt=f"Pág. {self.page_no()} de {{nb}}",
                  border="BR",
                  align="LEFT")
        self.ln(row_height * 2)

        if not self.is_render_table_over:
            self.tableHeader()

    def footer(self):
        self.set_y(-15)
        row_height = self.font_size * 2
        self.set_font(family='Helvetica', style='', size=8)
        self.cell(w=self.epw / 2,
                  h=row_height,
                  txt=PAGE_HEADER_DATA['codigo'],
                  border=0,
                  align="LEFT")
        self.cell(w=self.epw / 2,
                  h=row_height,
                  txt=f"REV. {PAGE_HEADER_DATA['revision']}",
                  border=0,
                  align="RIGHT")

    def tableHeader(self):
        self.set_font(family="Helvetica", style="B", size=10)
        gral_row_height = self.font_size
        row_height = gral_row_height * 2
        table_width = self.epw
        self.cell(w=0,
                  h=row_height,
                  txt=f"Productos No Conformes en el '{self.nombre_reporte}' ({self.fecha_reporte})",
                  border=1,
                  align="CENTER")
        self.ln(row_height)
        row_height = gral_row_height * 1.5
        cells_data = self.getCellsData()
        column_header_keys = list(COLUM_HEADERS.keys())
        for key in column_header_keys:
            width = cells_data[COLUM_HEADERS[key]]['w']
            # Dado que se esta imprimiendo los encabezados de cada columna
            # Primero se imprimen aquellos encabezados que van en primera fila
            # Por lo que si key es 'Si' o 'No' le corresponde al encabezado
            # 'Elimina PNC'
            if key == "Si":
                width = width * 2
                text = "Elimina PNC"
                # El encabezado Elimina PNC solo utiliza 1 fila (size=1.5)
                row_height = gral_row_height * 1.5
            elif key == "No":
                continue
            else:
                text = key
                # Los demás encabezados utilizan 2 filas (size=1.5 * 2)
                row_height = gral_row_height * 3

            self.cell(w=width,
                      h=row_height,
                      txt=text,
                      border=1,
                      align="CENTER")

        row_height = gral_row_height * 1.5
        self.ln(row_height)
        self.cell(w=table_width * 0.68,
                  h=row_height,
                  txt="",
                  border=0,
                  align="CENTER")
        self.cell(w=table_width * 0.07,
                  h=row_height,
                  txt="Si",
                  border=1,
                  align="CENTER")
        self.cell(w=table_width * 0.07,
                  h=row_height,
                  txt="No",
                  border=1,
                  align="CENTER")
        self.ln(row_height)

    def tableRow(self, pnc):
        self.set_font(family="Helvetica", style='', size=10)

        gral_row_height = self.font_size
        row_height = gral_row_height * 2

        cells_data = self.getCellsData()
        row_height_lines = 1
        lines_in_row = []
        text_in_rows = []
        column_header_keys = list(COLUM_HEADERS.keys())
        for key in column_header_keys:
            if key == "No. de RAC" or key == "Verifica" or key == "Libera":
                text = ""
            elif key == "No.":
                text = str(pnc[COLUM_HEADERS[key]])
            elif key == "Si":
                text = "X" if pnc[COLUM_HEADERS[key]] else ""
            elif key == "No":
                text = "X" if not pnc[COLUM_HEADERS[key]] else ""
            else:
                text = pnc[COLUM_HEADERS[key]]
            width = cells_data[COLUM_HEADERS[key]]["w"]
            align = cells_data[COLUM_HEADERS[key]]["align"]
            output = self.multi_cell(w=width,
                                     h=row_height,
                                     txt=text,
                                     border=1,
                                     align=align,
                                     dry_run=True,
                                     output=("LINES"))
            text_in_rows.append(output)
            lines_in_row.append(len(output))
            if len(output) > row_height_lines:
                row_height_lines = len(output)

        for line in range(row_height_lines):
            if line == 0:
                border = "LTR"
            elif line < row_height_lines - 1:
                border = "LR"
            else:
                border = "LBR"
                row_height = gral_row_height * 3

            for col_idx in range(len(COLUM_HEADERS)):
                if lines_in_row[col_idx] > line:
                    text = text_in_rows[col_idx][line]
                else:
                    text = '\n'
                width = cells_data[COLUM_HEADERS[column_header_keys[col_idx]]]["w"]
                align = cells_data[COLUM_HEADERS[column_header_keys[col_idx]]]["align"]
                self.cell(w=width,
                          h=row_height,
                          txt=text,
                          border=border,
                          align=align)
            self.ln(row_height)
        # Desactiva el renderizado del header de la tabla
        self.is_render_table_over = True

    def firmasBody(self):
        row_height = self.font_size
        self.set_font(family='Helvetica', style='', size=10)
        self.cell(w=self.epw / 3,
                  h=row_height,
                  txt="Elaboró",
                  border=0,
                  align="CENTER")
        self.cell(w=self.epw / 3,
                  h=row_height,
                  txt="Valida",
                  border=0,
                  align="CENTER")
        self.cell(w=self.epw / 3,
                  h=row_height,
                  txt="Vo. Bo.",
                  border=0,
                  align="CENTER")
        self.ln(row_height)
        self.ln(row_height * 4)
        self.cell(w=self.epw / 3,
                  h=row_height,
                  txt="Nombre y Firma del/de la jefe(a) de Área",
                  border=0,
                  align="CENTER")
        self.cell(w=self.epw / 3,
                  h=row_height,
                  txt="Nombre y Firma del/la Subdirector(a) de Área",
                  border=0,
                  align="CENTER")
        self.cell(w=self.epw / 3,
                  h=row_height,
                  txt="Nombre y Firma del/de la RD",
                  border=0,
                  align="CENTER")

    def printReporte(self,
                     registro_gral,
                     linked_pncs,
                     nombre_reporte="Reporte 1",
                     fecha_reporte="2023-05-21"):
        self.is_render_table_over = False
        self.nombre_reporte = nombre_reporte
        self.fecha_reporte = fecha_reporte
        self.add_page()
        for pnc in linked_pncs:
            self.is_render_table_over = False
            self.tableRow(registro_gral[pnc])
        self.ln(self.font_size * 3)
        self.firmasBody()


# pdf = PncPDF()
# pdf.printReporte()
# pdf.output('./pnc-pdf-letter.pdf')
