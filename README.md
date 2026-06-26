# Chat Socket con Autenticación y PostgreSQL

Un proyecto de chat en Python con cliente y servidor usando sockets TCP, autenticación de usuarios y almacenamiento en PostgreSQL.

## 🔥 ¿Qué hace este código?

- `server.py`:
  - Levanta un servidor TCP en `127.0.0.1:12345`.
  - Permite registrar nuevos usuarios `/register <usuario> <contraseña>`.
  - Permite iniciar sesión `/login <usuario> <contraseña>`.
  - Guarda usuarios y contraseñas hasheadas en una base de datos PostgreSQL.
  - Gestiona múltiples clientes conectados con hilos (`threading`).
  - Envía mensajes de chat entre clientes conectados.
  - Ofrece comandos de ayuda y funcionalidad extra:
    - `/todos`: enviar un mensaje "hola mundo" a todos.
    - `/usuarios`: listar usuarios conectados.
    - `/api`: obtener un dato curioso sobre gatos desde la API pública `catfact.ninja`.

- `client.py`:
  - Se conecta al servidor TCP.
  - Permite registrarse o iniciar sesión desde la consola.
  - Después de iniciar sesión, envía mensajes y recibe respuestas en tiempo real.
  - Maneja desconexiones amigables con `/salir`.

## 📦 Requisitos

- Python 3.x
- PostgreSQL en `localhost:5432`
- Base de datos `chat_db`
- Usuario PostgreSQL: `postgres`
- Contraseña PostgreSQL: `1234`
- Paquetes Python:
  - `pg8000`

## 🚀 Instalar dependencias

```bash
pip install -r requirements.txt
```

## 🛠️ Cómo usarlo

1. Asegúrate de que PostgreSQL esté corriendo en tu máquina.
2. Ejecuta `server.py`:

```bash
python server.py
```

3. En otra terminal, ejecuta `client.py`:

```bash
python client.py
```

4. Desde el cliente, elige:
  - `1` para iniciar sesión.
  - `2` para registrarte.
  - `3` para salir.

5. Una vez logueado, escribe mensajes y usa comandos de chat.

## 💡 Comandos disponibles

Antes de iniciar sesión:
- `/register <usuario> <contraseña>`
- `/login <usuario> <contraseña>`
- `/salir`

Después de iniciar sesión:
- `/todos`
- `/usuarios`
- `/api`
- `/ayuda`
- `/salir`

## 🧠 Notas

- El servidor registra los usuarios en PostgreSQL y verifica la contraseña usando SHA-256.
- El cliente y el servidor usan sockets TCP y envían texto en codificación UTF-8.
- Si el servidor se cierra, el cliente muestra un aviso y se desconecta.

## 📌 Archivos principales

- `server.py`: lógica del servidor, autenticación y broadcast de mensajes.
- `client.py`: interfaz de consola para el usuario.
- `requirements.txt`: dependencias necesarias.
