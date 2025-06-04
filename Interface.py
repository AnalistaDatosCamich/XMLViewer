import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinter import ttk
import tkinter as tk
import os
import sqlite3
import glob
from datetime import datetime
from lxml import etree
from XMLExtractData import process_xml_folder

ctk.set_appearance_mode("Dark")  # Dark mode
ctk.set_default_color_theme("dark-blue")  # Dark blue theme


class XMLViewerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Database variables
        self.db_connection = None
        self.current_db_path = ""
        self.current_table = ""
        self.datos_completos = []  # Almacenar todos los datos
        self.datos_actuales = []  # Datos filtrados actualmente
        # Configure window

        self.title("XMLViewer")
        self.geometry("1200x700")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        #Here we defined the uppertop functionalities section
        self.controls_frame = ctk.CTkFrame(self.main_frame)
        self.controls_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20), padx = 10)

        self.select_folder_button = ctk.CTkButton(
            self.controls_frame,
            text= "Selecciona la carpeta con XML",
            command= self.select_folder,
            width= 200
        )
        self.select_folder_button.grid(row=0, column=0, pady=10, padx=5, sticky = "ew")

        self.select_all_button = ctk.CTkButton(
            self.controls_frame,
            text="Seleccionar todo",
            command = self.seleccionar_todo_filtrado
        )
        self.select_all_button.grid(row=0, column=1, pady=10, padx=5, sticky = "ew")

        self.copy_button = ctk.CTkButton(
            self.controls_frame,
            text="Copiar seleccionados",
            command = self.copiar_seleccion
        )
        self.copy_button.grid(row=0, column=2, pady=10, padx=5, sticky = "ew")

        #Search field
        self.search_var = ctk.StringVar()
        self.search_var.trace('w', self.filtrar_datos)

        self.search_bar = ctk.CTkEntry(
            self.controls_frame,
            placeholder_text="Buscar...",
            textvariable= self.search_var,
            width=200
        )
        self.search_bar.grid(row=0, column=3, pady=10, padx=5, sticky = "ew")

        #Search between
        #First date
        self.first_date_text = ctk.StringVar()
        self.first_date_bar = ctk.CTkEntry(
            self.controls_frame,
            placeholder_text="Fecha inicial",
            textvariable= self.first_date_text,
            width=100
        )
        self.first_date_bar.grid(row=0, column=4, pady=10, padx=5, sticky = "ew")

        #Last date
        self.last_date_text = ctk.StringVar()
        self.last_date_bar = ctk.CTkEntry(
            self.controls_frame,
            placeholder_text="Fecha final",
            textvariable= self.last_date_text,
            width=100
        )
        self.last_date_bar.grid(row=0, column=5, pady=10, padx=5, sticky = "ew")

        self.clear_filter_button = ctk.CTkButton(
            self.controls_frame,
            text="Limpiar filtros",
            command=self.limpiar_filtros
        )
        self.clear_filter_button.grid(row=0, column=6, pady=10, padx=5, sticky = "ew")

        #Status label
        self.status_label = ctk.CTkLabel(self.controls_frame, text="Texto de prueba", width=100)
        self.status_label.grid(row=0, column=7, pady=10, padx=5, sticky = "ew")

        #To create auto-adjustable buttons
        for i in range(8):
            self.controls_frame.grid_columnconfigure(i, weight=1)

        self.controls_frame.grid_columnconfigure(0, weight=2)
        self.controls_frame.grid_columnconfigure(4, weight=2)



        #SQL database display
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.sql_section()

        #Export utilities section
        self.export_utilities = ctk.CTkFrame(self.main_frame, height = 50)
        self.export_utilities.grid(row=3, column=0, pady=10,  sticky="ew")
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=0)

        self.export_to_excel = ctk.CTkButton(
            self.export_utilities,
            text="Exportar selección a Excel"
        )
        self.export_to_excel.grid(row=0, column=0, pady=10, padx=5, sticky="ew")

        self.export_to_pdf = ctk.CTkButton(
            self.export_utilities,
            text="Exportar selección a PDF"
        )
        self.export_to_pdf.grid(row=0, column=1, pady=10, padx=5, sticky="ew")

        for i in range(2):
            self.export_utilities.grid_columnconfigure(i, weight=1)

        # Cargar base de datos al iniciar la aplicación
        self.load_initial_database()

    def sql_section(self):
        # ⬇️ This frame defines the SQL workplace
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(2, weight=1)  # ✅ permite que se expanda

        # ⬇️ Aquí dentro va el Treeview real
        tree_frame = tk.Frame(self.content_frame)
        tree_frame.grid(row=0, column=0, sticky="nsew")  # expandirse en content_frame

        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")

        # Treeview con selección múltiple
        self.tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            selectmode="extended"
        )

        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)

        # Layout of elements
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Expansión del Treeview
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

    def load_initial_database(self):
        """Cargar la base de datos mi_base.db al iniciar la aplicación"""
        db_path = "C://Analista de datos//Proyecto XML//mi_base.db"
        if os.path.exists(db_path):
            self.load_database(db_path)
        else:
            self.status_label.configure(text="mi_base.db no encontrada")

    def refresh_database(self):
        """Refrescar los datos de la base de datos mi_base.db"""
        db_path = "C://Analista de datos//Proyecto XML//mi_base.db"
        if os.path.exists(db_path):
            self.load_database(db_path)
            self.status_label.configure(text="Datos refrescados")
        else:
            messagebox.showerror("Error", "No se encontró el archivo mi_base.db")
            self.status_label.configure(text="mi_base.db no encontrada")

    # FUNCIONES COMENTADAS DEL SELECTOR DE CARPETA ORIGINAL
    def select_folder(self):
        """Open folder dialog and store selected path"""
        # folder_path = filedialog.askopenfilename(
        #     title="Seleccionar carpeta",
        #     filetypes=[
        #         ("Todos los archivos", "*.*"),
        #         ("Facturas y transferencias", "*.xml"),
        #         ("SQLite Database", "*.db"),
        #         ("SQLite Database", "*.sqlite"),
        #         ("SQLite Database", "*.sqlite3")
        #     ]
        # )
        # if folder_path:
        #     self.status_label.configure(text=f"Carpeta: {os.path.basename(folder_path)}")

        # Ahora la función refresh_database se encarga de esto
        self.refresh_database()

    def load_database(self, db_path):
        """Load SQLite database and display data"""
        try:
            if self.db_connection:
                self.db_connection.close()

            self.db_connection = sqlite3.connect(db_path)
            self.current_db_path = db_path

            # Load facturas table directly
            self.load_table_data("facturas")

            # Update status with record count
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM facturas")
            count = cursor.fetchone()[0]
            self.status_label.configure(text=f"BD: {count} registros")

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error:\n{str(e)}")
            self.status_label.configure(text="Database error")

    def load_table_data(self, table_name):
        """Load table data into Treeview"""
        if not self.db_connection:
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")

            # Clear existing data
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Get column names
            columnas = [description[0] for description in cursor.description]

            # Configure Treeview columns
            self.tree["columns"] = columnas
            self.tree["show"] = "headings"

            for col in columnas:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=100)

            # Insert data
            rows = cursor.fetchall()

            # Actualizar las variables de datos que usa el sistema de filtrado
            self.datos_completos = list(rows)  # Convertir a lista para poder modificar
            self.datos_actuales = list(rows)  # Copia de los datos completos

            # Insert data into treeview
            for row in rows:
                self.tree.insert("", "end", values=row)

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error loading table data:\n{str(e)}")

    def copiar_seleccion(self, event=None):
        """Copiar selección al clipboard"""
        seleccionados = self.obtener_seleccionados()
        if not seleccionados:
            self.status_label.configure(text="No hay elementos seleccionados")
            return

        # Crear texto separado por tabs (formato Excel)
        texto = []

        # Datos
        for fila in seleccionados:
            fila_texto = "\t".join(str(cell) if cell else "" for cell in fila)
            texto.append(fila_texto)

        # Copiar al clipboard
        contenido = "\n".join(texto)
        self.content_frame.clipboard_clear()
        self.content_frame.clipboard_append(contenido)

        self.status_label.configure(text=f"{len(seleccionados)} filas copiadas")

    def seleccionar_todo(self):
        """Seleccionar todo sin filtros (método adicional)"""
        # Limpiar filtro temporalmente para mostrar todo
        filtro_anterior = self.search_var.get()
        self.search_var.set("")  # Esto disparará filtrar_datos y mostrará todo

        # Seleccionar después de un pequeño delay para que se actualice la vista
        self.content_frame.after(10, lambda: self.seleccionar_todo_visible())

        # Restaurar filtro si había uno
        if filtro_anterior:
            self.content_frame.after(20, lambda: self.search_var.set(filtro_anterior))

    def seleccionar_todo_filtrado(self):
        """Seleccionar todas las filas filtradas (si no hay filtro, selecciona todo)"""
        # Obtener todos los items actualmente mostrados en el treeview
        items = self.tree.get_children()

        if items:
            # Seleccionar todos los items filtrados
            self.tree.selection_set(items)

            # Mensaje más descriptivo
            total_registros = len(getattr(self, 'datos_completos', []))
            registros_filtrados = len(items)

            if registros_filtrados == total_registros:
                self.status_label.configure(text=f"☑️ Todos los {registros_filtrados} registros seleccionados")
            else:
                self.status_label.configure(text=f"☑️ {registros_filtrados} registros filtrados seleccionados")
        else:
            self.status_label.configure(text="❌ No hay datos para seleccionar")

    def obtener_seleccionados(self):
        """Obtener filas seleccionadas"""
        items = self.tree.selection()
        return [self.tree.item(item)['values'] for item in items]

    def filtrar_datos(self, *args):
        """Filtrar datos en memoria"""
        if not hasattr(self, 'datos_completos'):
            return

        termino = self.search_var.get().lower()

        if not termino:
            self.datos_actuales = self.datos_completos.copy()
        else:
            # Filtrar en memoria
            self.datos_actuales = [
                fila for fila in self.datos_completos
                if any(str(celda).lower().find(termino) >= 0 for celda in fila if celda)
            ]

        self.actualizar_treeview()

    def limpiar_filtros(self):
        """Limpiar todos los filtros aplicados"""
        self.search_var.set("")
        self.first_date_text.set("")
        self.last_date_text.set("")

        # Restaurar todos los datos
        if hasattr(self, 'datos_completos'):
            self.datos_actuales = self.datos_completos.copy()
            self.actualizar_treeview()

    def actualizar_treeview(self):
        """Actualizar vista con datos actuales"""
        # Limpiar
        self.tree.delete(*self.tree.get_children())

        # Insertar datos filtrados/ordenados
        for fila in self.datos_actuales:
            self.tree.insert("", "end", values=fila)

        # Actualizar contador
        total = len(getattr(self, 'datos_completos', []))
        mostrados = len(self.datos_actuales)

        if mostrados == total:
            self.status_label.configure(text=f"{total} registros")
        else:
            self.status_label.configure(text=f"{mostrados}/{total} registros")


if __name__ == "__main__":
    app = XMLViewerApp()
    app.mainloop()
