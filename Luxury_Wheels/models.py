from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date

from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

db = SQLAlchemy()


class Clientes(db.Model, UserMixin):
    __tablename__ = "clientes"  # Nome da tabela no banco de dados

    # Definição das colunas da tabela
    id = db.Column(db.Integer, primary_key=True)  # Chave primária autoincremental
    nome = db.Column(db.String(100), nullable=False, index=True)  # Nome do cliente, obrigatório e indexado
    apelido = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    telefone = db.Column(db.String(30), nullable=False, index=True)
    data_nascimento = db.Column(db.Date, nullable=False)  # Data de nascimento obrigatória
    morada = db.Column(db.String(200), nullable=False)
    nif = db.Column(db.Integer, unique=True, nullable=False, index=True)
    password = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(10), default='client')  # Tipo de utilizador, por defeito é 'client'

    # Método construtor que inicializa um novo cliente
    def __init__(self, nome, apelido, email, telefone, data_nascimento, morada, nif, password):  # Inicializa um
        # cliente com os parâmetros especificados
        self.nome = nome.title()  # Converte as primeiras letras em maiúsculas e guarda o nome
        self.apelido = apelido.title()  # Converte as primeiras letras em maiúsculas
        self.telefone = telefone
        self.data_nascimento = data_nascimento
        self.morada = morada
        self.nif = nif
        self.email = email
        self.password = generate_password_hash(password)  # Encripta a password antes de guardar
        self.user_type = 'client'

    # Método requerido pelo Flask-Login para identificar utilizadores
    def get_id(self):
        return f"client_{self.id}"  # Retorna ID prefixado com 'client_'

    # Método para verificar se uma password está correta
    def verify_password(self, password):
        return check_password_hash(self.password, password)


# Define a classe Admin que também herda de db.Model e UserMixin
class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)  # Chave primária autoincremental
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(10), default='admin')  # Tipo de utilizador, por defeito é 'admin'

    # Método construtor que inicializa um novo administrador
    def __init__(self, username, password):
        self.username = username
        self.password = generate_password_hash(password)  # Encripta a password antes de guardar
        self.user_type = 'admin'

    # Método requerido pelo Flask-Login para identificar utilizadores
    def get_id(self):
        return f"admin_{self.id}"  # Retorna ID prefixado com 'admin_'

    # Propriedade que indica que este utilizador é um administrador
    @property
    def is_admin(self):
        return True


# Enumeração que define os tipos de veículos
class VehicleType(Enum):
    CARRO = "Carro"  # Define a opção CARRO com o valor "Carro"
    MOTA = "Mota"    # Define a opção MOTA com o valor "Mota"


# Define a classe Categoria que herda de db.Model (SQLAlchemy)
class Categoria(db.Model):
    # Define as colunas da tabela categorias
    id = db.Column(db.Integer, primary_key=True)  # Chave primária autoincremental
    nome = db.Column(db.String(60), nullable=False, unique=True)
    tipo_veiculo = db.Column(db.Enum(VehicleType), nullable=False)

    # Método construtor que inicializa uma nova categoria
    def __init__(self, nome, tipo_veiculo):
        self.nome = nome  # Define o nome da categoria
        self.tipo_veiculo = tipo_veiculo  # Define o tipo de veículo da categoria


class Veiculos(db.Model):
    __tablename__ = "veiculos"  # Nome da tabela no banco de dados

    # Definição das colunas da tabela
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(VehicleType), nullable=False)
    brand = db.Column(db.String(100), nullable=False, index=True)
    model = db.Column(db.String(100), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False)
    price_per_day = db.Column(db.Float, nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    bags = db.Column(db.Integer, nullable=False)
    transmission = db.Column(db.String(1), nullable=False, index=True)  # Neste campo só precisa de colocar as letras
    # M / A (manual / automático)
    fuel_consumption = db.Column(db.Float, nullable=False)

    # Estados do veículo
    status = db.Column(db.Boolean, default=True)
    in_maintenance = db.Column(db.Boolean, default=False)
    maintenance_start = db.Column(db.DateTime, nullable=True)
    maintenance_end = db.Column(db.DateTime, nullable=True)
    available_from = db.Column(db.DateTime, nullable=True)

    # Datas de manutenção
    last_maintenance = db.Column(db.Date)
    next_maintenance = db.Column(db.Date)
    maintenance_history = db.Column(db.String(1000), default="")

    # Estado de reserva
    is_reserved = db.Column(db.Boolean, default=False)

    last_legalization_date = db.Column(db.Date)
    next_legalization_date = db.Column(db.Date)
    legalization_history = db.Column(db.String(1000), default="")

    # Imagens e categoria
    imagens = db.Column(db.Text)  # Armazena caminhos de imagens separados por vírgula

    # Relações com outras tabelas
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"), nullable=False)  # Utiliza uma chave
    # forasteira que cria uma ligação entre a tabela veiculos e a tabela categoria
    categoria = db.relationship("Categoria", backref=db.backref("veiculos", lazy=True))  # O relationship permite
    # criar uma relação entre entre as tabelas veiculos e Categoria e desse modo as relações permitem navegar entre
    # tabelas relacionadas de maneira mais intuitiva e eficiente
    reservations = db.relationship("Reservation", backref="veiculos", lazy=True)  # O lazy=True (lazy loading) evita

    # Método construtor
    def __init__(self, type, brand, model, year, price_per_day, seats, bags, transmission, fuel_consumption, categoria,
                 status=True, maintenance_start=None, maintenance_end=None):
        self.type = type
        self.brand = brand.upper()  # Converte todas as letras em maiúsculas
        self.model = model.title()  # Converte as primeiras letras em maiúsculas
        self.year = year
        self.price_per_day = price_per_day
        self.seats = seats
        self.bags = bags
        self.transmission = transmission.title()  # Converte as primeiras letras em maiúsculas
        self.fuel_consumption = fuel_consumption
        self.maintenance_history = ""
        self.last_legalization_date = None
        self.next_legalization_date = None
        self.legalization_history = ""
        self.imagens = ""
        self.categoria = categoria
        self.status = status
        self.in_maintenance = False
        self.maintenance_start = maintenance_start
        self.maintenance_end = maintenance_end

    # Método para verificar reservas em tempo real.
    # Este método verifica se o veículo está atualmente reservado baseado na data/hora atual
    # retorna True se o veículo estiver reservado e o período de reserva ainda não terminou e,
    # retorna False se o veículo não estiver reservado ou se o período de reserva já terminou.
    def is_currently_reserved(self):
        if not self.is_reserved or not self.available_from:
            return False
        current_datetime = datetime.now()
        return current_datetime < self.available_from

    def is_in_maintenance(self):
        """Verifica se o veículo está em manutenção considerando data e hora"""
        if not self.maintenance_start or not self.maintenance_end:
            return False
        current_datetime = datetime.now()
        return self.maintenance_start <= current_datetime <= self.maintenance_end

    # Verifica em tempo real se uma reserva ainda está ativa, similar ao que já acontecia
    # com a manutenção. Isso garante que o status seja atualizado automaticamente quando
    # uma reserva expira
    def get_availability_status(self):
        # Verifica se está reservado usando o novo método
        if self.is_currently_reserved():
            return "Reservado", "reservado"

        # Verifica se o veículo está em manutenção
        if self.is_in_maintenance():
            return "Em Manutenção", "manutencao"

        # Se não está em manutenção nem reservado, verifica status e available_from
        if not self.status and self.available_from:
            current_datetime = datetime.now()
            if current_datetime < self.available_from:
                return "Indisponível até " + self.available_from.strftime('%d/%m/%Y'), "indisponivel"
            else:
                return "Disponível", "disponivel"

        # Verifica se está indisponível por algum outro motivo
        elif not self.status:
            return "Indisponível", "indisponivel"

        # Se passou por todas as verificações, está disponível
        else:
            return "Disponível", "disponivel"

    # Método para definir as imagens do veículo
    def set_imagens(self, imagens_list):
        # Se a lista de imagens existir, junta todos os caminhos com vírgulas
        # Se não existir, guarda uma string vazia
        self.imagens = ','.join(imagens_list) if imagens_list else ''

    # Método para obter as imagens do veículo
    def get_imagens(self):
        # Se não houver imagens, retorna uma lista vazia
        if not self.imagens:
            return []

        # Divide a string de imagens nas vírgulas para obter uma lista
        image_paths = self.imagens.split(',')

        # Retorna uma lista com os caminhos das imagens, removendo espaços em branco
        # e ignorando caminhos vazios
        return [path.strip() for path in image_paths if path.strip()]

    def is_available(self):
        """Verifica se o veículo está disponível para reserva"""
        current_datetime = datetime.now()

        # Se estiver em manutenção
        if self.is_in_maintenance():
            return False

        # Se estiver marcado como indisponível
        if not self.status:
            return False

        # Se tiver data futura de disponibilidade, verifica se já passou
        if self.available_from and current_datetime < self.available_from:
            return False

        return self.status

    def update_availability_after_reservation(self, end_datetime):
        """Atualiza a disponibilidade do veículo após uma reserva"""
        self.available_from = end_datetime
        self.status = False
        db.session.commit()

    def check_and_update_availability(self):
        """Verifica e atualiza o status de disponibilidade baseado no tempo"""

        # Verifica se o veículo está inativo (status=False) e tem uma data de disponibilidade definida
        if not self.status and self.available_from:
            current_datetime = datetime.now()  # Obtém a data e hora atual

            # Se a data/hora atual for maior ou igual à data de disponibilidade
            if current_datetime >= self.available_from:
                self.status = True  # Ativa o veículo
                self.available_from = None  # Remove a data de disponibilidade
                db.session.commit()  # Guarda as alterações no banco de dados
                return True   # Retorna True para indicar que houve atualização

        # Retorna False se não houve atualização
        return False

    @classmethod  # Decorator que indica que este é um método de classe (pode ser chamado sem instanciar a classe)
    def update_all_vehicles_availability(cls):
        """Atualiza a disponibilidade de todos os veículos"""

        try:
            # Busca todos os veículos que se enquadram em pelo menos uma das condições:
            vehicles = cls.query.filter(  # Utiliza-se o 'cls' (classe) para referir a própria classe,
                # isso utiliza-se quando têm o @classmethod
                or_(
                    cls.status == False,  # Veículo inativo
                    cls.available_from.isnot(None),  # Tem data de disponibilidade futura
                    cls.maintenance_end.isnot(None),  # Está em manutenção
                    cls.is_reserved == True  # Está reservado
                )
            ).all()

            # Obtém a data e hora atual
            current_datetime = datetime.now()
            updated_count = 0  # Contador de veículos atualizados

            # Para cada veículo encontrado
            for vehicle in vehicles:
                # Verifica se a manutenção terminou
                if vehicle.maintenance_end and current_datetime > vehicle.maintenance_end:
                    vehicle.in_maintenance = False  # Remove flag de manutenção
                    vehicle.maintenance_start = None  # Limpa data de início
                    vehicle.maintenance_end = None  # Limpa data de fim
                    updated_count += 1  # Incrementa o contador de veículos

                # Verifica se a reserva terminou
                if vehicle.is_reserved and vehicle.available_from and current_datetime >= vehicle.available_from:
                    vehicle.is_reserved = False  # Remove flag de reserva
                    vehicle.status = True  # Ativa o veículo
                    vehicle.available_from = None  # Limpa data de disponibilidade
                    updated_count += 1  # Incrementa o contador de veículos

                # Verifica se o período de indisponibilidade terminou (sem ser por reserva)
                elif not vehicle.is_reserved and vehicle.available_from and current_datetime >= vehicle.available_from:
                    vehicle.status = True  # Ativa o veículo
                    vehicle.available_from = None  # Limpa data de disponibilidade
                    updated_count += 1  # Incrementa o contador de veículos

            # Se houve alguma atualização, guarda no banco de dados
            if updated_count > 0:
                db.session.commit()

        except Exception as e:
            db.session.rollback()  # Em caso de erro, desfaz todas as alterações
            raise  # Propaga o erro para ser tratado em outro lugar


# Define a classe Reservation que representa uma reserva de veículo
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Chave primária autoincremental

    # Chave estrangeira para a tabela clientes (indica qual cliente fez a reserva)
    customer_id = db.Column(db.Integer, db.ForeignKey("clientes.id"),
                            nullable=False, name="fk_reservation_customer", index=True)

    # Chave estrangeira para a tabela veiculos (indica qual veículo foi reservado)
    veiculo_id = db.Column(db.Integer, db.ForeignKey("veiculos.id"),
                           nullable=False, name="fk_reservation_vehicle",index=True)

    start_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    duration = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=True)

    # Data e hora de criação da reserva (automático)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Estado da reserva (começa como "Pendente")
    status = db.Column(db.String(20), nullable=False, default="Pendente")

    # Método para adicionar uma nova reserva à base de dados
    def add_reservations(self):
        db.session.add(self)  # Adiciona a reserva à sessão
        db.session.commit()  # Guarda na base de dados

    # Atualiza as reservas concluídas para o status "Concluída"
    @staticmethod
    def update_completed_reservations():
        today = date.today()  # Obtém a data atual

        # Procura todas as reservas que:
        # 1. Já terminaram (end_date < hoje)
        # 2. Ainda não estão marcadas como concluídas
        completed_reservations = Reservation.query.filter(
            Reservation.end_date < today, Reservation.status != "Concluída").all()

        # Para cada reserva encontrada
        for reservation in completed_reservations:
            reservation.status = "Concluída"  # Atualiza o estado para "Concluída"
            db.session.commit()  # Guarda na base de dados
