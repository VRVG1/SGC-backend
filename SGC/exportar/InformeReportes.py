import xlsxwriter

# Datos a presentar
codigo_colores = {
    'verde': 'Entrega a tiempo.',
    'cafe': 'Entrega tarde.',
    'rojo': 'Fecha de entrega superada sin entrega.',
}


class InformeReportes:
    def __init__(self, path, filename):
        self.workbook = xlsxwriter.Workbook(path + filename)
        self.worksheet = None
        self.row = 4
        self.buildFormats()

    def buildFormats(self):
        # Format declaration
        encabezado_tabla = {
            'bold': 1,
            'border': 5,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#D9D9D9'
        }

        a_tiempo = {
            'border': 2,
            'bg_color': '#35BE21',
        }

        destiempo = {
            'border': 2,
            'bg_color': '#B77323'
        }

        no_entregado = {
            'border': 2,
            'bg_color': '#BE2121',
        }

        descripcion = {
            'border': 2,
        }

        descripcion_centrada = {
            'border': 2,
            'align': 'center',
            'valign': 'vcenter',
        }

        fecha = {
            'num_format': 'dd/mm/yy hh:mm AM/PM',
        }
        fecha = {**fecha, **descripcion_centrada}

        # Format Object
        self.headers_format = self.workbook.add_format(encabezado_tabla)
        self.nosubmit_format = self.workbook.add_format(no_entregado)
        self.on_time_format = self.workbook.add_format(a_tiempo)
        self.late_format = self.workbook.add_format(destiempo)
        self.dscp_format = self.workbook.add_format(descripcion)
        self.dscp_cnt_format = self.workbook.add_format(descripcion_centrada)
        self.fecha_format = self.workbook.add_format(fecha)

    def increseRow(self, increment=1):
        self.row += increment

    def resetRowCount(self):
        self.row = 4

    def buildColorsTable(self):
        worksheet = self.worksheet
        worksheet.set_row(self.row - 1, 20)

        # Construyendo tabla de codigo de colores
        # Encabezados
        worksheet.merge_range(f'D{self.row}:E{self.row}',
                              'Estados',
                              self.headers_format)
        worksheet.merge_range(f'F{self.row}:I{self.row}',
                              'Significados',
                              self.headers_format)
        self.increseRow()

        # Cuerpo
        for color, texto in codigo_colores.items():
            print(f'{color}, {texto}')
            if color == 'verde':
                # la celda será de color verde
                color_format = self.on_time_format
            elif color == 'cafe':
                # la celda será de color café
                color_format = self.late_format
            else:
                # la celda será de color rojo
                color_format = self.nosubmit_format

            # Fuciona las celdas en Dx:Ex y agrega un color de fondo del color
            # contenido en color_format
            worksheet.merge_range(f'D{self.row}:E{self.row}',
                                  '',
                                  color_format)
            # Fuciona las celdas en Fx:Gx e inserta el texto descriptivo de la
            # celda de color a su izquierda
            worksheet.merge_range(f'F{self.row}:I{self.row}',
                                  texto,
                                  self.dscp_format)
            self.increseRow()

    def buildMainTableHeaders(self, name):
        worksheet = self.worksheet
        # Construyendo tabla principal
        # Encabezados
        self.increseRow(2)
        # row_codigo = 9
        worksheet.merge_range(f'B{self.row}:L{self.row}',
                              # 'Nombre Profesor',
                              name,
                              self.headers_format)
        self.increseRow()
        # self.row += 1
        worksheet.merge_range(f'B{self.row}:D{self.row}',
                              'Materia',
                              self.headers_format)
        worksheet.write(f'E{self.row}',
                        'Grado',
                        self.headers_format)
        worksheet.write(f'F{self.row}',
                        'Grupo',
                        self.headers_format)
        worksheet.merge_range(f'G{self.row}:I{self.row}',
                              'Nombre del reporte',
                              self.headers_format)
        worksheet.write(f'J{self.row}',
                        'Estado',
                        self.headers_format)
        worksheet.merge_range(f'K{self.row}:L{self.row}',
                              'Fecha Entrega',
                              self.headers_format)
        # Cuerpo
        self.increseRow()

    def newWorksheet(self, name):
        self.resetRowCount()
        self.worksheet = self.workbook.add_worksheet(name)
        self.buildColorsTable()
        self.buildMainTableHeaders(name)

    def addRow(self, cell_text):
        """
        tableRow is a function that simplify the addition of table row in a
        excel file.

        @param cell_text    A list of 6 elements that represent every data that
                            going be in the row cells, the order of strings
                            data need be like:
                                [0] -> Nombre de la materia
                                [1] -> Grado
                                [2] -> Grupo
                                [3] -> Nombre del reporte
                                [4] -> Estado de entrega
                                [5] -> Fecha de entrega
        """
        worksheet = self.worksheet
        worksheet.merge_range(f'B{self.row}:D{self.row}',   # Nombre Materia
                              cell_text[0],
                              self.dscp_format)
        worksheet.write(f'E{self.row}',                     # Grado
                        cell_text[1],
                        self.dscp_cnt_format)
        worksheet.write(f'F{self.row}',                     # Grupo
                        cell_text[2],
                        self.dscp_cnt_format)
        worksheet.merge_range(f'G{self.row}:I{self.row}',   # Nombre Reporte
                              cell_text[3],
                              self.dscp_format)

        if cell_text[4] == 'Entrega a tiempo':              # Estado de entrega
            # El formato de color de fondo será verde
            color_format = self.on_time_format
        elif cell_text[4] == 'Entrega tarde':
            # El formato de color de fondo será café
            color_format = self.late_format
        else:
            # El formato de color de fondo será rojo
            color_format = self.nosubmit_format

        worksheet.write(f'J{self.row}',
                        '',
                        color_format)

        print(type(cell_text[5]))
        print(cell_text[5])
        worksheet.merge_range(f'K{self.row}:L{self.row}',   # Fecha de entrega
                              '',
                              self.dscp_format)
        worksheet.write_datetime(f'K{self.row}',   # Fecha de entrega
                                 cell_text[5],
                                 self.fecha_format)

        self.increseRow()

    def closeWorkbook(self):
        self.workbook.close()
