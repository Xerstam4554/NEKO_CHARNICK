import os
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Character, CLASSES, ABILITY_NAMES, TRADITIONS, PROFICIENCY_NAMES
import io

app = Flask(__name__)

# PostgreSQL (Replit) или SQLite для локального запуска
_db_url = os.environ.get('DATABASE_URL', 'sqlite:///characters.db')
# SQLAlchemy требует postgresql://, а не postgres://
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024
app.secret_key = os.environ.get('SECRET_KEY', 'pf2-secret-key-2024')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Войдите, чтобы получить доступ.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.context_processor
def utility_processor():
    def get_attribute(obj, attr):
        return getattr(obj, attr, None)

    def fmt_mod(value):
        return f'+{value}' if value >= 0 else str(value)

    return dict(attribute=get_attribute, fmt_mod=fmt_mod,
                classes=CLASSES, ability_names=ABILITY_NAMES,
                traditions=TRADITIONS, proficiency_names=PROFICIENCY_NAMES)


# ── Регистрация / Вход / Выход ───────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    from loginform import RegisterForm
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f'Добро пожаловать, {user.username}!')
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    from loginform import LoginForm
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Неверный email или пароль.')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# ── Главная страница ─────────────────────────────────────────────────────────

@app.route('/')
def index():
    if current_user.is_authenticated:
        characters = Character.query.filter_by(user_id=current_user.id)\
                                    .order_by(Character.created_at.desc()).all()
    else:
        characters = []
    return render_template('index.html', characters=characters)


# ── Просмотр персонажа ───────────────────────────────────────────────────────

@app.route('/character/<int:id>')
@login_required
def view_character(id):
    character = Character.query.get_or_404(id)
    if character.user_id != current_user.id:
        flash('У вас нет доступа к этому персонажу.')
        return redirect(url_for('index'))
    return render_template('character.html', character=character)


# ── Создание ─────────────────────────────────────────────────────────────────

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_character():
    if request.method == 'POST':
        character = Character(user_id=current_user.id)
        _fill_character(character, request.form, request.files)
        db.session.add(character)
        db.session.commit()
        return redirect(url_for('view_character', id=character.id))
    return render_template('create_character.html', character=None)


# ── Редактирование ───────────────────────────────────────────────────────────

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_character(id):
    character = Character.query.get_or_404(id)
    if character.user_id != current_user.id:
        flash('У вас нет доступа к этому персонажу.')
        return redirect(url_for('index'))
    if request.method == 'POST':
        _fill_character(character, request.form, request.files)
        db.session.commit()
        return redirect(url_for('view_character', id=character.id))
    return render_template('create_character.html', character=character)


# ── Удаление ─────────────────────────────────────────────────────────────────

@app.route('/delete/<int:id>')
@login_required
def delete_character(id):
    character = Character.query.get_or_404(id)
    if character.user_id != current_user.id:
        flash('У вас нет доступа к этому персонажу.')
        return redirect(url_for('index'))
    if character.avatar:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], character.avatar))
        except OSError:
            pass
    db.session.delete(character)
    db.session.commit()
    return redirect(url_for('index'))


# ── Быстрое обновление ХП ────────────────────────────────────────────────────

@app.route('/hp/<int:id>', methods=['POST'])
@login_required
def update_hp(id):
    character = Character.query.get_or_404(id)
    if character.user_id != current_user.id:
        return jsonify({'error': 'forbidden'}), 403
    data = request.get_json()
    delta = int(data.get('delta', 0))
    character.current_hp = max(0, min(character.max_hp, character.current_hp + delta))
    db.session.commit()
    return jsonify({'current_hp': character.current_hp, 'max_hp': character.max_hp})


# ── JSON экспорт ─────────────────────────────────────────────────────────────

@app.route('/export/<int:id>')
@login_required
def export_character(id):
    character = Character.query.get_or_404(id)
    if character.user_id != current_user.id:
        flash('У вас нет доступа к этому персонажу.')
        return redirect(url_for('index'))
    data = character.to_dict()
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    buf = io.BytesIO(json_bytes)
    safe_name = character.name.replace(' ', '_')
    return send_file(buf, mimetype='application/json',
                     as_attachment=True,
                     download_name=f'{safe_name}.json')


# ── JSON импорт ──────────────────────────────────────────────────────────────

@app.route('/import', methods=['GET', 'POST'])
@login_required
def import_character():
    if request.method == 'POST':
        f = request.files.get('json_file')
        if not f or not f.filename.endswith('.json'):
            flash('Выберите файл .json')
            return redirect(url_for('import_character'))
        try:
            data = json.load(f)
            character = Character.from_dict(data)
            character.user_id = current_user.id
            db.session.add(character)
            db.session.commit()
            return redirect(url_for('view_character', id=character.id))
        except Exception as e:
            flash(f'Ошибка импорта: {e}')
            return redirect(url_for('import_character'))
    return render_template('import.html')


# ── Внутренний помощник ──────────────────────────────────────────────────────

def _fill_character(character, form, files):
    character.name = form['name']
    character.level = int(form.get('level', 1))
    character.experience = int(form.get('experience', 0))
    character.ancestry = form.get('ancestry', '')
    character.background = form.get('background', '')
    character.character_class = form.get('character_class', '')
    character.languages = form.get('languages', '')

    for attr in ('strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'):
        setattr(character, attr, int(form.get(attr, 0)))

    skills = ['acrobatics', 'arcana', 'athletics', 'crafting', 'deception',
              'diplomacy', 'intimidation', 'lore', 'medicine', 'nature', 'occultism',
              'performance', 'religion', 'society', 'stealth', 'survival', 'thievery']
    for skill in skills:
        setattr(character, skill, int(form.get(skill, 0)))

    character.lore_topic = form.get('lore_topic', '')

    character.fortitude_prof = int(form.get('fortitude_prof', 0))
    character.reflex_prof = int(form.get('reflex_prof', 0))
    character.will_prof = int(form.get('will_prof', 0))
    character.perception_prof = int(form.get('perception_prof', 0))

    character.max_hp = int(form.get('max_hp', 10))
    character.current_hp = int(form.get('current_hp', 10))
    character.armor_class = int(form.get('armor_class', 10))
    character.speed = int(form.get('speed', 25))

    character.unarmored_prof = int(form.get('unarmored_prof', 0))
    character.light_armor_prof = int(form.get('light_armor_prof', 0))
    character.medium_armor_prof = int(form.get('medium_armor_prof', 0))
    character.heavy_armor_prof = int(form.get('heavy_armor_prof', 0))

    character.unarmed_prof = int(form.get('unarmed_prof', 0))
    character.simple_weapon_prof = int(form.get('simple_weapon_prof', 0))
    character.martial_weapon_prof = int(form.get('martial_weapon_prof', 0))
    character.advanced_weapon_prof = int(form.get('advanced_weapon_prof', 0))

    character.class_dc_prof = int(form.get('class_dc_prof', 0))
    character.class_dc_ability = form.get('class_dc_ability', 'strength')

    character.feats_json = form.get('feats_json', '[]')
    character.class_abilities_json = form.get('class_abilities_json', '[]')
    character.spells_json = form.get('spells_json', '{}')
    character.inventory_json = form.get('inventory_json', '[]')

    avatar_file = files.get('avatar')
    if avatar_file and avatar_file.filename and allowed_file(avatar_file.filename):
        filename = secure_filename(f'char_{character.name}_{avatar_file.filename}')
        avatar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        character.avatar = filename


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
