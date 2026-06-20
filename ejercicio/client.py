import socket
import threading
import sys

HOST = "127.0.0.1"
PORT = 12345

def receive_messages(sock, username, stop_event):
    while not stop_event.is_set():
        try:
            data = sock.recv(1024)
            if not data:
                print("\n[Sistema] El servidor se ha desconectado. Presiona Enter para salir.")
                stop_event.set()
                break
            
            respuesta = data.decode('utf-8')
            print(f"\r{respuesta}\n{username}: ", end="", flush=True)
        except Exception:
            break

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((HOST, PORT))
    except ConnectionRefusedError:
        print("Error: No se pudo conectar al servidor. Asegúrate de que server.py esté ejecutándose.")
        return

    print("=== Bienvenido al Chat Socket ===")
    nombre_usuario = ""
    while True:
        print("\nSeleccione una opción:")
        print("1. Iniciar sesión")
        print("2. Registrarse")
        print("3. Salir")
        
        opcion = input("Opción (1-3): ").strip()
        if opcion == "1":
            user = input("Usuario: ").strip()
            password = input("Contraseña: ").strip()
            if not user or not password:
                print("El usuario y la contraseña no pueden estar vacíos.")
                continue
            
            cmd = f"/login {user} {password}"
            s.sendall(cmd.encode('utf-8'))
            
            data = s.recv(1024).decode('utf-8').strip()
            if data.startswith("/login_ok"):
                nombre_usuario = user
                bienvenida = data.replace("/login_ok", "").strip()
                print(f"[Servidor] {bienvenida}")
                print(f"Conectado al servidor como '{nombre_usuario}'. Escribe '/salir' para terminar. Escribe '/ayuda' para ver comandos.")
                break
            else:
                print(data)
                
        elif opcion == "2":
            user = input("Nuevo usuario: ").strip()
            password = input("Nueva contraseña: ").strip()
            if not user or not password:
                print("El usuario y la contraseña no pueden estar vacíos.")
                continue
            
            cmd = f"/register {user} {password}"
            s.sendall(cmd.encode('utf-8'))
            
            data = s.recv(1024).decode('utf-8').strip()
            print(data)
            
        elif opcion == "3" or opcion.lower() == "/salir":
            s.sendall("/salir".encode('utf-8'))
            s.close()
            print("Desconectado.")
            return
        else:
            print("Opción inválida. Intente de nuevo.")

    stop_event = threading.Event()

    recv_thread = threading.Thread(target=receive_messages, args=(s, nombre_usuario, stop_event))
    recv_thread.daemon = True
    recv_thread.start()

    while not stop_event.is_set():
        try:
            mensaje = input(f"{nombre_usuario}: ")
            
            if stop_event.is_set():
                break

            if mensaje.strip() == "/salir":
                s.sendall(mensaje.encode('utf-8'))
                print("Cerrando conexión...")
                stop_event.set()
                break
            
            if mensaje.strip() != "":
                s.sendall(mensaje.encode('utf-8'))
                
        except (KeyboardInterrupt, EOFError):
            print("\nInterrupción detectada. Cerrando conexión...")
            try:
                s.sendall("/salir".encode('utf-8'))
            except Exception:
                pass
            stop_event.set()
            break
        except Exception as e:
            print(f"\nError al enviar mensaje: {e}")
            stop_event.set()
            break

    s.close()
    print("Desconectado.")
    sys.exit(0)

if __name__ == "__main__":
    main()