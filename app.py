from flask import Flask, render_template, request, redirect, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "sua_chave_secreta_aqui"

# Função para conectar ao banco de dados
def get_db_connection():
    conn = sqlite3.connect('eventos.db')
    conn.row_factory = sqlite3.Row  # Retorna as linhas como dicionários
    return conn

@app.route("/", methods=["GET", "POST"])
def index():
    conn = get_db_connection()
    if request.method == "POST":
        # Coleta os dados do formulário
        numero_sei = request.form["numero_sei"]
        tipo = request.form["tipo"]
        data_inicio = request.form["data_inicio"]
        data_fim = request.form["data_fim"]
        tecnicos = request.form.getlist("tecnicos")
        equipamentos_tipo = request.form.getlist("equipamentos_tipo[]")
        equipamentos_marca_modelo = request.form.getlist("equipamentos_marca_modelo[]")
        equipamentos_tombamento = request.form.getlist("equipamentos_tombamento[]")

        # Insere o evento no banco de dados
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO eventos (numero_sei, tipo, data_inicio, data_fim)
            VALUES (?, ?, ?, ?)
        ''', (numero_sei, tipo, data_inicio, data_fim))
        evento_id = cursor.lastrowid  # Obtém o ID do evento inserido

        # Associa os técnicos ao evento
        for tecnico_id in tecnicos:
            cursor.execute('''
                INSERT INTO eventos_tecnicos (evento_id, tecnico_id)
                VALUES (?, ?)
            ''', (evento_id, tecnico_id))

        # Insere os equipamentos no banco de dados
        for tipo_id, marca_modelo, tombamento in zip(equipamentos_tipo, equipamentos_marca_modelo, equipamentos_tombamento):
            cursor.execute('''
                INSERT INTO equipamentos (evento_id, tipo_id, marca_modelo, tombamento)
                VALUES (?, ?, ?, ?)
            ''', (evento_id, tipo_id, marca_modelo, tombamento))

        conn.commit()
        flash("Evento adicionado com sucesso!", "success")
        return redirect("/")

    # Recupera os dados para exibição
    eventos = conn.execute('SELECT * FROM eventos').fetchall()

    # Para cada evento, recupera os técnicos e equipamentos associados
    eventos_completos = []
    for evento in eventos:
        # Recupera os técnicos do evento
        tecnicos_evento = conn.execute('''
            SELECT t.nome
            FROM tecnicos t
            JOIN eventos_tecnicos et ON t.id = et.tecnico_id
            WHERE et.evento_id = ?
        ''', (evento['id'],)).fetchall()

        # Recupera os equipamentos do evento
        equipamentos_evento = conn.execute('''
            SELECT e.marca_modelo, e.tombamento, te.nome AS tipo
            FROM equipamentos e
            JOIN tipos_equipamentos te ON e.tipo_id = te.id
            WHERE e.evento_id = ?
        ''', (evento['id'],)).fetchall()

        # Adiciona os dados ao evento
        eventos_completos.append({
            **evento,  # Desempacota os dados do evento
            "tecnicos": [tecnico['nome'] for tecnico in tecnicos_evento],
            "equipamentos": equipamentos_evento
        })

    tecnicos_cadastrados = conn.execute('SELECT * FROM tecnicos').fetchall()
    tipos_equipamentos = conn.execute('SELECT * FROM tipos_equipamentos').fetchall()
    conn.close()

    return render_template("index.html", eventos=eventos_completos, tecnicos_cadastrados=tecnicos_cadastrados, tipos_equipamentos=tipos_equipamentos)

@app.route("/cadastrar_tecnico", methods=["GET", "POST"])
def cadastrar_tecnico():
    if request.method == "POST":
        novo_tecnico = request.form.get("novo_tecnico")
        if novo_tecnico:
            conn = get_db_connection()
            try:
                conn.execute('INSERT INTO tecnicos (nome) VALUES (?)', (novo_tecnico,))
                conn.commit()
                flash("Técnico cadastrado com sucesso!", "success")
            except sqlite3.IntegrityError:
                flash("Técnico já cadastrado!", "error")
            conn.close()
        else:
            flash("Nome do técnico inválido!", "error")
        return redirect("/cadastrar_tecnico")
    return render_template("cadastrar_tecnico.html")

@app.route("/cadastrar_tipo_equipamento", methods=["GET", "POST"])
def cadastrar_tipo_equipamento():
    if request.method == "POST":
        novo_tipo = request.form.get("novo_tipo")
        if novo_tipo:
            conn = get_db_connection()
            try:
                conn.execute('INSERT INTO tipos_equipamentos (nome) VALUES (?)', (novo_tipo,))
                conn.commit()
                flash("Tipo de equipamento cadastrado com sucesso!", "success")
            except sqlite3.IntegrityError:
                flash("Tipo de equipamento já cadastrado!", "error")
            conn.close()
        else:
            flash("Nome do tipo de equipamento inválido!", "error")
        return redirect("/cadastrar_tipo_equipamento")
    return render_template("cadastrar_tipo_equipamento.html")

@app.route("/editar/<int:evento_id>", methods=["GET", "POST"])
def editar_evento(evento_id):
    conn = get_db_connection()
    if request.method == "POST":
        # Atualiza os dados do evento
        numero_sei = request.form["numero_sei"]
        tipo = request.form["tipo"]
        data_inicio = request.form["data_inicio"]
        data_fim = request.form["data_fim"]
        tecnicos = request.form.getlist("tecnicos")
        equipamentos_tipo = request.form.getlist("equipamentos_tipo[]")
        equipamentos_marca_modelo = request.form.getlist("equipamentos_marca_modelo[]")
        equipamentos_tombamento = request.form.getlist("equipamentos_tombamento[]")

        # Atualiza o evento
        conn.execute('''
            UPDATE eventos
            SET numero_sei = ?, tipo = ?, data_inicio = ?, data_fim = ?
            WHERE id = ?
        ''', (numero_sei, tipo, data_inicio, data_fim, evento_id))

        # Remove as associações antigas de técnicos e equipamentos
        conn.execute('DELETE FROM eventos_tecnicos WHERE evento_id = ?', (evento_id,))
        conn.execute('DELETE FROM equipamentos WHERE evento_id = ?', (evento_id,))

        # Associa os novos técnicos ao evento
        for tecnico_id in tecnicos:
            conn.execute('''
                INSERT INTO eventos_tecnicos (evento_id, tecnico_id)
                VALUES (?, ?)
            ''', (evento_id, tecnico_id))

        # Insere os novos equipamentos
        for tipo_id, marca_modelo, tombamento in zip(equipamentos_tipo, equipamentos_marca_modelo, equipamentos_tombamento):
            conn.execute('''
                INSERT INTO equipamentos (evento_id, tipo_id, marca_modelo, tombamento)
                VALUES (?, ?, ?, ?)
            ''', (evento_id, tipo_id, marca_modelo, tombamento))

        conn.commit()
        flash("Evento atualizado com sucesso!", "success")
        return redirect("/")

    # Recupera os dados do evento para edição
    evento = conn.execute('SELECT * FROM eventos WHERE id = ?', (evento_id,)).fetchone()
    tecnicos_evento = conn.execute('''
        SELECT t.id, t.nome
        FROM tecnicos t
        JOIN eventos_tecnicos et ON t.id = et.tecnico_id
        WHERE et.evento_id = ?
    ''', (evento_id,)).fetchall()
    equipamentos_evento = conn.execute('''
        SELECT e.tipo_id, e.marca_modelo, e.tombamento
        FROM equipamentos e
        WHERE e.evento_id = ?
    ''', (evento_id,)).fetchall()
    tecnicos_cadastrados = conn.execute('SELECT * FROM tecnicos').fetchall()
    tipos_equipamentos = conn.execute('SELECT * FROM tipos_equipamentos').fetchall()
    conn.close()

    return render_template("editar.html", evento=evento, tecnicos_evento=tecnicos_evento, equipamentos_evento=equipamentos_evento, tecnicos_cadastrados=tecnicos_cadastrados, tipos_equipamentos=tipos_equipamentos)

@app.route("/excluir/<int:evento_id>")
def excluir_evento(evento_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM eventos WHERE id = ?', (evento_id,))
    conn.execute('DELETE FROM eventos_tecnicos WHERE evento_id = ?', (evento_id,))
    conn.execute('DELETE FROM equipamentos WHERE evento_id = ?', (evento_id,))
    conn.commit()
    conn.close()
    flash("Evento excluído com sucesso!", "success")
    return redirect("/")

@app.route("/remover_tecnico/<int:tecnico_id>")
def remover_tecnico(tecnico_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tecnicos WHERE id = ?', (tecnico_id,))
    conn.commit()
    conn.close()
    flash("Técnico removido com sucesso!", "success")
    return redirect("/")

@app.route("/remover_tipo_equipamento/<int:tipo_id>")
def remover_tipo_equipamento(tipo_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tipos_equipamentos WHERE id = ?', (tipo_id,))
    conn.commit()
    conn.close()
    flash("Tipo de equipamento removido com sucesso!", "success")
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)