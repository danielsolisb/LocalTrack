import serial
import socket
import threading
import tkinter as tk
from tkinter import messagebox
import time
from datetime import datetime
import queue
import selectors

BAUD_RATE = 9600

class SerialToSocketApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial to Socket Redirection")
        
        self.is_running = False
        
        self.status_label = tk.Label(root, text="Estado: Desconectado", fg="red")
        self.status_label.pack(pady=10)

        tk.Label(root, text="Dirección IP:").pack(pady=5)
        self.ip_entry = tk.Entry(root)
        self.ip_entry.insert(0, "192.168.1.185")
        self.ip_entry.pack(pady=5)

        tk.Label(root, text="Puerto:").pack(pady=5)
        self.port_entry = tk.Entry(root)
        self.port_entry.insert(0, "3333")
        self.port_entry.pack(pady=5)

        tk.Label(root, text="Puerto COM:").pack(pady=5)
        self.com_entry = tk.Entry(root)
        self.com_entry.insert(0, "COM22")
        self.com_entry.pack(pady=5)

        self.start_button = tk.Button(root, text="Iniciar", command=self.start)
        self.start_button.pack(pady=5)
        
        self.stop_button = tk.Button(root, text="Detener", command=self.stop, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.text_box = tk.Text(root, width=50, height=15)
        self.text_box.pack(pady=10)

        self.transfer_indicator = tk.Label(root, text="●", font=("Arial", 24), fg="gray")
        self.transfer_indicator.pack(pady=10)

        self.log_queue = queue.Queue()
        self.serial_queue = queue.Queue()
        self.socket_queue = queue.Queue()

        self.root.after(100, self.process_log_queue)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start(self):
        self.is_running = True
        self.status_label.config(text="Estado: Conectado", fg="green")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        ip_address = self.ip_entry.get()
        ip_port = int(self.port_entry.get())
        com_port = self.com_entry.get()
        
        self.datalog_file = open("datalog.txt", "a")

        self.serial_thread = threading.Thread(target=self.serial_worker, args=(com_port,), daemon=True)
        self.socket_thread = threading.Thread(target=self.socket_worker, args=(ip_address, ip_port,), daemon=True)
        self.serial_thread.start()
        self.socket_thread.start()

    def stop(self):
        self.is_running = False
        self.status_label.config(text="Estado: Desconectado", fg="red")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        if hasattr(self, 'datalog_file'):
            self.datalog_file.close()

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{timestamp} - {message}"
        self.log_queue.put(log_message)

    def process_log_queue(self):
        while not self.log_queue.empty():
            log_message = self.log_queue.get()
            self.text_box.insert(tk.END, log_message + "\n")
            self.text_box.see(tk.END)
            if hasattr(self, 'datalog_file'):
                self.datalog_file.write(log_message + "\n")
        self.root.after(100, self.process_log_queue)

    def bytes_to_hex(self, data):
        return ' '.join(f"{byte:02X}" for byte in data)

    def animate_transfer(self):
        self.transfer_indicator.config(fg="green")
        self.root.update_idletasks()
        self.root.after(50, lambda: self.transfer_indicator.config(fg="gray"))

    def serial_worker(self, com_port):
        try:
            ser = serial.Serial(com_port, BAUD_RATE, timeout=0)
            self.log(f"Puerto serial {com_port} abierto.")
            while self.is_running:
                data = ser.read(1024)
                if data:
                    hex_data = self.bytes_to_hex(data)
                    self.log(f"Leído desde serial: {hex_data}")
                    self.socket_queue.put(data)
                    self.animate_transfer()
                try:
                    data_to_send = self.serial_queue.get_nowait()
                    ser.write(data_to_send)
                except queue.Empty:
                    pass
        except Exception as e:
            self.log(f"Error en serial_worker: {e}")
        finally:
            if ser:
                ser.close()

    def socket_worker(self, ip_address, ip_port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip_address, ip_port))
            sock.setblocking(False)
            self.log(f"Conectado a {ip_address}:{ip_port}")
            while self.is_running:
                try:
                    data = sock.recv(1024)
                    if data:
                        hex_data = self.bytes_to_hex(data)
                        self.log(f"Recibido desde socket: {hex_data}")
                        self.serial_queue.put(data)
                        self.animate_transfer()
                except BlockingIOError:
                    pass
                except Exception as e:
                    self.log(f"Error en socket.recv: {e}")
                    break
                try:
                    data_to_send = self.socket_queue.get_nowait()
                    sock.sendall(data_to_send)
                except queue.Empty:
                    pass
                except Exception as e:
                    self.log(f"Error en socket.sendall: {e}")
                    break
        except Exception as e:
            self.log(f"Error en socket_worker: {e}")
        finally:
            if sock:
                sock.close()

    def on_closing(self):
        self.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialToSocketApp(root)
    root.mainloop()
