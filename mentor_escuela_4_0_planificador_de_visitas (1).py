import calendar
import datetime
import random
import sqlite3
import tkinter as tk
from tkinter import colorchooser, messagebox, ttk

DB_NAME = "visitas_escuela40.db"


def init_db():
    """Inicializa la base de datos SQLite creando las tablas de centros y visitas."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabla de Centros Educativos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS centros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            codigo TEXT,
            localidad TEXT,
            etapa TEXT,
            contacto_nombre TEXT,
            contacto_email TEXT,
            color TEXT NOT NULL DEFAULT '#3B82F6'
        )
    """)

    # Tabla de Visitas / Planificación
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            centro_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            modalidad TEXT,
            objetivo_lomloe TEXT,
            planificacion TEXT,
            observaciones TEXT,
            FOREIGN KEY (centro_id) REFERENCES centros(id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    # Datos de prueba iniciales si la base de datos está vacía
    cursor.execute("SELECT COUNT(*) FROM centros")
    if cursor.fetchone()[0] == 0:
        centros_demo = [
            (
                "CEIP LOMLOE Innovación",
                "38001234",
                "Santa Cruz",
                "Primaria",
                "Coordinador TDE",
                "tde@ceiplomloe.es",
                "#3B82F6",
            ),
            (
                "IES Pensamiento Computacional",
                "38005678",
                "La Laguna",
                "Secundaria",
                "Jefe de Estudios",
                "estudios@iespc.es",
                "#10B981",
            ),
            (
                "CEIP Robotica Futuro",
                "38009999",
                "Arona",
                "Infantil y Primaria",
                "Asesora TIC",
                "tic@ceiprobotica.es",
                "#F59E0B",
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO centros (nombre, codigo, localidad, etapa, contacto_nombre, contacto_email, color)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            centros_demo,
        )

        today_str = datetime.date.today().strftime("%Y-%m-%d")
        cursor.execute(
            """
            INSERT INTO visitas (centro_id, fecha, modalidad, objetivo_lomloe, planificacion, observaciones)
            VALUES (1, ?, 'Conectada (Scratch)', 'Competencia Específica STEM3 - Algoritmos', 'Sesión de iniciación a Scratch con 5º de Primaria.', 'Traer placas Micro:bit para pruebas.')
        """,
            (today_str,),
        )
        conn.commit()

    conn.close()


def get_db_connection():
    """Retorna una conexión activa a SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


class PlanificadorVisitasApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Mentor Código Escuela 4.0 - Planificador de Visitas")
        self.root.geometry("1100x720")
        self.root.minsize(950, 650)

        # Configuración de fecha actual seleccionada
        self.today = datetime.date.today()
        self.current_year = self.today.year
        self.current_month = self.today.month
        self.selected_centro_filter = tk.IntVar(value=0)  # 0 = Todos

        # Configuración de estilos
        self.setup_styles()

        # Creación de pestañas principales
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_calendario = ttk.Frame(self.notebook)
        self.tab_centros = ttk.Frame(self.notebook)
        self.tab_historial = ttk.Frame(self.notebook)

        self.notebook.add(
            self.tab_calendario, text="📅 Planning del Curso Escolar"
        )
        self.notebook.add(self.tab_centros, text="🏫 Gestión de Centros")
        self.notebook.add(self.tab_historial, text="📋 Listado de Visitas")

        # Construir cada pestaña
        self.build_tab_calendario()
        self.build_tab_centros()
        self.build_tab_historial()

    def setup_styles(self):
        """Aplica estilos modernos a los componentes ttk."""
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Colores generales
        BG_COLOR = "#F8FAFC"
        PRIMARY = "#1E293B"

        self.root.configure(bg=BG_COLOR)
        self.style.configure(".", background=BG_COLOR, font=("Segoe UI", 10))
        self.style.configure(
            "TNotebook.Tab", padding=[12, 6], font=("Segoe UI", 10, "bold")
        )
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 11, "bold"))
        self.style.configure(
            "Primary.TButton",
            font=("Segoe UI", 9, "bold"),
            background="#2563EB",
            foreground="white",
        )
        self.style.map("Primary.TButton", background=[("active", "#1D4ED8")])

    def build_tab_calendario(self):
        """Pestaña con el calendario mensual interactivo y filtros."""
        top_frame = ttk.Frame(self.tab_calendario)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        # Título
        lbl_title = ttk.Label(
            top_frame,
            text="Planificación Mensual de Visitas",
            style="Header.TLabel",
        )
        lbl_title.pack(side=tk.LEFT, padx=5)

        # Controles de navegación de Mes / Año
        nav_frame = ttk.Frame(top_frame)
        nav_frame.pack(side=tk.RIGHT, padx=5)

        btn_prev = ttk.Button(
            nav_frame, text="◀ Mes Ant.", command=self.prev_month
        )
        btn_prev.pack(side=tk.LEFT, padx=2)

        self.lbl_month_year = ttk.Label(
            nav_frame, text="", style="SubHeader.TLabel", width=18, anchor="center"
        )
        self.lbl_month_year.pack(side=tk.LEFT, padx=5)

        btn_next = ttk.Button(
            nav_frame, text="Mes Sig. ▶", command=self.next_month
        )
        btn_next.pack(side=tk.LEFT, padx=2)

        btn_today = ttk.Button(
            nav_frame, text="Hoy", command=self.go_to_today
        )
        btn_today.pack(side=tk.LEFT, padx=5)

        # Barra de Filtrado por Centro
        filter_frame = ttk.Frame(self.tab_calendario)
        filter_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        ttk.Label(
            filter_frame,
            text="🔍 Filtrar por Centro:",
            font=("Segoe UI", 10, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.combo_filter_centro = ttk.Combobox(
            filter_frame, state="readonly", width=35
        )
        self.combo_filter_centro.pack(side=tk.LEFT, padx=5)
        self.combo_filter_centro.bind(
            "<<ComboboxSelected>>", self.on_filter_changed
        )

        # Contenedor del rejilla del calendario
        self.calendar_grid_frame = ttk.Frame(self.tab_calendario)
        self.calendar_grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Cargar lista de filtros y renderizar
        self.refresh_filter_combobox()
        self.render_calendar()

    def refresh_filter_combobox(self):
        """Actualiza el desplegable de filtro de centros."""
        conn = get_db_connection()
        centros = conn.execute(
            "SELECT id, nombre FROM centros ORDER BY nombre"
        ).fetchall()
        conn.close()

        self.centros_filter_map = {"Todos los centros": 0}
        options = ["Todos los centros"]

        for c in centros:
            display_name = c["nombre"]
            options.append(display_name)
            self.centros_filter_map[display_name] = c["id"]

        self.combo_filter_centro["values"] = options
        self.combo_filter_centro.current(0)

    def on_filter_changed(self, event=None):
        """Maneja el cambio de selección en el filtro de centro."""
        selected_text = self.combo_filter_centro.get()
        self.selected_centro_filter.set(
            self.centros_filter_map.get(selected_text, 0)
        )
        self.render_calendar()

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.render_calendar()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.render_calendar()

    def go_to_today(self):
        self.current_year = self.today.year
        self.current_month = self.today.month
        self.render_calendar()

    def render_calendar(self):
        """Dibuja la cuadrícula del calendario correspondiente al mes y año actuales."""
        # Limpiar rejilla anterior
        for widget in self.calendar_grid_frame.winfo_children():
            widget.destroy()

        # Nombres de meses en español
        meses_es = [
            "",
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre",
        ]
        self.lbl_month_year.config(
            text=f"{meses_es[self.current_month]} {self.current_year}"
        )

        # Encabezados de días de la semana
        dias_semana = [
            "Lunes",
            "Martes",
            "Miércoles",
            "Jueves",
            "Viernes",
            "Sábado",
            "Domingo",
        ]
        for col_idx, dia in enumerate(dias_semana):
            lbl = tk.Label(
                self.calendar_grid_frame,
                text=dia,
                font=("Segoe UI", 9, "bold"),
                bg="#E2E8F0",
                fg="#334155",
                pady=5,
            )
            lbl.grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=1)

        # Obtener datos de visitas para este mes
        start_date = f"{self.current_year:04d}-{self.current_month:02d}-01"
        end_date = f"{self.current_year:04d}-{self.current_month:02d}-31"

        conn = get_db_connection()
        filter_id = self.selected_centro_filter.get()

        if filter_id == 0:
            query = """
                SELECT v.id, v.fecha, v.modalidad, c.nombre as centro_nombre, c.color
                FROM visitas v
                JOIN centros c ON v.centro_id = c.id
                WHERE v.fecha BETWEEN ? AND ?
            """
            params = (start_date, end_date)
        else:
            query = """
                SELECT v.id, v.fecha, v.modalidad, c.nombre as centro_nombre, c.color
                FROM visitas v
                JOIN centros c ON v.centro_id = c.id
                WHERE v.fecha BETWEEN ? AND ? AND v.centro_id = ?
            """
            params = (start_date, end_date, filter_id)

        visitas_mes = conn.execute(query, params).fetchall()
        conn.close()

        # Organizar visitas por fecha (YYYY-MM-DD -> list de visitas)
        visitas_por_dia = {}
        for v in visitas_mes:
            fecha_key = v["fecha"]
            if fecha_key not in visitas_por_dia:
                visitas_por_dia[fecha_key] = []
            visitas_por_dia[fecha_key].append(v)

        # Matriz del calendario (semana x día)
        cal = calendar.monthcalendar(self.current_year, self.current_month)

        for r_idx, week in enumerate(cal):
            self.calendar_grid_frame.grid_rowconfigure(r_idx + 1, weight=1)
            for c_idx, day in enumerate(week):
                self.calendar_grid_frame.grid_columnconfigure(c_idx, weight=1)

                if day == 0:
                    # Día fuera del mes
                    empty_frame = tk.Frame(
                        self.calendar_grid_frame,
                        bg="#F1F5F9",
                        bd=1,
                        relief="solid",
                    )
                    empty_frame.grid(
                        row=r_idx + 1, column=c_idx, sticky="nsew", padx=1, pady=1
                    )
                    continue

                date_str = f"{self.current_year:04d}-{self.current_month:02d}-{day:02d}"

                # Es hoy?
                is_today = (
                    day == self.today.day
                    and self.current_month == self.today.month
                    and self.current_year == self.today.year
                )

                bg_day = "#EFF6FF" if is_today else "#FFFFFF"

                day_frame = tk.Frame(
                    self.calendar_grid_frame,
                    bg=bg_day,
                    bd=1,
                    relief="solid",
                    cursor="hand2",
                )
                day_frame.grid(
                    row=r_idx + 1, column=c_idx, sticky="nsew", padx=1, pady=1
                )

                # Número de día
                lbl_day_num = tk.Label(
                    day_frame,
                    text=str(day),
                    font=(
                        "Segoe UI",
                        10,
                        "bold" if is_today else "normal",
                    ),
                    bg=bg_day,
                    fg="#1E40AF" if is_today else "#1E293B",
                    anchor="nw",
                )
                lbl_day_num.pack(anchor="nw", padx=3, pady=2)

                # Renderizar distintivos de visitas programadas para el día
                if date_str in visitas_por_dia:
                    for vis in visitas_por_dia[date_str]:
                        badge_color = vis["color"] or "#3B82F6"
                        # Contenedor de la visita con color de fondo del centro
                        lbl_badge = tk.Label(
                            day_frame,
                            text=f"• {vis['centro_nombre']}",
                            bg=badge_color,
                            fg="white",
                            font=("Segoe UI", 8, "bold"),
                            anchor="w",
                            padx=4,
                            pady=1,
                        )
                        lbl_badge.pack(fill=tk.X, padx=2, pady=1)
                        # Vincular clic también en el badge
                        lbl_badge.bind(
                            "<Button-1>",
                            lambda e, d=date_str: self.open_visit_dialog(d),
                        )

                # Evento de clic en la casilla del día para añadir/ver visitas
                day_frame.bind(
                    "<Button-1>",
                    lambda e, d=date_str: self.open_visit_dialog(d),
                )
                lbl_day_num.bind(
                    "<Button-1>",
                    lambda e, d=date_str: self.open_visit_dialog(d),
                )

    def open_visit_dialog(self, date_str):
        """Abre la ventana modal interactiva para gestionar las visitas de un día específico."""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Planificación de Visita - {date_str}")
        dialog.geometry("600x650")
        dialog.resizable(True, True)
        dialog.configure(bg="#F8FAFC")
        dialog.transient(self.root)

        # Centrar la ventana emergente respecto a la ventana principal
        dialog.update_idletasks()
        x = max(0, self.root.winfo_x() + (self.root.winfo_width() // 2) - 300)
        y = max(0, self.root.winfo_y() + (self.root.winfo_height() // 2) - 325)
        dialog.geometry(f"600x650+{x}+{y}")

        try:
            conn = get_db_connection()
            centros = conn.execute("SELECT id, nombre FROM centros ORDER BY nombre").fetchall()
            
            # Buscar si ya existe una visita grabada para esa fecha
            existing_visit = conn.execute(
                "SELECT * FROM visitas WHERE fecha = ?", (date_str,)
            ).fetchone()
            conn.close()
        except Exception as err:
            messagebox.showerror("Error", f"Error al acceder a la base de datos: {err}", parent=dialog)
            dialog.destroy()
            return

        # Cabecera de la ventana
        header_frame = tk.Frame(dialog, bg="#1E293B", pady=12, padx=15)
        header_frame.pack(fill=tk.X)

        lbl_header = tk.Label(
            header_frame,
            text=f"📅 Planificación del Día: {date_str}",
            font=("Segoe UI", 12, "bold"),
            fg="#FFFFFF",
            bg="#1E293B"
        )
        lbl_header.pack(anchor="w")

        # Panel principal del formulario con campos visibles de alto contraste
        container = tk.Frame(dialog, bg="#F8FAFC", padx=20, pady=15)
        container.pack(fill=tk.BOTH, expand=True)

        # 1. Selector / Entrada de Centro Educativo
        lbl_c = tk.Label(container, text="Centro Educativo:", font=("Segoe UI", 10, "bold"), bg="#F8FAFC", fg="#1E293B")
        lbl_c.grid(row=0, column=0, sticky="w", pady=(5, 2))

        centros_map = {c["nombre"]: c["id"] for c in centros} if centros else {}
        centros_list = list(centros_map.keys())

        centro_var = tk.StringVar()
        combo_centro = ttk.Combobox(container, textvariable=centro_var, values=centros_list, font=("Segoe UI", 10))
        combo_centro.grid(row=1, column=0, sticky="ew", pady=(0, 2))
        
        lbl_hint = tk.Label(container, text="💡 Elige un centro existente o escribe el nombre de uno nuevo.", font=("Segoe UI", 8, "italic"), bg="#F8FAFC", fg="#64748B")
        lbl_hint.grid(row=2, column=0, sticky="w", pady=(0, 10))

        # 2. Modalidad de Trabajo
        lbl_m = tk.Label(container, text="Modalidad de la Actividad:", font=("Segoe UI", 10, "bold"), bg="#F8FAFC", fg="#1E293B")
        lbl_m.grid(row=3, column=0, sticky="w", pady=(5, 2))

        modalidades = [
            "Conectada (Scratch, MakeCode, Python)",
            "Desconectada (Unplugged / Lógica / Juegos)",
            "Robótica / Hardware (Micro:bit, mBot, Spike)",
            "Asesoramiento LOMLOE / TDE",
            "Formación de Profesorado"
        ]
        combo_modalidad = ttk.Combobox(container, values=modalidades, state="readonly", font=("Segoe UI", 10))
        combo_modalidad.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        combo_modalidad.current(0)

        # 3. ¿Qué se va a hacer o se ha hecho?
        lbl_p = tk.Label(container, text="¿Qué se va a hacer o se ha hecho? (Planificación / Reto):", font=("Segoe UI", 10, "bold"), bg="#F8FAFC", fg="#1E293B")
        lbl_p.grid(row=5, column=0, sticky="w", pady=(5, 2))

        txt_plan = tk.Text(container, height=4, font=("Segoe UI", 10), bg="#FFFFFF", fg="#0F172A", relief="solid", bd=1, insertbackground="#000000")
        txt_plan.grid(row=6, column=0, sticky="ew", pady=(0, 10))

        # 4. Vinculación LOMLOE
        lbl_l = tk.Label(container, text="Vinculación LOMLOE (Competencias / Criterios):", font=("Segoe UI", 10, "bold"), bg="#F8FAFC", fg="#1E293B")
        lbl_l.grid(row=7, column=0, sticky="w", pady=(5, 2))

        txt_lomloe = tk.Text(container, height=3, font=("Segoe UI", 10), bg="#FFFFFF", fg="#0F172A", relief="solid", bd=1, insertbackground="#000000")
        txt_lomloe.grid(row=8, column=0, sticky="ew", pady=(0, 10))

        # 5. Observaciones
        lbl_o = tk.Label(container, text="Observaciones / Materiales:", font=("Segoe UI", 10, "bold"), bg="#F8FAFC", fg="#1E293B")
        lbl_o.grid(row=9, column=0, sticky="w", pady=(5, 2))

        txt_obs = tk.Text(container, height=3, font=("Segoe UI", 10), bg="#FFFFFF", fg="#0F172A", relief="solid", bd=1, insertbackground="#000000")
        txt_obs.grid(row=10, column=0, sticky="ew", pady=(0, 10))

        container.columnconfigure(0, weight=1)

        if existing_visit:
            conn = get_db_connection()
            c_row = conn.execute("SELECT nombre FROM centros WHERE id = ?", (existing_visit["centro_id"],)).fetchone()
            conn.close()
            if c_row:
                centro_var.set(c_row["nombre"])
            if existing_visit["modalidad"]:
                combo_modalidad.set(existing_visit["modalidad"])
            txt_plan.insert("1.0", existing_visit["planificacion"] or "")
            txt_lomloe.insert("1.0", existing_visit["objetivo_lomloe"] or "")
            txt_obs.insert("1.0", existing_visit["observaciones"] or "")
        elif centros_list:
            combo_centro.current(0)

        # Botones de la parte inferior
        btn_frame = tk.Frame(dialog, bg="#E2E8F0", pady=10, padx=15)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        def save_visit():
            centro_nombre = centro_var.get().strip()
            if not centro_nombre:
                messagebox.showerror("Campo vacío", "Por favor, escribe o selecciona un Centro Educativo.", parent=dialog)
                return

            conn = get_db_connection()
            
            # Comprobar si existe el centro o registrarlo automáticamente
            c_row = conn.execute("SELECT id FROM centros WHERE LOWER(nombre) = LOWER(?)", (centro_nombre,)).fetchone()
            if c_row:
                c_id = c_row["id"]
            else:
                palette = ["#3B82F6", "#10B981", "#F59E0B", "#EC4899", "#8B5CF6", "#06B6D4"]
                color_def = random.choice(palette)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO centros (nombre, color) VALUES (?, ?)",
                    (centro_nombre, color_def)
                )
                c_id = cursor.lastrowid

            mod = combo_modalidad.get()
            plan = txt_plan.get("1.0", tk.END).strip()
            lomloe = txt_lomloe.get("1.0", tk.END).strip()
            obs = txt_obs.get("1.0", tk.END).strip()

            if existing_visit:
                conn.execute(
                    """
                    UPDATE visitas
                    SET centro_id = ?, modalidad = ?, objetivo_lomloe = ?, planificacion = ?, observaciones = ?
                    WHERE id = ?
                    """,
                    (c_id, mod, lomloe, plan, obs, existing_visit["id"])
                )
            else:
                conn.execute(
                    """
                    INSERT INTO visitas (centro_id, fecha, modalidad, objetivo_lomloe, planificacion, observaciones)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (c_id, date_str, mod, lomloe, plan, obs)
                )

            conn.commit()
            conn.close()

            messagebox.showinfo("Éxito", "¡Planificación guardada correctamente!", parent=dialog)
            dialog.destroy()
            self.refresh_filter_combobox()
            self.render_calendar()
            self.load_historial_visitas()

        def delete_visit():
            if not existing_visit:
                return
            if messagebox.askyesno("Confirmar", "¿Deseas eliminar la visita de este día?", parent=dialog):
                conn = get_db_connection()
                conn.execute("DELETE FROM visitas WHERE id = ?", (existing_visit["id"],))
                conn.commit()
                conn.close()
                dialog.destroy()
                self.render_calendar()
                self.load_historial_visitas()

        btn_save = tk.Button(
            btn_frame,
            text="💾 Guardar Planificación",
            font=("Segoe UI", 10, "bold"),
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            activeforeground="white",
            padx=12,
            pady=6,
            bd=0,
            cursor="hand2",
            command=save_visit
        )
        btn_save.pack(side=tk.RIGHT, padx=5)

        if existing_visit:
            btn_del = tk.Button(
                btn_frame,
                text="🗑️ Eliminar",
                font=("Segoe UI", 9),
                bg="#EF4444",
                fg="white",
                activebackground="#DC2626",
                activeforeground="white",
                padx=10,
                pady=6,
                bd=0,
                cursor="hand2",
                command=delete_visit
            )
            btn_del.pack(side=tk.RIGHT, padx=5)

        btn_cancel = tk.Button(
            btn_frame,
            text="Cancelar",
            font=("Segoe UI", 9),
            bg="#94A3B8",
            fg="white",
            padx=10,
            pady=6,
            bd=0,
            cursor="hand2",
            command=dialog.destroy
        )
        btn_cancel.pack(side=tk.LEFT, padx=5)

    def build_tab_centros(self):
        """Pestaña para gestionar la base de datos de centros y sus colores."""
        main_split = ttk.PanedWindow(self.tab_centros, orient=tk.HORIZONTAL)
        main_split.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Izquierda: Formulario Agregar/Editar Centro
        form_frame = ttk.LabelFrame(
            main_split, text=" Datos del Centro ", padding=10
        )
        main_split.add(form_frame, weight=1)

        ttk.Label(form_frame, text="Nombre del Centro:").grid(
            row=0, column=0, sticky="w", pady=4
        )
        self.entry_c_nombre = ttk.Entry(form_frame, width=28)
        self.entry_c_nombre.grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(form_frame, text="Código del Centro:").grid(
            row=1, column=0, sticky="w", pady=4
        )
        self.entry_c_codigo = ttk.Entry(form_frame, width=28)
        self.entry_c_codigo.grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(form_frame, text="Localidad:").grid(
            row=2, column=0, sticky="w", pady=4
        )
        self.entry_c_localidad = ttk.Entry(form_frame, width=28)
        self.entry_c_localidad.grid(row=2, column=1, sticky="w", pady=4)

        ttk.Label(form_frame, text="Etapa Educativa:").grid(
            row=3, column=0, sticky="w", pady=4
        )
        self.combo_c_etapa = ttk.Combobox(
            form_frame,
            values=[
                "Infantil",
                "Primaria",
                "Secundaria",
                "Infantil y Primaria",
                "Centro Integrado (CEIPO/IES)",
            ],
            width=26,
        )
        self.combo_c_etapa.grid(row=3, column=1, sticky="w", pady=4)
        self.combo_c_etapa.current(1)

        ttk.Label(form_frame, text="Contacto (Nombre):").grid(
            row=4, column=0, sticky="w", pady=4
        )
        self.entry_c_contacto = ttk.Entry(form_frame, width=28)
        self.entry_c_contacto.grid(row=4, column=1, sticky="w", pady=4)

        ttk.Label(form_frame, text="Contacto (Email):").grid(
            row=5, column=0, sticky="w", pady=4
        )
        self.entry_c_email = ttk.Entry(form_frame, width=28)
        self.entry_c_email.grid(row=5, column=1, sticky="w", pady=4)

        # Color asociable al centro
        ttk.Label(form_frame, text="Color Referencia:").grid(
            row=6, column=0, sticky="w", pady=4
        )
        color_box = ttk.Frame(form_frame)
        color_box.grid(row=6, column=1, sticky="w", pady=4)

        self.selected_color = "#3B82F6"
        self.lbl_color_preview = tk.Label(
            color_box,
            text="   ",
            bg=self.selected_color,
            width=6,
            relief="solid",
            bd=1,
        )
        self.lbl_color_preview.pack(side=tk.LEFT, padx=(0, 5))

        btn_pick_color = ttk.Button(
            color_box, text="🎨 Seleccionar", command=self.pick_color
        )
        btn_pick_color.pack(side=tk.LEFT)

        # ID oculto para edición
        self.editing_centro_id = None

        # Botones de Acción para Centros
        btn_c_frame = ttk.Frame(form_frame)
        btn_c_frame.grid(row=7, column=0, columnspan=2, pady=15)

        self.btn_save_centro = ttk.Button(
            btn_c_frame,
            text="➕ Guardar Centro",
            style="Primary.TButton",
            command=self.save_centro,
        )
        self.btn_save_centro.pack(side=tk.LEFT, padx=5)

        btn_clear_centro = ttk.Button(
            btn_c_frame, text="Limpiar", command=self.clear_centro_form
        )
        btn_clear_centro.pack(side=tk.LEFT, padx=5)

        # Derecha: Tabla de Centros
        table_frame = ttk.LabelFrame(
            main_split, text=" Centros Registrados ", padding=10
        )
        main_split.add(table_frame, weight=2)

        columns = ("id", "nombre", "codigo", "localidad", "etapa", "contacto")
        self.tree_centros = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=12
        )

        self.tree_centros.heading("id", text="ID")
        self.tree_centros.heading("nombre", text="Nombre")
        self.tree_centros.heading("codigo", text="Código")
        self.tree_centros.heading("localidad", text="Localidad")
        self.tree_centros.heading("etapa", text="Etapa")
        self.tree_centros.heading("contacto", text="Contacto")

        self.tree_centros.column("id", width=30, anchor="center")
        self.tree_centros.column("nombre", width=160)
        self.tree_centros.column("codigo", width=70)
        self.tree_centros.column("localidad", width=90)
        self.tree_centros.column("etapa", width=90)
        self.tree_centros.column("contacto", width=110)

        scrollbar_c = ttk.Scrollbar(
            table_frame, orient=tk.VERTICAL, command=self.tree_centros.yview
        )
        self.tree_centros.configure(yscroll=scrollbar_c.set)

        self.tree_centros.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True
        )
        scrollbar_c.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_centros.bind(
            "<<TreeviewSelect>>", self.on_centro_select
        )

        # Cargar centros en la tabla
        self.load_centros_table()

    def pick_color(self):
        """Abre el selector de color de Tkinter."""
        color = colorchooser.askcolor(initialcolor=self.selected_color)
        if color[1]:
            self.selected_color = color[1]
            self.lbl_color_preview.config(bg=self.selected_color)

    def clear_centro_form(self):
        self.editing_centro_id = None
        self.entry_c_nombre.delete(0, tk.END)
        self.entry_c_codigo.delete(0, tk.END)
        self.entry_c_localidad.delete(0, tk.END)
        self.entry_c_contacto.delete(0, tk.END)
        self.entry_c_email.delete(0, tk.END)
        self.combo_c_etapa.current(1)
        self.selected_color = "#3B82F6"
        self.lbl_color_preview.config(bg=self.selected_color)
        self.btn_save_centro.config(text="➕ Guardar Centro")

    def save_centro(self):
        nombre = self.entry_c_nombre.get().strip()
        if not nombre:
            messagebox.showerror(
                "Error", "El nombre del centro es obligatorio."
            )
            return

        codigo = self.entry_c_codigo.get().strip()
        localidad = self.entry_c_localidad.get().strip()
        etapa = self.combo_c_etapa.get()
        contacto = self.entry_c_contacto.get().strip()
        email = self.entry_c_email.get().strip()
        color = self.selected_color

        conn = get_db_connection()
        if self.editing_centro_id:
            conn.execute(
                """
                UPDATE centros
                SET nombre = ?, codigo = ?, localidad = ?, etapa = ?, contacto_nombre = ?, contacto_email = ?, color = ?
                WHERE id = ?
            """,
                (
                    nombre,
                    codigo,
                    localidad,
                    etapa,
                    contacto,
                    email,
                    color,
                    self.editing_centro_id,
                ),
            )
            messagebox.showinfo("Éxito", "Centro actualizado correctamente.")
        else:
            conn.execute(
                """
                INSERT INTO centros (nombre, codigo, localidad, etapa, contacto_nombre, contacto_email, color)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (nombre, codigo, localidad, etapa, contacto, email, color),
            )
            messagebox.showinfo("Éxito", "Centro añadido correctamente.")

        conn.commit()
        conn.close()

        self.clear_centro_form()
        self.load_centros_table()
        self.refresh_filter_combobox()
        self.render_calendar()

    def load_centros_table(self):
        for item in self.tree_centros.get_children():
            self.tree_centros.delete(item)

        conn = get_db_connection()
        centros = conn.execute("SELECT * FROM centros ORDER BY nombre").fetchall()
        conn.close()

        for c in centros:
            self.tree_centros.insert(
                "",
                tk.END,
                values=(
                    c["id"],
                    c["nombre"],
                    c["codigo"],
                    c["localidad"],
                    c["etapa"],
                    c["contacto_nombre"],
                ),
            )

    def on_centro_select(self, event):
        selected_items = self.tree_centros.selection()
        if not selected_items:
            return

        item = self.tree_centros.item(selected_items[0])
        centro_id = item["values"][0]

        conn = get_db_connection()
        c = conn.execute(
            "SELECT * FROM centros WHERE id = ?", (centro_id,)
        ).fetchone()
        conn.close()

        if c:
            self.editing_centro_id = c["id"]
            self.entry_c_nombre.delete(0, tk.END)
            self.entry_c_nombre.insert(0, c["nombre"])

            self.entry_c_codigo.delete(0, tk.END)
            self.entry_c_codigo.insert(0, c["codigo"] or "")

            self.entry_c_localidad.delete(0, tk.END)
            self.entry_c_localidad.insert(0, c["localidad"] or "")

            self.combo_c_etapa.set(c["etapa"] or "Primaria")

            self.entry_c_contacto.delete(0, tk.END)
            self.entry_c_contacto.insert(0, c["contacto_nombre"] or "")

            self.entry_c_email.delete(0, tk.END)
            self.entry_c_email.insert(0, c["contacto_email"] or "")

            self.selected_color = c["color"] or "#3B82F6"
            self.lbl_color_preview.config(bg=self.selected_color)

            self.btn_save_centro.config(text="✏️ Actualizar Centro")

    def build_tab_historial(self):
        """Pestaña con el listado global de visitas planificadas con buscador."""
        top_bar = ttk.Frame(self.tab_historial)
        top_bar.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(
            top_bar,
            text="Listado Histórico de Visitas",
            style="Header.TLabel",
        ).pack(side=tk.LEFT)

        btn_refresh = ttk.Button(
            top_bar, text="🔄 Actualizar Lista", command=self.load_historial_visitas
        )
        btn_refresh.pack(side=tk.RIGHT)

        # Tabla de Historial
        columns = ("id", "fecha", "centro", "modalidad", "lomloe", "plan")
        self.tree_historial = ttk.Treeview(
            self.tab_historial, columns=columns, show="headings"
        )

        self.tree_historial.heading("id", text="ID")
        self.tree_historial.heading("fecha", text="Fecha")
        self.tree_historial.heading("centro", text="Centro")
        self.tree_historial.heading("modalidad", text="Modalidad")
        self.tree_historial.heading("lomloe", text="Objetivo LOMLOE")
        self.tree_historial.heading("plan", text="Planificación / Reto")

        self.tree_historial.column("id", width=30, anchor="center")
        self.tree_historial.column("fecha", width=90, anchor="center")
        self.tree_historial.column("centro", width=160)
        self.tree_historial.column("modalidad", width=140)
        self.tree_historial.column("lomloe", width=220)
        self.tree_historial.column("plan", width=250)

        scrollbar_h = ttk.Scrollbar(
            self.tab_historial,
            orient=tk.VERTICAL,
            command=self.tree_historial.yview,
        )
        self.tree_historial.configure(yscroll=scrollbar_h.set)

        self.tree_historial.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10)
        )
        scrollbar_h.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10))

        # Doble clic para abrir/editar la planificación
        self.tree_historial.bind("<Double-1>", self.on_historial_double_click)

        self.load_historial_visitas()

    def load_historial_visitas(self):
        """Carga todas las visitas programadas ordenadas por fecha."""
        for item in self.tree_historial.get_children():
            self.tree_historial.delete(item)

        conn = get_db_connection()
        query = """
            SELECT v.id, v.fecha, c.nombre as centro_nombre, v.modalidad, v.objetivo_lomloe, v.planificacion
            FROM visitas v
            JOIN centros c ON v.centro_id = c.id
            ORDER BY v.fecha DESC
        """
        visitas = conn.execute(query).fetchall()
        conn.close()

        for v in visitas:
            self.tree_historial.insert(
                "",
                tk.END,
                values=(
                    v["id"],
                    v["fecha"],
                    v["centro_nombre"],
                    v["modalidad"],
                    v["objetivo_lomloe"],
                    v["planificacion"],
                ),
            )

    def on_historial_double_click(self, event):
        selected_items = self.tree_historial.selection()
        if not selected_items:
            return

        item = self.tree_historial.item(selected_items[0])
        fecha = item["values"][1]
        self.open_visit_dialog(fecha)


if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = PlanificadorVisitasApp(root)
    root.mainloop()