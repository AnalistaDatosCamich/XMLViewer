import customtkinter as ctk
import sqlite3
from tkinter import ttk
import tkinter as tk
import threading

ctk.set_appearance_mode("Dark")  # Dark mode
ctk.set_default_color_theme("dark-blue")  # Dark blue theme

class ShowSQL:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Visor SQLite")
        self.root.geometry("1000x700")

        # Cache simple
        self.cache = {}
        self.datos_actuales = []
        self.columnas = []
        self.sort_column = None
        self.sort_reverse = False

        # Variables para arrastre
        self.drag_start = None
        self.dragging = False
        self.drag_start_item = None

        # Frame principal
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Frame de controles
        self.controls_frame = ctk.CTkFrame(self.main_frame)
        self.controls_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Botones
        self.refresh_btn = ctk.CTkButton(
            self.controls_frame,
            text="Seleccionar carpeta",
            command=self.actualizar_datos,
            width=120
        )
        self.refresh_btn.pack(side="left", padx=5)

        # Botón seleccionar todo filtrado
        self.select_all_btn = ctk.CTkButton(
            self.controls_frame,
            text="Seleccionar Todo",
            command=self.seleccionar_todo_filtrado,
            width=120
        )
        self.select_all_btn.pack(side="left", padx=5)

        # Botón copiar
        self.copy_btn = ctk.CTkButton(
            self.controls_frame,
            text="Copiar",
            command=self.copiar_seleccion,
            width=100
        )
        self.copy_btn.pack(side="left", padx=5)

        # Campo de búsqueda
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self.filtrar_datos)

        self.search_entry = ctk.CTkEntry(
            self.controls_frame,
            placeholder_text="🔍 Buscar...",
            textvariable=self.search_var,
            width=200
        )
        self.search_entry.pack(side="left", padx=10)

        # Label de estado
        self.status_label = ctk.CTkLabel(self.controls_frame, text="")
        self.status_label.pack(side="right", padx=10)

        # Treeview
        self.setup_treeview()

        # Cargar datos inicial
        self.cargar_datos()

    def setup_treeview(self):
        tree_frame = tk.Frame(self.main_frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")

        # Treeview con selección múltiple
        self.tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            selectmode="extended"  # Selección múltiple
        )

        # Bind para ordenamiento, selección y arrastre
        self.tree.bind('<Button-1>', self.on_click)
        self.tree.bind('<ButtonPress-1>', self.inicio_arrastre)
        self.tree.bind('<B1-Motion>', self.durante_arrastre)
        self.tree.bind('<ButtonRelease-1>', self.fin_arrastre)
        self.tree.bind('<Control-c>', self.copiar_seleccion)
        self.tree.bind('<Button-3>', self.menu_contextual)  # Click derecho

        # Configurar scrollbars
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)

        # Pack con scrollbars visibles
        h_scrollbar.pack(side="bottom", fill="x")
        v_scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

    def on_click(self, event):
        """Manejar clics (separar headers de filas)"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            self.on_header_click(event)

    def on_header_click(self, event):
        """Manejar clic en headers para ordenar"""
        column = self.tree.identify_column(event.x, event.y)
        col_name = self.tree['columns'][int(column) - 1]
        self.ordenar_por_columna(col_name)

    def inicio_arrastre(self, event):
        """Iniciar selección por arrastre"""
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
        """Durante el arrastre, seleccionar rango"""
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

    def ordenar_por_columna(self, columna):
        """Ordenar datos por columna en memoria"""
        if self.sort_column == columna:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = columna
            self.sort_reverse = False

        # Encontrar índice de columna
        col_index = self.columnas.index(columna)

        # Ordenar datos en memoria
        self.datos_actuales.sort(
            key=lambda x: x[col_index] or '',
            reverse=self.sort_reverse
        )

        # Actualizar vista
        self.actualizar_treeview()

        # Actualizar indicador visual
        for col in self.columnas:
            if col == columna:
                direction = " ↓" if self.sort_reverse else " ↑"
                self.tree.heading(col, text=col + direction)
            else:
                self.tree.heading(col, text=col)

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
                cursor.execute("SELECT * FROM facturas")
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

    def datos_cargados(self, datos, columnas):
        """Callback cuando datos están listos"""
        self.datos_completos = datos
        self.datos_actuales = datos.copy()
        self.columnas = columnas

        self.configurar_treeview()
        self.actualizar_treeview()

        self.status_label.configure(text=f"✅ {len(datos)} registros cargados")
        self.refresh_btn.configure(state="normal")

    def error_carga(self, error):
        """Callback para errores"""
        self.status_label.configure(text=f"❌ Error: {error}")
        self.refresh_btn.configure(state="normal")

    def configurar_treeview(self):
        """Configurar columnas del treeview"""
        self.tree["columns"] = self.columnas
        self.tree["show"] = "headings"

        for col in self.columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, minwidth=100)  # Más ancho para scroll horizontal

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
            self.status_label.configure(text=f"📊 {total} registros")
        else:
            self.status_label.configure(text=f"📊 {mostrados}/{total} registros")

    def actualizar_datos(self):
        """Limpiar cache y recargar"""
        self.cache.clear()
        self.search_var.set("")  # Limpiar búsqueda
        self.sort_column = None
        self.sort_reverse = False
        self.cargar_datos()

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

    def seleccionar_todo(self):
        """Seleccionar todo sin filtros (método adicional)"""
        # Limpiar filtro temporalmente para mostrar todo
        filtro_anterior = self.search_var.get()
        self.search_var.set("")  # Esto disparará filtrar_datos y mostrará todo

        # Seleccionar después de un pequeño delay para que se actualice la vista
        self.root.after(10, lambda: self.seleccionar_todo_visible())

        # Restaurar filtro si había uno
        if filtro_anterior:
            self.root.after(20, lambda: self.search_var.set(filtro_anterior))

    def copiar_seleccion(self, event=None):
        """Copiar selección al clipboard"""
        seleccionados = self.obtener_seleccionados()
        if not seleccionados:
            return

        # Crear texto separado por tabs (formato Excel)
        texto = []

        # Headers
        headers = "\t".join(self.columnas)
        texto.append(headers)

        # Datos
        for fila in seleccionados:
            fila_texto = "\t".join(str(cell) if cell else "" for cell in fila)
            texto.append(fila_texto)

        # Copiar al clipboard
        contenido = "\n".join(texto)
        self.root.clipboard_clear()
        self.root.clipboard_append(contenido)

        self.status_label.configure(text=f"📋 {len(seleccionados)} filas copiadas")

    def menu_contextual(self, event):
        """Menú click derecho"""
        # Seleccionar item bajo cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)

        # Crear menú
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="📋 Copiar selección (Ctrl+C)", command=self.copiar_seleccion)
        menu.add_separator()
        menu.add_command(label="☑️ Seleccionar todo filtrado", command=self.seleccionar_todo_filtrado)
        menu.add_command(label="📊 Seleccionar todo", command=self.seleccionar_todo)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def obtener_seleccionados(self):
        """Obtener filas seleccionadas"""
        items = self.tree.selection()
        return [self.tree.item(item)['values'] for item in items]

    def ejecutar(self):
        self.root.mainloop()


# Uso
if __name__ == "__main__":
    app = ShowSQL()
    app.ejecutar()