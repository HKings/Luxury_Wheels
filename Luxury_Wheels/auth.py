from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import Clientes, db, Admin
from datetime import datetime

bp = Blueprint('auth', __name__)


# ------------------------------- register area --------------------------------------

@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    # Verificação da autenticação do utilizador
    if current_user.is_authenticated:
        if isinstance(current_user, Admin):  # Verifica se o utilizador atual está autenticado e, caso o utilizador
            # atual for o admin aparece uma mensagem de aviso e redireciona a pág. para admin_home
            flash("You are already logged in!", "warning")
            return redirect(url_for("admin.admin_home"))
        flash("You are already logged in!", "warning")  # Mas caso o o utilizador atual não for o admin, exibe uma
        # mensagem de aviso e redireciona para pág. anterior ou home
        return redirect(request.args.get("next") or url_for("home"))

    if request.method == "POST":
        # Coleta os dados do formulário de registro
        nome = request.form["nomeUtilizador"]
        email = request.form["emailUtilizador"]
        apelido = request.form["apelidoUtilizador"]
        telefone = request.form["telefoneUtilizador"]
        data_nascimento = datetime.strptime(request.form["data_nascimentoUtilizador"], '%Y-%m-%d').date()
        morada = request.form["moradaUtilizador"]
        nif = request.form["nifUtilizador"]
        password = request.form["passwordUtilizador"]
        password_conf = request.form["passwordUtilizadorConf"]

        existing_client = Clientes.query.filter_by(email=email).first()

        if existing_client: # Verifica se o email já está registrado no banco de dados. Se estiver, exibe uma
            # mensagem de erro e redireciona para a página de registro
            flash("Email already registered. Please use a different email.", "error")
            return redirect(url_for('auth.registro'))

        elif password != password_conf:  # Verifica se as senhas digitadas coincidem. Se não coincidirem, exibe uma
            # mensagem de erro e redireciona para a página de registro
            flash("The passwords do not match. Please try again!", "error")
            return redirect(url_for('auth.registro'))

        # Cria um novo cliente com os dados fornecidos, adiciona-o ao banco de dados
        new_client = Clientes(nome=nome, email=email, apelido=apelido, telefone=telefone,
                              data_nascimento=data_nascimento, morada=morada, nif=nif, password=password)
        db.session.add(new_client)  # adicionar ao banco de dados
        db.session.commit()  # Confirma todas as alterações que foram adicionadas à sessão do banco de dados
        flash("Registration Successful", "success")
        return redirect(url_for("auth.login"))
    return render_template("registro.html")


# ------------------------------- user area --------------------------------------

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if hasattr(current_user, 'user_type') and current_user.user_type == 'admin':  # Verifica se o utilizador
            # atual já está autenticado e, caso for um administrador, exibe uma mensagem de aviso e redireciona para
            # admin_home
            flash("Olny customers access!", "warning")
            return redirect(url_for("admin.admin_home"))
        flash("You are already logged in!", "warning")
        return redirect(url_for("list_vehicle"))

    if request.method == "POST":
        # Coleta os dados do formulário de login.
        email = request.form["emailUtilizador"]
        password = request.form["passwordCliente"]

        client = Clientes.query.filter_by(email=email).first()  # Busca o cliente no banco de dados pelo email

        #  Verifica se o cliente existe no banco de dados e se a senha introduzida está correta
        if client and check_password_hash(client.password, password):
            session.clear()  # Limpa a sessão anterior
            session.permanent = True  # Define a sessão perante o tempo estabelecido
            # no app.py (app.permanent_session_lifetime = timedelta(minutes=xx))
            login_user(client)  # Faz o login do client
            # Exibe uma mensagem de boas-vindas e redireciona para list_vehicle.html
            flash(f"Welcome {client.nome} {client.apelido}", "success")
            return redirect(url_for("list_vehicle"))

        # Caso o login falhar, exibe uma mensagem de erro e redireciona para auth.login
        flash("Invalid email or password", "error")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


# ------------------------------- admin area --------------------------------------

@bp.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    if current_user.is_authenticated:
        if hasattr(current_user, 'user_type') and current_user.user_type == 'client':  # Verifica se o utilizador
            # atual já está autenticado e, caso for um cliente, exibe uma mensagem de aviso e redireciona para home
            flash("You can not access this page!", "warning")
            return redirect(url_for("home"))
        flash("You are already logged in!", "warning")
        return redirect(url_for("admin.admin_home"))

    if request.method == "POST":
        # Coleta os dados do formulário de login_admin.
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:  # Caso os credenciais não estiverem corretos o admin é redirecionado para
            # login_admin
            flash("Username and password are required", "error")
            return redirect(url_for("auth.login_admin"))

        admin_user = Admin.query.filter_by(username=username).first()  # Busca o administrador no banco de dados pelo
        # nome de utilizador

        if admin_user and check_password_hash(admin_user.password, password):  # Verifica se o admin existe e se a
            # senha está correta
            session.clear()  # Limpa a sessão anterior
            session.permanent = True  # Define a sessão perante o tempo estabelecido
            # no app.py (app.permanent_session_lifetime = timedelta(minutes=xx))
            login_user(admin_user)  # Faz o login do admin
            flash("Welcome to Admin area!", "success")
            return redirect(url_for("admin.admin_home"))

        flash("Invalid admin credentials", "error")  # Caso o login falhar, exibe uma mensagem de erro e redireciona
        # para auth.login_admin
        return redirect(url_for("auth.login_admin"))

    return render_template("login_admin.html")


# Sistema Logout
@bp.route("/logout")
@login_required
def logout():
    is_admin = isinstance(current_user, Admin)  # Verifica se o utilizador atual é um administrador e armazena o
    # resultado em is_admin.
    logout_user()  # Faz o logout do utilizador
    session.clear()  # Limpa a sessão

    if is_admin:  # Caso o utilizador for admin, exibe uma mensagem de sucesso e redireciona para a página auth.login
        flash("Admin logout successful!", "success")
        return redirect(url_for("auth.login"))

    # Caso o utilizador não for admin, exibe uma mensagem de sucesso e redireciona para a página auth.login
    flash("Successfully logged out!", "success")
    return redirect(url_for("auth.login"))