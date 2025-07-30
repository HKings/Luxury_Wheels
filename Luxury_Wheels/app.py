import os
from datetime import timedelta, datetime
from operator import or_

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, url_for, redirect, request, flash, current_app, session
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from werkzeug.exceptions import BadRequest
from werkzeug.security import generate_password_hash

import admin
import user
import auth
import urls
from models import Clientes, db, Admin, Veiculos, Categoria, VehicleType
from views import bp as views_bp

app = Flask(__name__)  # Criação da aplicação Flask

app.config['SECRET_KEY'] = "my_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurações para upload de arquivos
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads/')  # Assume que a pasta static está no mesmo diretório que
# seu arquivo app.py
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

db.init_app(app)  # Inicialização da aplicação usando a instância `db` importada
migrate = Migrate(app, db)  # Inicialização do Migrate

# Configuração do tempo máximo que uma sessão pode estar ativa
app.permanent_session_lifetime = timedelta(minutes=30)

# Cursor para a base de dados SQLite
# db = SQLAlchemy(app)

# Configuração do gestor de início de sessão do flask
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page!'  # Mensagem personalizada quando o utilizador não
# faz login
login_manager.login_message_category = 'warning'  # Categoria da mensagem ('warning')

# Criar um scheduler
scheduler = BackgroundScheduler()

# Adicionar a tarefa de atualização ao scheduler (Biblioteca de agendamento em Python, para agendar a execução de uma
# determinada função ou tarefa) Verifica a cada minuto
scheduler.add_job(func=Veiculos.update_all_vehicles_availability, trigger="interval", minutes=1)

# Iniciar o scheduler
scheduler.start()


# Tem como propósito carregar um usuário a partir do ID armazenado na sessão
@login_manager.user_loader
def load_user(user_id):  # A função load_user, recebe um parâmetro user_id. Este ID é o identificador único do usuário
    # Caso o usuário não foi encontrado na tabela Clientes, a função tenta carregar um usuário da tabela Admin usando o
    # mesmo método query.get()
    if user_id.startswith('admin_'):  # Verifica se o user_id começa com o 'admin', indicando que é um administrador
        admin_id = int(user_id.split('_')[1])  # Extrai o ID do admin e busca-o no banco de dados
        return Admin.query.get(admin_id)
    elif user_id.startswith('client_'):  # Verifica se o user_id começa com o 'client', indicando que é um cliente
        client_id = int(user_id.split('_')[1])  # Extrai o ID do client e busca-o no banco de dados
        return Clientes.query.get(client_id)
    return None  # Retorna None se não encontrar o padrão conhecido


# Registro de Blueprint de Autenticação no Flask
app.register_blueprint(auth.bp)
app.register_blueprint(urls.bp)
app.register_blueprint(views_bp)
app.register_blueprint(admin.bp)
app.register_blueprint(user.bp)


@app.route('/')
@app.route('/home')
def home():
    return render_template("home.html")


@app.route('/sobre_nos')
def sobre_nos():
    return render_template("sobre_nos.html")


# ------------------------------- Pág. de reserva dos veículos --------------------------------------


# Pág. da lista de veículos para reservar
@app.route('/list_vehicle')
def list_vehicle():
    try:
        # Primeiro, atualizar o status de todos os veículos que precisam ser atualizados
        current_datetime = datetime.now()

        vehicles_to_update = Veiculos.query.filter(
            or_(Veiculos.available_from.isnot(None), Veiculos.maintenance_end.isnot(None))).all()

        for vehicle in vehicles_to_update:
            # Se a manutenção acabou
            if vehicle.maintenance_end and current_datetime > vehicle.maintenance_end:
                vehicle.in_maintenance = False
                vehicle.status = True

            # Se o período de indisponibilidade acabou
            if vehicle.available_from and current_datetime >= vehicle.available_from:
                vehicle.status = True
                vehicle.available_from = None

        # Commit das alterações de status
        db.session.commit()

        # Obter parâmetros de filtro
        tipo = request.args.get('type', '')
        marca = request.args.get('brand', '')
        modelo = request.args.get('model', '')
        categoria_id = request.args.get('category')
        assentos = request.args.get('seats')
        transmissao = request.args.get('transmission', '')
        preco_dia = request.args.get('price_per_day', '')

        # Iniciar a query
        query = Veiculos.query

        # Aplicar filtros
        if tipo:
            query = query.filter(Veiculos.type == tipo)
        if marca:
            query = query.filter(Veiculos.brand.ilike(f'%{marca}%'))  # Utilizou-se o operador ilike porque ele não
            # faz distinção entre letras maiúsculas e minúsculas.
        if modelo:
            query = query.filter(Veiculos.model.ilike(f'%{modelo}%'))  # Utilizou-se o operador ilike porque ele não
            # faz distinção entre letras maiúsculas e minúsculas.
        if categoria_id:
            query = query.filter(Veiculos.categoria_id == int(categoria_id))
        if assentos:
            query = query.filter(Veiculos.seats == int(assentos))
        if transmissao:
            query = query.filter(Veiculos.transmission.ilike(f'%{transmissao}%'))  # Utilizou-se o operador ilike
            # para fazer a distinção entre letras maiúsculas e minúsculas.
        if preco_dia:
            query = query.filter(Veiculos.price_per_day == float(preco_dia))

        # Paginação dos cards
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Número de veículos por página
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        vehicles = pagination.items

        # Enviar uma mensagem caso não foram encontrados veículos pesquisados
        if not vehicles and (tipo or marca or modelo or categoria_id or assentos or transmissao or preco_dia):
            flash('Nenhum veículo encontrado com os critérios de busca especificados.', 'error')
            return redirect(url_for('list_vehicle'))

        # Carregar imagens para cada veículo
        for vehicle in vehicles:
            vehicle.images = vehicle.get_imagens()

            # Adicionar um atributo para indicar se o veículo está disponível para reserva
            vehicle.can_reserve = vehicle.is_available()

        # Obter todas as categorias para o filtro
        categories = Categoria.query.all()

        return render_template('list_vehicle.html', vehicles=vehicles, categories=categories, pagination=pagination,
                               marca=marca, modelo=modelo, assentos=assentos, tipo=tipo,
                               transmissao=transmissao, preco_dia=preco_dia, VehicleType=VehicleType)

    except BadRequest:
        flash('Erro nos parâmetros de busca. Por favor, tente novamente.', 'error')
        return redirect(url_for('list_vehicle'))

    except Exception as e:
        flash(f'Ocorreu um erro: {str(e)}', 'error')
        return redirect(url_for('list_vehicle'))


# Apagar pesquisa
@app.route('/list_vehicle/clear', methods=['GET'])
def clear_listVehicle():
    return redirect(url_for('list_vehicle'))


with app.app_context():  # Nesta linha o contexto da aplicação Flask é ativado, como as interações com o banco de dados
    db.create_all()  # Esta linha é MUITO IMPORTANTE, pois é RESPONSÁVEL por criar todas as tabelas no banco de dados
    # que ainda não existem

    Admin.query.update({Admin.user_type: 'admin'})
    Clientes.query.update({Clientes.user_type: 'client'})
    db.session.commit()  # Esta linha cria todas as tabelas no banco de dados que ainda não existem

    # with app.app_context():  # Nesta linha o contexto da aplicação Flask é ativado, como as interações com o banco de
    #     # dados
    #     db.create_all()  # Esta linha cria todas as tabelas no banco de dados que ainda não existem

    # ------------------------------- Criar e adicionar Admin --------------------------------------
    # Verifica se o administrador já existe, para não haver repetições
    admin_exists = Admin.query.filter_by(username="admin1").first()
    if not admin_exists:
        # Cria um administrador
        new_admin = Admin(username="admin1", password=generate_password_hash("admin", method='pbkdf2:sha256'))
        # Adiciona o administrador ao banco de dados
        db.session.add(new_admin)
        db.session.commit()
    else:
        # Atualizar a senha do administrador existente
        admin_exists.password = generate_password_hash("admin", method='pbkdf2:sha256')
        db.session.commit()

    # ------------------------------- Criar e adicionar categorias --------------------------------------
    # Criar categorias de carros
    categorias_carro = [
        Categoria("Mini", VehicleType.CARRO),
        Categoria("Económico", VehicleType.CARRO),
        Categoria("Compacto", VehicleType.CARRO),
        Categoria("Intermédio", VehicleType.CARRO),
        Categoria("Familiar", VehicleType.CARRO),
        Categoria("Luxo", VehicleType.CARRO),
        Categoria("Descapotável", VehicleType.CARRO),
        Categoria("SUV", VehicleType.CARRO),
        Categoria("Comercial", VehicleType.CARRO),
    ]

    # Criar categorias de motos
    categorias_moto = [
        Categoria("Motos Scooters", VehicleType.MOTA),
        Categoria("Motos de Turismo", VehicleType.MOTA),
        Categoria("Motos Desportivas", VehicleType.MOTA),
        Categoria("Motos de Aventura", VehicleType.MOTA),
        Categoria("Motos Off-Road", VehicleType.MOTA)
    ]

    # Adicionar todas as categorias no banco de dados
    for categoria in categorias_carro + categorias_moto:
        existing_categoria = Categoria.query.filter_by(nome=categoria.nome, tipo_veiculo=categoria.tipo_veiculo).first()
        if not existing_categoria:
            db.session.add(categoria)
    db.session.commit()  # Confirma as alterações no banco de dados

if __name__ == '__main__':
    app.run(debug=True)  # Função responsável por executar o servidor Web, o debug=True quer dizer que estamos no
    # modo desenvolvedor, de forma recarrecar automaticamente sozinho em cada modificação feita no código
