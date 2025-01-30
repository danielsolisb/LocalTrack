import mysql.connector
from datetime import datetime, timedelta
import time
import sys

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
    
    # Calcular el tiempo límite
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
            direction = None  # Valor nulo por defecto
            for lane_id in lane_ids:
                cursor.execute("SELECT lane, straight, turn FROM lane_parameter WHERE id = %s", (lane_id,))
                lane_data = cursor.fetchone()
                if lane_data:
                    lane_number, straight, turn = lane_data
                    lanes.append(lane_number)
                    
                    # Determinar dirección
                    if straight == 1 and turn == 1:
                        direction = 0  # Ambos activados, se considera giro (0)
                    elif straight == 1:
                        direction = 1  # Recto (1)
                    elif turn == 1:
                        direction = 0  # Giro (0)
                    elif straight == 0 and turn == 0:
                        print(f"[⚠] Error de configuración: Carril {lane_number} no tiene dirección válida.")
                        return None  # No guardar datos
                    
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

# Contar vehículos por fase y flujo
def count_vehicles_per_phase_and_flow(time_range, controller_id):
    lane_counts, start_time, end_time = count_vehicles_per_lane(time_range)
    phase_data = get_phases_and_flows()
    if phase_data is None:
        return  # No ejecutar si hay error de configuración
    
    sample_time = time_range.total_seconds()
    
    for phase, flows in phase_data.items():
        for flow, data in flows.items():
            lanes, direction = data
            total_vehicles = sum(lane_counts.get(lane, 0) for lane in lanes)
            num_lanes = len(lanes)
            save_adaptive_results(controller_id, phase, flow, num_lanes, total_vehicles, direction, start_time, end_time, sample_time)

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
            count_vehicles_per_phase_and_flow(time_range, controller_id)
        else:
            print("[⚠] No hay fases o flujos configurados. El servicio esperará.")
        
        show_waiting_bar(int(time_range.total_seconds()))

# Iniciar el servicio
if __name__ == "__main__":
    run_service()
