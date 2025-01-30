import mysql.connector
from datetime import datetime, timedelta

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

# Obtener el rango de tiempo desde adaptive_control_config
def get_time_range():
    db = db_connect()
    cursor = db.cursor()
    cursor.execute("SELECT saturation_flow FROM adaptive_control_config LIMIT 1")
    result = cursor.fetchone()
    db.close()
    
    if result:
        saturation_flow = result[0]
        if saturation_flow == 1800:
            return timedelta(hours=1)
        elif saturation_flow == 900:
            return timedelta(minutes=30)
        elif saturation_flow == 450:
            return timedelta(minutes=15)
    return timedelta(hours=1)  # Valor por defecto

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
    
    print("\n[📊] Conteo de Vehículos por Carril en el Último", time_range)
    print(f"Muestra tomada desde {start_time.strftime('%Y-%m-%d %H:%M:%S')} hasta {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    for lane, total in results:
        print(f"Carril {lane}: {total} vehículos")
    return dict(results), start_time, end_time

# Obtener fases y flujos de la intersección
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
            
            # Obtener los números de carril reales
            lanes = []
            for lane_id in lane_ids:
                cursor.execute("SELECT lane FROM lane_parameter WHERE id = %s", (lane_id,))
                lane_number = cursor.fetchone()
                if lane_number:
                    lanes.append(lane_number[0])
            
            phase_data[phase_name][flow_name] = lanes
    
    db.close()
    return phase_data

# Contar vehículos por fase y flujo
def count_vehicles_per_phase_and_flow(time_range):
    lane_counts, start_time, end_time = count_vehicles_per_lane(time_range)
    phase_data = get_phases_and_flows()
    
    print("\n[🚦] Conteo de Vehículos por Fase y Flujo en el Último", time_range)
    print(f"Muestra tomada desde {start_time.strftime('%Y-%m-%d %H:%M:%S')} hasta {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    for phase, flows in phase_data.items():
        print(f"\nFase: {phase} (Total Flujos: {len(flows)})")
        for flow, lanes in flows.items():
            total_vehicles = sum(lane_counts.get(lane, 0) for lane in lanes)
            print(f"  Flujo {flow}: {total_vehicles} vehículos (Total Carriles: {len(lanes)})")

# Ejecutar el análisis
time_range = get_time_range()
count_vehicles_per_phase_and_flow(time_range)