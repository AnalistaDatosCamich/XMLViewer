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
            text="Seleccionar todo"
        )
        self.select_all_button.grid(row=0, column=1, pady=10, padx=5, sticky = "ew")

        self.copy_button = ctk.CTkButton(
            self.controls_frame,
            text="Copiar seleccionados"
        )
        self.copy_button.grid(row=0, column=2, pady=10, padx=5, sticky = "ew")

        #Search field
        self.search_var = ctk.StringVar()

        self.search_bar = ctk.CTkEntry(
            self.controls_frame,
            placeholder_text="Buscar...",
            textvariable= self.search_var,
            width=200
        )
        self.search_bar.grid(row=0, column=3, pady=10, padx=5, sticky = "ew")

        #Search between
        #First date
        self.first_date_bar = ctk.CTkEntry(
            self.controls_frame,
            placeholder_text="Fecha inicial",
            textvariable= self.search_var,
            width=100
        )
        self.first_date_bar.grid(row=0, column=4, pady=10, padx=5, sticky = "ew")

        #Last date
        self.last_date_bar = ctk.CTkEntry(
            self.controls_frame,
            placeholder_text="Fecha final",
            textvariable= self.search_var,
            width=100
        )
        self.last_date_bar.grid(row=0, column=5, pady=10, padx=5, sticky = "ew")

        self.clear_filter_button = ctk.CTkButton(
            self.controls_frame,
            text="Limpiar filtros"
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

    def select_folder(self):
        """Open folder dialog and store selected path"""
        folder_path = filedialog.askdirectory(title="Select Folder")
        if folder_path:
            self.status_label.configure(text=f"Carpeta: {os.path.basename(folder_path)}")

    def select_database(self):
        """Seleccionar archivo de base de datos SQLite"""
        db_path = filedialog.askopenfilename(
            title="Seleccionar Base de Datos",
            filetypes=[
                ("SQLite Database", "*.db *.sqlite *.sqlite3"),
                ("Todos los archivos", "*.*")
            ]
        )

        if db_path:
            self.load_database(db_path)

    def load_database(self, db_path):
        """Cargar base de datos SQLite"""
        try:
            # Cerrar conexión anterior si existe
            if self.db_connection:
                self.db_connection.close()

            # Conectar a la nueva base de datos
            self.db_connection = sqlite3.connect(db_path)
            self.current_db_path = db_path

            # Obtener lista de tablas
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

            if tables:
                # Actualizar ComboBox con las tablas disponibles
                self.table_combo.configure(values=tables)
                self.table_combo.set(tables[0])  # Seleccionar la primera tabla
                self.current_table = tables[0]

                # Cargar la primera tabla automáticamente
                self.load_table_data(tables[0])

                self.status_label.configure(text=f"BD: {os.path.basename(db_path)} - {len(tables)} tabla(s)")
            else:
                self.status_label.configure(text="No se encontraron tablas en la BD")
                messagebox.showwarning("Advertencia", "No se encontraron tablas en la base de datos.")

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al cargar la base de datos:\n{str(e)}")
            self.status_label.configure(text="Error al cargar BD")


if __name__ == "__main__":
    app = XMLViewerApp()
    app.mainloop()
