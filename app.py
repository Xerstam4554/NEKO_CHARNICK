import os
import json
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, flash
from werkzeug.utils import secure_filename
from models import db, Character, CLASSES, ABILITY_NAMES, TRADITIONS, PROFICIENCY_NAMES
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///characters.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024  # 4 MB
app.secret_key = 'pf2-secret-key-2024'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db.init_app(app)

with app.app_context():
    db.create_all()
    # Миграция: добавляем новые колонки если их нет
    db_path = os.path.join('instance', 'characters.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    new_columns = [
        ('lore',                'INTEGER DEFAULT 0'),
        ('lore_topic',          'VARCHAR(100) DEFAULT ""'),
        ('unarmored_prof',      'INTEGER DEFAULT 0'),
        ('light_armor_prof',    'INTEGER DEFAULT 0'),
        ('medium_armor_prof',   'INTEGER DEFAULT 0'),
        ('heavy_armor_prof',    'INTEGER DEFAULT 0'),
        ('unarmed_prof',        'INTEGER DEFAULT 0'),
        ('simple_weapon_prof',  'INTEGER DEFAULT 0'),
        ('martial_weapon_prof', 'INTEGER DEFAULT 0'),
        ('advanced_weapon_prof','INTEGER DEFAULT 0'),
    ]
    for col_name, col_def in new_columns:
        try:
            cursor.execute(f'ALTER TABLE character ADD COLUMN {col_name} {col_def}')
        except sqlite3.OperationalError:
            pass  # Колонка уже существует
    conn.commit()
    conn.close()


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


# ── Главная страница ─────────────────────────────────────────────────────────

@app.route('/')
def index():
    characters = Character.query.order_by(Character.created_at.desc()).all()
    return render_template('index.html', characters=characters)


# ── Просмотр персонажа ───────────────────────────────────────────────────────

@app.route('/character/<int:id>')
def view_character(id):
    character = Character.query.get_or_404(id)
    return render_template('character.html', character=character)


# ── Создание ─────────────────────────────────────────────────────────────────

@app.route('/create', methods=['GET', 'POST'])
def create_character():
    if request.method == 'POST':
        character = Character()
        _fill_character(character, request.form, request.files)
        db.session.add(character)
        db.session.commit()
        return redirect(url_for('view_character', id=character.id))
    return render_template('create_character.html', character=None)


# ── Редактирование ───────────────────────────────────────────────────────────

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_character(id):
    character = Character.query.get_or_404(id)
    if request.method == 'POST':
        _fill_character(character, request.form, request.files)
        db.session.commit()
        return redirect(url_for('view_character', id=character.id))
    return render_template('create_character.html', character=character)


# ── Удаление ─────────────────────────────────────────────────────────────────

@app.route('/delete/<int:id>')
def delete_character(id):
    character = Character.query.get_or_404(id)
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
def update_hp(id):
    character = Character.query.get_or_404(id)
    data = request.get_json()
    delta = int(data.get('delta', 0))
    character.current_hp = max(0, min(character.max_hp, character.current_hp + delta))
    db.session.commit()
    return jsonify({'current_hp': character.current_hp, 'max_hp': character.max_hp})


# ── JSON экспорт ─────────────────────────────────────────────────────────────

@app.route('/export/<int:id>')
def export_character(id):
    character = Character.query.get_or_404(id)
    data = character.to_dict()
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    buf = io.BytesIO(json_bytes)
    safe_name = character.name.replace(' ', '_')
    return send_file(buf, mimetype='application/json',
                     as_attachment=True,
                     download_name=f'{safe_name}.json')


# ── JSON импорт ──────────────────────────────────────────────────────────────

@app.route('/import', methods=['GET', 'POST'])
def import_character():
    if request.method == 'POST':
        f = request.files.get('json_file')
        if not f or not f.filename.endswith('.json'):
            flash('Выберите файл .json')
            return redirect(url_for('import_character'))
        try:
            data = json.load(f)
            character = Character.from_dict(data)
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

    # Владение доспехами
    character.unarmored_prof = int(form.get('unarmored_prof', 0))
    character.light_armor_prof = int(form.get('light_armor_prof', 0))
    character.medium_armor_prof = int(form.get('medium_armor_prof', 0))
    character.heavy_armor_prof = int(form.get('heavy_armor_prof', 0))

    # Владение оружием
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


# ── ДЕМО — только Flask, без JS ──────────────────────────────────────────────

@app.route('/demo')
def demo_index():
    characters = Character.query.order_by(Character.created_at.desc()).all()
    return render_template('demo/index.html', characters=characters)


@app.route('/demo/create', methods=['GET', 'POST'])
def demo_create():
    if request.method == 'POST':
        character = Character()
        _fill_demo(character, request.form)
        db.session.add(character)
        db.session.commit()
        return redirect(f'/demo/character/{character.id}')
    return render_template('demo/create.html', c=None)


@app.route('/demo/edit/<int:id>', methods=['GET', 'POST'])
def demo_edit(id):
    character = Character.query.get_or_404(id)
    if request.method == 'POST':
        _fill_demo(character, request.form)
        db.session.commit()
        return redirect(f'/demo/character/{character.id}')
    return render_template('demo/create.html', c=character)


@app.route('/demo/character/<int:id>')
def demo_view(id):
    character = Character.query.get_or_404(id)
    return render_template('demo/character.html', c=character)


@app.route('/demo/hp/<int:id>', methods=['POST'])
def demo_hp(id):
    character = Character.query.get_or_404(id)
    delta = int(request.form.get('delta', 0))
    character.current_hp = max(0, min(character.max_hp, character.current_hp + delta))
    db.session.commit()
    return redirect(f'/demo/character/{id}')


def _fill_demo(character, form):
    character.name = form['name']
    character.level = int(form.get('level', 1))
    character.experience = int(form.get('experience', 0))
    character.ancestry = form.get('ancestry', '')
    character.background = form.get('background', '')
    character.character_class = form.get('character_class', '')
    character.languages = form.get('languages', '')

    for attr in ('strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'):
        setattr(character, attr, int(form.get(attr, 0)))

    for sk in ['acrobatics', 'arcana', 'athletics', 'crafting', 'deception',
               'diplomacy', 'intimidation', 'lore', 'medicine', 'nature', 'occultism',
               'performance', 'religion', 'society', 'stealth', 'survival', 'thievery']:
        setattr(character, sk, int(form.get(sk, 0)))

    character.lore_topic = form.get('lore_topic', '')
    character.fortitude_prof = int(form.get('fortitude_prof', 0))
    character.reflex_prof = int(form.get('reflex_prof', 0))
    character.will_prof = int(form.get('will_prof', 0))
    character.max_hp = int(form.get('max_hp', 10))
    character.current_hp = int(form.get('current_hp', 10))
    character.armor_class = int(form.get('armor_class', 10))
    character.speed = int(form.get('speed', 25))

    feats = []
    for i in range(8):
        name = form.get(f'feat_name_{i}', '').strip()
        if name:
            feats.append({
                'name': name,
                'type': form.get(f'feat_type_{i}', 'general'),
                'level': form.get(f'feat_level_{i}', ''),
                'description': form.get(f'feat_desc_{i}', ''),
            })
    character.feats_json = json.dumps(feats, ensure_ascii=False)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
