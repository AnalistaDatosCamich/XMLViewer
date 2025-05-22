#import sqlite3
from lxml import etree
#from datetime import datetime

#We will define de parsing function
def extract_xml_data(xml_path):
    try:
        tree = etree.parse(xml_path)
        root = tree.getroot()

        # Definir los namespaces (ajusta si usas otros prefijos)
        ns = {
            'cfdi': 'http://www.sat.gob.mx/cfd/4',  # o cfd/3 dependiendo de tu versión
            'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
        }
        timbre = root.find('.//cfdi:Complemento/tfd:TimbreFiscalDigital', ns)
        comprobante_attributes = ["Serie", "Folio", "Fecha", "Total", "Sello", "NoCertificado", "FormaPago", "Certificado", "CondicionesDePago", "SubTotal", "Descuento", "Moneda", "Total", "TipoDeComprobante", "MetodoPago", "LugarExpedicion"]

        data = {attr: root.get(attr, None) for attr in comprobante_attributes}
        """comprobante = root.find('.//cfdi:Comprobante', namespaces=ns)
        if comprobante is not None:
            return comprobante.attrib  # Esto es un diccionario con todos los atributos
        else:
            return None """

        data["UUID"] = timbre.get('UUID', None)

        return data

    except Exception:
        return "Error durante la extracción"

#Extraer datos
Datos = extract_xml_data("C://Auxiliar Administración//Proyecto XML//testXML.xml")
print(Datos)
