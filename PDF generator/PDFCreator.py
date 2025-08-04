from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether
from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from num2words import num2words
import qrcode


def numero_a_moneda_en_letras(cantidad):
    entero = int(cantidad)
    decimal = round((cantidad - entero) * 100)
    letras = num2words(entero, lang='es').upper()
    return f"{letras} PESOS CON {decimal:02}/100 M.N."

def addStyle ( data, processed_data, style):
    for row in data:
        processed_row = []
        for cell in row:
            if cell:
                processed_row.append(Paragraph(cell, style))
            else:
                processed_row.append('')
        processed_data.append(processed_row)


# Documento base
doc = SimpleDocTemplate("factura_cfdi.pdf", pagesize=letter, rightMargin=10*mm, leftMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
elements = []
styles = getSampleStyleSheet()

azul_marino = Color(0.0, 87/255, 1)  # Azul marino oscuro
estilo_producto = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4382ff")),  # Encabezados azul
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ('VALIGN', (0, 1), (-1, -1), 'TOP'),
    ('BOX', (0,0), (-1,-1), 1, colors.black),
    ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
])

estilo_interna = TableStyle([
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ('TOPPADDING', (0,0), (-1,-1), 0),
])

estilo_externa = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4382ff")),  # Encabezados azul
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ('VALIGN', (0, 1), (-1, -1), 'TOP'),
    ('BOX', (0,0), (-1,-1), 1, colors.white),
    ('INNERGRID', (0,0), (-1,-1), 0.5, colors.white),
])

emisor_data =[
    ["Nombre:", "Camich"],
    ["RFC:", "HPLC010203ABC"],
    ["Regimen Fiscal:", "601"],
    ["No. certificado digital:", "000100050000064"],
    ["Folio Fiscal", "b9b7qerdfgajfhj5d40hjy"]
]

ancho_columna = 120

emisor_procesado = []
general_style = ParagraphStyle('SmallStyle', fontSize = 10, leading = 12)
addStyle(emisor_data, emisor_procesado, general_style)

tabla_emisor = Table(emisor_procesado, colWidths=[ancho_columna, 270-ancho_columna])
tabla_emisor.setStyle(estilo_interna)

documento_data = [  
    ["Serial:", "SAL-41578"],
    ["Fecha de emisión:", "2025-04-25"],
    ["Lugar de emisión:", "58100"],
    ["Tipo de comprobante:", "Ingreso"]
]

documento_procesado = []
addStyle(documento_data, documento_procesado, general_style)

tabla_documento = Table(documento_procesado, colWidths=[ancho_columna, 270-ancho_columna])
tabla_documento.setStyle(estilo_interna)

tabla1 = Table([
    ["Emisor", "CFDI Ingreso"],
    [tabla_emisor, tabla_documento]
], colWidths=[270, 270])
tabla1.setStyle(estilo_externa)


# 2. Receptor / Folio Fiscal
receptor_data =[
    ["Nombre:", "Camich Lerma"],
    ["RFC:", "CLA1654979711"]
]


receptor_procesado = []
addStyle(receptor_data, receptor_procesado, general_style)
tabla_receptor = Table(receptor_procesado, colWidths=[ancho_columna, 270-ancho_columna])
tabla_receptor.setStyle(estilo_interna)


folio_data =[
    ["Domicilio fiscal:", "58100"],
    ["Regimen fiscal:", "601 - General de las personas morales"],
    ["Uso CFDI:", "G03 - Gastos en general"]
]

folio_procesado = []
addStyle(folio_data, folio_procesado, general_style)
tabla_folio = Table(folio_procesado, colWidths=[ancho_columna, 270-ancho_columna])
tabla_folio.setStyle(estilo_interna)


tabla2 = Table([
    ["Receptor",""],
    [tabla_receptor, tabla_folio]
], colWidths=[270, 270])
tabla2.setStyle(estilo_externa)

# 3. Producto (una sola celda que puedes expandir luego)


tabla3 = Table([
    ["ClProdServ", "NoIdent", "Cantidad", "Clv. Unidad", "Unidad", "Descripción", "Valor Unitario", "Descuento", "Importe"],
    ["261111707", "001001", "4", "H87", " ","Acumulador", "2599.14", "0", "10396.56"],
    ["261111707", "001001", "4", "H87", " ","Acumulador", "2599.14", "0", "10396.56"],
    ["261111707", "001001", "4", "H87", " ","Acumulador", "2599.14", "0", "10396.56"]
], colWidths=[50, 35, 40, 50, 30, 175, 60, 50, 60])

tabla3.setStyle(estilo_producto)


# Importe en letras
importe_letra = Paragraph("  Importe en letra: " + numero_a_moneda_en_letras(12060.01), 
    ParagraphStyle(
        name="CenteredTemp",
        parent=general_style,
        alignment=TA_CENTER,
        fontSize= 10
    )
)


# 4. Forma de pago / Subtotal
pago_data =[
    ["Forma pago:", "04 - tarjeta de crédito"],
    ["Método de pago:", "PUE - pago en una sola exibición"],
    ["Condición de pago:", "Contado (2)"],
    ["Version comprobante:", "4.0"],
    ["Moneda:", "MXN"],
    ["Tipo de cambio:", "1"]
]

pago_procesado = []
addStyle(pago_data, pago_procesado, general_style)
tabla_pago = Table(pago_procesado, colWidths=[110, 160])
tabla_pago.setStyle(estilo_interna)

valor_data =[
    ["Subtotal:", "10396.56"],
    ["Descuento:", "0.00"],
    ["IEPS:", "0"],
    ["IVA:", "1663.45"],
    ["Retenciones ISR:", "0"],
    ["Retenciones IVA:", "0"],
    ["Total", "12060.01"]
]

valor_procesado = []
addStyle(valor_data, valor_procesado, general_style)
tabla_valor = Table(valor_procesado, colWidths=[150, 120])
tabla_valor.setStyle(estilo_interna)


tabla4 = Table([
    ["", ""],
    [tabla_pago, tabla_valor]
], colWidths=[270, 270])
tabla4.setStyle(estilo_externa)

# Crear imagen QR
qr = qrcode.make("https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx")
qr.save("qr.png")

# Cargar imagen
qr_img = Image("qr.png", width=30*mm, height=30*mm)


# Datos de la tabla
pie_data = [
    ['RFC proveedor de certificación:', 'Número de certificado SAT:', 'Fecha y hora de certificación:'],
    ['MSE090205D9A', '00001000000711327115', '16 Ene. 2025 - 16:28:47'],
    ['Cadena original del timbre:', 'Sello digital del SAT:', 'Sello digital del CFDI:'],
    ['||1.1|0be9b385-3485-4a9c-9162-f2417af2ab04|2025-01-16T16:28:47|MSE090205D9A|Fw1ssbnn79XuHmxy', 'NHBSq8CkwZf+wiCBW9Sj6QQ4x4XO6FTwxyu39POve', 'Fw1ssbnn79XuHmxyLwQuqpqgjBt8pWUHAy7n6d2Ls5']
]

small_style = ParagraphStyle('SmallStyle', fontSize=6, leading=7)
# Convertir datos a párrafos
processed_data = []
addStyle( pie_data, processed_data, small_style)

# Tabla final con datos extras
pie = Table(processed_data, colWidths=[55*mm, 55*mm, 55*mm])
estilo_pie = TableStyle([
    ('BOX', (0, 0), (-1, -1), 2, colors.HexColor("#A5A5A5")),
    ('INNERGRID', (0, 0), (-1, -1), 1, colors.HexColor("#A5A5A5")),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ('TOPPADDING', (0, 0), (-1, -1), 1),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
])

pie.setStyle(estilo_pie)

# Layout horizontal: imagen + tabla (anchos corregidos)
layout_data = [[qr_img, pie]]
datos_extras = Table(layout_data, colWidths=[30*mm, 165*mm])  # Total: 195mm
datos_extras.setStyle(TableStyle([
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('ALIGN', (0, 0), (0, 0), 'LEFT'),      # Alinear imagen a la izquierda
    ('ALIGN', (1, 0), (1, 0), 'LEFT'),      # Alinear tabla a la izquierda
    ('LEFTPADDING', (0, 0), (-1, -1), 0),   # Sin padding izquierdo
    ('RIGHTPADDING', (0, 0), (-1, -1), 0),  # Sin padding derecho  
    ('TOPPADDING', (0, 0), (-1, -1), 0),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
]))

mini_style = ParagraphStyle(
    name='Mini',
    parent=styles['Normal'],
    fontSize=6,
    leading=6.5,  # Espaciado entre líneas
    alignment=TA_CENTER  # Horizontal center
)

# Pie de página
footer = Paragraph("Este documento es una representación impresa de un CFDI versión 4.0", mini_style)

# Agregar elementos con espacio
elements.extend([
    tabla1, Spacer(1, 10),
    tabla2, Spacer(1, 10),
    tabla3, Spacer(1, 10),
    importe_letra, Spacer(1,10),
    tabla4, Spacer(1, 10),
    datos_extras, Spacer(1, 1),
    footer
])

# Construir PDF
doc.build(elements)


