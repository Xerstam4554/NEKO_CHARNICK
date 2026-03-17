import json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

PROFICIENCY_NAMES = {
    0: "Необучен",
    1: "Обучен",
    2: "Эксперт",
    3: "Мастер",
    4: "Легендарный"
}

PROFICIENCY_BONUS = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8}

CLASSES = [
    "Алхимик", "Анимист", "Бард", "Варвар", "Ведьма", "Воин", "Волшебник",
    "Друид", "Жрец", "Изобретатель", "Кинетик", "Монах", "Оракул", "Плут",
    "Поборник", "Следователь", "Следопыт", "Сорвиголова", "Стрелок",
    "Чародей", "Экземплар"
]

ABILITY_NAMES = {
    'strength': 'Сила',
    'dexterity': 'Ловкость',
    'constitution': 'Телосложение',
    'intelligence': 'Интеллект',
    'wisdom': 'Мудрость',
    'charisma': 'Харизма',
}

TRADITIONS = {
    'arcane': 'Мистические',
    'divine': 'Сакральные',
    'occult': 'Оккультные',
    'primal': 'Первобытные',
}


class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    ancestry = db.Column(db.String(100))
    background = db.Column(db.String(100))
    character_class = db.Column(db.String(50))
    avatar = db.Column(db.String(200))

    # Модификаторы характеристик (напрямую, без значений)
    strength = db.Column(db.Integer, default=0)
    dexterity = db.Column(db.Integer, default=0)
    constitution = db.Column(db.Integer, default=0)
    intelligence = db.Column(db.Integer, default=0)
    wisdom = db.Column(db.Integer, default=0)
    charisma = db.Column(db.Integer, default=0)

    # Навыки (0=необучен, 1=обучен, 2=эксперт, 3=мастер, 4=легендарный)
    acrobatics = db.Column(db.Integer, default=0)
    arcana = db.Column(db.Integer, default=0)        # Мистицизм
    athletics = db.Column(db.Integer, default=0)
    crafting = db.Column(db.Integer, default=0)
    deception = db.Column(db.Integer, default=0)
    diplomacy = db.Column(db.Integer, default=0)
    intimidation = db.Column(db.Integer, default=0)
    lore = db.Column(db.Integer, default=0)          # Знание
    lore_topic = db.Column(db.String(100), default='')
    medicine = db.Column(db.Integer, default=0)
    nature = db.Column(db.Integer, default=0)
    occultism = db.Column(db.Integer, default=0)
    performance = db.Column(db.Integer, default=0)
    religion = db.Column(db.Integer, default=0)
    society = db.Column(db.Integer, default=0)
    stealth = db.Column(db.Integer, default=0)
    survival = db.Column(db.Integer, default=0)
    thievery = db.Column(db.Integer, default=0)

    # Испытания — уровень владения
    fortitude_prof = db.Column(db.Integer, default=0)
    reflex_prof = db.Column(db.Integer, default=0)
    will_prof = db.Column(db.Integer, default=0)

    # Восприятие
    perception_prof = db.Column(db.Integer, default=0)

    # Боевые параметры
    max_hp = db.Column(db.Integer, default=10)
    current_hp = db.Column(db.Integer, default=10)
    armor_class = db.Column(db.Integer, default=10)
    speed = db.Column(db.Integer, default=25)

    # Владение доспехами
    unarmored_prof = db.Column(db.Integer, default=0)
    light_armor_prof = db.Column(db.Integer, default=0)
    medium_armor_prof = db.Column(db.Integer, default=0)
    heavy_armor_prof = db.Column(db.Integer, default=0)

    # Владение оружием
    unarmed_prof = db.Column(db.Integer, default=0)
    simple_weapon_prof = db.Column(db.Integer, default=0)
    martial_weapon_prof = db.Column(db.Integer, default=0)
    advanced_weapon_prof = db.Column(db.Integer, default=0)

    # Классовая сложность
    class_dc_prof = db.Column(db.Integer, default=0)
    class_dc_ability = db.Column(db.String(20), default='strength')

    # Текстовые/JSON поля
    languages = db.Column(db.Text, default='')
    feats_json = db.Column(db.Text, default='[]')
    class_abilities_json = db.Column(db.Text, default='[]')
    spells_json = db.Column(db.Text, default='{}')
    inventory_json = db.Column(db.Text, default='[]')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Вспомогательные методы ──────────────────────────────

    def _prof_bonus(self, prof):
        if prof == 0:
            return 0
        return self.level + PROFICIENCY_BONUS[prof]

    def get_skill_bonus(self, skill_value, ability_mod):
        if skill_value == 0:
            return ability_mod
        return self.level + PROFICIENCY_BONUS[skill_value] + ability_mod

    def get_proficiency_name(self, value):
        return PROFICIENCY_NAMES.get(value, "Необучен")

    # ── Испытания ────────────────────────────────────────────

    @property
    def fortitude_bonus(self):
        return self._prof_bonus(self.fortitude_prof) + self.constitution

    @property
    def reflex_bonus(self):
        return self._prof_bonus(self.reflex_prof) + self.dexterity

    @property
    def will_bonus(self):
        return self._prof_bonus(self.will_prof) + self.wisdom

    # ── Восприятие ───────────────────────────────────────────

    @property
    def perception_bonus(self):
        return self._prof_bonus(self.perception_prof) + self.wisdom

    # ── Классовая сложность ──────────────────────────────────

    @property
    def class_dc(self):
        mod = getattr(self, self.class_dc_ability, 0)
        return 10 + self._prof_bonus(self.class_dc_prof) + mod

    @property
    def class_spell_attack(self):
        mod = getattr(self, self.class_dc_ability, 0)
        return self._prof_bonus(self.class_dc_prof) + mod

    # ── JSON-поля ────────────────────────────────────────────

    @property
    def feats(self):
        try:
            return json.loads(self.feats_json or '[]')
        except Exception:
            return []

    @property
    def class_abilities(self):
        try:
            return json.loads(self.class_abilities_json or '[]')
        except Exception:
            return []

    @property
    def spells(self):
        try:
            return json.loads(self.spells_json or '{}')
        except Exception:
            return {}

    @property
    def inventory(self):
        try:
            return json.loads(self.inventory_json or '[]')
        except Exception:
            return []

    # ── Экспорт / импорт ────────────────────────────────────

    def to_dict(self):
        return {
            'name': self.name,
            'level': self.level,
            'experience': self.experience,
            'ancestry': self.ancestry,
            'background': self.background,
            'character_class': self.character_class,
            'strength': self.strength,
            'dexterity': self.dexterity,
            'constitution': self.constitution,
            'intelligence': self.intelligence,
            'wisdom': self.wisdom,
            'charisma': self.charisma,
            'acrobatics': self.acrobatics,
            'arcana': self.arcana,
            'athletics': self.athletics,
            'crafting': self.crafting,
            'deception': self.deception,
            'diplomacy': self.diplomacy,
            'intimidation': self.intimidation,
            'lore': self.lore,
            'lore_topic': self.lore_topic,
            'medicine': self.medicine,
            'nature': self.nature,
            'occultism': self.occultism,
            'performance': self.performance,
            'religion': self.religion,
            'society': self.society,
            'stealth': self.stealth,
            'survival': self.survival,
            'thievery': self.thievery,
            'fortitude_prof': self.fortitude_prof,
            'reflex_prof': self.reflex_prof,
            'will_prof': self.will_prof,
            'perception_prof': self.perception_prof,
            'unarmored_prof': self.unarmored_prof,
            'light_armor_prof': self.light_armor_prof,
            'medium_armor_prof': self.medium_armor_prof,
            'heavy_armor_prof': self.heavy_armor_prof,
            'unarmed_prof': self.unarmed_prof,
            'simple_weapon_prof': self.simple_weapon_prof,
            'martial_weapon_prof': self.martial_weapon_prof,
            'advanced_weapon_prof': self.advanced_weapon_prof,
            'max_hp': self.max_hp,
            'current_hp': self.current_hp,
            'armor_class': self.armor_class,
            'speed': self.speed,
            'class_dc_prof': self.class_dc_prof,
            'class_dc_ability': self.class_dc_ability,
            'languages': self.languages,
            'feats': self.feats,
            'class_abilities': self.class_abilities,
            'spells': self.spells,
            'inventory': self.inventory,
        }

    @staticmethod
    def from_dict(data):
        c = Character()
        fields = [
            'name', 'level', 'experience', 'ancestry', 'background',
            'character_class', 'strength', 'dexterity', 'constitution',
            'intelligence', 'wisdom', 'charisma', 'acrobatics', 'arcana',
            'athletics', 'crafting', 'deception', 'diplomacy', 'intimidation',
            'lore', 'lore_topic', 'medicine', 'nature', 'occultism', 'performance',
            'religion', 'society', 'stealth', 'survival', 'thievery',
            'fortitude_prof', 'reflex_prof', 'will_prof', 'perception_prof',
            'unarmored_prof', 'light_armor_prof', 'medium_armor_prof', 'heavy_armor_prof',
            'unarmed_prof', 'simple_weapon_prof', 'martial_weapon_prof', 'advanced_weapon_prof',
            'max_hp', 'current_hp', 'armor_class', 'speed', 'class_dc_prof',
            'class_dc_ability', 'languages',
        ]
        for f in fields:
            if f in data:
                setattr(c, f, data[f])
        c.feats_json = json.dumps(data.get('feats', []), ensure_ascii=False)
        c.class_abilities_json = json.dumps(data.get('class_abilities', []), ensure_ascii=False)
        c.spells_json = json.dumps(data.get('spells', {}), ensure_ascii=False)
        c.inventory_json = json.dumps(data.get('inventory', []), ensure_ascii=False)
        return c
