from flask import Flask, render_template, request, redirect, url_for
from models import db, Character

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///characters.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.context_processor
def utility_processor():
    def get_attribute(obj, attr):
        return getattr(obj, attr, None)
    return dict(attribute=get_attribute)

@app.route('/')
def index():
    characters = Character.query.all()
    return render_template('index.html', characters=characters)

@app.route('/character/<int:id>')
def view_character(id):
    character = Character.query.get_or_404(id)
    return render_template('character.html', character=character)

@app.route('/create', methods=['GET', 'POST'])
def create_character():
    if request.method == 'POST':
        character = Character(
            name=request.form['name'],
            level=int(request.form.get('level', 1)),
            ancestry=request.form.get('ancestry', ''),
            background=request.form.get('background', ''),
            character_class=request.form.get('class', ''),
            
            strength=int(request.form.get('strength', 10)),
            dexterity=int(request.form.get('dexterity', 10)),
            constitution=int(request.form.get('constitution', 10)),
            intelligence=int(request.form.get('intelligence', 10)),
            wisdom=int(request.form.get('wisdom', 10)),
            charisma=int(request.form.get('charisma', 10)),
            
            max_hp=int(request.form.get('max_hp', 10)),
            current_hp=int(request.form.get('current_hp', 10)),
            armor_class=int(request.form.get('armor_class', 10))
        )
        
        skills = ['acrobatics', 'arcana', 'athletics', 'crafting', 'deception',
                  'diplomacy', 'intimidation', 'medicine', 'nature', 'occultism',
                  'performance', 'religion', 'society', 'stealth', 'survival', 'thievery']
        
        for skill in skills:
            skill_value = request.form.get(skill, 0)
            setattr(character, skill, int(skill_value))
        
        db.session.add(character)
        db.session.commit()
        
        return redirect(url_for('view_character', id=character.id))
    
    return render_template('create_character.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_character(id):
    character = Character.query.get_or_404(id)
    
    if request.method == 'POST':
        character.name = request.form['name']
        character.level = int(request.form.get('level', 1))
        character.ancestry = request.form.get('ancestry', '')
        character.background = request.form.get('background', '')
        character.character_class = request.form.get('class', '')
        
        character.strength = int(request.form.get('strength', 10))
        character.dexterity = int(request.form.get('dexterity', 10))
        character.constitution = int(request.form.get('constitution', 10))
        character.intelligence = int(request.form.get('intelligence', 10))
        character.wisdom = int(request.form.get('wisdom', 10))
        character.charisma = int(request.form.get('charisma', 10))
        
        character.max_hp = int(request.form.get('max_hp', 10))
        character.current_hp = int(request.form.get('current_hp', 10))
        character.armor_class = int(request.form.get('armor_class', 10))
        
        skills = ['acrobatics', 'arcana', 'athletics', 'crafting', 'deception',
                  'diplomacy', 'intimidation', 'medicine', 'nature', 'occultism',
                  'performance', 'religion', 'society', 'stealth', 'survival', 'thievery']
        
        for skill in skills:
            skill_value = request.form.get(skill, 0)
            setattr(character, skill, int(skill_value))
        
        db.session.commit()
        return redirect(url_for('view_character', id=character.id))
    
    return render_template('create_character.html', character=character)

@app.route('/delete/<int:id>')
def delete_character(id):
    character = Character.query.get_or_404(id)
    db.session.delete(character)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
