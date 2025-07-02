import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinter import ttk
import tkinter as tk
import os
import sqlite3

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

        self.drag_start = None
        self.dragging = False
        self.drag_start_item = None
        self.sort_column = None
        self.sort_reverse = False

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
        self.first_date_text.trace('w', self.filtrar_datos)
        self.last_date_text.trace('w', self.filtrar_datos)

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
        #self.load_initial_database()

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

    # FUNCIONES COMENTADAS DEL SELECTOR DE CARPETA ORIGINAL
    def select_folder(self):
        #"""Open folder dialog and process XML files"""
        from XMLExtractData import process_xml_folder, create_second_table_from_first, get_resource_path
        folder_path = filedialog.askdirectory(
            title="Seleccionar carpeta con archivos XML"
        )
        
        if folder_path:
            self.status_label.configure(text="Procesando XMLs...")
            self.update()  # Actualizar la interfaz
            
            try:
                # Crear/conectar a la base de datos
                db_path = os.path.join(get_resource_path(), "mi_base.db")
                conn = sqlite3.connect(db_path)
                
                # Procesar XMLs
                success = process_xml_folder(folder_path, conn)
                
                if success:
                    # Crear tabla XMLDATA
                    create_second_table_from_first(conn)
                    conn.close()
                    
                    # Cargar los datos procesados
                    self.load_database(db_path)
                    self.status_label.configure(text=f"XMLs procesados desde: {os.path.basename(folder_path)}")
                else:
                    conn.close()
                    self.status_label.configure(text="Error procesando XMLs")
                    messagebox.showerror("Error", "No se pudieron procesar los archivos XML")
                    
            except Exception as e:
                self.status_label.configure(text="Error en procesamiento")
                messagebox.showerror("Error", f"Error procesando XMLs:\n{str(e)}")

    def load_database(self, db_path):
        """Load SQLite database and display data"""
        try:
            if self.db_connection:
                self.db_connection.close()

            self.db_connection = sqlite3.connect(db_path)
            self.current_db_path = db_path

            # Load facturas table directly
            self.load_table_data("XMLDATA")

            # Update status with record count
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM XMLDATA")
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
                self.tree.heading(col, text=col, command=lambda c=col: self.ordenar_por_columna(c))
                # Calcular ancho óptimo una sola vez
                header_width = len(col) * 8 + 40
                optimal_width = max(header_width, 300)
                optimal_width = min(optimal_width, 120)
                self.tree.column(col, width=optimal_width, minwidth=80, stretch= False)

            # Insert data
            rows = cursor.fetchall()

            # Actualizar las variables de datos que usa el sistema de filtrado
            self.datos_completos = list(rows)  # Convertir a lista para poder modificar
            self.datos_actuales = list(rows)  # Copia de los datos completos

            # Insert data into treeview
            self.tree.bind('<ButtonPress-1>', self.inicio_arrastre)
            self.tree.bind('<B1-Motion>', self.durante_arrastre)
            self.tree.bind('<ButtonRelease-1>', self.fin_arrastre)
            self.tree.bind('<Control-c>', self.copiar_seleccion)
            #self.tree.bind('<Control-a>', self.seleccionar_todo_filtrado)

            for row in rows:
                self.tree.insert("", "end", values=row)
            

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error loading table data:\n{str(e)}")

    def ordenar_por_columna(self, columna):
        """Ordenar datos por columna seleccionada"""
        if not hasattr(self, 'datos_actuales') or not self.datos_actuales:
            return
        
        # Obtener índice de la columna
        columnas = [description[0] for description in self.db_connection.cursor().execute(f"SELECT * FROM {self.current_table or 'XMLDATA'} LIMIT 0").description]
        col_idx = columnas.index(columna)
        
        # Alternar orden si es la misma columna
        if self.sort_column == columna:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = columna
            self.sort_reverse = False
        
        # Ordenar datos actuales
        def sort_key(fila):
            valor = fila[col_idx]
            if valor is None:
                return ""
            # Intentar convertir a número para ordenamiento numérico
            try:
                return float(valor)
            except (ValueError, TypeError):
                return str(valor).lower()
        
        self.datos_actuales.sort(key=sort_key, reverse=self.sort_reverse)
        self.actualizar_treeview()

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
            fila_texto = "\t".join(str(cell) if cell not in [None, ""] else "" for cell in fila)
            texto.append(fila_texto)

        # Copiar al clipboard
        contenido = "\n".join(texto)
        self.content_frame.clipboard_clear()
        self.content_frame.clipboard_append(contenido)

        self.status_label.configure(text=f"{len(seleccionados)} filas copiadas")

    def inicio_arrastre(self, event):
        #Iniciar selección por arrastre"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":  # Solo en celdas, no en headers
            item = self.tree.identify_row(event.y)
            if item:
                self.drag_start = event.y
                self.drag_start_item = item
                self.dragging = False

                # Si no hay Ctrl presionado, limpiar selección
                if not (event.state & 0x4):  # Ctrl no presionado
                    self.tree.selection_set(item)

    def durante_arrastre(self, event):
        #Durante el arrastre, seleccionar rango"""
        if self.drag_start is None:
            return

        # Detectar si realmente estamos arrastrando
        if abs(event.y - self.drag_start) > 3:
            self.dragging = True

            # Obtener item actual
            current_item = self.tree.identify_row(event.y)
            if not current_item:
                return

            # Obtener todos los items
            all_items = self.tree.get_children()

            try:
                start_idx = all_items.index(self.drag_start_item)
                current_idx = all_items.index(current_item)

                # Determinar rango
                min_idx = min(start_idx, current_idx)
                max_idx = max(start_idx, current_idx)

                # Limpiar selección previa si no hay Ctrl
                if not (event.state & 0x4):
                    self.tree.selection_set([])

                # Seleccionar rango
                for i in range(min_idx, max_idx + 1):
                    self.tree.selection_add(all_items[i])

            except ValueError:
                pass  # Item no encontrado

    def fin_arrastre(self, event):
        """Finalizar arrastre"""
        if not self.dragging and self.drag_start_item:
            # Fue un clic simple, no arrastre
            if not (event.state & 0x4):  # Sin Ctrl
                self.tree.selection_set(self.drag_start_item)
            else:  # Con Ctrl, toggle selección
                if self.drag_start_item in self.tree.selection():
                    self.tree.selection_remove(self.drag_start_item)
                else:
                    self.tree.selection_add(self.drag_start_item)

        # Reset variables
        self.drag_start = None
        self.dragging = False
        self.drag_start_item = None


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
                self.status_label.configure(text=f"Todos los {registros_filtrados} registros seleccionados")
            else:
                self.status_label.configure(text=f"{registros_filtrados} registros filtrados seleccionados")
        else:
            self.status_label.configure(text="No hay datos para seleccionar")

    def obtener_seleccionados(self):
        """Obtener filas seleccionadas"""
        items = self.tree.selection()
        return [self.tree.item(item)['values'] for item in items]

    def filtrar_datos(self, *args):
        """Filtrar datos en memoria"""
        if not hasattr(self, 'datos_completos'):
            return

        termino = self.search_var.get().lower()
        fecha_min = self.first_date_text.get().strip()
        fecha_max = self.last_date_text.get().strip()

        if not termino and not fecha_min and not fecha_max:
            self.datos_actuales = self.datos_completos.copy()
        else:
                # Obtener índice de columna de fecha
            if self.db_connection:
                cursor = self.db_connection.cursor()
                columnas = [desc[0].lower() for desc in cursor.execute(f"SELECT * FROM {self.current_table or 'XMLDATA'} LIMIT 0").description]
                fecha_idx = next((i for i, col in enumerate(columnas) if 'fecha' in col), None)
            
            # Convertir fechas de dd-mm-yyyy a yyyy-mm-dd
            def convertir_fecha(fecha_str):
                try:
                    if len(fecha_str) == 10 and fecha_str.count('-') == 2:
                        dd, mm, yyyy = fecha_str.split('-')
                        return f"{yyyy}-{mm}-{dd}"
                    return fecha_str
                except:
                    return fecha_str
            
            fecha_min_conv = convertir_fecha(fecha_min) if fecha_min else ""
            fecha_max_conv = convertir_fecha(fecha_max) if fecha_max else ""
            
            self.datos_actuales = []
            for fila in self.datos_completos:
                # Filtro de texto
                cumple_texto = not termino or any(str(celda).lower().find(termino) >= 0 for celda in fila if celda)
                
                # Filtro de fecha
                cumple_fecha = True
                if fecha_idx is not None and (fecha_min_conv or fecha_max_conv):
                    fecha_fila = convertir_fecha(str(fila[fecha_idx])) if fila[fecha_idx] else ""
                    
                    if fecha_min_conv and fecha_fila < fecha_min_conv:
                        cumple_fecha = False
                    if fecha_max_conv and fecha_fila > fecha_max_conv:
                        cumple_fecha = False
                
                if cumple_texto and cumple_fecha:
                    self.datos_actuales.append(fila)

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
        """Actualizar vista con datos actuales manteniendo ordenamiento"""
        # Aplicar ordenamiento si hay uno activo
        if hasattr(self, 'sort_column') and self.sort_column and self.datos_actuales:
            cursor = self.db_connection.cursor()
            columnas = [desc[0] for desc in cursor.execute(f"SELECT * FROM {self.current_table or 'XMLDATA'} LIMIT 0").description]
            
            if self.sort_column in columnas:
                col_idx = columnas.index(self.sort_column)
                
                def sort_key(fila):
                    valor = fila[col_idx]
                    if valor is None:
                        return ""
                    try:
                        return float(valor)
                    except (ValueError, TypeError):
                        return str(valor).lower()
                
                self.datos_actuales.sort(key=sort_key, reverse=self.sort_reverse)
        
        # Limpiar y insertar datos
        self.tree.delete(*self.tree.get_children())
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
