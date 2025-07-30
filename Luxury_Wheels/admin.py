import os
from operator import or_
from sqlalchemy import or_  # Operadores or_  do SQLAlchemy para construção de queries complexas
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import Clientes, db, Admin, Veiculos, VehicleType, Categoria, Reservation
from utils import allowed_file
from functools import wraps  # Adicionado este import para os decorators personalizados
from datetime import datetime

bp = Blueprint('admin', __name__)


# Decorators personalizados para controle de acesso
def admin_required(f):  # É utilizado a funão 'f' para adicionar verificação de acesso
    @wraps(f)  # O @wraps é utilizado para preserverar o nome e a docstring da função original
    def decorated_function(*args, **kwargs):
        # Verificação do utilizador atual não está autenticado ou não tem atributo user_type, ou se o user_type
        # não é 'admin'
        if not current_user.is_authenticated or not hasattr(current_user,
                                                            'user_type') or current_user.user_type != 'admin':
            flash("Error to access this page 😥", "error")
            return redirect(request.args.get("next") or url_for("home"))  # Caso a verificação for verdadeira, irá
            # exibir uma mensagem de erro e redireciona o utilizador para a página inicial ou a página anterior.
        return f(*args, **kwargs)  # Caso contrário, a função original 'f' é executada com seus argumentos originais

    return decorated_function  # Retorna a função decorada.


@bp.route('/admin/admin_home', methods=['GET'])
@admin_required
def admin_home():
    # Obtém a data e hora atual
    current_datetime = datetime.now()

    # Contagem dos veículos que existem no sistema consoante o VehicleType
    car_count = Veiculos.query.filter_by(type=VehicleType.CARRO).count()
    motorcycle_count = Veiculos.query.filter_by(type=VehicleType.MOTA).count()

    # Calcula o total de veículos somando carros e motas
    total_vehicles = car_count + motorcycle_count

    # Contagem de carros por status

    # Conta carros que estão:
    # - Disponíveis (status=True)
    # - Não estão em manutenção (in_maintenance=False)
    # - Não têm data de disponibilidade futura OU a data já passou
    cars_available = Veiculos.query.filter(Veiculos.type == VehicleType.CARRO,  # Filtra apenas veículos pelo tipo
                                           Veiculos.status == True,
                                           Veiculos.in_maintenance == False,
                                           or_(
                                               Veiculos.available_from.is_(None),
                                               Veiculos.available_from <= current_datetime)).count()

    # Conta carros que estão:
    # - Reservados (is_reserved=True)
    # - Com data de disponibilidade futura (Veiculos.available_from > current_datetime)
    cars_reserved = Veiculos.query.filter(Veiculos.type == VehicleType.CARRO,
                                          Veiculos.is_reserved == True,
                                          Veiculos.available_from > current_datetime).count()

    # Conta carros em manutenção que:
    # - Têm data de início de manutenção definida
    # - Têm data de fim de manutenção definida
    # - A manutenção já começou (data atual >= data início)
    # - A manutenção ainda não terminou (data atual <= data fim)
    cars_unavailable = Veiculos.query.filter(Veiculos.type == VehicleType.CARRO,
                                             Veiculos.maintenance_start.isnot(None),  # Tem data de início de
                                             # manutenção definida
                                             Veiculos.maintenance_end.isnot(None),  # Tem data de fim de manutenção
                                             # definida
                                             Veiculos.maintenance_start <= current_datetime,  # A data de início já
                                             # passou ou é agora
                                             Veiculos.maintenance_end >= current_datetime).count()  # A data de fim
    # ainda não chegou

    # Contagem de motos disponíveis e indisponíveis

    # Conta motos que estão:
    # - Disponíveis (status=True)
    # - Não estão em manutenção (in_maintenance=False)
    # - Não têm data de disponibilidade futura OU a data já passou
    motorcycle_available = Veiculos.query.filter(Veiculos.type == VehicleType.MOTA,
                                                 Veiculos.status == True,
                                                 Veiculos.in_maintenance == False,
                                                 or_(
                                                     Veiculos.available_from.is_(None),
                                                     Veiculos.available_from <= current_datetime)).count()

    # Conta motos que estão:
    # - Reservados (is_reserved=True)
    # - Com data de disponibilidade futura (Veiculos.available_from > current_datetime)
    motorcycle_reserved = Veiculos.query.filter(Veiculos.type == VehicleType.MOTA,
                                                Veiculos.is_reserved == True,
                                                Veiculos.available_from > current_datetime).count()

    # Conta motos em manutenção que:
    # - Têm data de início de manutenção definida
    # - Têm data de fim de manutenção definida
    # - A manutenção já começou (data atual >= data início)
    # - A manutenção ainda não terminou (data atual <= data fim)
    motorcycle_unavailable = Veiculos.query.filter(Veiculos.type == VehicleType.MOTA,
                                                   Veiculos.maintenance_start.isnot(None),
                                                   Veiculos.maintenance_end.isnot(None),
                                                   Veiculos.maintenance_start <= current_datetime,
                                                   Veiculos.maintenance_end >= current_datetime).count()

    # Contagem dos clientes
    total_clients = Clientes.query.count()

    # Renderiza o template HTML passando todas as variáveis calculadas
    return render_template('admin/admin_home.html', VehicleType=VehicleType, car_count=car_count,
                           motorcycle_count=motorcycle_count, total_clients=total_clients,
                           total_vehicles=total_vehicles, cars_available=cars_available, cars_reserved=cars_reserved,
                           cars_unavailable=cars_unavailable, motorcycle_available=motorcycle_available,
                           motorcycle_reserved=motorcycle_reserved, motorcycle_unavailable=motorcycle_unavailable)


# ------------------------------- Admin_Pag Clients --------------------------------------
# Pesquisar clientes e obter todos os clientes
@bp.route('/admin/clients', methods=['GET'])
@admin_required
def clients():
    # Obtém os parâmetros de busca, se não existirem, retorna string vazia
    nome = request.args.get('nome', '')
    apelido = request.args.get('apelido', '')
    data_nascimento = request.args.get('data_nascimento', '')
    nif = request.args.get('nif', '')

    # Inicia a query base para buscar clientes
    query = Clientes.query

    # Se houver nome na busca, filtra clientes que contenham esse nome
    if nome:
        query = query.filter(Clientes.nome.ilike(f'%{nome}%'))
    # Se houver apelido, filtra clientes que contenham esse apelido
    if apelido:
        query = query.filter(Clientes.apelido.ilike(f'%{apelido}%'))
    # Se houver data de nascimento, filtra clientes com essa data exata
    if data_nascimento:
        query = query.filter(Clientes.data_nascimento == datetime.strptime(data_nascimento, '%Y-%m-%d').date())
    # Se houver NIF, filtra clientes que contenham esse NIF
    if nif:
        query = query.filter(Clientes.nif.ilike(f'%{nif}%'))

    # Executa a query e obtém todos os resultados
    clientes = query.all()

    # Verifica se algum filtro foi aplicado (retorna True se qualquer filtro foi usado), por esse motivo que
    # utilizado o bool para que converte um valor para booleano (True ou False)
    filtros_aplicados = bool(nome or apelido or data_nascimento or nif)

    # Caso não for encontrado clientes e há filtros, mostra mensagem de não encontrado
    if not clientes and filtros_aplicados:
        flash('Client not found!', 'warning')
    # Se não encontrou clientes na base de dados e não há filtros, mostra mensagem de sem dados
    elif not clientes:
        flash('No data to show!', 'warning')

    # Renderiza o template com os resultados e parâmetros de busca
    return render_template('admin/clients.html', clientes=clientes,
                           nome=nome, apelido=apelido,
                           data_nascimento=data_nascimento, nif=nif,
                           filtros_aplicados=filtros_aplicados)


# Rota para limpar os filtros de pesquisa e voltar à listagem inicial
@bp.route('/clients/clear', methods=['GET'])
@admin_required
def clear_search():
    return redirect(url_for('admin.clients'))


# Rota para editar dados de um cliente específico, por isso que utilizza o /<int:id>
@bp.route('/admin/edit_clients/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_clients(id):  # A função edit_clients(id) utiliza o id como parâmetro para identificar qual cliente
    # deve ser editado

    cliente = Clientes.query.get_or_404(id)  # A linha [get_or_404] obtem o registro com o ID especifico,
    # ou, caso naõ encontrar o registro automaticamente retorna o erro 404(Not Found)

    if request.method == 'POST':
        # Atualiza os dados do cliente com os valores do formulário
        cliente.nome = request.form['nome']
        cliente.apelido = request.form['apelido']
        cliente.email = request.form['email']
        cliente.telefone = request.form['telefone']
        cliente.data_nascimento = datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date()
        cliente.morada = request.form['morada']

        try:
            # Tenta salvar as alterações no banco de dados
            db.session.commit()
            flash('Cliente atualizado com sucesso', 'success')
            return redirect(url_for('admin.clients'))
        except Exception as e:
            # Se houver erro, desfaz as alterações e mostra mensagem de erro
            db.session.rollback()
            flash(f'Erro ao atualizar cliente: {str(e)}', 'error')

    # Se for GET, renderiza o formulário de edição
    return render_template('/admin/edit_clients.html', cliente=cliente)


# Rota para excluir um cliente específico, por isso que utilizza o /<int:id>
@bp.route('/delete_client/<int:id>', methods=['POST'])
@admin_required
def delete_client(id):
    # Busca o cliente pelo ID ou retorna 404 se não encontrar
    cliente = Clientes.query.get_or_404(id)

    db.session.delete(cliente)  # Remove o cliente do banco de dados
    db.session.commit()  # Salva a alteração
    flash(f"O cliente {cliente.nome} foi apagado dos registros!", "success")
    return redirect(url_for('admin.clients'))  # Redireciona para a lista de clientes


# Rota para pesquisa de veículos no painel admin que aceita o método GET
@bp.route('/admin/search_vehicles', methods=['GET'])
@admin_required
def search_vehicles():
    # Obtém os parâmetros, se não existirem retorna string vazia
    tipo = request.args.get('type', '')
    marca = request.args.get('brand', '')
    modelo = request.args.get('model', '')
    ano = request.args.get('year', '')
    transmissao = request.args.get('transmission', '')
    assentos = request.args.get('seats', '')
    bagagem = request.args.get('bags', '')
    preco_dia = request.args.get('price_per_day', '')
    categoria_nome = request.args.get('categoria', '')

    # Inicia a query base para veículos
    query_vehicle = Veiculos.query

    if tipo:  # Se foi fornecido um tipo de veículo
        try:
            vehicle_type = VehicleType[tipo]  # Tenta converter a string 'tipo' para um valor do enum VehicleType
            query_vehicle = query_vehicle.filter(Veiculos.type == vehicle_type)  # Filtra a query pelo tipo
        except:
            # Se tipo for inválido, mostra mensagem de erro
            flash(f'Invalid vehicle type: {tipo}', 'error')

    # Filtra por marca se fornecida, usando LIKE case-insensitive, pois, busca textos sem diferenciar maiúsculas de
    # minúsculas no SQL.
    if marca:
        query_vehicle = query_vehicle.filter(Veiculos.brand.ilike(f'%{marca}%'))
    # Filtra por modelo se fornecido, usando LIKE case-insensitive
    if modelo:
        query_vehicle = query_vehicle.filter(Veiculos.model.ilike(f'%{modelo}%'))
    # Filtra por ano se fornecido, convertendo-o para inteiro
    if ano:
        query_vehicle = query_vehicle.filter(Veiculos.year == int(ano))
    # Filtra por transmissão se fornecido, usando LIKE case-insensitive
    if transmissao:
        query_vehicle = query_vehicle.filter(Veiculos.transmission.ilike(f'%{transmissao}%'))
    # Filtra por número de assentos se fornecido
    if assentos:
        query_vehicle = query_vehicle.filter(Veiculos.seats == int(assentos))
    # Filtra por capacidade de bagagem se fornecido
    if bagagem:
        query_vehicle = query_vehicle.filter(Veiculos.bags == int(bagagem))
    # Filtra por preço/dia se fornecido
    if preco_dia:
        query_vehicle = query_vehicle.filter(Veiculos.price_per_day == float(preco_dia))
    # Filtra por categoria se fornecido, fazendo join com tabela de categorias
    if categoria_nome:  # Usa a função join() para conectar duas tabelas em uma consulta db, para este caso conecta
        # a tabela Veiculos com a tabela Categoria
        query_vehicle = query_vehicle.join(Veiculos.categoria).filter(Categoria.nome == categoria_nome)

    # Executa a query e obtém todos os resultados
    veiculos = query_vehicle.all()

    # Obtém lista de todas as categorias para o formulário
    categorias = Categoria.query.all()

    # Verifica se algum filtro foi aplicado
    filtros_veiculos = bool(
        tipo or marca or modelo or ano or transmissao or assentos or bagagem or preco_dia or categoria_nome)

    # Se não encontrou veículos e há filtros, mostra aviso
    if not veiculos and filtros_veiculos:
        flash('Vehicle not found', 'warning')
    # Se não há veículos cadastrados, mostra aviso
    elif not veiculos:
        flash('No data to show!', 'warning')

    # Renderiza template com todos os dados necessários
    return render_template('admin/search_vehicles.html', veiculos=veiculos,
                           tipo=tipo, marca=marca,
                           modelo=modelo, ano=ano, transmissao=transmissao, assentos=assentos, bagagem=bagagem,
                           preco_dia=preco_dia, categorias=categorias,
                           filtros_veiculos=filtros_veiculos, VehicleType=VehicleType)


# Rota para limpar os filtros de pesquisa
@bp.route('/search_vehicles/clear', methods=['GET'])
@admin_required
def clear_vehicle():
    # Redireciona para a pesquisa sem filtros
    return redirect(url_for('admin.search_vehicles'))


# Função que valida os dados do formulário de veículo
def validate_vehicle_data(form_data):
    # Lista para armazenar mensagens de erro
    errors = []

    # Valida se o ano é um número válido e está dentro de um intervalo aceitável
    try:
        # Tenta converter o ano recebido do formulário para número inteiro
        year = int(form_data['year'])

        # Verifica se o ano está dentro de um intervalo lógico:
        # - Não pode ser menor que 1900 (carros muito antigos, valor não aceitável)
        # - Não pode ser maior que o ano atual
        if year < 1900 or year > datetime.now().year:
            errors.append('Ano inválido!')
    except ValueError:
        # Se não conseguir converter para número (ex: se usuário digitou "abc")
        # Adiciona mensagem de erro
        errors.append('Ano deve ser um número válido!')

    # Validar preço
    try:
        # Tenta converter o preço recebido do formulário para número decimal
        price = float(form_data['price_per_day'])

        # Verifica se o preço é positivo
        # Um preço menor ou igual a zero não faz sentido
        if price <= 0:
            errors.append('Preço por dia deve ser maior que zero!')

    except ValueError:
        # Se não conseguir converter para número (ex: se usuário digitou "abc")
        # Adiciona mensagem de erro
        errors.append('Preço deve ser um número válido!')

    # Validar datas de manutenção
    if form_data['maintenance_start'] and form_data['maintenance_end']:
        try:
            # Converte strings de data e hora para objetos datetime
            maintenance_start = datetime.strptime(
                f"{form_data['maintenance_start']} {form_data['maintenance_start_time']}",
                '%Y-%m-%d %H:%M'
            )
            maintenance_end = datetime.strptime(
                f"{form_data['maintenance_end']} {form_data['maintenance_end_time']}",
                '%Y-%m-%d %H:%M'
            )

            # Verifica se a data final é posterior à inicial
            if maintenance_start >= maintenance_end:
                errors.append('A data de fim da manutenção deve ser posterior à data de início!')

        except ValueError:
            # O except ValueError captura erros que ocorre quando (O formato da data/hora não está correto e
            # a data/hora fornecida é inválida)
            errors.append('Formato de data/hora inválido!')

    # Retorna lista de erros encontrados
    return errors


# Adicionar veiculos
@bp.route('/admin/add_vehicles', methods=['GET', 'POST'])
@admin_required
def add_vehicles():
    vehicle_types = list(VehicleType)  # variável vehicle_types armazena a lista de todos os tipos de veículos
    # disponíveis
    veiculos = Veiculos.query.all()  # variável veiculos armazena todos os registros da tabela Veiculos do banco de
    # dados

    selected_type = request.form.get('type',
                                     vehicle_types[0].name)  # variável selected_type obtém o tipo de veículo
    # selecionado no formulário, ou o primeiro tipo de veículo caso nenhum for selecionado
    categorias = Categoria.query.filter_by(tipo_veiculo=VehicleType[selected_type]).all()  # variável categorias
    # armazena todas as categorias filtradas pelo tipo de veículo selecionado

    vehicle = None

    if request.method == 'POST':
        # Verifica se o formulário contém o campo add_vehicle, indicando que o usuário deseja adicionar um novo
        # veículo, e o button com name="add_vehicle" faz ponte entre eles
        if 'add_vehicle' in request.form:
            try:

                # Validar dados primeiro
                validation_errors = validate_vehicle_data(request.form)
                if validation_errors:
                    for error in validation_errors:
                        flash(error, 'error')
                    return redirect(url_for('add_vehicles'))

                # O valor do campo categoria_id é obtido do formulário enviado pelo usuário que por sua vez vai
                # busca-lo a categoria específica no banco de dados
                categoria = Categoria.query.get(request.form['categoria_id'])
                # new_vehicle cria uma nova instância de Veículos com os dados do formulário
                new_vehicle = Veiculos(
                    type=VehicleType[request.form['type']],
                    brand=request.form['brand'],
                    model=request.form['model'],
                    seats=request.form['seats'],
                    bags=request.form['bags'],
                    transmission=request.form['transmission'],
                    fuel_consumption=float(request.form['fuel_consumption']),
                    year=int(request.form['year']),
                    price_per_day=float(request.form['price_per_day']),
                    categoria=categoria,
                    status=request.form.get('status') == 'active',
                    maintenance_start=datetime.strptime(
                        f"{request.form['maintenance_start']} {request.form['maintenance_start_time']}",
                        '%Y-%m-%d %H:%M') if request.form['maintenance_start'] else None,
                    # Data e hora de início da manutenção
                    maintenance_end=datetime.strptime(
                        f"{request.form['maintenance_end']} {request.form['maintenance_end_time']}",
                        '%Y-%m-%d %H:%M') if request.form['maintenance_end'] else None
                    # Data e hora de fim da manutenção
                )

                # Cria uma lista vazia para armazenar os caminhos das imagens
                image_paths = []

                # Verifica se existe algum arquivo de imagem no request
                if 'image' in request.files:
                    files = request.files.getlist('image')  # Obtém todos os arquivos enviados com o nome 'image'

                    # Itera sobre cada arquivo enviado
                    for file in files:
                        if file and allowed_file(file.filename):  # Verifica se o arquivo existe e se tem uma extensão
                            # permitida
                            filename = secure_filename(file.filename)   # Valida o nome do ficheiro para evitar
                            # problemas de segurança
                            upload_folder = current_app.config['UPLOAD_FOLDER']  # Obtém o caminho da pasta de upload
                            # configurada na aplicação

                            # Verifica se a pasta de upload existe, se não, cria
                            if not os.path.exists(upload_folder):
                                os.makedirs(upload_folder)
                            file_path = os.path.join(upload_folder, filename)   # Cria o caminho completo onde o
                            # arquivo será salvo
                            file.save(file_path)   # Salva o arquivo no caminho especificado
                            if os.path.exists(file_path):
                                image_paths.append(f'uploads/{filename}')   # Adiciona o caminho relativo da imagem à
                                # list

                # Associa as imagens ao novo veículo usando o método set_imagens
                new_vehicle.set_imagens(image_paths)

                db.session.add(new_vehicle)  # adiciona um novo veículo ao banco de dados
                db.session.commit()  # Esta linha confirma as alterações feitas no banco de dados
                flash('Veículo adicionado com sucesso!', 'success')

            except Exception as e:
                db.session.rollback()  # Em caso de erro para garantir que nenhuma mudança parcial seja feita no banco
                # de dados
                flash(f'Erro ao adicionar veículo: {str(e)}', 'error')
            return redirect(url_for('admin.add_vehicles'))

        elif 'update' in request.form:
            # Quando o tipo de veículo é alterado, atualiza-se a página com as novas categorias
            return render_template('add_vehicles.html', categorias=categorias, vehicle_types=vehicle_types,
                                   veiculos=veiculos, selected_type=selected_type)

    # Renderiza a página add_vehicles.html com as categorias, tipos de veículos, veículos e tipo selecionado
    return render_template('/admin/add_vehicles.html', categorias=categorias, vehicle_types=vehicle_types,
                           veiculos=veiculos,
                           vehicle=vehicle, selected_type=selected_type)


# Tipo de Eidição
@bp.route('/admin/edit_type/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_type(id):
    # Buscar o veículo pelo ID
    vehicle = Veiculos.query.get_or_404(id)

    return render_template('/admin/edit_type.html', vehicle=vehicle)


# Editar veiculos
@bp.route('/admin/edit_vehicle/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_vehicle(
        id):  # A função edit_vehicle(id) utiliza o id como parâmetro para identificar qual veículo deve ser
    # editado
    veiculo = Veiculos.query.get_or_404(id)  # A linha [get_or_404] obtem o registro com o ID especifico, ou,
    # caso naõ encontrar o registro automaticamente retorna o erro 404(Not Found)
    vehicle_types = list(VehicleType)  # Esta linha cria uma lista de todos os tipos de veículos disponíveis
    categorias = Categoria.query.filter_by(tipo_veiculo=veiculo.type).all()  # Esta linha filtra e obtém todas as
    # categorias que correspondem ao tipo de veículo específico que está sendo editado.

    if request.method == 'POST':
        try:

            # Atualiza os dados do veículo
            veiculo.type = VehicleType[request.form['type']]
            veiculo.brand = request.form['brand'].upper()
            veiculo.model = request.form['model'].title()
            veiculo.seats = int(request.form['seats'])
            veiculo.bags = int(request.form['bags'])
            veiculo.transmission = request.form['transmission'].title()
            veiculo.fuel_consumption = float(request.form['fuel_consumption'])
            veiculo.year = int(request.form['year'])
            veiculo.price_per_day = float(request.form['price_per_day'])
            veiculo.categoria_id = int(request.form['categoria_id'])

            # Commit das alterações no banco de dados
            db.session.commit()
            flash('Veículo atualizado com sucesso!', 'success')
            return redirect(url_for('admin.edit_type', id=veiculo.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar veículo: {str(e)}', 'error')

    return render_template('/admin/edit_vehicle.html', veiculo=veiculo, vehicle_types=vehicle_types,
                           categorias=categorias)


# Status e manutenção dos veículos
@bp.route('/admin/toggle_vehicle_status/<int:id>', methods=['GET', 'POST'])
@admin_required
def toggle_vehicle_status(id):
    """
    Manipula a alteração de status de um veículo (Ativo, Em Manutenção, ou Reservado).

    Args:
        id (int): ID do veículo a ser modificado

    Returns:
        render_template ou redirect: Renderiza a página de alteração de status ou
        redireciona para a página de edição do veículo
    """
    vehicle = Veiculos.query.get_or_404(id)

    # Armazenar na sessão se o status foi alterado
    if 'status_changed' not in session:
        session['status_changed'] = False

    if request.method == 'POST':
        if 'alterar_status' in request.form:
            status_type = request.form.get('status')

            # Define o status baseado na seleção
            if status_type == 'active':
                actual_status = True
                is_reserved = False
                is_maintenance = False
            elif status_type == 'maintenance':
                actual_status = False
                is_reserved = False
                is_maintenance = True
            elif status_type == 'reserved':
                actual_status = False
                is_reserved = True
                is_maintenance = False

            session['temp_status'] = actual_status
            session['temp_is_reserved'] = is_reserved
            session['temp_is_maintenance'] = is_maintenance
            session['status_changed'] = True

            # Se o status for ativo, atualiza imediatamente
            if status_type == 'active':

                # Se mudar para ativo, cancela qualquer reserva existente
                if vehicle.is_reserved:
                    existing_reservation = Reservation.query.filter_by(veiculo_id=vehicle.id, status='Pendente').first()

                    if existing_reservation:
                        db.session.delete(existing_reservation)

                vehicle.status = actual_status
                vehicle.in_maintenance = False
                vehicle.is_reserved = False
                vehicle.maintenance_start = None
                vehicle.maintenance_end = None
                vehicle.available_from = None
                db.session.commit()

                # Limpa os dados temporários da sessão
                _clear_session_data()

                flash('Status do veículo atualizado para "Ativo" com sucesso!', 'success')
                return redirect(url_for('admin.edit_type', id=id))

            # Mostra mensagem apropriada baseada no status selecionado
            status_message = "Em Manutenção" if is_maintenance else "Reservado"
            flash(
                f'Status atualizado para "{status_message}"! Por favor preenche os dados necessários para finalizar o processo.',
                'success')
            return redirect(url_for('admin.toggle_vehicle_status', id=id))

        # Botão "Salvar Alterações" foi clicado
        elif 'salvar_alteracoes' in request.form and session.get('status_changed'):
            try:
                status = session.get('temp_status')
                is_reserved = session.get('temp_is_reserved')
                is_maintenance = session.get('temp_is_maintenance')

                vehicle.status = status
                vehicle.is_reserved = is_reserved

                if not status:  # Se em manutenção ou reservado
                    start_date = request.form.get('maintenance_start')
                    start_time = request.form.get('maintenance_start_time', '00:00')
                    end_date = request.form.get('maintenance_end')
                    end_time = request.form.get('maintenance_end_time', '23:59')

                    if not all([start_date, start_time, end_date, end_time]):
                        field_type = "manutenção" if is_maintenance else "reserva"
                        flash(f'Todos os campos de data e hora da {field_type} são obrigatórios.', 'error')
                        return redirect(url_for('admin.toggle_vehicle_status', id=id))

                    start_datetime = datetime.strptime(f"{start_date} {start_time}", '%Y-%m-%d %H:%M')
                    end_datetime = datetime.strptime(f"{end_date} {end_time}", '%Y-%m-%d %H:%M')

                    if start_datetime > end_datetime:
                        flash('A data/hora de início não pode ser posterior à data/hora de fim.', 'error')
                        return redirect(url_for('admin.toggle_vehicle_status', id=id))

                    if is_maintenance:
                        vehicle.in_maintenance = True
                        vehicle.is_reserved = False
                        vehicle.maintenance_start = start_datetime
                        vehicle.maintenance_end = end_datetime
                        vehicle.available_from = end_datetime
                    else:  # is_reserved
                        vehicle.in_maintenance = False
                        vehicle.is_reserved = True
                        vehicle.maintenance_start = None
                        vehicle.maintenance_end = None
                        vehicle.available_from = end_datetime

                        # Criar reservas através do admin
                        duration = (end_datetime - start_datetime).total_seconds() / 3600
                        total_price = (duration / 24) * vehicle.price_per_day

                        new_reservation = Reservation(
                            customer_id=current_user.id,  # ID do Admin
                            veiculo_id=vehicle.id,
                            start_date=start_datetime.date(),
                            start_time=start_datetime.time(),
                            end_date=end_datetime.date(),
                            end_time=end_datetime.time(),
                            duration=duration,
                            price=total_price,
                            payment_method='Admin Reservation',
                            status='Pendente'
                        )
                        db.session.add(new_reservation)

                else:  # Se ativo
                    # Remoção da reserva existente
                    existing_reservation = Reservation.query.filter_by(veiculo_id=vehicle.id, status='Pendente').first()

                    if existing_reservation:
                        db.session.delete(existing_reservation)

                    vehicle.in_maintenance = False
                    vehicle.is_reserved = False
                    vehicle.maintenance_start = None
                    vehicle.maintenance_end = None
                    vehicle.available_from = None

                db.session.commit()

                # Limpa os dados temporários da sessão
                _clear_session_data()

                flash('Status do veículo atualizado com sucesso!', 'success')
                return redirect(url_for('admin.edit_type', id=id))

            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao atualizar status: {str(e)}', 'error')
                return redirect(url_for('admin.toggle_vehicle_status', id=id))

        # Botão "Reverter Status" foi acionado
        elif 'reverter_status' in request.form and session.get('status_changed'):
            try:
                # Reverte o veículo para o estado ativo
                vehicle.status = True
                vehicle.in_maintenance = False
                vehicle.is_reserved = False
                vehicle.maintenance_start = None
                vehicle.maintenance_end = None
                vehicle.available_from = None

                # Remoção da reserva ao reverter status
                existing_reservation = Reservation.query.filter_by(veiculo_id=vehicle.id, status='Pendente').first()

                if existing_reservation:
                    db.session.delete(existing_reservation)

                db.session.commit()

                _clear_session_data()
                flash('Status do veículo revertido para "Ativo"!', 'warning')
                return redirect(url_for('admin.edit_type', id=id))

            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao reverter status: {str(e)}', 'error')
                return redirect(url_for('admin.toggle_vehicle_status', id=id))

        # Botão "Cancelar" foi acionado
        elif 'cancelar' in request.form:
            _clear_session_data()
            return redirect(url_for('admin.toggle_vehicle_status', id=id))

    return render_template('/admin/toggle_status.html',
                           vehicle=vehicle,
                           status_changed=session.get('status_changed', False),
                           temp_status=session.get('temp_status', vehicle.status),
                           temp_is_reserved=session.get('temp_is_reserved', False),
                           temp_is_maintenance=session.get('temp_is_maintenance', False))


def _clear_session_data():
    """
    Função auxiliar para limpar os dados temporários da sessão.
    Remove todas as variáveis temporárias relacionadas ao status do veículo.
    """
    session.pop('status_changed', None)
    session.pop('temp_status', None)
    session.pop('temp_is_reserved', None)
    session.pop('temp_is_maintenance', None)


# Editar imagem dos veículos
@bp.route('/admin/replace_img/<int:id>', methods=['GET', 'POST'])
@admin_required
def replace_img(id):
    veiculo = Veiculos.query.get_or_404(id)  # Obtém o veículo pelo ID ou retorna erro 404 se não existir

    # Rota para apagar imagens dos veículos, se necessário
    if request.args.get('delete_image'):
        return delete_vehicle_image(id, request.args.get('delete_image'))

    if request.method == 'POST':
        try:
            image_paths = []   # Inicia uma lista vazia para guardar os caminhos das novas imagens

            # Verifica se foram enviadas imagens no formulário
            if 'image' in request.files:
                files = request.files.getlist('image')   # Obtém todas as imagens enviadas

                # Para cada ficheiro enviado
                for file in files:
                    if file and allowed_file(file.filename):  # Verifica se o ficheiro existe e tem uma extensão
                        # permitida
                        filename = secure_filename(file.filename)  # Limpa o nome do ficheiro para garantir segurança
                        upload_folder = current_app.config['UPLOAD_FOLDER']  # Obtém o caminho da pasta onde as
                        # imagens serão guardadas

                        # Cria a pasta de upload se não existir
                        if not os.path.exists(upload_folder):
                            os.makedirs(upload_folder)

                        # Cria o caminho completo do ficheiro
                        file_path = os.path.join(upload_folder, filename)
                        file.save(file_path)  # Guarda o ficheiro no sistema

                        # Verifica se o ficheiro foi guardado com sucesso
                        if os.path.exists(file_path):
                            image_paths.append(f'uploads/{filename}')  # Adiciona o caminho relativo à lista

                # Atualiza as imagens do veículo no banco de dados
                veiculo.set_imagens(image_paths)

                # Commit das alterações no banco de dados
                db.session.commit()
                flash('Veículo atualizado com sucesso!', 'success')
                return redirect(url_for('admin.replace_img', id=veiculo.id))  # Redireciona de volta para a página de
                # substituição de imagens

        # Se ocorrer algum erro
        except Exception as e:
            db.session.rollback()  # Desfaz todas as alterações no banco de dados
            flash(f'Erro ao atualizar veículo: {str(e)}', 'error')

    # Obtém a lista de imagens atual do veículo
    # Se existirem imagens, divide a string pelos separadores (,)
    # Se não existirem imagens, retorna uma lista vazia
    imagens_veiculos = veiculo.imagens.split(',') if veiculo.imagens else []

    # Renderiza a página com o veículo e suas imagens atuais
    return render_template('/admin/replace_img.html', veiculo=veiculo, imagens_veiculos=imagens_veiculos)


# Função de apagar as imagens
def delete_vehicle_image(vehicle_id, filename):
    vehicle = Veiculos.query.get_or_404(vehicle_id)

    if not vehicle.imagens:
        flash('Nenhuma imagem para apagar!', 'error')
        return redirect(url_for('admin.replace_img', id=vehicle_id))

    # Converter string de imagens em lista
    imagens = vehicle.imagens.split(',')

    if filename in imagens:
        # Remover arquivo físico
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)

            # Remover referência do banco de dados
            imagens.remove(filename)
            vehicle.imagens = ','.join(imagens) if imagens else None
            db.session.commit()
            flash('Imagem removida com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao remover imagem: {str(e)}', 'error')
    else:
        flash('Imagem não encontrada.', 'error')

    return redirect(url_for('admin.replace_img', id=vehicle_id))


# Apagar veiculos
@bp.route('/delete_vehicle/<int:id>', methods=['POST'])
@admin_required
def delete_vehicle(id):
    veiculo = Veiculos.query.get_or_404(id)  # A linha [get_or_404] obtem o registro com o ID especifico,
    # ou, caso naõ encontrar o registro automaticamente retorna o erro 404(Not Found)

    try:
        # Primeiro apaga todos as reservas relacionadas, caso contrário não deixa apagar o veículo
        reservations = Reservation.query.filter_by(veiculo_id=id).all()
        for reservation in reservations:
            db.session.delete(reservation)

        # Depois apaga o veículo
        db.session.delete(veiculo)
        db.session.commit()
        flash(f"Veículo {veiculo.brand} e suas reservas foram apagados com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao apagar veículo: {str(e)}", "error")

    return redirect(url_for('admin.search_vehicles'))
