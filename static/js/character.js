/* ========================================================
   PF2e Character Sheet — клиентская логика
   ======================================================== */

// ── Динамические данные формы ─────────────────────────────────────────────

let feats        = [];
let abilities    = [];
let spellsData   = {};
let inventoryArr = [];

function initForm(initFeats, initAbilities, initSpells, initInventory) {
    feats        = Array.isArray(initFeats)    ? initFeats    : [];
    abilities    = Array.isArray(initAbilities) ? initAbilities : [];
    spellsData   = (initSpells && typeof initSpells === 'object') ? initSpells : {};
    inventoryArr = Array.isArray(initInventory) ? initInventory : [];

    renderFeats();
    renderAbilities();
    renderInventory();
    initSpellSection();

    const form = document.getElementById('char-form');
    if (form) form.addEventListener('submit', serializeAll);
}

// ── Черты ─────────────────────────────────────────────────────────────────

const FEAT_TYPES = [
    { value: 'general',  label: 'Общая черта' },
    { value: 'skill',    label: 'Черта навыка' },
    { value: 'ancestry', label: 'Черта происхождения' },
    { value: 'class',    label: 'Классовая черта' },
];

function addFeat() {
    feats.push({ name: '', type: 'general', level: '', description: '' });
    renderFeats();
}

function removeFeat(i) {
    feats.splice(i, 1);
    renderFeats();
}

function renderFeats() {
    const container = document.getElementById('feats-list');
    if (!container) return;
    container.innerHTML = feats.map((f, i) => `
        <div class="dynamic-row">
            <div class="dynamic-fields">
                <input type="text" placeholder="Название черты" value="${esc(f.name)}"
                       onchange="feats[${i}].name=this.value">
                <select onchange="feats[${i}].type=this.value">
                    ${FEAT_TYPES.map(t =>
                        `<option value="${t.value}" ${f.type===t.value?'selected':''}>${t.label}</option>`
                    ).join('')}
                </select>
                <input type="number" placeholder="Уровень" value="${esc(f.level)}" min="1" max="20" style="width:80px"
                       onchange="feats[${i}].level=this.value">
            </div>
            <textarea placeholder="Описание (необязательно)" rows="2"
                      onchange="feats[${i}].description=this.value">${esc(f.description)}</textarea>
            <button type="button" class="btn btn-sm btn-danger remove-btn" onclick="removeFeat(${i})">✕</button>
        </div>
    `).join('');
}

// ── Классовые умения ──────────────────────────────────────────────────────

function addAbility() {
    abilities.push({ name: '', level: '', description: '' });
    renderAbilities();
}

function removeAbility(i) {
    abilities.splice(i, 1);
    renderAbilities();
}

function renderAbilities() {
    const container = document.getElementById('abilities-list');
    if (!container) return;
    container.innerHTML = abilities.map((a, i) => `
        <div class="dynamic-row">
            <div class="dynamic-fields">
                <input type="text" placeholder="Название умения" value="${esc(a.name)}"
                       onchange="abilities[${i}].name=this.value">
                <input type="number" placeholder="Уровень" value="${esc(a.level)}" min="1" max="20" style="width:80px"
                       onchange="abilities[${i}].level=this.value">
            </div>
            <textarea placeholder="Описание" rows="2"
                      onchange="abilities[${i}].description=this.value">${esc(a.description)}</textarea>
            <button type="button" class="btn btn-sm btn-danger remove-btn" onclick="removeAbility(${i})">✕</button>
        </div>
    `).join('');
}

// ── Инвентарь ─────────────────────────────────────────────────────────────

function addItem() {
    inventoryArr.push({ name: '', quantity: 1, weight: '', price: '', description: '', equipped: false });
    renderInventory();
}

function removeItem(i) {
    inventoryArr.splice(i, 1);
    renderInventory();
}

function renderInventory() {
    const container = document.getElementById('inventory-list');
    if (!container) return;
    container.innerHTML = inventoryArr.map((item, i) => `
        <div class="dynamic-row inventory-row">
            <div class="dynamic-fields inventory-fields">
                <input type="text" placeholder="Название предмета" value="${esc(item.name)}"
                       onchange="inventoryArr[${i}].name=this.value" style="flex:2">
                <input type="number" placeholder="Кол-во" value="${esc(item.quantity)}" min="1" style="width:70px"
                       onchange="inventoryArr[${i}].quantity=+this.value">
                <input type="text" placeholder="Вес" value="${esc(item.weight)}" style="width:70px"
                       onchange="inventoryArr[${i}].weight=this.value">
                <input type="text" placeholder="Цена" value="${esc(item.price)}" style="width:90px"
                       onchange="inventoryArr[${i}].price=this.value">
                <label class="check-label">
                    <input type="checkbox" ${item.equipped?'checked':''} onchange="inventoryArr[${i}].equipped=this.checked">
                    Экип.
                </label>
            </div>
            <input type="text" placeholder="Описание" value="${esc(item.description)}"
                   onchange="inventoryArr[${i}].description=this.value">
            <button type="button" class="btn btn-sm btn-danger remove-btn" onclick="removeItem(${i})">✕</button>
        </div>
    `).join('');
}

// ── Заклинания ────────────────────────────────────────────────────────────

function initSpellSection() {
    const cb = document.getElementById('is-caster');
    if (!cb) return;

    if (spellsData.is_caster) {
        cb.checked = true;
        showSpellSection();
        // Заполнить сохранённые значения
        setVal('spell-tradition',    spellsData.tradition);
        setVal('spell-casting-type', spellsData.casting_type);
        setVal('spell-attack-prof',  spellsData.spell_attack_prof);

        const slots = spellsData.slots || {};
        document.querySelectorAll('.slot-input').forEach(inp => {
            const rank = inp.dataset.rank;
            inp.value = slots[rank] || 0;
        });
        renderCantrips(spellsData.cantrips || []);
        renderSpells(spellsData.spells || []);
    }
}

function toggleSpells(cb) {
    if (cb.checked) {
        if (!spellsData.cantrips) spellsData.cantrips = [];
        if (!spellsData.spells)   spellsData.spells   = [];
        showSpellSection();
    } else {
        document.getElementById('spell-section').style.display = 'none';
    }
}

function showSpellSection() {
    document.getElementById('spell-section').style.display = 'block';
    if (!spellsData.cantrips) spellsData.cantrips = [];
    if (!spellsData.spells)   spellsData.spells   = [];
    renderCantrips(spellsData.cantrips);
    renderSpells(spellsData.spells);
}

function addSpell(kind) {
    if (kind === 'cantrip') {
        spellsData.cantrips = spellsData.cantrips || [];
        spellsData.cantrips.push({ name: '', description: '' });
        renderCantrips(spellsData.cantrips);
    } else {
        spellsData.spells = spellsData.spells || [];
        spellsData.spells.push({ name: '', rank: 1, description: '' });
        renderSpells(spellsData.spells);
    }
}

function removeCantrip(i) {
    spellsData.cantrips.splice(i, 1);
    renderCantrips(spellsData.cantrips);
}

function removeSpell(i) {
    spellsData.spells.splice(i, 1);
    renderSpells(spellsData.spells);
}

function renderCantrips(list) {
    const c = document.getElementById('cantrips-list');
    if (!c) return;
    c.innerHTML = list.map((s, i) => `
        <div class="dynamic-row">
            <div class="dynamic-fields">
                <input type="text" placeholder="Название заговора" value="${esc(s.name)}"
                       onchange="spellsData.cantrips[${i}].name=this.value">
                <input type="text" placeholder="Описание" value="${esc(s.description)}"
                       onchange="spellsData.cantrips[${i}].description=this.value" style="flex:2">
            </div>
            <button type="button" class="btn btn-sm btn-danger remove-btn" onclick="removeCantrip(${i})">✕</button>
        </div>
    `).join('');
}

function renderSpells(list) {
    const c = document.getElementById('spells-list');
    if (!c) return;
    c.innerHTML = list.map((s, i) => `
        <div class="dynamic-row">
            <div class="dynamic-fields">
                <input type="text" placeholder="Название заклинания" value="${esc(s.name)}"
                       onchange="spellsData.spells[${i}].name=this.value" style="flex:2">
                <input type="number" placeholder="Ранг" value="${esc(s.rank || 1)}" min="1" max="10" style="width:70px"
                       onchange="spellsData.spells[${i}].rank=+this.value">
                <input type="text" placeholder="Описание" value="${esc(s.description)}"
                       onchange="spellsData.spells[${i}].description=this.value" style="flex:2">
            </div>
            <button type="button" class="btn btn-sm btn-danger remove-btn" onclick="removeSpell(${i})">✕</button>
        </div>
    `).join('');
}

// ── Сериализация перед отправкой ──────────────────────────────────────────

function serializeAll() {
    setHidden('feats_json',            feats);
    setHidden('class_abilities_json',  abilities);
    setHidden('inventory_json',        inventoryArr);

    const cb = document.getElementById('is-caster');
    if (cb && cb.checked) {
        const slots = {};
        document.querySelectorAll('.slot-input').forEach(inp => {
            const v = +inp.value;
            if (v > 0) slots[inp.dataset.rank] = v;
        });
        spellsData.is_caster       = true;
        spellsData.tradition       = getVal('spell-tradition');
        spellsData.casting_type    = getVal('spell-casting-type');
        spellsData.spell_attack_prof = +getVal('spell-attack-prof');
        spellsData.slots           = slots;
    } else {
        spellsData = {};
    }
    setHidden('spells_json', spellsData);
}

// ── Аватар превью ─────────────────────────────────────────────────────────

function previewAvatar(input) {
    const preview = document.getElementById('avatar-img');
    if (!input.files || !input.files[0]) return;
    const reader = new FileReader();
    reader.onload = e => {
        preview.outerHTML = `<img id="avatar-img" src="${e.target.result}" alt="Аватар" style="max-width:200px;border-radius:8px">`;
    };
    reader.readAsDataURL(input.files[0]);
}

// ── Быстрое обновление ХП ─────────────────────────────────────────────────

function changeHP(charId, delta) {
    fetch(`/hp/${charId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ delta })
    })
    .then(r => r.json())
    .then(data => {
        const el = document.getElementById('current-hp');
        if (el) el.textContent = data.current_hp;
        const bar = document.getElementById('hp-bar');
        if (bar) {
            const pct = Math.round(data.current_hp / data.max_hp * 100);
            bar.style.width = Math.min(pct, 100) + '%';
            bar.className = 'hp-bar' + (pct < 25 ? ' hp-crit' : pct < 50 ? ' hp-low' : '');
        }
    });
}

// ── Утилиты ───────────────────────────────────────────────────────────────

function esc(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function setHidden(id, value) {
    const el = document.getElementById(id);
    if (el) el.value = JSON.stringify(value);
}

function getVal(id) {
    const el = document.getElementById(id);
    return el ? el.value : '';
}

function setVal(id, value) {
    const el = document.getElementById(id);
    if (el && value !== undefined && value !== null) el.value = value;
}
