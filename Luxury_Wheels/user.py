from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import Clientes, db, Admin, Veiculos, VehicleType, Categoria, Reservation
from functools import wraps  # Adicionado este import para os decorators personalizados
from datetime import datetime

bp = Blueprint('user', __name__)


# Função helper para inicializar o carrinho de um ou múltiplas reservas
def init_reservation_cart():
    if 'reservation_cart' not in session:
        session['reservation_cart'] = []


# Decorator
def client_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificação do utilizado  r atual não está autenticado ou não tem atributo user_type, ou se o user_type não é
        # 'client'
        if not current_user.is_authenticated or not hasattr(current_user,
                                                            'user_type') or current_user.user_type != 'client':
            return redirect(url_for('auth.login'))  # Se as condições acima forem verdadeiras, exibe uma mensagem de
            # erro e redireciona o usuário para a página de login dos clientes
        return f(*args, **kwargs)  # Caso contrário, a função original 'f' é executada com seus argumentos originais

    return decorated_function  # Retorna a função decorada.


@bp.route('/user/client_perfil', methods=['GET', 'POST'])
@client_required
def client_perfil():
    # Obtém os dados do cliente atual usando o ID do utilizador autenticado
    cliente = Clientes.query.get(current_user.id)

    # Se o método for POST (quando o formulário é submetido)
    if request.method == 'POST':
        # Atualiza os dados do cliente com os valores do formulário
        cliente.nome = request.form['nome']
        cliente.apelido = request.form['apelido']
        cliente.telefone = request.form['telefone']
        cliente.data_nascimento = datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date()  # Converte a
        # string da data para um objeto date do Python
        cliente.morada = request.form['morada']
        cliente.nif = request.form['nif']

        try:
            db.session.commit()  # Tenta guardar as alterações no banco de dados
            flash('O perfil foi atualizado com sucesso!', 'success')
            return redirect(url_for('user.client_perfil'))  # Redireciona de volta para a página do perfil

        # Se ocorrer algum erro durante a atualização
        except Exception as e:
            db.session.rollback()  # Desfaz todas as alterações no banco de dados
            flash(f'Erro ao atualizar: {str(e)}', 'error')

    # Se o método for GET, renderiza a página do perfil com os dados do cliente
    return render_template("user/client_perfil.html", cliente=cliente)


@bp.route('/user/reserve_vehicle/<int:id>', methods=['GET', 'POST'])
@client_required
def reserve_vehicle(id):
    vehicle = Veiculos.query.get_or_404(id)  # A linha busca um veículo pelo seu ID na base de dados. Caso o veículo
    # não for encontrado, um erro 404 é retornado.
    init_reservation_cart()  # inicialização do carrinho de reservas.
    cart = session.get('reservation_cart', [])  # Obtém o carrinho de reservas da sessão, ou cria um novo se não
    # existir.

    # Verifica se está em modo de edição tanto por args e, foi adicionado o estado is_editing na sessão para
    # persistir durante todo o processo para não cair no else do estdo do (is_duplicate)
    is_editing = request.args.get('edit') == 'true' or session.get('is_editing')  # Verifica se a requisição contém o
    # parâmetro 'edit' com valor 'true' ou se a sessão já tem um estado de edição.
    cart_index = None  # Variável que é usada para armazenar o índice do item no carrinho e o próprio item, também
    existing_item = None  # Variável que é usada para armazenar o índice do item no carrinho e o próprio item, também

    # Se o parâmetro 'edit' for 'true', define a sessão como sendo no modo de edição e modifica a sessão.
    if request.args.get('edit') == 'true':
        session['is_editing'] = True
        session.modified = True

    # Se estiver no modo de edição, busca o item no carrinho que corresponde ao ID do veículo.
    if is_editing:
        # Encontra o item no carrinho
        for idx, item in enumerate(cart):
            if item['vehicle_id'] == id:
                existing_item = item
                cart_index = idx
                break

        # Se encontrar o item e ainda não houver um índice de edição na sessão, salva o índice e o item original na
        # sessão e dá a sessão como modificada.
        if cart_index is not None and 'edit_item_index' not in session:
            session['edit_item_index'] = cart_index
            session['edit_item_original'] = existing_item
            session.modified = True

    # Se for um POST, processa o formulário, obtendo os dados (datas e horários de início e fim).
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time')
        end_date = request.form.get('end_date')
        end_time = request.form.get('end_time')

        try:
            # Converte as datas e horários em objetos datetime.
            start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

            # Verifica se a data de início é anterior à data de fim. Se não for, exibe uma mensagem de erro e
            # redireciona para a página de reserva do veículo.
            if start_datetime >= end_datetime:
                flash('A data de início deve ser anterior à data do fim.', 'error')
                return redirect(url_for('user.reserve_vehicle', id=id))

            # Define a taxa de IVA e o preço por dia do veículo. Calcula o total de horas da reserva
            IVA = 0.23
            price_per_day = vehicle.price_per_day  # Preço por dia
            total_hours = (end_datetime - start_datetime).total_seconds() / 3600

            # Calcula o preço total com e sem IVA
            if total_hours < 24:
                total_price_no_iva = vehicle.price_per_day  # Atribui o preço de 1 dia caso a reserva for inferior a 24h
                total_price = total_price_no_iva + (IVA * vehicle.price_per_day)
            else:
                price_per_hour = vehicle.price_per_day / 24
                total_price_no_iva = total_hours * price_per_hour
                total_price = total_price_no_iva + (IVA * vehicle.price_per_day)

            # Clálculo do tempo da reserva
            days = total_hours // 24  # Número inteiro de dias
            remaining_hours = total_hours % 24  # Horas restantes

            # IVA da reserva
            reserve_iva = total_price - total_price_no_iva

            # Criar o item de reserva
            reservation_item = {
                'vehicle_id': vehicle.id,
                'brand': vehicle.brand,
                'model': vehicle.model,
                'start_date': start_date,
                'start_time': start_time,
                'end_date': end_date,
                'end_time': end_time,
                'total_price': total_price,
                'days': days,
                'remaining_hours': remaining_hours,
                'reserve_iva': reserve_iva,
                'price_per_day': price_per_day,
                'imagens': vehicle.get_imagens() if hasattr(vehicle, 'get_imagens') else None  # Adiciona as imagens
                # ao item (Esta linha vai buscar as imagens de cada veículo individualmente). Utilizou-se o "
                # hasattr" de forma a evitar erros como AttributeError, pois, ela é uma função built-in do Python que
                # verifica se um objeto tem um determinado atributo ou método. E ela busca o 'get_imagens' que vem da
                # função def get_imagens(self) contida no models.py
            }

            # Verifica se está em modo de edição
            if session.get('is_editing') and 'edit_item_index' in session:  # Esta linha verifica se a sessão atual
                # está no modo de edição e se há um índice de item de edição na sessão
                cart_index = session.pop('edit_item_index')  # Se estiver no modo de edição, remove o índice do item
                # de edição da sessão e o armazena na variável cart_index
                cart[cart_index] = reservation_item  # Substitui o item no carrinho pelo novo item de reserva usando
                # o índice extraído
                session.pop('edit_item_original', None)  # Remove as variáveis relacionadas à edição da sessão para
                # limpar o estado de edição
                session.pop('is_editing', None)  # Remove as variáveis relacionadas à edição da sessão para limpar o
                # estado de edição e Limpa o estado de edição após concluir a atualização
                flash('Reserva atualizada com sucesso!', 'success')
            else:
                # Verifica duplicações apenas se NÃO estiver no modo de edição
                is_duplicate = False  # Inicializa a variável is_duplicate como False
                for item in cart:  # Percorre todos os itens no carrinho
                    if item['vehicle_id'] == id:  # Verifica se o ID do veículo do item atual é igual ao ID do
                        # veículo que está sendo adicionado
                        is_duplicate = True  # Se encontrar uma duplicação, marca a variável is_duplicate como True e
                        # interrompe a iteração
                        break

                if is_duplicate:
                    flash('Este veículo já está no seu carrinho. Por favor selecione um veículo diferente.',
                          'error')
                    return redirect(url_for('list_vehicle'))

                cart.append(reservation_item)  # Se não houver duplicação, adiciona o novo item de reserva ao carrinho
                flash('Veículo adicionado ao carrinho com sucesso!', 'success')

            session['reservation_cart'] = cart  # Armazena o carrinho de reservas atualizado (cart) na sessão do
            # usuário com a chave 'reservation_cart'
            session.modified = True  # Garante que as mudanças na sessão sejam salvas principalmente quando é
            # adicionado um veículo novo a lista de reserva com as suas especificações como a imagem e não só

            return redirect(url_for('user.confirm_reserve', id=id))

        except ValueError:
            flash('Formato de data ou hora inválido.', 'error')
            return redirect(url_for('user.reserve_vehicle', id=id))

    # Handler para "Cancelar" ou "Ver carrinho" durante o modo edição
    if is_editing and request.args.get('action') in ['cancel', 'view_cart']:
        # Se tiver um item original salvo na sessão e se a ação for cancelar
        if request.args.get('action') == 'cancel' and 'edit_item_original' in session:
            # Restaura o item original no carrinho
            cart = session.get('reservation_cart', [])
            original_item = session.get('edit_item_original')
            edit_index = session.get('edit_item_index')

            if edit_index is not None and edit_index < len(cart):
                cart[edit_index] = original_item
                session['reservation_cart'] = cart
                flash('Edição cancelada. A reserva foi mantida como estava anteriormente.', 'warning')

        # Limpa todas as variáveis de sessão relacionadas à edição
        session.pop('edit_item_index', None)
        session.pop('edit_item_original', None)
        session.pop('is_editing', None)
        session.modified = True

        if request.args.get('action') == 'cancel':
            return redirect(url_for('user.view_cart'))
        else:  # para o view_cart
            return redirect(url_for('user.view_cart'))

    # Para GET request
    if not vehicle.is_available():
        flash('Este veículo não está disponível para reserva.', 'error')
        return redirect(url_for('list_vehicle'))

    return render_template('user/reserve_vehicle.html', vehicle=vehicle,
                           edit_data=existing_item,
                           is_editing=is_editing)


@bp.route('/user/confirm_reserve/<int:id>', methods=['GET'])
@client_required
def confirm_reserve(id):
    # Inicializa o carrinho
    init_reservation_cart()
    cart = session.get('reservation_cart', [])
    vehicle = Veiculos.query.get_or_404(id)

    # Garantir que todos os itens do carrinho tenham o elemento remaining_hours
    for item in cart:
        if 'remaining_hours' not in item:
            item['remaining_hours'] = 0

    # Verificação para carrinho vazio
    if not cart and not (request.args.get('start_date') and request.args.get('end_date')):
        flash('Não existe nenhum veículo na reserva!', 'warning')
        return redirect(url_for('list_vehicle'))

    # lógica do carrinho
    if cart:
        total_reservation_price = sum(float(item['total_price']) for item in cart)
        total_vehicles = len(cart)
        return render_template('user/confirm_reserve.html',
                               cart=cart,
                               vehicle=vehicle,
                               total_price=total_reservation_price,
                               total_vehicles=total_vehicles)

    # Se não houver itens no carrinho, apanha os parâmetros da URL
    start_date = request.args.get('start_date')
    start_time = request.args.get('start_time')
    end_date = request.args.get('end_date')
    end_time = request.args.get('end_time')
    total_price = float(request.args.get('total_price', 0))

    # Calcular IVA e outros detalhes necessários
    IVA = 0.23
    total_price_no_iva = float(total_price) / (1 + IVA)
    reserve_iva = total_price - total_price_no_iva

    # Calcular dias e horas
    try:
        start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
        total_hours = (end_datetime - start_datetime).total_seconds() / 3600
        days = total_hours // 24  # Número inteiro de dias
        remaining_hours = total_hours % 24  # Horas restantes
    except (ValueError, TypeError):
        days = 0
        remaining_hours = 0

    # Criar um cart com um único item
    single_item = {
        'vehicle_id': vehicle.id,
        'brand': vehicle.brand,
        'model': vehicle.model,
        'start_date': start_date,
        'start_time': start_time,
        'end_date': end_date,
        'end_time': end_time,
        'total_price': total_price,
        'days': days,
        'remaining_hours': remaining_hours,
        'reserve_iva': reserve_iva,
        'price_per_day': vehicle.price_per_day,
        'imagens': vehicle.get_imagens() if hasattr(vehicle, 'get_imagens') else None
    }

    # Verificar se 'remaining_hours' foi definido
    if 'remaining_hours' not in single_item:
        single_item['remaining_hours'] = 0

    return render_template('user/confirm_reserve.html',
                           cart=[single_item],
                           vehicle=vehicle,
                           total_price=total_price,
                           total_vehicles=1)  # Para caso de item único


@bp.route('/user/remove_from_cart/<int:vehicle_id>', methods=['POST'])
@client_required
def remove_from_cart(vehicle_id):
    cart = session.get('reservation_cart', [])  # Caso "reservation_cart" não existir na sessão, retorna uma lista
    # vazia [] em vez de dar erro.

    # Encontrar o veículo removido
    removed_vehicle = next((item for item in cart if item['vehicle_id'] == vehicle_id), None)  # Esta linha utiliza o
    # next() com um gerador para encontrar o primeiro item que corresponde à condição, caso contrario o valor None
    # diz que nenhum item foi encontrado e vem como valor padrão

    # Atualizar o carrinho removendo o veículo
    cart = [item for item in cart if item['vehicle_id'] != vehicle_id]
    session['reservation_cart'] = cart  # A linha tem como função atualizar sempre o carrinho e salva na sessão,
    # isto porque o flask não detecta automaticamente mudanças em estreuturas de dados complexos

    # Verificação para carrinho vazio após remoção
    if not cart:
        flash('Não há nenhum veículo adicionado. Por favor adicione um veículo para continuar!', 'warning')
        return redirect(url_for('list_vehicle'))

    # Ao remover um veículo, irá aparecer uma mensagem com o veículo que foi removido
    if removed_vehicle:
        flash(f"O veículo {removed_vehicle['brand']} {removed_vehicle['model']} foi removido da reserva.", 'success')
    else:
        flash('Veículo removido da reserva.', 'success')

    return redirect(url_for('user.confirm_reserve', id=vehicle_id))


@bp.route('/user/view_cart', methods=['GET'])
@client_required
def view_cart():
    init_reservation_cart()
    cart = session.get('reservation_cart', [])

    if not cart:
        flash('Não existe nenhum veículo no carrinho!', 'warning')

    # Calcular o preço total e o Nº de veículos
    total_price = sum(float(item['total_price']) for item in cart)
    total_vehicles = len(cart)

    # Obter o primeiro veículo do carrinho para manter compatibilidade com o template
    first_vehicle = Veiculos.query.get(cart[0]['vehicle_id']) if cart else None
    vehicles = {item['vehicle_id']: Veiculos.query.get(item['vehicle_id']) for item in cart}

    # Calcular IVA e outros detalhes necessários
    IVA = 0.23
    total_price_no_iva = float(total_price) / (1 + IVA)
    reserve_iva = total_price - total_price_no_iva

    return render_template('user/confirm_reserve.html',
                           cart=cart,
                           total_price=total_price,
                           total_price_no_iva=total_price_no_iva,
                           reserve_iva=reserve_iva,
                           vehicle=first_vehicle,  # Adicionando o primeiro veículo
                           vehicles=vehicles,  # Adicionando todos os veículos
                           total_vehicles=total_vehicles,
                           start_date=cart[0]['start_date'] if cart else None,
                           start_time=cart[0]['start_time'] if cart else None,
                           end_date=cart[0]['end_date'] if cart else None,
                           end_time=cart[0]['end_time'] if cart else None)


@bp.route('/user/payment_method', methods=['GET'])
@client_required
def payment_method():
    cart = session.get('reservation_cart', [])

    # Verificação para carrinho vazio
    if not cart:
        flash('Não existe nenhum veículo no carrinho!', 'warning')
        return redirect(url_for('list_vehicle'))

    # Calcular totais
    total_price = sum(float(item['total_price']) for item in cart)
    total_vehicles = len(cart)

    # Calcular IVA e outros detalhes
    IVA = 0.23
    total_price_no_iva = float(total_price) / (1 + IVA)
    reserve_iva = total_price - total_price_no_iva

    return render_template('user/payment_method.html',
                           cart=cart,
                           total_price=total_price,
                           total_price_no_iva=total_price_no_iva,
                           reserve_iva=reserve_iva,
                           total_vehicles=total_vehicles)


@bp.route('/user/create_reservation', methods=['POST'])
@client_required
def create_reservation():
    payment_method = request.form.get('payment_method')
    cart = session.get('reservation_cart', [])

    try:
        if not cart:
            flash('Não existe veículos no carrinho.', 'error')
            return redirect(url_for('list_vehicle'))

        if cart:
            # processamento de múltiplas reservas
            for item in cart:
                start_datetime = datetime.strptime(f"{item['start_date']} {item['start_time']}", "%Y-%m-%d %H:%M")
                end_datetime = datetime.strptime(f"{item['end_date']} {item['end_time']}", "%Y-%m-%d %H:%M")

                # Calcular a duração em horas
                duration = (end_datetime - start_datetime).total_seconds() / 3600

                vehicle = Veiculos.query.get(item['vehicle_id'])

                vehicle.is_reserved = True  # Define o status do veículo como reservado no banco de dados e, marca-o
                # como reservado para garantir que apareça como "Reservado" na interface

                new_reservation = Reservation(
                    customer_id=current_user.id,
                    veiculo_id=vehicle.id,
                    start_date=start_datetime.date(),
                    start_time=start_datetime.time(),
                    end_date=end_datetime.date(),
                    end_time=end_datetime.time(),
                    duration=duration,
                    price=item['total_price'],
                    payment_method=payment_method,
                    status='Pendente'  # Fica 'Pendente' até confirmação de pagamento da parte do cliente
                )

                db.session.add(new_reservation)
                vehicle.update_availability_after_reservation(end_datetime)

        db.session.commit()
        session.pop('reservation_cart', None)  # limpeza do carrinho
        flash(f'Reserva(s) realizada(s) com sucesso!', 'success')
        return redirect(url_for('user.confirmation_page'))

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar reserva: {str(e)}', 'error')
        return redirect(url_for('user.payment_method'))


@bp.route('/user/confirmation_page')
@client_required
def confirmation_page():
    # Obter todas as reservas do cliente ordenadas por ID em ordem decrescente
    reservations = Reservation.query.filter_by(customer_id=current_user.id).order_by(Reservation.id.desc()).all()

    if not reservations:
        flash('Não foi encontrada nenhuma reserva!', 'error')
        return redirect(url_for('list_vehicle'))

    # Apanha as reservas mais recentes (do último conjunto)
    latest_reservations = []
    if reservations and reservations[0].created_at:  # Verifica se existe created_at
        latest_timestamp = reservations[0].created_at  # Assumindo que há um campo created_at
        for res in reservations:
            if res.created_at and abs((res.created_at - latest_timestamp).total_seconds()) < 1:  # Reservas feitas no mesmo segundo
                latest_reservations.append(res)
    else:
        # Se não houver timestamp, será utilizado apenas a primeira reserva
        latest_reservations = [reservations[0]]

    # Obter detalhes do cliente
    cliente = Clientes.query.get(current_user.id)

    # Obter detalhes dos veículos
    vehicles = {}
    for reservation in latest_reservations:
        vehicles[reservation.veiculo_id] = Veiculos.query.get(reservation.veiculo_id)

    # Calcular o preço total
    total_price = sum(item.price for item in latest_reservations)

    return render_template('user/confirmation_page.html',
                           reservations=latest_reservations,
                           cliente=cliente,
                           vehicles=vehicles,
                           total_price=total_price)
