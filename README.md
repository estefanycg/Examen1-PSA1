# Instalar Flask
pip install Flask

# Iniciar la app
py app.py


@app.route('/revertir-cuota', methods=['POST'])
def revertirCuota():
    id_cuota = request.form.get('id_cuota')
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    query = "UPDATE progsistemasabiertos1.Cuotas SET estado = 0, fechaRealPago = NULL, referencia = '' WHERE idCuotas = %s;"
    values = (int(id_cuota), )
    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('pagoCuotas'))