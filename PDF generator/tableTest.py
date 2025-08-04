from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

doc = SimpleDocTemplate("tabla_emisor_receptor.pdf", pagesize=letter)

estilo_interna = TableStyle([
    ('FONTSIZE', (0,0), (-1,-1), 10),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ('TOPPADDING', (0,0), (-1,-1), 2),
])
# Subtabla Emisor
tabla_emisor = Table([
    ["Nombre:", "Camich"],
    ["Régimen fiscal:", "G03"],
    ["Domicilio:", "58100"]
], colWidths=[80, 150])
tabla_emisor.setStyle(estilo_interna)

# Subtabla Receptor
tabla_receptor = Table([
    ["Nombre:", "Autopartes"],
    ["CFDI:", "Relación"]
], colWidths=[80, 150])
tabla_receptor.setStyle(estilo_interna)

# Tabla principal con encabezados + subtables
tabla_final = Table([
    ["Emisor", "Receptor"],
    [tabla_emisor, tabla_receptor]
], colWidths=[230, 230])

estilo_externa = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0057FF")),  # Encabezados azul
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ('VALIGN', (0, 1), (-1, -1), 'TOP'),
    ('BOX', (0,0), (-1,-1), 1, colors.black),
    ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
])

tabla_final.setStyle(estilo_externa)

doc.build([tabla_final])
