from flask import Flask, request
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime

# --- Configuração do App ---
app = Flask(__name__)
api = Api(app)

# --- Configuração do ORM (SQLAlchemy) ---
# 1. String de conexão no formato que o SQLAlchemy espera
# (Usa 'postgres' como host, pois é o nome do serviço no seu docker-compose)
DATABASE_URI = "postgresql+psycopg2://test:test@postgres:5432/databasetest"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 2. Inicializa o ORM
db = SQLAlchemy(app)

# --- Definição do Modelo (O ORM!) ---
# 3. Mapeamento da classe Python para a tabela do banco
class UserModel(db.Model):
    __tablename__ = 'users'  # Nome da tabela no banco

    # Colunas que você pediu
    id = db.Column(db.Integer, primary_key=True)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    data_nascimento = db.Column(db.Date, nullable=True) # Coluna de Data

    # Função para converter o objeto em JSON para a API
    def to_json(self):
        return {
            'id': self.id,
            'cpf': self.cpf,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'data_nascimento': self.data_nascimento.isoformat() if self.data_nascimento else None
        }

# --- Recursos da API ---

# 4. HealthCheck agora usa o ORM
class HealthCheck(Resource):
    def get(self):
        try:
            # Tenta executar um comando usando a sessão do SQLAlchemy
            db.session.execute(text('SELECT 1'))
            return {'status': 'ok', 'db_connection': 'successful'}, 200
        except Exception as e:
            # str(e) é importante para ver o erro completo
            return {'status': 'error', 'db_connection': f'failed: {str(e)}'}, 500

# 5. Resource de Usuário (Singular) - Para criar ou buscar UM
class User(Resource):
    # Parser para validar os dados que chegam no POST
    parser = reqparse.RequestParser()
    parser.add_argument('cpf', type=str, required=True, help='CPF é obrigatório')
    parser.add_argument('first_name', type=str, required=True, help='Primeiro nome é obrigatório')
    parser.add_argument('last_name', type=str, required=True, help='Último nome é obrigatório')
    parser.add_argument('email', type=str, required=True, help='Email é obrigatório')
    parser.add_argument('data_nascimento', type=str, required=False, help='Data de nascimento (Formato: YYYY-MM-DD)')

    # POST - Criar um novo usuário
    def post(self):
        dados = self.parser.parse_args()

        # Verifica se CPF ou Email já existem
        if UserModel.query.filter_by(cpf=dados['cpf']).first():
            return {'message': f"Usuário com CPF {dados['cpf']} já existe."}, 400
        if UserModel.query.filter_by(email=dados['email']).first():
            return {'message': f"Usuário com email {dados['email']} já existe."}, 400

        # Converte a string da data para um objeto 'date'
        data_nasc = None
        if dados['data_nascimento']:
            try:
                data_nasc = datetime.strptime(dados['data_nascimento'], '%Y-%m-%d').date()
            except ValueError:
                return {'message': 'Formato de data inválido. Use YYYY-MM-DD.'}, 400

        # Cria o objeto Python
        novo_usuario = UserModel(
            cpf=dados['cpf'],
            first_name=dados['first_name'],
            last_name=dados['last_name'],
            email=dados['email'],
            data_nascimento=data_nasc
        )

        # Salva no banco usando o ORM
        try:
            db.session.add(novo_usuario)
            db.session.commit()
            return {'message': 'Usuário criado!', 'user': novo_usuario.to_json()}, 201
        except Exception as e:
            db.session.rollback() # Desfaz em caso de erro
            return {'message': f'Erro ao salvar no banco: {str(e)}'}, 500

    # GET - Buscar um usuário pelo CPF
    def get(self, cpf):
        # Busca no banco usando o ORM
        usuario = UserModel.query.filter_by(cpf=cpf).first()
        
        if usuario:
            return usuario.to_json(), 200
        else:
            return {'message': 'Usuário não encontrado'}, 404

# 6. Resource de Usuários (Plural) - Para listar TODOS
class Users(Resource):
    def get(self):
        # 1. Busca TODOS os usuários no banco
        usuarios = UserModel.query.all()
        # 2. Converte cada um para JSON (usando uma list comprehension)
        lista_json = [u.to_json() for u in usuarios]
        # 3. Retorna a lista
        return {'users': lista_json}, 200
    
# --- Registro dos Recursos na API ---
api.add_resource(HealthCheck, '/health')
api.add_resource(User, '/user', '/user/<string:cpf>') # Endpoint para UM usuário
api.add_resource(Users, '/users') # Endpoint para TODOS os usuários

# --- Execução ---
if __name__ == '__main__':
    # 7. Cria as tabelas ANTES de rodar o app
    with app.app_context():
        db.create_all()
        
    app.run(debug=True, host='0.0.0.0')