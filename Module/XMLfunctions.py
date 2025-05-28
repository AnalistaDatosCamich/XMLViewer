import os
import sqlite3


def cargar_datos(self):
    """Cargar datos con cache"""
    cache_key = "facturas_all"

    # Verificar cache
    if cache_key in self.cache:
        self.datos_completos = self.cache[cache_key]['datos']
        self.columnas = self.cache[cache_key]['columnas']
        self.datos_actuales = self.datos_completos.copy()
        self.configurar_treeview()
        self.actualizar_treeview()
        self.status_label.configure(text="📁 Datos desde cache")
        return

    # Cargar desde BD en hilo separado
    self.status_label.configure(text="⏳ Cargando...")
    self.refresh_btn.configure(state="disabled")

    def cargar_en_hilo():
        try:
            conn = sqlite3.connect('C://Auxiliar Administración//Proyecto XML//mi_base.db')
            cursor = conn.cursor()

            # Obtener datos
            cursor.execute("SELECT * FROM facturas LIMIT 1000")
            datos = cursor.fetchall()

            # Obtener columnas
            cursor.execute("PRAGMA table_info(facturas)")
            columnas_info = cursor.fetchall()
            columnas = [col[1] for col in columnas_info]

            conn.close()

            # Guardar en cache
            self.cache[cache_key] = {
                'datos': datos,
                'columnas': columnas
            }

            # Actualizar en main thread
            self.root.after(0, self.datos_cargados, datos, columnas)

        except Exception as e:
            self.root.after(0, self.error_carga, str(e))

    threading.Thread(target=cargar_en_hilo, daemon=True).start()
