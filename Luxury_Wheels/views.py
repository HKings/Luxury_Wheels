from flask import Blueprint, redirect, url_for, render_template, flash
from flask_login import login_required, current_user


bp = Blueprint('views', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login_redirect():
    return redirect(url_for('auth.login'))


@bp.route('/registro', methods=['GET', 'POST'])
def registro_redirect():
    return redirect(url_for('auth.registro'))


@bp.route('/login_admin')
def login_admin():
    return render_template('login_admin.html')


