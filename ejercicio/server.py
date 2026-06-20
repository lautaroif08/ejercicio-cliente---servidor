import socket
import threading
# pyrefly: ignore [missing-import]
import pg8000
import sys
import hashlib
import urllib.request
import json

DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "chat_db"
DB_USER = "postgres"
DB_PASSWORD = "1234"  

def get_db_connection():
    try:
        conn = pg8000.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"[Error de BD] No se pudo conectar a PostgreSQL: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password_hash VARCHAR(256) NOT NULL
                    );
                """)
                conn.commit()
                print("[BD] Tabla 'usuarios' verificada/creada con éxito.")
        except Exception as e:
            print(f"[Error de BD] Error al inicializar tabla: {e}")
        finally:
            conn.close()
    else:
        print("[BD] Continuando sin conexión de base de datos activa. Asegúrese de que PostgreSQL esté ejecutándose y configurado.")

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def register_user(username, password):
    conn = get_db_connection()
    if not conn:
        return False, "Error: No se pudo establecer conexión con la base de datos."
    try:
        password_hash = hash_password(password)
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM usuarios WHERE username = %s;", (username,))
            if cur.fetchone():
                return False, f"El nombre de usuario '{username}' ya está registrado."
            
            cur.execute(
                "INSERT INTO usuarios (username, password_hash) VALUES (%s, %s);",
                (username, password_hash)
            )
            conn.commit()
            return True, "Registro exitoso. Ahora puede iniciar sesión."
    except Exception as e:
        return False, f"Error en el registro: {e}"
    finally:
        conn.close()

def login_user(username, password):
    conn = get_db_connection()
    if not conn:
        return False, "Error: No se pudo establecer conexión con la base de datos."
    try:
        password_hash = hash_password(password)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT password_hash FROM usuarios WHERE username = %s;",
                (username,)
            )
            row = cur.fetchone()
            if not row:
                return False, "Usuario no encontrado."
            
            stored_hash = row[0]
            if stored_hash == password_hash:
                return True, "Inicio de sesión exitoso."
            else:
                return False, "Contraseña incorrecta."
    except Exception as e:
        return False, f"Error al iniciar sesión: {e}"
    finally:
        conn.close()

hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)
print("Your Computer name is: " + hostname)
print("Your computer IP Adress is: " + ip)

HOST = "127.0.0.1"
PORT = 12345

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(10) 

print(f"El servidor está escuchando en el puerto {PORT}")

clients = []
clients_lock = threading.Lock()

def broadcast(message, sender_socket=None):
    mensaje_codificado = message.encode('utf-8')
    with clients_lock:
        to_remove = []
        for client_socket, username in clients:
            if client_socket != sender_socket:
                try:
                    client_socket.sendall(mensaje_codificado)
                except Exception:
                    to_remove.append((client_socket, username))
        
        for client in to_remove:
            if client in clients:
                clients.remove(client)
                try:
                    client[0].close()
                except Exception:
                    pass
                print(f"[Sistema] Conexión limpia con {client[1]} eliminada debido a un error de envío.")

def handle_client(client_socket, address):
    username = ""
    authenticated = False
    print(f"Se estableció una conexión con {address} (No autenticado)")
    
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
                
            mensaje = data.decode('utf-8').strip()
            if not mensaje:
                continue
            
            if mensaje == "/salir":
                break
            
            if not authenticated:
                if mensaje.startswith("/register"):
                    parts = mensaje.split(" ", 2)
                    if len(parts) < 3:
                        client_socket.sendall("[Servidor] Uso: /register <usuario> <contraseña>\n".encode('utf-8'))
                    else:
                        reg_user = parts[1].strip()
                        reg_pass = parts[2].strip()
                        if not reg_user or not reg_pass:
                            client_socket.sendall("[Servidor] Usuario o contraseña no válidos.\n".encode('utf-8'))
                        else:
                            success, msg = register_user(reg_user, reg_pass)
                            client_socket.sendall(f"[Servidor] {msg}\n".encode('utf-8'))
                            
                elif mensaje.startswith("/login"):
                    parts = mensaje.split(" ", 2)
                    if len(parts) < 3:
                        client_socket.sendall("[Servidor] Uso: /login <usuario> <contraseña>\n".encode('utf-8'))
                    else:
                        log_user = parts[1].strip()
                        log_pass = parts[2].strip()
                        if not log_user or not log_pass:
                            client_socket.sendall("[Servidor] Usuario o contraseña no válidos.\n".encode('utf-8'))
                        else:
                            already_logged = False
                            with clients_lock:
                                for _, u in clients:
                                    if u == log_user:
                                        already_logged = True
                                        break
                            if already_logged:
                                client_socket.sendall("[Servidor] Error: Este usuario ya tiene una sesión iniciada.\n".encode('utf-8'))
                            else:
                                success, msg = login_user(log_user, log_pass)
                                if success:
                                    username = log_user
                                    authenticated = True
                                    with clients_lock:
                                        clients.append((client_socket, username))
                                    client_socket.sendall(f"/login_ok Bienvenido {username}!\n".encode('utf-8'))
                                    broadcast(f"\n[Servidor] {username} se ha unido al chat", client_socket)
                                    print(f"Cliente en {address} autenticado como '{username}'")
                                else:
                                    client_socket.sendall(f"[Servidor] Error: {msg}\n".encode('utf-8'))
                                    
                elif mensaje == "/ayuda":
                    ayuda_msg = "\nComandos disponibles (Sin iniciar sesión):\n 1) /register <usuario> <contraseña>: crea una cuenta\n 2) /login <usuario> <contraseña>: inicia sesión\n 3) /salir: cierra la conexión\n"
                    client_socket.sendall(ayuda_msg.encode('utf-8'))
                else:
                    client_socket.sendall("[Servidor] Debes iniciar sesión antes de enviar mensajes o comandos. Usa /login <usuario> <contraseña> o /register <usuario> <contraseña>.\n".encode('utf-8'))
            
            else:
                if mensaje == "/ayuda":
                    ayuda_msg = "\nComandos disponibles:\n 1) /todos: envía un 'hola mundo' a todos los conectados\n 2) /usuarios: muestra la lista de usuarios conectados\n 3) /api: muestra un dato curioso sobre gatos\n 4) /salir: cierra la conexión\n"
                    client_socket.sendall(ayuda_msg.encode('utf-8'))
                    
                elif mensaje == "/todos":
                    broadcast(f"[Broadcast de {username}]: hola mundo", client_socket)
                    client_socket.sendall("[Servidor] Broadcast de 'hola mundo' enviado.\n".encode('utf-8'))
                    
                elif mensaje == "/usuarios":
                    with clients_lock:
                        user_list = [u for _, u in clients]
                    lista_msg = f"[Servidor] Usuarios conectados: {', '.join(user_list)}\n"
                    client_socket.sendall(lista_msg.encode('utf-8'))
                    
                elif mensaje == "/api":
                    try:
                        req = urllib.request.Request(
                            "https://catfact.ninja/fact",
                            headers={'User-Agent': 'Mozilla/5.0'}
                        )
                        with urllib.request.urlopen(req, timeout=5) as response:
                            raw_data = response.read()
                            json_data = json.loads(raw_data.decode('utf-8'))
                            fact = json_data.get("fact", "No se encontró ningún dato curioso.")
                            client_socket.sendall(f"[API Cat Fact] Sabías que: {fact}\n".encode('utf-8'))
                    except Exception as e:
                        client_socket.sendall(f"[Servidor] Error al consultar la API: {e}\n".encode('utf-8'))
                
                elif mensaje.startswith("/register") or mensaje.startswith("/login"):
                    client_socket.sendall("[Servidor] Ya has iniciado sesión.\n".encode('utf-8'))
                    
                else:
                    print(f"{username}: {mensaje}")
                    broadcast(f"{username}: {mensaje}", client_socket)
                    
    except Exception as e:
        print(f"[Error] Error manejando al cliente {username or address}: {e}")
    finally:
        client_socket.close()
        if authenticated:
            with clients_lock:
                for client in clients:
                    if client[0] == client_socket:
                        clients.remove(client)
                        break
            if username:
                print(f"El cliente {username} se ha desconectado.")
                broadcast(f"[Servidor] {username} ha salido del chat!")
        else:
            print(f"La conexión no autenticada con {address} se ha cerrado.")

def accept_connections():
    while True:
        try:
            client_socket, address = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, address))
            client_thread.daemon = True
            client_thread.start()
        except Exception as e:
            break

accept_thread = threading.Thread(target=accept_connections)
accept_thread.daemon = True
accept_thread.start()

print("Servidor listo. Escribe un mensaje en la consola para difundirlo a todos o '/salir' para apagar el servidor.\n")

while True:
    try:
        admin_input = input()
        if admin_input.strip() == "/salir":
            print("Cerrando el servidor...")
            with clients_lock:
                for client_socket, username in clients:
                    try:
                        client_socket.sendall("[Servidor] El servidor se está cerrando. Desconectando...".encode('utf-8'))
                        client_socket.close()
                    except Exception:
                        pass
                clients.clear()
            break
        elif admin_input.strip():
            broadcast(f"[Servidor (Admin)]: {admin_input}")
    except (KeyboardInterrupt, SystemExit):
        print("\nApagando servidor...")
        break

server_socket.close()
sys.exit(0)