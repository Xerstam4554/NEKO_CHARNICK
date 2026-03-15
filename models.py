from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, default=1)
    ancestry = db.Column(db.String(50))
    background = db.Column(db.String(50))
    character_class = db.Column(db.String(50))
    
    strength = db.Column(db.Integer, default=10)
    dexterity = db.Column(db.Integer, default=10)
    constitution = db.Column(db.Integer, default=10)
    intelligence = db.Column(db.Integer, default=10)
    wisdom = db.Column(db.Integer, default=10)
    charisma = db.Column(db.Integer, default=10)
    
    acrobatics = db.Column(db.Integer, default=0)
    arcana = db.Column(db.Integer, default=0)
    athletics = db.Column(db.Integer, default=0)
    crafting = db.Column(db.Integer, default=0)
    deception = db.Column(db.Integer, default=0)
    diplomacy = db.Column(db.Integer, default=0)
    intimidation = db.Column(db.Integer, default=0)
    medicine = db.Column(db.Integer, default=0)
    nature = db.Column(db.Integer, default=0)
    occultism = db.Column(db.Integer, default=0)
    performance = db.Column(db.Integer, default=0)
    religion = db.Column(db.Integer, default=0)
    society = db.Column(db.Integer, default=0)
    stealth = db.Column(db.Integer, default=0)
    survival = db.Column(db.Integer, default=0)
    thievery = db.Column(db.Integer, default=0)
    
    max_hp = db.Column(db.Integer, default=10)
    current_hp = db.Column(db.Integer, default=10)
    armor_class = db.Column(db.Integer, default=10)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_modifier(self, score):
        return (score - 10) // 2
    
    @property
    def strength_mod(self):
        return self.calculate_modifier(self.strength)
    
    @property
    def dexterity_mod(self):
        return self.calculate_modifier(self.dexterity)
    
    @property
    def constitution_mod(self):
        return self.calculate_modifier(self.constitution)
    
    @property
    def intelligence_mod(self):
        return self.calculate_modifier(self.intelligence)
    
    @property
    def wisdom_mod(self):
        return self.calculate_modifier(self.wisdom)
    
    @property
    def charisma_mod(self):
        return self.calculate_modifier(self.charisma)
    
    def get_skill_bonus(self, skill_value, ability_mod):
        if skill_value == 0:
            return ability_mod
        else:
            proficiency_bonus = {
                1: 2,
                2: 4,
                3: 6,
                4: 8
            }
            return self.level + proficiency_bonus[skill_value] + ability_mod
    
    def get_proficiency_name(self, value):
        names = {
            0: "Необучен",
            1: "Обучен",
            2: "Эксперт",
            3: "Мастер",
            4: "Легендарный"
        }
        return names.get(value, "Необучен")
