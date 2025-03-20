import sqlite3

# Conecta ao banco de dados (ou cria se não existir)
conn = sqlite3.connect('eventos.db')
cursor = conn.cursor()

# Cria as tabelas
cursor.execute('''
CREATE TABLE IF NOT EXISTS tecnicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS tipos_equipamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_sei TEXT NOT NULL,
    tipo TEXT NOT NULL,
    data_inicio TEXT NOT NULL,
    data_fim TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS eventos_tecnicos (
    evento_id INTEGER,
    tecnico_id INTEGER,
    FOREIGN KEY (evento_id) REFERENCES eventos (id),
    FOREIGN KEY (tecnico_id) REFERENCES tecnicos (id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS equipamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evento_id INTEGER,
    tipo_id INTEGER,
    marca_modelo TEXT NOT NULL,
    tombamento TEXT NOT NULL,
    FOREIGN KEY (evento_id) REFERENCES eventos (id),
    FOREIGN KEY (tipo_id) REFERENCES tipos_equipamentos (id)
)
''')

conn.commit()