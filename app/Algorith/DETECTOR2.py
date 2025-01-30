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


global running
# Definir la variable running como global al inicio del script
running = True

# Configuración del servidor
HOST = '0.0.0.0'
PORT = 8088
RECONNECT_DELAY = 60
NO_DATA_TIMEOUT = 60

# Configuración de la base de datos
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
        print(f"[✔] Datos guardados correctamente para la cámara {camera_id}")
    except mysql.connector.Error as err:
        print(f"Error al insertar datos en MySQL: {err}")
    finally:
        db.close()

# Procesar tramas largas
def process_long_frame(frame, cam_ip, intersection_id):
    print(f"[📡] Trama recibida (hex): {frame.hex()}")

    if frame[0] != 0x7e or frame[-1] != 0x7e:
        print("[⚠] Trama no válida (no inicia o termina con 0x7E)")
        return

    # Eliminar los bytes de inicio y fin
    frame = frame[1:-1]

    try:
        num_channels = frame[17]  # Número de canales (Verifica si es correcto en la trama recibida)
        print(f"[ℹ] Número de canales detectados: {num_channels}")

        channels_info = frame[18:]  # Resto de la trama
        expected_length = num_channels * 12  # Cada canal ocupa 12 bytes

        print(f"[ℹ] Longitud esperada de datos de canales: {expected_length} bytes")
        print(f"[ℹ] Longitud real de datos de canales recibidos: {len(channels_info)} bytes")

        if len(channels_info) < expected_length:
            print("[x] Datos insuficientes para los canales, se ignora la trama.")
            return

        camera_id = get_camera_id(cam_ip, intersection_id)
        if camera_id is None:
            print("[⚠] No se encontró la cámara asociada, se ignora la trama.")
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

            print(f"[+] Datos procesados -> Lane: {canal}, A: {vehicles_class_a}, B: {vehicles_class_b}, C: {vehicles_class_c}, Speed: {average_speed}, Headway: {headway}, Camera: {camera_id}")

            save_measurement(timestamp, canal, vehicles_class_a, vehicles_class_b, vehicles_class_c, average_speed, headway, camera_id)

            offset += 12

    except IndexError as e:
        print(f"[x] Error al procesar la trama: {e}")

# Manejo de clientes
def handle_client(conn, addr, last_data_time, intersection_id):
    cam_ip = addr[0]
    print(f"[**] Conexión establecida desde {cam_ip}")
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
                print(f"[⚠] Trama ignorada por tamaño: {frame.hex()}")

    conn.close()

# Función para reiniciar el servidor si no recibe datos en cierto tiempo
def restart_server_socket():
    global server_socket
    global running

    print('[⚠] Reiniciando el servidor por inactividad...')
    
    try:
        server_socket.close()
        time.sleep(RECONNECT_DELAY)  # Esperar antes de reiniciar
        
        # Crear un nuevo socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        
        print(f"[✔] Servidor reiniciado en puerto {PORT}")

    except Exception as e:
        print(f"[X] Error al reiniciar el servidor: {e}")
        sys.exit(1)


# Aceptar conexiones
def accept_connections(intersection_id):
    global running  # ← Asegura que se usa la variable global
    last_data_time = [time.time()]

    try:
        while running:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr, last_data_time, intersection_id))
            client_thread.start()

            if time.time() - last_data_time[0] > NO_DATA_TIMEOUT:
                restart_server_socket()

    except KeyboardInterrupt:
        print("\n[INFO] Interrupción detectada. Cerrando servidor...")
        running = False  # ← Ahora modificamos correctamente la variable global
        server_socket.close()
        sys.exit(0)

# Manejo de señales
def signal_handler(sig, frame):
    global running  # ← Asegura que se use la variable global
    print("\n[INFO] Interrupción detectada. Apagando servidor...")
    running = False
    server_socket.close()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# Iniciar servidor
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
