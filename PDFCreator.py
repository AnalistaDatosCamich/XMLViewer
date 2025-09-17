from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether
from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.utils import ImageReader
from io import BytesIO
from num2words import num2words
import qrcode
import sqlite3 

def obtener_factura_por_uuid(uuid, db_path = "mi_base.db"):
    """"Obtiene datos de una factura específica por su UUID"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM facturas WHERE UUID1 = ?", (uuid,))
    factura = cursor.fetchone()

    if factura:
        columns = [description[0] for description in cursor.description]
        factura_dict = dict(zip(columns, factura))
    else:
        factura_dict = None

    conn.close()
    return factura_dict


def obtener_productos_por_uuid(uuid, db_path = "mi_base.db"):
    """"Obtiene datos de una factura específica por UUID"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM productos WHERE uuid_factura = ?", (uuid,))
    productos = cursor.fetchall()

    #Convertir a lista de diccionario
    columns = [description[0] for description in cursor.description]
    productos_list = [dict(zip(columns, producto)) for producto in productos]

    conn.close()
    return productos_list

def crear_pdf_factura(uuid, db_path = "mi_base.db"):
    """Crea PDF con datos reales de la base de datos"""
    factura = obtener_factura_por_uuid(uuid, db_path)
    productos = obtener_productos_por_uuid(uuid, db_path)
    
    if not factura:
        print(f"No se encontró factura con UUID: {uuid}")
        return
    
    if not productos:
        print(f"No se encontraron productos para UUID: {uuid}")
        return
    
    # Crear el documento PDF
    doc = SimpleDocTemplate(f"factura_{uuid[:8]}.pdf", pagesize=letter, rightMargin=10*mm, leftMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos y configuraciones
    azul_claro = colors.HexColor("#739ef3")
    estilo_producto = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), azul_claro),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
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
        ('BACKGROUND', (0, 0), (-1, 0), azul_claro),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('BOX', (0,0), (-1,-1), 1, colors.white),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.white),
    ])
    
    ancho_columna = 120
    general_style = ParagraphStyle('SmallStyle', fontSize = 10, leading = 12)
    
    # 1. Tabla Emisor/Documento
    emisor_data = [
        ["Nombre:", factura.get('NombreEmisor', '')],
        ["RFC:", factura.get('RFCEmisor', '')],
        ["Regimen Fiscal:", factura.get('RegimenFiscal', '')],
        ["No. certificado digital:", factura.get('NoCertificado', '')],
        ["Folio Fiscal:", factura.get('UUID1', '')]
    ]

    emisor_procesado = []
    addStyle(emisor_data, emisor_procesado, general_style)
    tabla_emisor = Table(emisor_procesado, colWidths=[ancho_columna, 270-ancho_columna])
    tabla_emisor.setStyle(estilo_interna)

    documento_data = [  
        ["Serial:", factura.get('Folio', '')],
        ["Fecha de emisión:", factura.get('Fecha', '')[:10] if factura.get('Fecha') else ''],
        ["Lugar de emisión:", factura.get('LugarExpedicion', '')],
        ["Tipo de comprobante:", "Ingreso" if factura.get('TipoDeComprobante') == 'I' else 'Egreso']
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

    # 2. Tabla Receptor
    receptor_data = [
        ["Nombre:", factura.get('NombreReceptor', '')],
        ["RFC:", factura.get('RFCReceptor', '')]
    ]

    receptor_procesado = []
    addStyle(receptor_data, receptor_procesado, general_style)
    tabla_receptor = Table(receptor_procesado, colWidths=[ancho_columna, 270-ancho_columna])
    tabla_receptor.setStyle(estilo_interna)

    folio_data = [
        ["Domicilio fiscal:", factura.get('DomicilioFiscalReceptor', '')],
        ["Regimen fiscal:", factura.get('RegimenFiscalReceptor', '')],
        ["Uso CFDI:", factura.get('UsoCFDI', '')]
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

    # 3. Tabla de Productos
    productos_data = [["Cód. SAT", "NoIdent", "Cantidad", "Clv. Unidad", "Unidad", "Descripción", "Valor Unitario", "Descuento", "Importe"]]
    
    for producto in productos:
        fila = [
            producto.get('clave_producto', ''),
            "",  # NoIdent
            str(producto.get('cantidad', 0)),
            producto.get("clave_unidad",""),  # Clv. Unidad  
            producto.get('unidad', ''),
            producto.get('descripcion', ''),
            f"{producto.get('valor_unitario', 0):.2f}",
            f"{producto.get('descuento', 0):.2f}",
            f"{producto.get('importe', 0):.2f}"
        ]
        productos_data.append(fila)

    tabla3 = Table(productos_data, colWidths=[40, 35, 35, 40, 30, 175, 50, 45, 50])
    tabla3.setStyle(estilo_producto)

    # Importe en letras
    total = float(factura.get('Total', 0))
    importe_letra = Paragraph("  Importe en letra: " + numero_a_moneda_en_letras(total), 
        ParagraphStyle(
            name="CenteredTemp",
            parent=general_style,
            alignment=TA_CENTER,
            fontSize= 10
        )
    )

    # 4. Tabla Pago/Valores
    forma_pago = factura.get('FormaPago', '')
    forma_pago_desc = {
        "01": "01 - Efectivo",
        "02": "02 - Cheque", 
        "03": "03 - Transferencia electrónica",
        "04": "04 - Tarjeta de crédito"
    }.get(forma_pago, forma_pago)
    
    metodo_pago = factura.get('MetodoPago', '')
    metodo_pago_desc = {
        "PUE": "PUE - Pago en una sola exhibición",
        "PPD": "PPD - Pago en parcialidades o diferido"
    }.get(metodo_pago, metodo_pago)

    pago_data = [
        ["Forma pago:", forma_pago_desc],
        ["Método de pago:", metodo_pago_desc],
        ["Condición de pago:", factura.get('CondicionesDePago', '')],
        ["Version comprobante:", factura.get('Version', '')],
        ["Moneda:", factura.get('Moneda', '')],
        ["Tipo de cambio:", factura.get('TipoCambio', '')]
    ]

    pago_procesado = []
    addStyle(pago_data, pago_procesado, general_style)
    tabla_pago = Table(pago_procesado, colWidths=[110, 160])
    tabla_pago.setStyle(estilo_interna)

    valor_data = [
        ["Subtotal:", f"{float(factura.get('SubTotal', 0)):.2f}"],
        ["Descuento:", f"{float(factura.get('Descuento', 0) or 0):.2f}"],
        ["IEPS:", f"{float(factura.get('IEPS', 0) or 0):.2f}"],
        ["IVA:", f"{float(factura.get('IVA16%', 0) or 0):.2f}"],
        ["Retenciones ISR:", f"{float(factura.get('retenidoISR', 0) or 0):.2f}"],
        ["Retenciones IVA:", f"{float(factura.get('retenidoIVA', 0) or 0):.2f}"],
        ["Total", f"{float(factura.get('Total', 0)):.2f}"]
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

    # Crear QR en memoria
    sello = factura.get("Sello", "")
    ultimos_8_sello = sello[-8:] 
    qr = qrcode.QRCode()
    qr.add_data("https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?id=" + factura.get("UUID1") + "&re=" + factura.get("RFCEmisor") +
                "&rr=" + factura.get("RFCReceptor") + "&tt=" + factura.get("Total") + "&fe=" + ultimos_8_sello)
    qr.make()

    qr_pil = qr.make_image()
    qr_buffer = BytesIO()
    qr_pil.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_img = Image(qr_buffer, width=30*mm, height=30*mm)

    # Datos del pie
    cadena = "||1.1|" + factura.get("UUID1") +"|"+ factura.get("FechaTimbrado") +"|"+ factura.get("RfcProvCertif")+"|"+ factura.get("Sello")+"|"+ factura.get("NoCertificado")+"||"
    pie_data = [
        ['RFC proveedor de certificación:', 'Número de certificado SAT:', 'Fecha y hora de certificación:'],
        [factura.get("RfcProvCertif"), factura.get('NoCertificadoSAT', ''), factura.get('FechaTimbrado', '')],
        [ 'Sello digital del CFDI:', 'Sello digital del SAT:', 'Cadena original del timbre:'],
        [ factura.get('Sello', ''), factura.get('SelloSAT', ''), cadena ]
    ]

    small_style = ParagraphStyle('SmallStyle', fontSize=6, leading=7)
    processed_data = []
    addStyle(pie_data, processed_data, small_style)

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

    layout_data = [[qr_img, pie]]
    datos_extras = Table(layout_data, colWidths=[30*mm, 165*mm])
    datos_extras.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),  
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    mini_style = ParagraphStyle(
        name='Mini',
        parent=styles['Normal'],
        fontSize=6,
        leading=6.5,
        alignment=TA_CENTER
    )

    footer = Paragraph("Este documento es una representación impresa de un CFDI versión 4.0", mini_style)

    # Agregar elementos
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
    print(f"PDF generado: factura_{uuid[:8]}.pdf")


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


if __name__ == "__main__":
    # Ejemplo de uso - cambia el UUID por uno real de tu base de datos
    uuid_ejemplo = "02C89887-DB16-4D97-BDDC-EA90B0A333C9"
    crear_pdf_factura(uuid_ejemplo)
