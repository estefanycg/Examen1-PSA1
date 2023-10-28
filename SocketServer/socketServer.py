from flask import Flask, render_template
# pip install flask_socketio
from flask_socketio import SocketIO, emit
import mysql.connector
from datetime import datetime
import random, string
import time

# MySQL configurations
db_config = {
    'user': 'progsistemasabiertos',
    'password': 'RootProgsistemasabiertos',
    'host': '178.128.156.175',
    'database': 'progsistemasabiertos1',
}

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Página default para cuando entramos a la url http://127.0.0.1:8000/
@app.route('/')
def index():
    return render_template('index.html')

def registrarPago(parametros): 
    id_cuota = parametros['id_cuota']

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        fecha_actual = datetime.today().strftime('%Y-%m-%d')
        letras_aleatorias = ''.join(random.choice(string.ascii_uppercase) for _ in range(3))
        numero_aleatorio = random.randint(1000, 9999)
        referencia = letras_aleatorias + "-" + str(numero_aleatorio)
        
        query = "UPDATE progsistemasabiertos1.Cuotas SET estado = 1,fechaRealPago = %s, referencia = %s WHERE idCuotas = %s;"
        values = (fecha_actual,referencia,id_cuota)
        cursor.execute(query, values)
        
        conn.commit()
        cursor.close()
        conn.close()

        return True
    except Exception as e:
        print(f'Error: {str(e)}')
        return False

# Capturar el evento "solicitar_listaClientes" iniciado por el html
@socketio.on('realizarPagoCuota', namespace='/pago')
def realizarPagoCuota(parametros):
    print(datetime.today(), "realizarPagoCuota", parametros)
    respuesta = registrarPago(parametros)

    data = {
        'ok': respuesta,
        'mensaje': "Ok" if respuesta else "Error al registrar pago",
        'data': parametros['id_cuota']
    }

    time.sleep(5)
    emit('respuesta_cambioEstadoCuota', data)

def registrarReversion(parametros):
    id_cuota = parametros['id_cuota']
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    query = "UPDATE progsistemasabiertos1.Cuotas SET estado = 0, fechaRealPago = NULL, referencia = '' WHERE idCuotas = %s;"
    values = (int(id_cuota), )
    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()


@socketio.on('listarCuotas', namespace='/pago')
def listaCuotas(parametros):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    id_cliente = parametros['id_cliente']
    estado_cuotas = parametros['estado_cuotas']
    if estado_cuotas == 'pagadas':
        estado_cuotas = 1
    elif estado_cuotas == 'pendientes':
        estado_cuotas = 0
    else:
        estado_cuotas = '*'

    if estado_cuotas != '*':
        query = "SELECT * FROM Cuotas WHERE idCliente = %s AND estado = %s;"
        values = (id_cliente, estado_cuotas)
        cursor.execute(query, values)
    else:
        query = "SELECT * FROM Cuotas WHERE idCliente = %s"
        values = (id_cliente,)
        cursor.execute(query, values)
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    emit('respuesta_listarCuotas', data)
    

@socketio.on('realizarReversionCuota', namespace='/pago')
def realizarPagoCuota(parametros):
    print(datetime.today(), "realizarReversionCuota", parametros)
    respuesta = registrarReversion(parametros)

    data = {
        'ok': respuesta,
        'mensaje': "Ok" if respuesta else "Error al reversar pago",
        'data': parametros['id_cuota']
    }

    time.sleep(5)
    emit('respuesta_cambioEstadoCuota', data)


def registrarListaCuotas(parametros):
    id_cliente = parametros['id_cliente']
    cuotas = parametros['cuotas']
    fecha_inicio = parametros['fecha_inicio']
    monto = parametros['monto']

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Obtener el idPrestamo más alto
        cursor.execute("SELECT MAX(idPrestamo) FROM progsistemasabiertos1.Cuotas")
        result = cursor.fetchone()
        max_id_prestamo = result[0] if result[0] is not None else 0

        # Incrementar el idPrestamo
        new_id_prestamo = max_id_prestamo + 1

        for i in range(1, int(cuotas) + 1):
            query = "INSERT INTO progsistemasabiertos1.Cuotas(numCuota, monto, fechaPago, idCliente, idPrestamo) VALUES (%s, %s, DATE_ADD(%s, INTERVAL %s MONTH), %s, %s);"
            values = (i, monto, fecha_inicio, i - 1, id_cliente, new_id_prestamo)
            cursor.execute(query, values)
        conn.commit()

        cursor.close()
        conn.close()

        return True
    except Exception as e:
        print(f'Error: {str(e)}')
        return False


# Capturar el evento "solicitar_listaClientes" iniciado por el html
@socketio.on('registrarListaCuotas', namespace='/registro-cuotas')
def realizarPagoCuota(parametros):
    print(datetime.today(), "registrarListaCuotas" , parametros)
    respuesta = registrarListaCuotas(parametros)

    data = {
            'ok': respuesta,
            'mensaje': "Cuotas registradas correctamente" if respuesta else "Error al registrar pago"
        }

    emit('respuesta_registrarListaCuotas', data)


def obtenerClientesActivos():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM Cliente where estado = '1'")
        clientes = cursor.fetchall()
        cursor.close()
        conn.close()

        return clientes
    except Exception as e:
        print(f'Error: {str(e)}')
        return []

# Capturar el evento "solicitar_listaClientes" iniciado por el html
@socketio.on('solicitar_listaClientes', namespace='/clientes')
def solicitar_listaClientes():
    print(datetime.today(), "solicitar_listaClientes")

    listaClientes = obtenerClientesActivos()

    
    # Armar objeto para respuesta
    # respuesta = {
    #     'data': listaClientes,
    #     'cuotas': listaClientes,
    #     'pagos': listaClientes,
    # }
    respuesta = {
        'data': listaClientes,
    }

    # Disparar el evento "solicitar_listaClientes" se envía el objeto armado previamente, que luego es capturado por el html
    emit('respuesta_listaClientes', respuesta)


@socketio.on('validarLogin', namespace='/clientes')
def validarLo(data):
    username = data.user
    password = data.password
    # Conecta a la base de datos
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Realiza una consulta para buscar el usuario y contraseña
    cursor.execute(
        "SELECT username, password FROM Usuarios WHERE username = %s AND password = %s",
        (username, password))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:
        emit('respuesta_loginOk', {})
    else:
        emit('respuesta_loginIncorrecto', { 'mensaje': "Datos invalidos" })

if __name__ == '__main__':
    socketio.run(app, port=8000, debug=True)
