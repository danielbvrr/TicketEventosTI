from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configuração do banco de dados SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de Dados (Tabela de Eventos)
class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # ID único para cada evento
    tipo = db.Column(db.String(100), nullable=False)  # Tipo de evento
    origem = db.Column(db.String(100), nullable=False)  # Origem da solicitação
    data = db.Column(db.String(20), nullable=False)  # Data do evento
    numero_sei = db.Column(db.String(50), nullable=False)  # Número do processo SEI
    tecnicos = db.Column(db.String(200), nullable=False)  # Técnicos responsáveis
    equipamentos = db.Column(db.String(200), nullable=False)  # Equipamentos utilizados
    tombamentos = db.Column(db.String(200), nullable=False)  # Números de tombamento

# Criar as tabelas no banco de dados
with app.app_context():
    db.create_all()

# Página inicial com o formulário de cadastro
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Coletando dados do formulário
        tipo = request.form['tipo']
        origem = request.form['origem']
        data = request.form['data']
        numero_sei = request.form['numero_sei']
        tecnicos = request.form['tecnicos']
        equipamentos = request.form['equipamentos']
        tombamentos = request.form['tombamentos']

        # Criando um novo evento no banco de dados
        novo_evento = Evento(
            tipo=tipo,
            origem=origem,
            data=data,
            numero_sei=numero_sei,
            tecnicos=tecnicos,
            equipamentos=equipamentos,
            tombamentos=tombamentos
        )

        db.session.add(novo_evento)  # Adicionando ao banco de dados
        db.session.commit()  # Salvando as alterações

        return redirect(url_for('index'))  # Redirecionando para a página inicial

    eventos = Evento.query.all()  # Recuperando todos os eventos cadastrados
    return render_template('index.html', eventos=eventos)  # Renderizando o HTML

if __name__ == '__main__':
    app.run(debug=True)  # Executando o servidor
