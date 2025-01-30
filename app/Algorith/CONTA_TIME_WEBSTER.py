import mysql.connector
from datetime import datetime, timedelta
import time
import sys
import math
from decimal import Decimal

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

# Obtener el rango de tiempo, controller_id, amber_time y clearance_time
def get_time_config():
    db = db_connect()
    cursor = db.cursor()
    cursor.execute("SELECT saturation_flow, controller_id, amber_time, clearance_time FROM adaptive_control_config LIMIT 1")
    result = cursor.fetchone()
    db.close()
    
    if result:
        saturation_flow, controller_id, amber_time, clearance_time = result
        time_range = timedelta(hours=1) if saturation_flow == 1800 else timedelta(minutes=30) if saturation_flow == 900 else timedelta(minutes=15)
        return float(saturation_flow), controller_id, float(amber_time), float(clearance_time), time_range
    return 1800.0, None, 3.0, 1.0, timedelta(hours=1)  # Valores por defecto

# Obtener conteo de vehículos dentro del rango de tiempo
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
            flow_data = []
            for lane_id in lane_ids:
                cursor.execute("SELECT lane, straight, turn FROM lane_parameter WHERE id = %s", (lane_id,))
                lane_info = cursor.fetchone()
                
                if lane_info:
                    lane_number, straight, turn = lane_info
                    lanes.append(lane_number)
                    
                    # Determinar dirección y factor de equivalencia
                    feq = float(1.0 if straight == 1 else 1.2)
                    flow_data.append({
                        "lane": lane_number,
                        "feq": feq
                    })
            
            phase_data[phase_name][flow_name] = flow_data
    
    db.close()
    return phase_data

# Calcular tiempos de verde óptimos
def calculate_webster(saturation_flow, amber_time, clearance_time, time_range):
    phase_data = get_phases_and_flows()
    lane_counts, start_time, end_time = count_vehicles_per_lane(time_range)
    
    indices_saturacion = []
    for phase, flows in phase_data.items():
        fase_indices = []
        for flow, flow_values in flows.items():
            for flujo in flow_values:
                num_carros = float(lane_counts.get(flujo["lane"], 0))
                q = (num_carros * flujo["feq"]) / 1  # Se toma el valor de un solo carril
                Si = q / saturation_flow
                fase_indices.append(Si)
        indices_saturacion.append(max(fase_indices))
    
    S = sum(indices_saturacion)
    L = (amber_time + clearance_time) * len(phase_data)
    
    Tco = (1.5 * L + 5) / (1 - S) if S < 1 else 60
    tiempos_verde = [(Si / S) * (Tco - L) for Si in indices_saturacion]
    
    print(f"\n[🔹] Tiempo de ciclo óptimo (Tco): {Tco:.2f} segundos")
    for i, Tv in enumerate(tiempos_verde, 1):
        print(f"[🟢] Tiempo de verde óptimo para Fase {i}: {Tv:.2f} segundos")
    
    return tiempos_verde, start_time, end_time

# Servicio en bucle
def run_service():
    while True:
        saturation_flow, controller_id, amber_time, clearance_time, time_range = get_time_config()
        lane_counts, start_time, end_time = count_vehicles_per_lane(time_range)
        
        print(f"\n[📊] Conteo de Vehículos entre {start_time.strftime('%Y-%m-%d %H:%M:%S')} y {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        for lane, total in lane_counts.items():
            print(f"Carril {lane}: {total} vehículos")
        
        tiempos_verde, _, _ = calculate_webster(saturation_flow, amber_time, clearance_time, time_range)
        
        print(f"[⏳] Esperando {int(time_range.total_seconds())} segundos para el siguiente cálculo...")
        time.sleep(time_range.total_seconds())

if __name__ == "__main__":
    run_service()