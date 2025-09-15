import sqlite3
import glob
import os
import sys
from lxml import etree

def get_resource_path():
    """Obtiene la ruta correcta para recursos, funciona tanto en desarrollo como en .exe"""
    if getattr(sys, 'frozen', False):
        # Si está compilado con PyInstaller
        return os.path.dirname(sys.executable)
    else:
        # Si está en desarrollo
        return os.path.dirname(os.path.abspath(__file__))

def extract_xml_data(xml_path):
    try:
        tree = etree.parse(xml_path)
        root = tree.getroot()

        # Define namespaces (adjust if you use other prefixes)
        ns = {
            'cfdi': 'http://www.sat.gob.mx/cfd/4',
            'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
        }

        timbrado = root.find('.//cfdi:Complemento/tfd:TimbreFiscalDigital', ns)
        emisor = root.find('.//cfdi:Emisor', ns)
        receptor = root.find('.//cfdi:Receptor', ns)

        comprobante_attr = [
            "Version", "Serie", "Folio", "Fecha", "Total", "Sello", "NoCertificado",
            "FormaPago", "Certificado", "CondicionesDePago", "SubTotal",
            "Descuento", "Moneda", "Total", "TipoDeComprobante",
            "MetodoPago", "LugarExpedicion", "Exportacion", "TipoCambio"
        ]
        timbrado_attr = [ "UUID", "FechaTimbrado", "RfcProvCertif", "SelloCFD", "NoCertificadoSAT", "SelloSAT"]
        emisor_attr = ["Nombre", "Rfc", "RegimenFiscal"]
        receptor_attr = ["Nombre", "Rfc", "RegimenFiscalReceptor", "DomicilioFiscalReceptor", "UsoCFDI"]
        
        data = {attr: root.get(attr, "") for attr in comprobante_attr}
        data.update({attr: timbrado.get(attr, "") for attr in timbrado_attr})
        data["UUID1"] = data.pop("UUID")
        data.update({attr: emisor.get(attr, "") for attr in emisor_attr})
        data["RFCEmisor"] = data.pop("Rfc")
        data["NombreEmisor"] = data.pop("Nombre")
        data.update({attr: receptor.get(attr, "") for attr in receptor_attr})
        data["RFCReceptor"] = data.pop("Rfc")
        data["NombreReceptor"] = data.pop("Nombre")

        try:
            uuid_value = root.find(".//cfdi:CfdiRelacionado", ns).get("UUID", "")
            data.update({"UUIDRelacion": uuid_value})
        except AttributeError:
            data.update({"UUIDRelacion": ""})

        impuestos_node = root.find("./cfdi:Impuestos", ns)

        filename = os.path.basename(xml_path)
        data.update({"ArchivoXML": filename})

        conceptos = root.findall('.//cfdi:Concepto', ns)
        descripciones = [concepto.get("Descripcion", "") for concepto in conceptos if concepto.get("Descripcion", "")]
        data.update({"Conceptos": " * ".join(descripciones) if descripciones else ""})

        clave_prod = [concepto.get("ClaveProdServ", "") for concepto in conceptos if concepto.get("Descripcion", "")]
        data.update({"claveProducto": " * ".join(clave_prod) if clave_prod else ""})

        impuestos_node = root.find('./cfdi:Impuestos', ns)
        if impuestos_node is not None:
            data.update({"TotalTrasladados": impuestos_node.get("TotalImpuestosTrasladados", 0)})
            data.update({"TotalRetenidos": impuestos_node.get("TotalImpuestosRetenidos", 0)})
        else:
            data.update({"TotalTrasladados": 0 })
            data.update({"TotalRetenidos": 0 })

        # Extraer retenciones IVA e ISR
        # Inicializar valores
        iva_trasladado = 0
        ieps_trasladado = 0
        retenido_iva = 0
        retenido_isr = 0
        total_local_trasladados = 0

        # Definir namespace para impuestos locales
        ns_local = {'implocal': 'http://www.sat.gob.mx/implocal'}

        # Inicializar IEPS por porcentajes
        ieps_porcentajes = {
            "IEPS3": 0, "IEPS6": 0, "IEPS7": 0, "IEPS8": 0, 
            "IEPS9": 0, "IEPS265": 0, "IEPS30": 0, 
            "IEPS53": 0, "IEPS160": 0
        }

        # Obtener IVA trasladado del nodo principal de impuestos
        if impuestos_node is not None:
            traslados_nodes = impuestos_node.findall('./cfdi:Traslados/cfdi:Traslado', ns)
            for traslado in traslados_nodes:
                impuesto = traslado.get("Impuesto", "")
                importe = float(traslado.get("Importe", "0"))

                if impuesto == "002":  # IVA
                    iva_trasladado += importe
                elif impuesto == "003":  # IEPS
                    ieps_trasladado += importe

                    tasa = float(traslado.get("TasaOCuota", "0"))
                    tasa_porcentaje = tasa*100

                    # Mapear según el porcentaje
                    if tasa_porcentaje == 3:
                        ieps_porcentajes["IEPS3"] += importe
                    elif tasa_porcentaje == 6:
                        ieps_porcentajes["IEPS6"] += importe
                    elif tasa_porcentaje == 7:
                        ieps_porcentajes["IEPS7"] += importe
                    elif tasa_porcentaje == 8:
                        ieps_porcentajes["IEPS8"] += importe
                    elif tasa_porcentaje == 9:
                        ieps_porcentajes["IEPS9"] += importe
                    elif tasa_porcentaje == 26.5:
                        ieps_porcentajes["IEPS265"] += importe
                    elif tasa_porcentaje == 30:
                        ieps_porcentajes["IEPS30"] += importe
                    elif tasa_porcentaje == 53:
                        ieps_porcentajes["IEPS53"] += importe
                    elif tasa_porcentaje == 160:
                        ieps_porcentajes["IEPS160"] += importe

            # Obtener retenciones de IVA (si existen en el nodo principal)
            retenciones_nodes = impuestos_node.findall('./cfdi:Retenciones/cfdi:Retencion', ns)
            for retencion in retenciones_nodes:
                impuesto = retencion.get("Impuesto", "")
                importe = float(retencion.get("Importe", "0"))
                
                if impuesto == "001": # ISR
                    retenido_isr = importe
                elif impuesto == "002":  # IVA retenido
                    retenido_iva = importe

        # Obtener total de traslados locales del complemento
        complemento_node = root.find('.//cfdi:Complemento', ns)
        if complemento_node is not None:
            impuestos_locales = complemento_node.find('.//implocal:ImpuestosLocales', ns_local)
            if impuestos_locales is not None:
                total_local_trasladados = float(impuestos_locales.get("TotaldeTraslados", "0"))

        # Actualizar data
        data.update({
            "IVA16%": iva_trasladado,
            "IEPS": ieps_trasladado if ieps_trasladado > 0 else 0,
            "retenidoISR": retenido_isr,
            "retenidoIVA": retenido_iva,
            "totalLocalTrasladados": total_local_trasladados
        })

        #Agregar todos los porcentajes de IEPS
        data.update(ieps_porcentajes)


        if "Folio" in data:
            data["Folio"] = "​" + str(data["Folio"]) 

        return data

    except Exception as e:
        print(f"Error extracting data from {xml_path}: {e}")
        return None


def infer_sqlite_type(value, column_name = None):
    if column_name == "Folio":
        value = str(value)
        return "TEXT"
    elif isinstance(value, int):
        return "INTEGER"
    elif isinstance(value, float):
        return "REAL"
    return "TEXT"


def process_invoices_with_transaction(invoice_data, connection, clear_table=True):
    cursor = connection.cursor()
    table_name = 'facturas'

    try:
        # Start transaction
        connection.execute('BEGIN TRANSACTION')

        # Create table using first record as reference
        if invoice_data:
            first_record = invoice_data[0]
            columns_def = ', '.join([f'"{k}" {infer_sqlite_type(v, k)}' for k, v in first_record.items()])
            create_table_sql = f'CREATE TABLE IF NOT EXISTS {table_name} ({columns_def})'
            cursor.execute(create_table_sql)
            print(f"📊 Table {table_name} created/verified")

        # Clear table if needed (after creation)
        if clear_table:
            cursor.execute(f'DELETE FROM {table_name}')
            print(f"🗑️ Table {table_name} cleared")

        # Insert all data
        successful_inserts = 0
        for record in invoice_data:
            if record is not None:  # Skip None records from failed extractions
                columns = ', '.join([f'"{k}"' for k in record.keys()])
                placeholders = ', '.join(['?'] * len(record))
                values = list(record.values())
                cursor.execute(f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})', values)
                successful_inserts += 1

        # Commit transaction
        connection.commit()
        print(f"✅ {successful_inserts} invoices processed successfully")
        return True

    except Exception as e:
        # Rollback in case of error
        connection.rollback()
        print(f"❌ Error processing invoices: {e}")
        print("🔄 Transaction rolled back")
        return False

    finally:
        cursor.close()


def process_xml_folder(folder_path, connection):
    """
    Processes all XML files in a folder
    """
    # Get all XML files
    pattern = os.path.join(folder_path, "*.xml")
    xml_files = glob.glob(pattern)

    if not xml_files:
        print("❌ No XML files found in the folder")
        return False

    print(f"📂 Found {len(xml_files)} XML files")

    # Extract data from all XML files
    all_data = []
    errors = []

    for file in xml_files:
        data = extract_xml_data(file)
        if data is not None:
            all_data.append(data)
            #print(f"✅ {os.path.basename(file)}")
        else:
            errors.append(file)
            #print(f"❌ {os.path.basename(file)}: Error during extraction")

    if not all_data:
        print("❌ No XML files could be processed")
        return False

    # Process with transaction
    success = process_invoices_with_transaction(all_data, connection)

    if errors:
        print(f"⚠️ {len(errors)} files had errors")

    return success

def create_second_table_from_first(connection, source_table='facturas', target_table='XMLDATA'):
    """
    Crea una segunda tabla a partir de la tabla de facturas
    """
    cursor = connection.cursor()
    
    try:
        #Eliminar tabla si existe ara recrearla
        cursor.execute(f'DROP TABLE IF EXISTS {target_table}')
        
        # Crear la segunda tabla "XMLDATA"
        # Crear la tabla XMLDATA con tu consulta específica
        create_xmldata_sql = f'''
        CREATE TABLE {target_table} AS
        SELECT Version AS Versión, 
            CASE
                WHEN TipoDeComprobante = "I" THEN "Factura"
                WHEN TipoDeComprobante = "E" THEN "NotaCredito"
                ELSE TipoDeComprobante
            END AS Tipo,
        SUBSTRING(Fecha,1, 10) AS "Fecha de emisión", FechaTimbrado AS "Fecha de Timbrado","" AS "Estado de pago", "" AS "Fecha de pago", Serie, Folio, UUID1 AS "UUID", 
        UUIDRelacion, RFCEmisor AS "RFC Emisor", NombreEmisor AS "Nombre Emisor", LugarExpedicion AS "Lugar de Expedición", RFCEmisor AS "RFC Emisor", 
        NombreReceptor AS "Nombre Receptor", "" AS "Residencia Fiscal", "" AS NumRegIdTrib, 
            CASE 
                WHEN UsoCFDI = "G03" THEN "G03 - Gastos en general"
                WHEN UsoCFDI = "I08" THEN "I08 - Otra maquinaria y equipo"
                WHEN UsoCFDI = "G02" THEN "G02 - Devoluciones, descuentos o bonificaciones"
                WHEN UsoCFDI = "CP01" THEN  "CP01 - Pagos"
                ELSE UsoCFDI
            END AS "Uso CFDI", 
            CASE 
                WHEN TipoDeComprobante = 'E' THEN SubTotal
                ELSE SubTotal
            END AS SubTotal,
            CASE 
                WHEN Descuento IS NULL THEN 0.0
                WHEN TipoDeComprobante = 'E' THEN Descuento
                ELSE Descuento
            END AS Descuento,
        IEPS AS "TOTAL IEPS", "IVA16%", retenidoIVA, retenidoISR, 0 AS ISH,
            CASE 
                WHEN TipoDeComprobante = 'E' THEN Total
                ELSE Total
            END AS Total_Final,
        "" AS "Total original", TotalTrasladados , TotalRetenidos, totalLocalTrasladados AS "Total local trasladado", 0 AS "Total local retenido",
        "" AS "Complemento" , Moneda, TipoCambio AS "Tipo de Cambio", 
            CASE
                WHEN FormaPago = "01" THEN "01 - Efectivo" 
                WHEN FormaPago = "02" THEN "02 - Cheque"
                WHEN FormaPago = "03" THEN "03 - Transferencia electrónica de fondos"
                WHEN FormaPago = "04" THEN "04 - Tarjeta de crédito"
                WHEN FormaPago = "05" THEN "05 - Monedero Electrónico"
                WHEN FormaPago = "28" THEN "28 - Tarjeta de débito"
                WHEN FormaPago = "30" THEN "30 - Aplicación de anticipos"
                WHEN FormaPago = "99" THEN "99 - Por definir"
                ELSE FormaPago
            END AS "Forma de pago", 
            CASE 
                WHEN MetodoPago = "PUE" THEN "PUE- Pago en una sola exhibición"  
                WHEN MetodoPago = "PPD" THEN "PPD- Pago en parcialidades o diferido"
                ELSE MetodoPago
            END AS "Método de pago", 
        "" AS "NumCtaPago", CondicionesDePago AS "Condición de pago", Conceptos,
            CASE
                WHEN INSTR(claveProducto, "15101505")>0 /*Diesel*/	
                OR INSTR(claveProducto, "15101514")>0 /*Gasolina normal*/
                OR INSTR(claveProducto, "15101515")>0 /*Gasolina Premium*/
                OR INSTR(claveProducto, "15111510")>0 /*Gas licuado */
                OR INSTR(claveProducto, "15111512")>0 /*Gas natural */
                THEN "Si"
                ELSE "No"
            END AS "Combustible",
        IEPS3 AS "IEPS 3%", IEPS6 AS "IEPS 6%", IEPS7 AS "IEPS 7%",
        IEPS8 AS "IEPS 8%" , IEPS9 AS "IEPS 9%", IEPS265 AS "IEPS 26.5%", IEPS30 AS "IEPS 30%", IEPS53 AS "IEPS 53%", IEPS160 AS "IEPS 160%", 
        ArchivoXML, "" AS "Dirección Emisor", "" AS "Localidad emisor", "" AS "Dirección Receptor", "" AS "Localidad Receptor",
        0 AS "IVA 8%", 0 AS "IEPS 30,4%", 0 AS "IVA Ret 6%", RegimenFiscalReceptor, DomicilioFiscalReceptor
        FROM {source_table} WHERE TipoDeComprobante IN ("E", "I")
        '''

        cursor.execute(create_xmldata_sql)
                
        # Obtener número de registros insertados
        cursor.execute(f'SELECT COUNT(*) FROM {target_table}')
        rows_count = cursor.fetchone()[0]
        
        connection.commit()
        print(f"📊 Table {target_table} created successfully")
        print(f"✅ {rows_count} records processed in {target_table}")
        return True
        
    except Exception as e:
        connection.rollback()
        print(f"❌ Error creating second table: {e}")
        return False
    
    finally:
        cursor.close()

def extract_products_from_xml(xml_path):
    """Extrae productos de un XML específico"""
    try:
        tree = etree.parse(xml_path)
        root = tree.getroot()
        
        ns = {
            'cfdi': 'http://www.sat.gob.mx/cfd/4',
            'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
        }
        
        # Obtener UUID
        timbrado = root.find('.//cfdi:Complemento/tfd:TimbreFiscalDigital', ns)
        uuid = timbrado.get('UUID')
        
        # Extraer conceptos
        conceptos = root.findall('.//cfdi:Concepto', ns)
        productos = []
        
        for concepto in conceptos:
            producto = {
                'uuid_factura': uuid,
                'clave_producto': concepto.get('ClaveProdServ', ''),
                'descripcion': concepto.get('Descripcion', ''),
                'cantidad': float(concepto.get('Cantidad', 0)),
                'clave_unidad':concepto.get('ClaveUnidad', ''),
                'unidad': concepto.get('Unidad', ''),
                'valor_unitario': float(concepto.get('ValorUnitario', 0)),
                'importe': float(concepto.get('Importe', 0)),
                'descuento': float(concepto.get('Descuento', 0))
            }
            productos.append(producto)
        
        return productos
    except Exception as e:
        print(f"Error extracting products from {xml_path}: {e}")
        return []

def create_products_table(connection):
    """Crea tabla de productos y la llena con datos de todos los XMLs"""
    cursor = connection.cursor()
    
    try:
        # Crear tabla productos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid_factura TEXT,
            clave_producto TEXT,
            descripcion TEXT,
            cantidad REAL,
            clave_unidad TEXT,
            unidad TEXT,
            valor_unitario REAL,
            importe REAL,
            descuento REAL,
            FOREIGN KEY (uuid_factura) REFERENCES facturas (UUID1)
        )
        ''')
        
        # Limpiar tabla
        cursor.execute('DELETE FROM productos')
        
        # Obtener todos los archivos XML de la carpeta
        folder_path = "C://AdminXML//BovedaCFDi//CLE230712B31//Recibidas//2025//12. DICIEMBRE 2024//12 todo dic"
        pattern = os.path.join(folder_path, "*.xml")
        xml_files = glob.glob(pattern)
        
        total_productos = 0
        for xml_file in xml_files:
            productos = extract_products_from_xml(xml_file)
            for producto in productos:
                cursor.execute('''
                INSERT INTO productos (uuid_factura, clave_producto, descripcion, cantidad, clave_unidad, unidad, valor_unitario, importe, descuento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?,?)
                ''', tuple(producto.values()))
                total_productos += 1
        
        connection.commit()
        print(f"✅ Tabla productos creada con {total_productos} registros")
        return True
        
    except Exception as e:
        connection.rollback()
        print(f"❌ Error creando tabla productos: {e}")
        return False
    finally:
        cursor.close()

def main():
    folder_path = "C://AdminXML//BovedaCFDi//CLE230712B31//Recibidas//2025//12. DICIEMBRE 2024//12 todo dic"

    # Create/connect to mi_base.db database
    print("🔗 Connecting to database mi_base.db...")
    conn = sqlite3.connect("mi_base.db")


    try:
        success = process_xml_folder(folder_path, conn)
        if success:
            print("🎉 Process completed successfully!")

            create_second_table_from_first(conn)
            create_products_table(conn)
        else:
            print("⚠️ Process completed with errors")
    finally:
        conn.close()
        print("🔒 Database connection closed")



if __name__ == "__main__":
    main()

