from flask import Flask, render_template, request, redirect, url_for, session
#AGREGADO MÓDULO SESSION
import mysql.connector
from datetime import datetime
import random, string
import socketio

#pip install socketio
#pip install flask
#pip install mysql-connector-python

# Initialize the Socket.IO client
sio = socketio.Client()

app = Flask(__name__)

#AGREGADO
app.secret_key = '1234'
usuario = None


# MySQL configurations
db_config = {
    'user': 'progsistemasabiertos',
    'password': 'RootProgsistemasabiertos',
    'host': '178.128.156.175',
    'database': 'progsistemasabiertos1',
}

@app.route('/')
def pageDefault():
    return render_template('index.html')

#MODIFICADO
@app.route('/login', methods=['GET', 'POST'])
def pageLogin():

    error_message = ""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            error_message = "*Rellene todos los campos antes de continuar."
            return render_template('pages/login.html', error_message=error_message)

        if validarLogin(username, password):
            session['username'] = username
            return redirect(url_for('pageInicio')) 
        else:
            error_message = "Credenciales incorrectas. Inténtelo nuevamente."
            return render_template('pages/login.html', error_message=error_message)

    return render_template('pages/login.html')




#MODIFICADO
def validarLogin(username, password):
    try:
        # Conecta a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Realiza una consulta para buscar el usuario y contraseña
        cursor.execute("SELECT username, password FROM Usuarios WHERE username = %s AND password = %s", (username, password))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return True
        else:
            return False
    except Exception as e:
        print(f'Error: {str(e)}')
        return False
    

#MODIFICADO
@app.route('/inicio')
def pageInicio():
    if 'username' in session:
        usuario = session['username']
        return render_template('pages/home.html', usuario=usuario)
    else:
        return redirect(url_for('pageLogin'))

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

#MODIFICADO
from flask import flash

@app.route('/clientes/agregar_cliente', methods=['GET', 'POST'])
def pageAgregarCliente():
    if 'username' in session:
        usuario = session['username']
        
        success_message = None  # Inicializa success_message como None

        if request.method == 'POST':
            nombre = request.form.get('nombre')
            apellido = request.form.get('apellido')

            if not nombre or not apellido:
                error_message = "Los campos de nombre y apellido son obligatorios."
            else:
                # Construir el valor del campo "nombre" concatenando "nombre" y "apellido"
                nombre_completo = nombre + ' ' + apellido
                print(nombre_completo)

                try:
                    # Crear una conexión a la base de datos
                    conn = mysql.connector.connect(**db_config)
                    cursor = conn.cursor()

                    # Insertar los valores en la base de datos
                    cursor.execute("INSERT INTO Cliente (nombre, estado) VALUES (%s, %s)", (nombre_completo, 1))

                    # Confirmar la transacción y cerrar la conexión
                    conn.commit()
                    conn.close()

                    # Establecer el mensaje de éxito
                    success_message = "Cliente agregado exitosamente."

                except Exception as e:
                    success_message = "Error al intentar agregar un cliente."

        return render_template('forms/agregar_cliente.html', usuario=usuario, success_message=success_message)
    else:
        return redirect(url_for('pageLogin'))



@app.route('/clientes', methods=['GET'])
def listaClientes():
    if 'username' in session:
        usuario = session['username']
        try:
            data = [] #obtenerClientesActivos()
            return render_template('forms/cliente.html', usuario=usuario, data=data, var2=data)
        except Exception as e:
            error_message = "Error al recuperar la lista de clientes: " + str(e)
            return render_template('forms/cliente.html', usuario=usuario, error_message=error_message)
    else:
        return redirect(url_for('pageLogin'))


@app.route('/pago', methods=['GET', 'POST'])
def pagoCuotas():
    if 'username' in session:
        usuario = session['username']

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        clientes = obtenerClientesActivos()

        # Obtener la lista de idCuotas pendientes
        idCuotasPendientes = obtenerIdCuotasPendientes()
        idCuotasPagadas = obtenerCuotasARevertir()

        if request.method == 'GET':
            if request.args:
                try:
                    id_cliente = request.args.get('IdCliente')
                    estado_cuotas = request.args.get('estadocuota')
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
                except Exception as e:
                    return f'Error: {str(e)}'

                return render_template('forms/pago_cuotas.html', data=data, usuario=usuario, 
                                       clientes=clientes, cliente_seleccionado=id_cliente, estado_seleccionado=estado_cuotas,
                                       idCuotasPendientes=idCuotasPendientes,
                                       idCuotasPagadas=idCuotasPagadas)

        if request.method == 'POST':
            id_cuota = request.form.get('id_cuota')

            query = "SELECT * FROM Cuotas"
            cursor.execute(query)
            data = cursor.fetchall()

            conn.commit()
            cursor.close()
            conn.close()
            return render_template('forms/pago_cuotas.html', data=data, usuario=usuario, clientes=clientes, idCuotasPendientes=idCuotasPendientes, idCuotasPagadas=idCuotasPagadas)

        try:
            query = "SELECT * FROM Cuotas"
            cursor.execute(query)
            data = cursor.fetchall()

            cursor.close()
            conn.close()
        except Exception as e:
            return f'Error: {str(e)}'

        return render_template('forms/pago_cuotas.html', data=data, usuario=usuario, clientes=clientes, idCuotasPendientes=idCuotasPendientes, idCuotasPagadas=idCuotasPagadas)

    else:
        return redirect(url_for('pageLogin'))



def obtenerIdCuotasPendientes():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        query = """
        SELECT c1.idCuotas
        FROM progsistemasabiertos1.Cuotas c1
        JOIN progsistemasabiertos1.Cliente Cli ON Cli.idCliente = c1.idCliente
        WHERE c1.estado = 0
        AND c1.idCuotas = (
          SELECT MIN(c2.idCuotas)
          FROM progsistemasabiertos1.Cuotas c2
          WHERE c2.idPrestamo = c1.idPrestamo
          AND c2.estado = 0
        )
        GROUP BY c1.idCuotas;
        """
        cursor.execute(query)
        id_cuotas = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return id_cuotas
    except Exception as e:
        print(f'Error al obtener las idCuotas que cumplen el criterio: {str(e)}')
        return []

def obtenerCuotasARevertir():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Modifica la consulta SQL para obtener las cuotas a revertir
        query = """
        SELECT Cu.idCuotas
        FROM progsistemasabiertos1.Cuotas Cu
        WHERE Cu.estado = 1
        AND Cu.idCuotas = (
            SELECT MAX(Cu2.idCuotas)
            FROM progsistemasabiertos1.Cuotas Cu2
            WHERE Cu2.idPrestamo = Cu.idPrestamo
            AND Cu2.estado = 1
        )
        """
        cursor.execute(query)

        cuotas_revertir = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        return cuotas_revertir
    except Exception as e:
        print(f'Error: {str(e)}')
        return []

# @sio.on('respuesta_registrarListaCuotas', namespace='/registro-cuotas')
# def realizarPagoCuota(respuesta):
#     print(respuesta)
    
#     # if (respuesta['ok']):
#     #     flash(respuesta['mensaje'], "success")
#     # else:
#     #     flash(respuesta['mensaje'], "error")

#     sio.disconnect()


@app.route('/registro-cuotas', methods=['GET', 'POST'])
def registroCuotas():

    if 'username' in session:
        usuario = session['username']

        success_message = None  # Inicializa success_message como None

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        clientes = obtenerClientesActivos()
        
        # if request.method == 'POST':
        #     id_cliente = request.form.get('IdCliente')
        #     cuotas = request.form.get('cantcuotas')
        #     fecha_inicio = request.form.get('fechaini')
        #     monto = request.form.get('monto')
        #     data =  {
        #         "id_cliente": id_cliente,
        #         "cuotas": cuotas,
        #         "fecha_inicio": fecha_inicio,
        #         "monto": monto
        #     }
        #     print(data)

        #     sio.connect('http://127.0.0.1:8000')

        #     sio.emit('registrarListaCuotas', data=data, namespace='/registro-cuotas')
        
        cursor.close()
        conn.close()
        return render_template('forms/registro_cuotas.html', usuario=usuario, clientes=clientes, fechaDefault=datetime.now().strftime("%Y-%m-%d"))
    else:
        return redirect(url_for('pageLogin'))



#AGREGADO
@app.route('/cerrar-sesion')
def cerrarSesion():
    if 'username' in session:
        session.pop('username', None)  # Elimina la variable de sesión
    return redirect(url_for('pageLogin'))

if __name__ == '__main__':
    
    #Connect to a Socket.IO server in the /test namespace
    #sio.connect('http://127.0.0.1:8000/clientes')

    app.run(debug=True)