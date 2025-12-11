import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import random
import statistics
import simpy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ==========================================================
#      LOGICA DE SIMULACIÓN (BACKEND) - SIN CAMBIOS
# ==========================================================

FACTOR_POSICION = {
    "portero":      {"ataque": 0.01, "control": 0.2, "medio": 0.5},
    "defensa":      {"ataque": 0.15, "control": 0.5, "medio": 0.8},
    "mediocampo":   {"ataque": 0.60, "control": 1.0, "medio": 1.0},
    "delantero":    {"ataque": 1.30, "control": 0.7, "medio": 0.9}
}

FACTOR_TACTICA = {
    "defensivo": {"ataque_rival": 0.5, "defensa_rival": 1.5},
    "neutral":   {"ataque_rival": 1.0, "defensa_rival": 1.0},
    "ofensivo":  {"ataque_rival": 1.5, "defensa_rival": 0.8}
}

def regresion_lineal(datos):
    if not datos or len(datos) < 2: return 0, 0
    X = [d[0] for d in datos]
    Y = [d[2] for d in datos]
    x_prom = statistics.mean(X)
    y_prom = statistics.mean(Y)
    num = sum((x - x_prom) * (y - y_prom) for x, y in zip(X, Y))
    den = sum((x - x_prom)**2 for x in X)
    if den == 0: return 0, y_prom
    b = num / den
    a = y_prom - b * x_prom
    return a, b

def rendimiento_esperado(a, b, fuerza_rival, localia, posicion, tactica):
    pases_base = a + b * fuerza_rival
    pases_base *= 1.10 if localia == 1 else 0.90
    pos_factor = FACTOR_POSICION[posicion]
    tact_factor = FACTOR_TACTICA[tactica]
    sigma_pases = 12 if (posicion == "defensa" and tactica == "ofensivo") else 5
    pases_estimados = pases_base * pos_factor.get("medio", 1.0) * tact_factor["defensa_rival"]
    pases = max(0, random.gauss(pases_estimados, sigma_pases))
    chance_base = pos_factor["ataque"]
    factor_fuerza = (11 - fuerza_rival) * 0.15
    factor_defensa = 1 / tact_factor["defensa_rival"]
    prob_gol = (chance_base * factor_fuerza * factor_defensa) * 0.15
    prob_gol = min(prob_gol, 0.60) 
    oportunidades = int(max(1, random.gauss(3, 1)))
    goles = 0
    for _ in range(oportunidades):
        if random.random() < prob_gol:
            goles += 1
    tiros = oportunidades + random.randint(0, 2)
    return pases, tiros, goles

def sim_montecarlo(env, a, b, fuerza, loc, pos, tac, res):
    while True:
        p, t, g = rendimiento_esperado(a, b, fuerza, loc, pos, tac)
        res["pases"].append(p)
        res["tiros"].append(t)
        res["goles"].append(g)
        yield env.timeout(1)

def ejecutar_simulacion_logica(historial_data, fuerza, localia, posicion, tactica, n=300):
    a, b = regresion_lineal(historial_data)
    env = simpy.Environment()
    resultados = {"pases": [], "tiros": [], "goles": []}
    env.process(sim_montecarlo(env, a, b, fuerza, localia, posicion, tactica, resultados))
    env.run(until=n)
    return resultados

# ==========================================================
#      INTERFAZ GRÁFICA (FRONTEND)
# ==========================================================

class AplicacionSimulacion:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Rendimiento Deportivo")
        self.root.geometry("1100x750") 
        
        self.historial_cargado = []
        
        # --- PANELES PRINCIPALES ---
        self.panel_izquierdo = tk.Frame(self.root, width=350, padx=10, pady=10)
        self.panel_izquierdo.pack(side="left", fill="y")
        
        ttk.Separator(self.root, orient="vertical").pack(side="left", fill="y", padx=5)

        self.panel_derecho = tk.Frame(self.root, padx=20, pady=10, bg="#f5f5f5")
        self.panel_derecho.pack(side="right", fill="both", expand=True)

        self.crear_widgets_izquierda()
        self.crear_widgets_derecha()

    def crear_widgets_izquierda(self):
        lbl_titulo = tk.Label(self.panel_izquierdo, text="Configuración", font=("Arial", 14, "bold"))
        lbl_titulo.pack(pady=(0, 10))

        frame_inputs = tk.LabelFrame(self.panel_izquierdo, text="Datos del Partido", padx=10, pady=10)
        frame_inputs.pack(fill="x", pady=5)

        tk.Label(frame_inputs, text="Nombre Jugador:").grid(row=0, column=0, sticky="e")
        self.ent_nombre = tk.Entry(frame_inputs)
        self.ent_nombre.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        tk.Label(frame_inputs, text="Posición:").grid(row=1, column=0, sticky="e")
        self.combo_pos = ttk.Combobox(frame_inputs, values=list(FACTOR_POSICION.keys()), state="readonly")
        self.combo_pos.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.combo_pos.current(3)

        tk.Label(frame_inputs, text="Nombre Rival:").grid(row=2, column=0, sticky="e")
        self.ent_rival = tk.Entry(frame_inputs)
        self.ent_rival.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        tk.Label(frame_inputs, text="Táctica Rival:").grid(row=3, column=0, sticky="e")
        self.combo_tactica = ttk.Combobox(frame_inputs, values=list(FACTOR_TACTICA.keys()), state="readonly")
        self.combo_tactica.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.combo_tactica.current(1)

        tk.Label(frame_inputs, text="Fuerza Rival (1-10):").grid(row=4, column=0, sticky="e")
        self.scale_fuerza = tk.Scale(frame_inputs, from_=1, to=10, orient="horizontal")
        self.scale_fuerza.set(5)
        self.scale_fuerza.grid(row=4, column=1, sticky="w", padx=5, pady=5)

        tk.Label(frame_inputs, text="Localía:").grid(row=5, column=0, sticky="e")
        self.var_localia = tk.IntVar(value=1)
        f_radio = tk.Frame(frame_inputs)
        f_radio.grid(row=5, column=1, sticky="w")
        tk.Radiobutton(f_radio, text="Local", variable=self.var_localia, value=1).pack(side="left")
        tk.Radiobutton(f_radio, text="Visitante", variable=self.var_localia, value=0).pack(side="left")

        frame_file = tk.LabelFrame(self.panel_izquierdo, text="Datos Históricos", padx=10, pady=10)
        frame_file.pack(fill="x", pady=10)
        
        btn_cargar = tk.Button(frame_file, text="📂 Cargar Excel/CSV", command=self.cargar_archivo, bg="#e1e1e1")
        btn_cargar.pack(side="left", padx=5)
        self.lbl_archivo = tk.Label(frame_file, text="Sin archivo", fg="red", font=("Arial", 8))
        self.lbl_archivo.pack(side="left")

        btn_simular = tk.Button(self.panel_izquierdo, text="▶ EJECUTAR SIMULACIÓN", command=self.simular, 
                                bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), height=2)
        btn_simular.pack(fill="x", pady=20)

    def crear_widgets_derecha(self):
        # 1. Título y Resumen del Partido
        self.lbl_resumen_titulo = tk.Label(self.panel_derecho, text="Resultados de Simulación", font=("Arial", 16, "bold"), bg="#f5f5f5")
        self.lbl_resumen_titulo.pack(pady=(0, 5))
        
        self.lbl_resumen_detalle = tk.Label(self.panel_derecho, text="Configure los datos y presione Ejecutar", font=("Arial", 10), bg="#f5f5f5", fg="#555")
        self.lbl_resumen_detalle.pack(pady=(0, 15))

        # 2. TABLA (Treeview) para mostrar resultados numéricos
        # Definimos las columnas
        columns = ("metrica", "valor")
        self.tabla = ttk.Treeview(self.panel_derecho, columns=columns, show="headings", height=6)
        
        # Configurar encabezados
        self.tabla.heading("metrica", text="Indicador Clave")
        self.tabla.heading("valor", text="Valor Estimado")
        
        # Configurar columnas (tamaño y alineación)
        self.tabla.column("metrica", width=250, anchor="center")
        self.tabla.column("valor", width=150, anchor="center")
        
        self.tabla.pack(fill="x", padx=10)

        # 3. Área para Gráficas
        self.frame_grafica = tk.Frame(self.panel_derecho, bg="white", bd=2, relief="sunken")
        self.frame_grafica.pack(fill="both", expand=True, padx=10, pady=15)
        
        tk.Label(self.frame_grafica, text="Las gráficas se generarán aquí...", bg="white", fg="#aaa").pack(expand=True)

    def cargar_archivo(self):
        filepath = filedialog.askopenfilename(filetypes=[("Datos", "*.xlsx *.xls *.csv")])
        if not filepath: return
        try:
            if filepath.endswith('.csv'): df = pd.read_csv(filepath)
            else: df = pd.read_excel(filepath)
            
            required = {'fuerza_rival', 'localia', 'pases', 'tiros', 'goles'}
            if not required.issubset(df.columns):
                messagebox.showerror("Error", f"Faltan columnas: {required - set(df.columns)}")
                return

            self.historial_cargado = df[['fuerza_rival', 'localia', 'pases', 'tiros', 'goles']].values.tolist()
            self.lbl_archivo.config(text=f"Cargado ({len(self.historial_cargado)})", fg="green")
            messagebox.showinfo("Listo", "Historial cargado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def simular(self):
        if not self.historial_cargado or len(self.historial_cargado) < 2:
            messagebox.showwarning("Faltan Datos", "Cargue un archivo con historial (min 2 partidos).")
            return

        nom = self.ent_nombre.get()
        riv = self.ent_rival.get()
        if not nom or not riv:
            messagebox.showwarning("Incompleto", "Ingrese nombres de jugador y rival.")
            return

        pos = self.combo_pos.get()
        tac = self.combo_tactica.get()
        fue = self.scale_fuerza.get()
        loc = self.var_localia.get()

        try:
            # --- Lógica de Simulación ---
            res = ejecutar_simulacion_logica(self.historial_cargado, fue, loc, pos, tac)
            
            # --- Cálculos ---
            p_prom = statistics.mean(res["pases"])
            t_prom = statistics.mean(res["tiros"])
            g_prom = statistics.mean(res["goles"])
            prob_gol = (sum(1 for g in res["goles"] if g > 0) / len(res["goles"])) * 100
            
            scores = [(p*0.05 + t*1 + g*5) for p,t,g in zip(res["pases"], res["tiros"], res["goles"])]
            umbral = statistics.mean(scores) + statistics.stdev(scores)
            prob_mvp = (sum(1 for s in scores if s > umbral) / len(scores)) * 100

            # --- ACTUALIZAR UI ---
            
            # 1. Actualizar Resumen (Labels)
            self.lbl_resumen_titulo.config(text=f"Resultados: {nom.upper()}")
            condicion = "Local" if loc == 1 else "Visitante"
            self.lbl_resumen_detalle.config(text=f"Vs {riv} (Fuerza {fue}) | {tac.capitalize()} | {condicion}")

            # 2. Actualizar TABLA (Limpiar y Llenar)
            for i in self.tabla.get_children():
                self.tabla.delete(i)
            
            # Insertar filas
            self.tabla.insert("", "end", values=("Pases Esperados", f"{p_prom:.2f}"))
            self.tabla.insert("", "end", values=("Tiros a Gol (Aprox)", f"{t_prom:.2f}"))
            self.tabla.insert("", "end", values=("Goles Esperados", f"{g_prom:.2f}"))
            self.tabla.insert("", "end", values=("Probabilidad de Anotar", f"{prob_gol:.1f}%"))
            self.tabla.insert("", "end", values=("Probabilidad de MVP", f"{prob_mvp:.1f}%"))

            # 3. Actualizar GRÁFICAS
            self.mostrar_graficas_embebidas(res)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def mostrar_graficas_embebidas(self, res):
        for widget in self.frame_grafica.winfo_children():
            widget.destroy()

        fig = plt.Figure(figsize=(6, 4), dpi=100)
        
        # Pases
        ax1 = fig.add_subplot(121)
        ax1.plot(res["pases"][:50], 'o-', color='#3498db', markersize=4, alpha=0.7)
        ax1.set_title("Variabilidad de Pases")
        ax1.set_xlabel("Simulaciones")
        ax1.grid(True, linestyle='--', alpha=0.5)

        # Goles
        ax2 = fig.add_subplot(122)
        ax2.hist(res["goles"], bins=[-0.5, 0.5, 1.5, 2.5, 3.5], color='#2ecc71', edgecolor='black', rwidth=0.8)
        ax2.set_title("Probabilidad de Goles")
        ax2.set_xlabel("Goles")
        ax2.set_xticks([0, 1, 2, 3])

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafica)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacionSimulacion(root)
    root.mainloop()