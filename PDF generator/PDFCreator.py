from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from num2words import num2words


def numero_a_moneda_en_letras(cantidad):
    entero = int(cantidad)
    decimal = round((cantidad - entero) * 100)
    letras = num2words(entero, lang='es').upper()
    return f"{letras} PESOS CON {decimal:02}/100 M.N."


# Documento base
doc = SimpleDocTemplate("factura_cfdi.pdf", pagesize=letter, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
elements = []
styles = getSampleStyleSheet()



# --- Datos del emisor y receptor ---
emisor_info = [
    ["Emisor", "CONSTRUCARR CONCRETOS SA DE CV"],
    ["RFC", "CCO190228A80"],
    ["Régimen Fiscal", "601 - General de Ley Personas Morales"],
    ["Lugar de expedición", "44660"],
    ["Fecha de emisión", "2025-06-07T12:39:24"]
]
receptor_info = [
    ["Receptor", "CAMICH LERMA-CHAPALA"],
    ["RFC", "CLE230712B31"],
    ["Uso CFDI", "G03 - Gastos en general"],
    ["Domicilio fiscal", "58100"],
    ["Régimen Fiscal", "601 - General de Ley Personas Morales"]
]


# Crear tablas individuales para emisor y receptor
emisor_table = Table(emisor_info, colWidths=[80, 200])
receptor_table = Table(receptor_info, colWidths=[80, 200])

# Estilo opcional para ambas
for t in [emisor_table, receptor_table]:
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

# Combinar ambas tablas en una sola fila
datos_combinados = Table(
    [[emisor_table, receptor_table]],
    colWidths=[270, 270]
)

datos_combinados.setStyle(TableStyle([
    ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
]))


elements.append(datos_combinados)
elements.append(Spacer(1, 12))

#for title, data in [("Datos del Emisor", emisor_info), ("Datos del Receptor", receptor_info)]:
#    elements.append(Paragraph(f"<b>{title}</b>", styles['Heading4']))
#    table = Table(data, colWidths=[120, 350])
#    table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "LEFT")]))
#    elements.append(table)
#    elements.append(Spacer(1, 8))

# --- Tabla de conceptos ---
elements.append(Paragraph("<b>Conceptos</b>", styles['Heading4']))

conceptos = [
    ["ClaveProdServ", "Cantidad", "Unidad", "Descripción", "Valor Unitario", "Importe"],
    ["30111505", "4.00000", "MTQ", "Suministro de concreto hidráulico Fc? 150", "$1872.16", "$7488.62"],
    ["30111505", "1.00000", "MTQ", "Servicio mínimo de vacío", "$270.00", "$270.00"]
]

table = Table(conceptos, colWidths=[70, 60, 60, 200, 70, 70])
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ("ALIGN", (1, 1), (-1, -1), "CENTER")
]))
elements.append(table)
elements.append(Spacer(1, 10))

# --- Totales ---
totales = [
    ["Subtotal:", "$7758.62"],
    ["Descuento:", "$0.00"],
    ["IVA (16%):", "$1241.38"],
    ["Total:", "$9000.00"],
    ["Importe en letra:", "NUEVE MIL PESOS CON 00/100 M.N"],
    ["Forma de pago:", "03 - Transferencia electrónica de fondos"],
    ["Método de pago:", "PUE - Pago en una sola exhibición"],
    ["Moneda:", "MXN"]
]
table = Table(totales, colWidths=[150, 250])
table.setStyle(TableStyle([
    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ("FONTSIZE", (0, 0), (-1, -1), 10),
]))
elements.append(Paragraph("<b>Totales y forma de pago</b>", styles['Heading4']))
elements.append(table)
elements.append(Spacer(1, 10))

# --- Datos fiscales adicionales ---
elements.append(Paragraph("<b>Datos fiscales</b>", styles['Heading4']))
fiscales = [
    ["Folio Fiscal:", "A6388A26-F696-4B34-AF02-A3A19C7F9574"],
    ["Certificado SAT:", "00001000000709182898"],
    ["Certificado Digital:", "00001000000714169522"],
    ["Versión CFDI:", "4.0"]
]
table = Table(fiscales, colWidths=[150, 350])
elements.append(table)
elements.append(Spacer(1, 10))

# --- Sello Digital ---
sello = ("Sello Digital (CFDI): VNJu9RJGebQ/jBh17j0W0l4YjErEX1eJ47Od... (truncado por espacio)")
elements.append(Paragraph(sello, styles["Normal"]))
elements.append(Spacer(1, 12))

elements.append(Paragraph("Este documento es una representación impresa de un CFDI. La reproducción no autorizada constituye un delito.", styles["Italic"]))

# --- Construcción del PDF ---
doc.build(elements)
