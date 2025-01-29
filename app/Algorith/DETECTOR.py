import socket
import threading
import csv
from datetime import datetime
import time
import signal
import sys
import mysql.connector
import os
import paho.mqtt.client as mqtt

# Configuración del servidor
HOST = '0.0.0.0'  # Escuchar en todas las interfaces de red
PORT = 8088       # Puerto de escucha
RECONNECT_DELAY = 60  # Tiempo en segundos para cerrar y reabrir el puerto
NO_DATA_TIMEOUT = 60  # Tiempo en segundos para cerrar el puerto si no se reciben datos

# Configuración del broker MQTT (si es necesario)
broker_address = "35.222.201.195"  

# Variable global para controlar la ejecución
running = True

# Función para conectar a la base de datos
def db_connect():
    try:
        return mysql.connector.connect(
            host="35.222.201.195",
            user="root",
            password="daniel586",
            database="Localtrack"
        )
    except mysql.connector.Error as err:
        print(f"Error de conexión a MySQL: {err}")
        sys.exit(1)

# Reinicio del servidor en caso de inactividad
def restart_server_socket():
    global server_socket
    print('Reiniciando el servidor...')
    server_socket.close()
    time.sleep(RECONNECT_DELAY)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Servidor reiniciado en el puerto {PORT}")

# Obtener el ID de la intersección desde un archivo
def get_intersection_id_from_file(file_path='data.txt'):
    try:
        with open(file_path, 'r') as file:
            return int(file.read().strip())
    except (FileNotFoundError, ValueError) as e:
        print(f"Error al leer el archivo {file_path}: {e}")
        sys.exit(1)

# Obtener el ID de la cámara con base en la IP y la intersección
def get_camera_id(cam_ip, intersection_id):
    db = db_connect()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM camera WHERE ip_address = %s AND intersection_id = %s", (cam_ip, intersection_id))
    camera = cursor.fetchone()
    db.close()
    if camera:
        return camera[0]
    else:
        print(f"No se encontró la cámara con IP {cam_ip} en la intersección {intersection_id}")
        return None

# Guardar datos en la tabla measurement
def save_measurement(timestamp, lane, vehicles_class_a, vehicles_class_b, vehicles_class_c, average_speed, headway, camera_id):
    db = db_connect()
    cursor = db.cursor()
    query = """
    INSERT INTO measurement (timestamp, lane, vehicles_class_a, vehicles_class_b, vehicles_class_c, average_speed, headway, camera_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(query, (timestamp, lane, vehicles_class_a, vehicles_class_b, vehicles_class_c, average_speed, headway, camera_id))
        db.commit()
    except mysql.connector.Error as err:
        print(f"Error al insertar datos en MySQL: {err}")
    finally:
        db.close()

    # Guardar los datos en un archivo CSV
    csv_file = 'measurements.csv'
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['timestamp', 'lane', 'vehicles_class_a', 'vehicles_class_b', 'vehicles_class_c', 'average_speed', 'headway', 'camera_id'])
        writer.writerow([timestamp, lane, vehicles_class_a, vehicles_class_b, vehicles_class_c, average_speed, headway, camera_id])

# Procesar tramas largas recibidas de las cámaras
def process_long_frame(frame, cam_ip, intersection_id):
    if frame[0] != 0x7e or frame[-1] != 0x7e:
        print("Trama no válida")
        return

    frame = frame[1:-1]

    try:
        time_field = frame[4:8]
        num_channels = frame[16]
        channels_info = frame[17:]
        expected_length = num_channels * 12
        
        if len(channels_info) < expected_length:
            print("Datos insuficientes para los canales")
            return
        
        camera_id = get_camera_id(cam_ip, intersection_id)
        if camera_id is None:
            return

        offset = 0
        for _ in range(num_channels):
            canal = channels_info[offset]
            vehicles_class_a = channels_info[offset + 1]
            vehicles_class_b = channels_info[offset + 2]
            vehicles_class_c = channels_info[offset + 3]
            average_speed = channels_info[offset + 5]
            headway = channels_info[offset + 7]
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            save_measurement(timestamp, canal, vehicles_class_a, vehicles_class_b, vehicles_class_c, average_speed, headway, camera_id)
            
            offset += 12
            
    except IndexError:
        print("Error al procesar la trama: datos insuficientes")

# Manejo de clientes que envían datos
def handle_client(conn, addr, last_data_time, intersection_id):
    cam_ip = addr[0]
    print(f"Conexión establecida desde {cam_ip}")
    buffer = b""
    while running:
        data = conn.recv(4096)
        if not data:
            break

        last_data_time[0] = time.time()
        buffer += data

        while True:
            start = buffer.find(b'\x7e')
            end = buffer.find(b'\x7e', start + 1)
            if start == -1 or end == -1:
                break

            frame = buffer[start:end + 1]
            buffer = buffer[end + 1:]

            if len(frame) >= 20:
                process_long_frame(frame, cam_ip, intersection_id)
            else:
                print(f"Trama ignorada por tamaño: {frame.hex()}")

    conn.close()

# Aceptar conexiones entrantes
def accept_connections(intersection_id):
    last_data_time = [time.time()]
    global running
    try:
        while running:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr, last_data_time, intersection_id))
            client_thread.start()

            if time.time() - last_data_time[0] > NO_DATA_TIMEOUT:
                restart_server_socket()

    except KeyboardInterrupt:
        print("\nInterrupción detectada. Cerrando servidor...")
        running = False
        server_socket.close()
        sys.exit(0)

# Manejo de señales para cerrar el servidor
def signal_handler(sig, frame):
    global running
    print('Interrupción recibida. Cerrando servidor...')
    running = False
    server_socket.close()

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    intersection_id = get_intersection_id_from_file()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Servidor escuchando en puerto {PORT}")

    accept_thread = threading.Thread(target=accept_connections, args=(intersection_id,))
    accept_thread.start()
    accept_thread.join()
