from flask import Flask, render_template, request, redirect, flash, jsonify, send_file
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO

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

    # Para cada evento, recupera os técnicos, equipamentos e atividades associados
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

        # Recupera as atividades do evento
        atividades_evento = conn.execute('''
            SELECT a.data, a.descricao, t.nome AS tecnico
            FROM atividades a
            JOIN tecnicos t ON a.tecnico_id = t.id
            WHERE a.evento_id = ?
        ''', (evento['id'],)).fetchall()

        # Adiciona os dados ao evento
        eventos_completos.append({
            **evento,  # Desempacota os dados do evento
            "tecnicos": [tecnico['nome'] for tecnico in tecnicos_evento],
            "equipamentos": equipamentos_evento,
            "atividades": atividades_evento
        })

    tecnicos_cadastrados = conn.execute('SELECT * FROM tecnicos').fetchall()
    tipos_equipamentos = conn.execute('SELECT * FROM tipos_equipamentos').fetchall()
    conn.close()

    return render_template("index.html", eventos=eventos_completos, tecnicos_cadastrados=tecnicos_cadastrados, tipos_equipamentos=tipos_equipamentos)

# Rota para relatorio_atividades
@app.route("/relatorio_atividades/<int:evento_id>", methods=["GET", "POST"])
def relatorio_atividades(evento_id):
    conn = get_db_connection()
    if request.method == "POST":
        # Coleta os dados do formulário
        tecnico_id = request.form["tecnico"]
        data = request.form["data"]
        descricao = request.form["descricao"]

        # Insere a atividade no banco de dados
        conn.execute('''
            INSERT INTO atividades (evento_id, tecnico_id, data, descricao)
            VALUES (?, ?, ?, ?)
        ''', (evento_id, tecnico_id, data, descricao))
        conn.commit()
        flash("Atividade registrada com sucesso!", "success")
        return redirect(f"/relatorio_atividades/{evento_id}")

    # Recupera os dados do evento e as atividades
    evento = conn.execute('SELECT * FROM eventos WHERE id = ?', (evento_id,)).fetchone()
    atividades = conn.execute('''
        SELECT a.data, a.descricao, t.nome AS tecnico
        FROM atividades a
        JOIN tecnicos t ON a.tecnico_id = t.id
        WHERE a.evento_id = ?
    ''', (evento_id,)).fetchall()
    tecnicos = conn.execute('SELECT * FROM tecnicos').fetchall()
    conn.close()

    return render_template("relatorio_atividades.html", evento=evento, atividades=atividades, tecnicos=tecnicos)

# Rota para cadastrar técnico
@app.route("/cadastrar_tecnico", methods=["POST"])
def cadastrar_tecnico():
    nome = request.form.get("novo_tecnico")
    if nome:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO tecnicos (nome) VALUES (?)', (nome,))
        tecnico_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"success": True, "id": tecnico_id, "nome": nome})
    else:
        return jsonify({"success": False, "message": "Nome do técnico não pode estar vazio."})

# Rota para cadastrar tipo de equipamento
@app.route("/cadastrar_tipo_equipamento", methods=["POST"])
def cadastrar_tipo_equipamento():
    nome = request.form.get("novo_tipo")
    if nome:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO tipos_equipamentos (nome) VALUES (?)', (nome,))
        tipo_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"success": True, "id": tipo_id, "nome": nome})
    else:
        return jsonify({"success": False, "message": "Nome do tipo de equipamento não pode estar vazio."})

# Rota para editar técnico
@app.route("/editar_tecnico/<int:tecnico_id>", methods=["GET", "POST"])
def editar_tecnico(tecnico_id):
    conn = get_db_connection()
    tecnico = conn.execute('SELECT * FROM tecnicos WHERE id = ?', (tecnico_id,)).fetchone()
    if request.method == "POST":
        novo_nome = request.form["novo_nome"]
        if novo_nome:
            conn.execute('UPDATE tecnicos SET nome = ? WHERE id = ?', (novo_nome, tecnico_id))
            conn.commit()
            conn.close()
            flash("Técnico atualizado com sucesso!", "success")
            return redirect("/")
        else:
            flash("Nome do técnico não pode estar vazio.", "error")

    conn.close()
    return render_template("editar_tecnico.html", tecnico=tecnico)

# Rota para excluir técnico
@app.route("/remover_tecnico/<int:tecnico_id>")
def remover_tecnico(tecnico_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tecnicos WHERE id = ?', (tecnico_id,))
    conn.commit()
    conn.close()
    flash("Técnico removido com sucesso!", "success")
    return redirect("/")

# Rota para excluir tipo de equipamento
@app.route("/remover_tipo_equipamento/<int:tipo_id>")
def remover_tipo_equipamento(tipo_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tipos_equipamentos WHERE id = ?', (tipo_id,))
    conn.commit()
    conn.close()
    flash("Tipo de equipamento removido com sucesso!", "success")
    return redirect("/")

@app.route("/editar/<int:evento_id>", methods=["GET", "POST"])
def editar_evento(evento_id):
    conn = get_db_connection()

    if request.method == "POST":
        # Atualiza os dados do evento
        numero_sei = request.form["numero_sei"]
        tipo = request.form["tipo"]
        data_inicio = request.form["data_inicio"]
        data_fim = request.form["data_fim"]

        conn.execute('''
            UPDATE eventos
            SET numero_sei = ?, tipo = ?, data_inicio = ?, data_fim = ?
            WHERE id = ?
        ''', (numero_sei, tipo, data_inicio, data_fim, evento_id))

        # Atualiza os técnicos associados ao evento
        tecnicos = request.form.getlist("tecnicos")
        conn.execute('DELETE FROM eventos_tecnicos WHERE evento_id = ?', (evento_id,))
        for tecnico_id in tecnicos:
            conn.execute('INSERT INTO eventos_tecnicos (evento_id, tecnico_id) VALUES (?, ?)', (evento_id, tecnico_id))

        # Atualiza os equipamentos associados ao evento
        equipamentos_tipo = request.form.getlist("equipamentos_tipo[]")
        equipamentos_marca_modelo = request.form.getlist("equipamentos_marca_modelo[]")
        equipamentos_tombamento = request.form.getlist("equipamentos_tombamento[]")
        conn.execute('DELETE FROM equipamentos WHERE evento_id = ?', (evento_id,))
        for tipo_id, marca_modelo, tombamento in zip(equipamentos_tipo, equipamentos_marca_modelo, equipamentos_tombamento):
            conn.execute('''
                INSERT INTO equipamentos (evento_id, tipo_id, marca_modelo, tombamento)
                VALUES (?, ?, ?, ?)
            ''', (evento_id, tipo_id, marca_modelo, tombamento))

        conn.commit()
        conn.close()
        flash("Evento atualizado com sucesso!", "success")
        return redirect("/")

    # Recupera os dados do evento
    evento = conn.execute('SELECT * FROM eventos WHERE id = ?', (evento_id,)).fetchone()

    # Recupera os técnicos associados ao evento
    tecnicos_evento = conn.execute('''
        SELECT t.id, t.nome
        FROM tecnicos t
        JOIN eventos_tecnicos et ON t.id = et.tecnico_id
        WHERE et.evento_id = ?
    ''', (evento_id,)).fetchall()

    # Recupera os equipamentos associados ao evento
    equipamentos_evento = conn.execute('''
        SELECT e.id, e.tipo_id, e.marca_modelo, e.tombamento
        FROM equipamentos e
        WHERE e.evento_id = ?
    ''', (evento_id,)).fetchall()

    # Recupera todos os técnicos e tipos de equipamentos cadastrados
    tecnicos_cadastrados = conn.execute('SELECT * FROM tecnicos').fetchall()
    tipos_equipamentos = conn.execute('SELECT * FROM tipos_equipamentos').fetchall()

    conn.close()

    return render_template(
        "editar.html",
        evento=evento,
        tecnicos_cadastrados=tecnicos_cadastrados,
        tecnicos_evento=tecnicos_evento,
        equipamentos_evento=equipamentos_evento,
        tipos_equipamentos=tipos_equipamentos
    )

# Rota para excluir evento
@app.route("/excluir/<int:evento_id>")
def excluir_evento(evento_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM eventos WHERE id = ?', (evento_id,))
    conn.commit()
    conn.close()
    flash("Evento excluído com sucesso!", "success")
    return redirect("/")

# Rota para expoxtar para pdf
@app.route("/exportar_pdf/<int:evento_id>")
def exportar_pdf(evento_id):
    conn = get_db_connection()

    # Recupera os dados do evento
    evento = conn.execute('SELECT * FROM eventos WHERE id = ?', (evento_id,)).fetchone()
    if not evento:
        conn.close()
        flash("Evento não encontrado.", "error")
        return redirect("/")

    # Recupera os técnicos, equipamentos e atividades
    tecnicos_evento = conn.execute('''
        SELECT t.nome
        FROM tecnicos t
        JOIN eventos_tecnicos et ON t.id = et.tecnico_id
        WHERE et.evento_id = ?
    ''', (evento_id,)).fetchall()

    equipamentos_evento = conn.execute('''
        SELECT e.marca_modelo, e.tombamento, te.nome AS tipo
        FROM equipamentos e
        JOIN tipos_equipamentos te ON e.tipo_id = te.id
        WHERE e.evento_id = ?
    ''', (evento_id,)).fetchall()

    atividades_evento = conn.execute('''
        SELECT a.data, a.descricao, t.nome AS tecnico
        FROM atividades a
        JOIN tecnicos t ON a.tecnico_id = t.id
        WHERE a.evento_id = ?
    ''', (evento_id,)).fetchall()

    conn.close()

    # Cria o PDF
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Adiciona conteúdo ao PDF
    story.append(Paragraph("Relatório de Evento", styles['Title']))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Nº SEI:</b> {evento['numero_sei']}", styles['Normal']))
    story.append(Paragraph(f"<b>Tipo:</b> {evento['tipo']}", styles['Normal']))
    story.append(Paragraph(f"<b>Data de Início:</b> {evento['data_inicio']}", styles['Normal']))
    story.append(Paragraph(f"<b>Data de Fim:</b> {evento['data_fim']}", styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Técnicos Responsáveis:</b>", styles['Normal']))
    tecnicos_text = ", ".join([tecnico['nome'] for tecnico in tecnicos_evento])
    story.append(Paragraph(tecnicos_text, styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Equipamentos:</b>", styles['Normal']))
    equipamentos_data = [["Tipo", "Marca/Modelo", "Tombamento"]]
    for equipamento in equipamentos_evento:
        equipamentos_data.append([equipamento['tipo'], equipamento['marca_modelo'], equipamento['tombamento']])
    equipamentos_table = Table(equipamentos_data)
    equipamentos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(equipamentos_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Atividades Registradas:</b>", styles['Normal']))
    atividades_data = [["Data", "Técnico", "Descrição"]]
    for atividade in atividades_evento:
        atividades_data.append([atividade['data'], atividade['tecnico'], atividade['descricao']])
    atividades_table = Table(atividades_data)
    atividades_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(atividades_table)

    # Gera o PDF
    pdf.build(story)

    # Retorna o PDF como resposta
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"relatorio_evento_{evento_id}.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    app.run(debug=True)