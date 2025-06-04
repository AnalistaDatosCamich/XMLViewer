import sqlite3
import glob
import os
from lxml import etree


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
            "MetodoPago", "LugarExpedicion", "Exportacion"
        ]
        timbrado_attr = [ "UUID", "FechaTimbrado", "RfcProvCertif", "SelloCFD", "NoCertificadoSAT", "SelloSAT"]
        emisor_attr = ["Nombre", "Rfc", "RegimenFiscal"]
        receptor_attr = ["Nombre", "Rfc", "RegimenFiscalReceptor", "DomicilioFiscalReceptor", "UsoCFDI"]

        data = {attr: root.get(attr, "") for attr in comprobante_attr}
        data.update({attr: timbrado.get(attr, "") for attr in timbrado_attr})
        data.update({attr: emisor.get(attr, "") for attr in emisor_attr})
        data["FechaEmision"] = data.pop("Fecha")
        data["RFCEmisor"] = data.pop("Rfc")
        data["NombreEmisor"] = data.pop("Nombre")
        data.update({attr: receptor.get(attr, "") for attr in receptor_attr})
        data["RFCReceptor"] = data.pop("Rfc")
        data["NombreReceptor"] = data.pop("Nombre")

        return data

    except Exception as e:
        print(f"Error extracting data from {xml_path}: {e}")
        return None


def get_table_schema():
    """
    Define the complete table schema with custom column order and additional null columns.
    Modify this function to customize your table structure.
    """
    # Define columns in your desired order with their data types
    schema = [
        # Primary identifiers first
        ("Version", "TEXT"),
        ("Tipo", "TEXT"),
        ("FechaEmision", "TEXT"),
        ("FechaTimbrado", "TEXT"),
        ("EstadoPago", "TEXT"),
        ("FechaPago", "TEXT"),
        ("Serie", "TEXT"),
        ("Folio", "TEXT"),
        ("UUID", "TEXT"),
        ("UUIDRelacion", "TEXT"),

        # Emisor information
        ("RFCEmisor", "TEXT"),
        ("NombreEmisor", "TEXT"),
        ("RegimenFiscal", "TEXT"),
        ("LugarEmision", "TEXT"),

        # Receptor information
        ("RFCReceptor", "TEXT"),
        ("NombreReceptor", "TEXT"),
        ("RegimenFiscalReceptor", "TEXT"),
        ("DomicilioFiscalReceptor", "TEXT"),
        ("UsoCFDI", "TEXT"),


        # Financial information
        ("SubTotal", "REAL"),
        ("Descuento", "REAL"),
        ("Total", "REAL"),
        ("Moneda", "TEXT"),
        ("TipoDeComprobante", "TEXT"),
        ("FormaPago", "TEXT"),
        ("MetodoPago", "TEXT"),
        ("CondicionesDePago", "TEXT"),

        # Technical fields
        ("Sello", "TEXT"),
        ("NoCertificado", "TEXT"),
        ("Certificado", "TEXT"),
        ("LugarExpedicion", "TEXT"),
        ("Exportacion", "TEXT"),
        ("RfcProvCertif", "TEXT"),
        ("SelloCFD", "TEXT"),
        ("NoCertificadoSAT", "TEXT"),
        ("SelloSAT", "TEXT"),

        # Additional null columns - Add your custom columns here
        ("Observaciones", "TEXT"),
        ("Estado", "TEXT"),
        ("Categoria", "TEXT"),
        ("Proveedor", "TEXT"),
        ("CentroCosto", "TEXT"),
        ("FechaVencimiento", "TEXT"),
        ("Pagado", "INTEGER"),  # 0 for False, 1 for True
        ("ImportePagado", "REAL"),
        ("FechaPago", "TEXT"),
        ("ReferenciaPago", "TEXT"),
        ("Proyecto", "TEXT"),
        ("Departamento", "TEXT"),
        ("Autorizado", "INTEGER"),  # 0 for False, 1 for True
        ("FechaAutorizacion", "TEXT"),
        ("AutorizadoPor", "TEXT"),
        ("Notas", "TEXT"),
    ]

    return schema


def create_ordered_record(extracted_data, schema):
    """
    Create a record with the specified column order, filling missing columns with None
    """
    ordered_record = {}

    for column_name, column_type in schema:
        if column_name in extracted_data:
            ordered_record[column_name] = extracted_data[column_name]
        else:
            # Set default values for additional columns
            if column_type == "INTEGER":
                ordered_record[column_name] = 0  # or 0 if you prefer
            elif column_type == "REAL":
                ordered_record[column_name] = 0.0  # or 0.0 if you prefer
            else:  # TEXT
                ordered_record[column_name] = ""  # or "" if you prefer empty strings

    return ordered_record


def process_invoices_with_transaction(invoice_data, connection, clear_table=True):
    cursor = connection.cursor()
    table_name = 'facturas'
    schema = get_table_schema()

    try:
        # Start transaction
        connection.execute('BEGIN TRANSACTION')

        # Create table with predefined schema
        columns_def = ', '.join([f'"{name}" {dtype}' for name, dtype in schema])
        create_table_sql = f'CREATE TABLE IF NOT EXISTS {table_name} ({columns_def})'
        cursor.execute(create_table_sql)
        print(f"📊 Table {table_name} created/verified with {len(schema)} columns")

        # Clear table if needed (after creation)
        if clear_table:
            cursor.execute(f'DELETE FROM {table_name}')
            print(f"🗑️ Table {table_name} cleared")

        # Process and insert all data
        successful_inserts = 0
        for extracted_record in invoice_data:
            if extracted_record is not None:  # Skip None records from failed extractions
                # Create ordered record with all columns
                ordered_record = create_ordered_record(extracted_record, schema)

                columns = ', '.join([f'"{k}"' for k in ordered_record.keys()])
                placeholders = ', '.join(['?'] * len(ordered_record))
                values = list(ordered_record.values())

                cursor.execute(f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})', values)
                successful_inserts += 1

        # Commit transaction
        connection.commit()
        print(f"✅ {successful_inserts} invoices processed successfully")

        # Show table info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        print(f"📋 Table structure: {len(columns_info)} columns")
        for col_info in columns_info[:10]:  # Show first 10 columns
            print(f"   - {col_info[1]} ({col_info[2]})")
        if len(columns_info) > 10:
            print(f"   ... and {len(columns_info) - 10} more columns")

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


def show_sample_data(connection, limit=1):
    """
    Display sample data from the table to verify the structure
    """
    cursor = connection.cursor()
    table_name = 'facturas'

    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"\n📊 Total records in table: {count}")

        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            rows = cursor.fetchall()

            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]

            print(f"\n🔍 Sample data (first {min(limit, len(rows))} records):")
            for i, row in enumerate(rows, 1):
                print(f"\n--- Record {i} ---")
                for col_name, value in zip(columns, row):
                    if value is not None:
                        print(f"{col_name}: {value}")

    except Exception as e:
        print(f"Error showing sample data: {e}")
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
            # Show sample data to verify structure
            # show_sample_data(conn)
        else:
            print("⚠️ Process completed with errors")
    finally:
        conn.close()
        print("🔒 Database connection closed")



if __name__ == "__main__":
    main()
