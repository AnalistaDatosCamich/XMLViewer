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

        stamp = root.find('.//cfdi:Complemento/tfd:TimbreFiscalDigital', ns)
        invoice_attributes = [
            "Serie", "Folio", "Fecha", "Total", "Sello", "NoCertificado",
            "FormaPago", "Certificado", "CondicionesDePago", "SubTotal",
            "Descuento", "Moneda", "Total", "TipoDeComprobante",
            "MetodoPago", "LugarExpedicion"
        ]

        data = {attr: root.get(attr, None) for attr in invoice_attributes}
        data["UUID"] = stamp.get('UUID', None) if stamp is not None else None

        return data

    except Exception as e:
        print(f"Error extracting data from {xml_path}: {e}")
        return None


def infer_sqlite_type(value):
    if isinstance(value, int):
        return "INTEGER"
    elif isinstance(value, float):
        return "REAL"
    return "TEXT"


def process_invoices_with_transaction(invoice_data, connection, clear_table=True):
    """
    Process invoices with a complete transaction

    Args:
        invoice_data: List of dictionaries with invoice data
        connection: Database connection
        clear_table: If True, clears the table before inserting
    """
    cursor = connection.cursor()
    table_name = 'facturas'

    try:
        # Start transaction
        connection.execute('BEGIN TRANSACTION')

        # Create table using first record as reference
        if invoice_data:
            first_record = invoice_data[0]
            columns_def = ', '.join([f'"{k}" {infer_sqlite_type(v)}' for k, v in first_record.items()])
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
            print(f"✅ {os.path.basename(file)}")
        else:
            errors.append(file)
            print(f"❌ {os.path.basename(file)}: Error during extraction")

    if not all_data:
        print("❌ No XML files could be processed")
        return False

    # Process with transaction
    success = process_invoices_with_transaction(all_data, connection)

    if errors:
        print(f"⚠️ {len(errors)} files had errors")

    return success


def main():
    folder_path = "C://AdminXML//BovedaCFDi//CLE230712B31//Recibidas//2025.2//21 AL 26 MAYO 2025"

    # Create/connect to mi_base.db database
    print("🔗 Connecting to database mi_base.db...")
    conn = sqlite3.connect("mi_base.db")

    try:
        success = process_xml_folder(folder_path, conn)
        if success:
            print("🎉 Process completed successfully!")
        else:
            print("⚠️ Process completed with errors")
    finally:
        conn.close()
        print("🔒 Database connection closed")


# Example usage for testing a single XML file
def test_single_xml():
    data = extract_xml_data("C://Auxiliar Administración//Proyecto XML//testXML.xml")
    print("Single XML test result:")
    print(data)


if __name__ == "__main__":
    main()
    # Uncomment the line below to test with a single XML file
    # test_single_xml()