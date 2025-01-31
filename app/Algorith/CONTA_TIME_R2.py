import mysql.connector
from datetime import datetime, timedelta
import time
import sys
import math  # [NUEVO]
from decimal import Decimal  # [NUEVO]

# Configuración de la base de datos
db_config = {
    "host": "35.222.201.195",
    "user": "root",
    "password": "daniel586",
    "database": "Localtrack"
}

# Conectar a la base de datos
def db_connect():
    return mysql.connector.connect(**db_config)

# Obtener el rango de tiempo y el controller_id desde adaptive_control_config
def get_time_range():
    db = db_connect()
    cursor = db.cursor()
    cursor.execute("SELECT saturation_flow, controller_id FROM adaptive_control_config LIMIT 1")
    result = cursor.fetchone()
    db.close()
    
    if result:
        saturation_flow, controller_id = result
        # Estos 1800, 900, 450 equivalen a la ventana de muestreo en tiempo,
        # pero OJO: en el cálculo Webster se usan tal cual (1800, 900 o 450) como flujo de saturación.
        if saturation_flow == 1800:
            return timedelta(hours=1), controller_id
        elif saturation_flow == 900:
            return timedelta(minutes=30), controller_id
        elif saturation_flow == 450:
            return timedelta(minutes=15), controller_id
    return timedelta(hours=1), None  # Valor por defecto

# Verificar si hay fases y flujos configurados
def has_phases_and_flows():
    db = db_connect()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM phase")
    phase_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM flow")
    flow_count = cursor.fetchone()[0]
    db.close()
    return phase_count > 0 and flow_count > 0

# Contar los vehículos por carril en el tiempo establecido
def count_vehicles_per_lane(time_range):
    db = db_connect()
    cursor = db.cursor()
    
    end_time = datetime.now()
    start_time = end_time - time_range
    
    query = """
        SELECT lane, SUM(vehicles_class_a + vehicles_class_b + vehicles_class_c) AS total_vehicles
        FROM measurement
        WHERE timestamp BETWEEN %s AND %s
        GROUP BY lane
    """
    cursor.execute(query, (start_time, end_time))
    results = cursor.fetchall()
    db.close()
    
    return dict(results), start_time, end_time

# Obtener fases, flujos y determinar la dirección de los carriles
def get_phases_and_flows():
    db = db_connect()
    cursor = db.cursor()
    
    query = "SELECT id, name FROM phase"
    cursor.execute(query)
    phases = cursor.fetchall()
    
    phase_data = {}
    for phase_id, phase_name in phases:
        cursor.execute("SELECT id, name FROM flow WHERE phase_id = %s", (phase_id,))
        flows = cursor.fetchall()
        
        phase_data[phase_name] = {}
        for flow_id, flow_name in flows:
            cursor.execute("SELECT lane_id FROM flow_lane WHERE flow_id = %s", (flow_id,))
            lane_ids = [row[0] for row in cursor.fetchall()]
            
            lanes = []
            direction = None
            for lane_id in lane_ids:
                cursor.execute("SELECT lane, straight, turn FROM lane_parameter WHERE id = %s", (lane_id,))
                lane_data = cursor.fetchone()
                if lane_data:
                    lane_number, straight, turn = lane_data
                    lanes.append(lane_number)
                    
                    # Verificar coherencia del sentido
                    if straight == 1 and turn == 1:
                        dir_val = 0  # Se interpretará como giro
                    elif straight == 1 and turn == 0:
                        dir_val = 1  # Recto
                    elif straight == 0 and turn == 1:
                        dir_val = 0  # Giro
                    else:
                        print(f"[⚠] Error de configuración: Carril {lane_number} no tiene dirección válida.")
                        return None
                    
                    # Si todavía no tenemos direction, tomamos esta
                    if direction is None:
                        direction = dir_val
                    else:
                        # Si encontramos un carril con sentido distinto, error de config
                        if direction != dir_val:
                            print(f"[⚠] Error de configuración: Los carriles en el flujo '{flow_name}' no coinciden en dirección.")
                            return None
            
            phase_data[phase_name][flow_name] = (lanes, direction)
    
    db.close()
    return phase_data

# Guardar resultados en adaptive_results
def save_adaptive_results(controller_id, phase, flow, num_lanes, total_vehicles, direction, start_time, end_time, sample_time):
    db = db_connect()
    cursor = db.cursor()
    query = """
        INSERT INTO adaptive_results (controller_id, phase, flow, num_lanes, num_vehicles, direction, start_time, end_time, sample_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (controller_id, phase, flow, num_lanes, total_vehicles, direction, start_time, end_time, sample_time))
    db.commit()
    db.close()

    # [NUEVO] Mostrar en consola lo que se insertó
    print("[INFO] Guardado en adaptive_results:")
    print(f"       controller_id={controller_id}, phase={phase}, flow={flow}, num_lanes={num_lanes}, "
          f"total_vehicles={total_vehicles}, direction={direction}, start_time={start_time}, "
          f"end_time={end_time}, sample_time={sample_time}")
   
    
# --------------------------------------------------------------------------
# NUEVA FUNCIÓN: contará vehículos por fase y flujo y además devolverá
# un diccionario con los datos necesarios para Webster: # de vehículos,
# # de carriles y dirección por fase-flujo.
# --------------------------------------------------------------------------
def count_vehicles_per_phase_and_flow(time_range, controller_id):
    lane_counts, start_time, end_time = count_vehicles_per_lane(time_range)
    phase_data = get_phases_and_flows()
    if phase_data is None:
        return None  # No ejecutar si hay error de configuración
    
    sample_time = time_range.total_seconds()
    
    webster_data = {
        "controller_id": controller_id,
        "start_time": start_time,
        "end_time": end_time,
        "phases": {}  # Aquí irá la info de cada fase
    }
    
    for phase, flows in phase_data.items():
        webster_data["phases"][phase] = {}
        for flow, (lanes, direction) in flows.items():
            total_vehicles = sum(lane_counts.get(lane, 0) for lane in lanes)
            num_lanes = len(lanes)
            
            # Guardar en DB (adaptive_results) como antes
            save_adaptive_results(
                controller_id, phase, flow, num_lanes, total_vehicles,
                direction, start_time, end_time, sample_time
            )
            
            # También guardar en la estructura local para Webster
            webster_data["phases"][phase][flow] = {
                "num_vehicles": total_vehicles,
                "num_lanes": num_lanes,
                "direction": direction
            }
    
    return webster_data


# [NUEVO] Función para obtener los parámetros de Webster desde DB
def get_webster_config():
    db = db_connect()
    cursor = db.cursor()
    cursor.execute("""
        SELECT saturation_flow, amber_time, clearance_time,
               green_time_1, green_time_2, green_time_3, green_time_4
        FROM adaptive_control_config
        LIMIT 1
    """)
    result = cursor.fetchone()
    db.close()

    if result:
        saturation_flow, amber_time, clearance_time, g1, g2, g3, g4 = result
        return {
            "saturation_flow": float(saturation_flow),
            "amber_time": float(amber_time),
            "clearance_time": float(clearance_time),
            "green_times": [float(g1 or 0), float(g2 or 0), float(g3 or 0), float(g4 or 0)]
            # 'float(g1 or 0)' => por si viene NULL en BD, se usa 0
        }
    else:
        # Valores por defecto si no hay nada en DB
        return {
            "saturation_flow": 1800.0,
            "amber_time": 3.0,
            "clearance_time": 1.0,
            "green_times": [0, 0, 0, 0]
        }

# [NUEVO] Función para calcular y mostrar tiempos de verde usando la fórmula de Webster
def calculate_webster_times(webster_data):
    """
    webster_data: un diccionario con:
        {
          "controller_id": <int>,
          "start_time": datetime,
          "end_time": datetime,
          "phases": {
             "Phase 1": {
                "Flow A": {...},
                "Flow B": {...}
             },
             "Phase 2": {...},
             ...
          }
        }
    """
    # Leer config (incluyendo green_times)
    config = get_webster_config()
    saturation_flow = config["saturation_flow"]
    amber_time = config["amber_time"]
    clearance_time = config["clearance_time"]
    green_times = config["green_times"]  # [g1, g2, g3, g4]

    # Extractar info básica de webster_data
    controller_id = webster_data["controller_id"]
    start_time = webster_data["start_time"]
    end_time = webster_data["end_time"]
    phase_dict = webster_data["phases"]

    # Identificar cuántas fases hay
    phases = list(phase_dict.keys())
    num_fases = len(phases)

    # Calcular el índice de saturación máximo (Si_fase) por fase
    Si_fase = []
    for phase_name in phases:
        flows_info = phase_dict[phase_name]
        max_Si = 0.0
        for flow_name, fdata in flows_info.items():
            num_vehicles = fdata["num_vehicles"]
            num_lanes = fdata["num_lanes"]
            direction = fdata["direction"]

            feq = 1.0 if direction == 1 else 1.2
            if num_lanes == 0:
                continue

            q = (float(num_vehicles) * feq) / float(num_lanes)
            Si = q / float(saturation_flow)
            if Si > max_Si:
                max_Si = Si
        Si_fase.append(max_Si)

    # S = suma de los Si_fase
    S = sum(Si_fase)

    # Calcular L
    L = (amber_time + clearance_time) * num_fases

    if S >= 1:
        print("[⚠] Advertencia: El valor de S es mayor o igual a 1. Webster podría no ser aplicable.")
        # Podrías decidir seguir o no calculando. Aquí continuo, pero advierto.
        # return  # Si prefieres abortar.

    # Tco
    Tco = (1.5 * L + 5) / (1 - S) if (1 - S) > 0 else 9999  # Evitar /0

    # Mostrar resultados en consola
    print("\n[WEBSTER] Cálculo de Tiempos de Fases")
    print("--------------------------------------")
    print(f"Flujo de saturación usado: {saturation_flow}")
    print(f"Tiempo de ámbar: {amber_time} s")
    print(f"Tiempo de despeje: {clearance_time} s")
    print(f"Valor de S (suma índices saturación): {S:.4f}")
    print(f"Tiempo de ciclo óptimo (Tco): {Tco:.2f} s\n")

    # Para cada fase, calculamos el verde teórico y lo comparamos con su green_time
    for i, phase_name in enumerate(phases):
        si = Si_fase[i]
        if S > 0:
            verde_calculado = (si / S) * (Tco - L)
        else:
            verde_calculado = 0.0

        # Redondear a 2 decimales si gustas
        verde_calculado = round(verde_calculado, 2)

        # Tomar "mínimo" o "umbral" para esta fase (i => green_time[i])
        min_green = 0.0
        if i < len(green_times):
            min_green = green_times[i]

        # Regla:
        # si verde_calculado < min_green => recommended_time = min_green
        # si verde_calculado >= min_green => recommended_time = verde_calculado
        if verde_calculado < min_green:
            recommended_time = min_green
        else:
            recommended_time = verde_calculado
        
        print(f"Fase {phase_name} => Tiempo de verde óptimo (calculado): {verde_calculado} s")
        print(f"               => Tiempo recomendado (comparado con min_green={min_green}): {recommended_time} s\n")

        # Guardar en phase_timing_results
        # (controller_id, phase, calculated_time, suggested_time, start_time, end_time)
        save_phase_timing_result(
            controller_id=controller_id,
            phase=phase_name,
            calculated_time=verde_calculado,
            suggested_time=recommended_time,
            start_time=start_time,
            end_time=end_time
        )

    print("--------------------------------------\n")


# [NUEVO] Función para insertar valores a phase_timing_results
def save_phase_timing_result(controller_id, phase, calculated_time, suggested_time, start_time, end_time):
    db = db_connect()
    cursor = db.cursor()
    query = """
        INSERT INTO phase_timing_results
        (controller_id, phase, calculated_time, suggested_time, start_time, end_time)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (
        controller_id,
        phase,
        calculated_time,
        suggested_time,
        start_time,
        end_time
    ))
    db.commit()
    db.close()
    
    # Si deseas imprimir también en consola
    print("[INFO] Guardado en phase_timing_results:")
    print(f"       controller_id={controller_id}, phase={phase}, "
          f"calculated_time={calculated_time:.2f}, suggested_time={suggested_time:.2f}, "
          f"start_time={start_time}, end_time={end_time}")

# Mostrar barra de espera
def show_waiting_bar(wait_time):
    for remaining in range(wait_time, 0, -1):
        sys.stdout.write(f"\r[⏳] Esperando {remaining} segundos para la siguiente muestra...")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r[✅] Tomando nueva muestra...\n")
    sys.stdout.flush()

# Servicio en bucle mientras haya fases y flujos configurados
def run_service():
    while True:
        if has_phases_and_flows():
            time_range, controller_id = get_time_range()
            
            # 1) Contar vehículos y guardar en adaptive_results
            webster_data = count_vehicles_per_phase_and_flow(time_range, controller_id)
            
            if webster_data is not None:
                # 2) Calcular tiempos de verde con Webster:
                #    (justo después de guardar el conteo).
                calculate_webster_times(webster_data)
            else:
                print("[⚠] Se omitió el cálculo de Webster por error en configuración de fases/flows.")
                
        else:
            print("[⚠] No hay fases o flujos configurados. El servicio esperará.")
        
        # 3) Esperar el tiempo configurado antes de nueva muestra
        show_waiting_bar(int(time_range.total_seconds()))

# Iniciar el servicio
if __name__ == "__main__":
    run_service()
