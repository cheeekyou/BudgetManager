import asyncio
import json
import os
import math
import random
import re
import sqlite3
from datetime import datetime
import calendar
from typing import Dict, Optional

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite

from dotenv import load_dotenv
import os

# Загружаем переменные из файла .env
load_dotenv()

# Теперь BOT_TOKEN берем из окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ================== КОНФИГУРАЦИЯ ==================
DB_FILE = "budget_bot.db"               # SQLite файл
HUMOR_FILE = "humor_phrases.json"       # файл с шутками (необязательный)

# ================== ЗАГРУЗКА ШУТОК ==================
def load_humor_phrases() -> Dict:
    if os.path.exists(HUMOR_FILE):
        try:
            with open(HUMOR_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    # встроенные шутки по умолчанию (короткие, но рабочие)
    return {
        "greeting": ["Привет!", "Здарова!", "О, привет!"],
        "goodbye": ["Пока!", "До встречи!", "Бывай!"],
        "no_expenses": ["Ноль трат! 👍", "Молодец! +{saved} в копилку"],
        "over_limit_critical": ["Ого! В 2 раза больше лимита!", "Жесть!"],
        "over_limit": ["Лимит превышен на {over}!", "Перебор!"],
        "good_saving": ["Экономия {saved}!", "Красава!"],
        "category_warning": ["Осталось {remaining}!", "Береги лимит!"],
        "month_result_great": ["Отличный месяц! +{saved}", "Ты гений!"],
        "month_result_good": ["Неплохо! +{saved}", "Хороший результат"],
        "month_result_ok": ["Средне, но +{saved}", "Могло быть лучше"],
        "month_result_bad": ["В этом месяце не срослось", "Плохо"],
        "daily_check": ["Проверим день?", "Как успехи?"],
        "fun_fact": ["Копейка рубль бережет!", "Деньги любят счет"]
    }

HUMOR_PHRASES = load_humor_phrases()

# ================== СТИЛИ СООБЩЕНИЙ ==================
MESSAGES = {
    "welcome": {
        "official": "Добро пожаловать в Персональный Финансовый Помощник!",
        "conversational": "Привет! Давай разберемся с твоими финансами.",
        "humorous": None
    },
    "goodbye": {
        "official": "До свидания! Желаем успехов в накоплении капитала!",
        "conversational": "Пока! Будут вопросы – заходи, разберемся.",
        "humorous": None
    },
    "month_summary": {
        "official": "Уважаемый пользователь, ваш бюджет за месяц составил {budget} рублей. Вы увеличили свой капитал на {saved} рублей. {encouragement}",
        "conversational": "За месяц ты заработал {budget}, а сэкономил {saved}. {encouragement}",
        "humorous": "{encouragement}"
    },
    "encouragement_great": {
        "official": "Превосходный результат, так держать!",
        "conversational": "Отличный результат! Так и продолжай!",
        "humorous": None
    },
    "encouragement_good": {
        "official": "Хороший результат, продолжайте в том же духе!",
        "conversational": "Неплохо! Достойный результат.",
        "humorous": None
    },
    "encouragement_ok": {
        "official": "Неплохо, но есть куда стремиться.",
        "conversational": "Бывает. В следующем месяце получится лучше.",
        "humorous": None
    },
    "encouragement_bad": {
        "official": "Будьте внимательнее с расходами в следующем месяце.",
        "conversational": "Месяц не очень. Давай в следующем поднажмем!",
        "humorous": None
    },
    "daily_check_start": {
        "official": "Ежедневная проверка финансового состояния:",
        "conversational": "Давай проверим, как прошел день.",
        "humorous": None
    },
    "daily_limit_info": {
        "official": "Ваш дневной лимит сегодня составляет {limit} рублей.",
        "conversational": "Сегодня можно потратить {limit}.",
        "humorous": "Сегодня лимит {limit}. Не прожги всё сразу!"
    },
    "remaining_budget": {
        "official": "Остаток бюджета на месяц: {remaining} рублей.",
        "conversational": "Осталось на месяц: {remaining}.",
        "humorous": "В загашнике осталось {remaining}. Дотянуть бы до зарплаты!"
    },
    "already_checked": {
        "official": "Вы уже отчитались сегодня. Возвращайтесь завтра!",
        "conversational": "Ты сегодня уже чекался. Завтра приходи!",
        "humorous": "Сегодня уже были разборки с бюджетом. Давай завтра, ок?"
    },
    "skip_check": {
        "official": "Пропускаем проверку.",
        "conversational": "Ок, пропускаем.",
        "humorous": "Ладно, живи пока без контроля! 🏃‍♂️"
    },
    "no_expenses_today": {
        "official": "Отлично! Вы не потратили ни рубля сегодня. Сэкономлено {saved} рублей.",
        "conversational": "Круто! День без трат. В копилку +{saved}!",
        "humorous": None
    },
    "expense_added": {
        "official": "Расход в размере {amount} рублей добавлен в категорию {category}.",
        "conversational": "Потратил {amount} на {category}.",
        "humorous": "И еще {amount} улетело в {category}! ✈️"
    },
    "expense_description": {
        "official": "Описание операции: {description}",
        "conversational": "({description})",
        "humorous": "Зачем? {description} А, ну понятно..."
    },
    "advice_critical": {
        "official": "Критическое превышение! Трата в 2 раза превышает дневной лимит. Рекомендуем пересмотреть необходимость крупных покупок.",
        "conversational": "Ого! Это в 2 раза больше дневного лимита. Может, не так уж и нужно было?",
        "humorous": None
    },
    "advice_over_limit": {
        "official": "Внимание! Вы превысили дневной лимит на {over} рублей. Постарайтесь завтра экономить.",
        "conversational": "Превысил лимит на {over}. Завтра придется экономить.",
        "humorous": None
    },
    "advice_normal": {
        "official": "Трата в пределах нормы. Вы близки к лимиту, следите за расходами.",
        "conversational": "В лимит уложился, но почти на пределе.",
        "humorous": "Еще чуть-чуть и был бы перебор. В следующий раз аккуратнее!"
    },
    "advice_good": {
        "official": "Отличная экономия! Вы сэкономили {saved} рублей от дневного лимита.",
        "conversational": "Хорошая экономия! +{saved} к накоплениям.",
        "humorous": None
    },
    "category_fixed": {
        "official": "Постоянные расходы",
        "conversational": "обязательные",
        "humorous": "жизненно необходимые"
    },
    "category_temporary": {
        "official": "Временные расходы",
        "conversational": "текущие",
        "humorous": "хотелки"
    },
    "category_unexpected": {
        "official": "Непредвиденные расходы",
        "conversational": "внезапные",
        "humorous": "сюрпризы"
    },
    "category_estimated": {
        "official": "Предположительные расходы",
        "conversational": "плановые",
        "humorous": "запланированные удовольствия"
    },
    "category_daily": {
        "official": "Ежедневные покупки",
        "conversational": "повседневные",
        "humorous": "кофе-пирожки"
    },
    "category_warning": {
        "official": "Внимание! Вы превышаете лимит по категории! Остаток: {remaining} рублей.",
        "conversational": "Осторожно! Осталось всего {remaining} на эту категорию.",
        "humorous": None
    },
    "total_fund": {
        "official": "Ваш общий капитал составляет {amount} рублей.",
        "conversational": "Всего на счетах: {amount}.",
        "humorous": "💰 Всего денег: {amount}. Не слабо!"
    },
    "history_title": {
        "official": "История финансов по месяцам:",
        "conversational": "Что было по месяцам:",
        "humorous": "Архив финансовых подвигов:"
    },
    "history_item": {
        "official": "Период {month}: сэкономлено {saved} рублей, общий фонд {fund} рублей",
        "conversational": "{month}: +{saved}, всего {fund}",
        "humorous": "📅 {month}: Отложил {saved}, в кубышке {fund}"
    },
    "status_title": {
        "official": "ТЕКУЩЕЕ ФИНАНСОВОЕ СОСТОЯНИЕ",
        "conversational": "ЧТО ПО ФИНАНСАМ:",
        "humorous": "ФИНАНСОВАЯ СВОДКА (барабанная дробь):"
    },
    "category_status": {
        "official": "{category}: План {planned}, Потрачено {spent} ({percent}%), Остаток {remaining}",
        "conversational": "{category}: осталось {remaining} из {planned}",
        "humorous": "{category}: в кармане {remaining}, потрачено {spent} (это {percent}% от плана)"
    },
    "style_menu": {
        "official": "Выберите стиль общения:",
        "conversational": "Как будем разговаривать?",
        "humorous": "Выбери мой голос:"
    },
    "style_official": {
        "official": "Официальный (как в банке)",
        "conversational": "Официальный",
        "humorous": "👔 Солидный, как банкир"
    },
    "style_conversational": {
        "official": "Разговорный (повседневный)",
        "conversational": "Обычный",
        "humorous": "🗣️ Человеческий, понятный"
    },
    "style_humorous": {
        "official": "Юмористический (с приколами)",
        "conversational": "С юмором",
        "humorous": "😂 Прикольный, с мемасами"
    },
    "money_hint": {
        "official": "Подсказка по вводу чисел:",
        "conversational": "Как вводить деньги:",
        "humorous": "Инструкция для чайников:"
    },
    "style_changed": {
        "official": "Стиль общения изменен на {style_ru}.",
        "conversational": "Ок, теперь буду {style_ru}.",
        "humorous": "🃏 Врубаю {style_ru} режим! Погнали!"
    }
}

# ================== УТИЛИТЫ ==================
def get_random_humor(key: str, **kwargs) -> str:
    phrases = HUMOR_PHRASES.get(key, [])
    if not phrases:
        return ""
    phrase = random.choice(phrases)
    try:
        return phrase.format(**kwargs)
    except:
        return phrase

def get_message(style: str, key: str, **kwargs) -> str:
    """Получить сообщение для данного стиля."""
    if style == "humorous" and key in HUMOR_PHRASES:
        return get_random_humor(key, **kwargs)
    msg_dict = MESSAGES.get(key, {})
    template = msg_dict.get(style) or msg_dict.get("conversational", "")
    if not template:
        return ""
    try:
        return template.format(**kwargs)
    except:
        return template

def format_money(amount: int, style: str) -> str:
    if style in ["conversational", "humorous"]:
        if amount >= 1000:
            thousands = amount / 1000
            if thousands.is_integer():
                return f"{int(thousands)}к"
            else:
                return f"{thousands:.1f}к".replace('.', ',')
        else:
            return str(amount)
    else:
        return f"{amount:,}".replace(",", " ")

def parse_money(text: str) -> Optional[int]:
    """Преобразует пользовательский ввод в целое число рублей."""
    if not text or not isinstance(text, str):
        return None
    text = text.lower().strip()
    text = re.sub(r'\s+', '', text)

    if text.endswith('к'):
        try:
            num = float(text[:-1])
            return math.ceil(num * 1000)
        except ValueError:
            return None

    if 'тыс' in text:
        match = re.match(r'^([\d.,]+)', text)
        if match:
            num_str = match.group(1).replace(',', '.')
            try:
                num = float(num_str)
                return math.ceil(num * 1000)
            except ValueError:
                return None
        return None

    text = text.replace(',', '.')
    if '.' in text:
        try:
            num = float(text)
            return math.ceil(num)
        except ValueError:
            return None

    try:
        return int(float(text))
    except ValueError:
        return None

def get_category_emoji(cat: str) -> str:
    return {"fixed": "🏠", "temporary": "🛍️", "unexpected": "🚨", "estimated": "📝", "daily": "☕"}.get(cat, "📊")

def get_category_name(style: str, cat: str) -> str:
    key = f"category_{cat}"
    return get_message(style, key)

def calculate_daily_limit(remaining: int, days: int) -> int:
    if days <= 0:
        return 0
    return math.ceil(remaining / days)

# ================== БАЗА ДАННЫХ (SQLite) ==================
async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                data TEXT NOT NULL,
                speech_style TEXT DEFAULT 'conversational'
            )
        ''')
        await db.commit()

async def load_user_data(user_id: int) -> Optional[Dict]:
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute('SELECT data FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row[0])
    return None

async def save_user_data(user_id: int, data: Dict, style: str):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            INSERT INTO users (user_id, data, speech_style)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET data = excluded.data, speech_style = excluded.speech_style
        ''', (user_id, json.dumps(data, ensure_ascii=False), style))
        await db.commit()

async def get_user_style(user_id: int) -> str:
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute('SELECT speech_style FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
    return "conversational"

async def update_user_style(user_id: int, style: str):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('UPDATE users SET speech_style = ? WHERE user_id = ?', (style, user_id))
        await db.commit()

# ================== FSM СОСТОЯНИЯ ==================
class BudgetSetup(StatesGroup):
    income = State()
    fund = State()
    fixed = State()
    temporary = State()
    unexpected = State()
    estimated = State()
    daily = State()

class AddExpense(StatesGroup):
    choosing_category = State()
    entering_amount = State()
    entering_description = State()

class DailyCheck(StatesGroup):
    waiting_for_choice = State()

# ================== КЛАВИАТУРЫ ==================
def main_keyboard(style: str) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="🌅 Ежедневная проверка"), KeyboardButton(text="📝 Добавить расход")],
        [KeyboardButton(text="📊 Статус"), KeyboardButton(text="💰 Общий фонд")],
        [KeyboardButton(text="📈 История"), KeyboardButton(text="🗣️ Стиль")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def category_keyboard(style: str) -> InlineKeyboardMarkup:
    buttons = []
    cats = ["fixed", "temporary", "unexpected", "estimated", "daily"]
    for cat in cats:
        name = get_category_name(style, cat)
        emoji = get_category_emoji(cat)
        buttons.append([InlineKeyboardButton(text=f"{emoji} {name}", callback_data=f"cat_{cat}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def style_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_message("conversational", "style_official"), callback_data="style_official")],
        [InlineKeyboardButton(text=get_message("conversational", "style_conversational"), callback_data="style_conversational")],
        [InlineKeyboardButton(text=get_message("conversational", "style_humorous"), callback_data="style_humorous")]
    ])

# ================== ХЕЛПЕРЫ ДЛЯ ДАННЫХ ==================
def new_user_data(income: int, fund: int, fixed: int, temporary: int, unexpected: int, estimated: int, daily: int) -> Dict:
    today = datetime.now()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_left = days_in_month - today.day + 1
    total_expenses = fixed + temporary + unexpected + estimated + daily
    remaining = income - total_expenses
    return {
        "start_date": today.isoformat(),
        "current_month": today.strftime("%Y-%m"),
        "initial_income": income,
        "total_fund": fund,
        "remaining_budget": remaining,
        "days_left": days_left,
        "daily_limit": calculate_daily_limit(remaining, days_left),
        "expense_categories": {
            "fixed": {"planned": fixed, "spent": 0, "remaining": fixed},
            "temporary": {"planned": temporary, "spent": 0, "remaining": temporary},
            "unexpected": {"planned": unexpected, "spent": 0, "remaining": unexpected},
            "estimated": {"planned": estimated, "spent": 0, "remaining": estimated},
            "daily": {"planned": daily, "spent": 0, "remaining": daily}
        },
        "expense_history": [],
        "saved_money": 0,
        "last_check_date": None,
        "monthly_summary": {}
    }

# ================== ОБРАБОТЧИКИ ==================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await load_user_data(user_id)
    if data:
        style = await get_user_style(user_id)
        await message.answer(get_message(style, "welcome"), reply_markup=main_keyboard(style))
    else:
        await message.answer(
            "Привет! Давай настроим бюджет.\n"
            "Введи свой доход за этот месяц. Можно использовать такие форматы:\n"
            "• 30000\n"
            "• 30 000\n"
            "• 30к\n"
            "• 30 тыс\n"
            "• 30 тысяч\n"
            "• 30 тысяч 500 (будет 30500)"
        )
        await state.set_state(BudgetSetup.income)

# ----- НАСТРОЙКА БЮДЖЕТА -----
async def get_money_input(message: Message, state: FSMContext, next_state, field_name):
    value = parse_money(message.text)
    if value is None:
        await message.answer("Не понял сумму. Попробуй ещё раз (например: 30к, 15000, 20 тысяч).")
        return False
    await state.update_data({field_name: value})
    await state.set_state(next_state)
    return True

@dp.message(BudgetSetup.income)
async def process_income(message: Message, state: FSMContext):
    if await get_money_input(message, state, BudgetSetup.fund, "income"):
        await message.answer("Отлично! Теперь введи общий фонд денег (все накопления):")

@dp.message(BudgetSetup.fund)
async def process_fund(message: Message, state: FSMContext):
    if await get_money_input(message, state, BudgetSetup.fixed, "fund"):
        await message.answer("Теперь введи сумму постоянных расходов (аренда, коммуналка):")

@dp.message(BudgetSetup.fixed)
async def process_fixed(message: Message, state: FSMContext):
    if await get_money_input(message, state, BudgetSetup.temporary, "fixed"):
        await message.answer("Временные расходы (развлечения, одежда):")

@dp.message(BudgetSetup.temporary)
async def process_temporary(message: Message, state: FSMContext):
    if await get_money_input(message, state, BudgetSetup.unexpected, "temporary"):
        await message.answer("Непредвиденные расходы (на случай ЧП):")

@dp.message(BudgetSetup.unexpected)
async def process_unexpected(message: Message, state: FSMContext):
    if await get_money_input(message, state, BudgetSetup.estimated, "unexpected"):
        await message.answer("Предположительные расходы (планы):")

@dp.message(BudgetSetup.estimated)
async def process_estimated(message: Message, state: FSMContext):
    if await get_money_input(message, state, BudgetSetup.daily, "estimated"):
        await message.answer("И последнее – ежедневные покупки (кофе, продукты и т.п.):")

@dp.message(BudgetSetup.daily)
async def process_daily_cat(message: Message, state: FSMContext):
    value = parse_money(message.text)
    if value is None:
        await message.answer("Не понял сумму. Попробуй ещё раз (например: 30к, 15000).")
        return
    data = await state.get_data()
    user_id = message.from_user.id
    new_data = new_user_data(
        income=data['income'],
        fund=data['fund'],
        fixed=data['fixed'],
        temporary=data['temporary'],
        unexpected=data['unexpected'],
        estimated=data['estimated'],
        daily=value
    )
    style = "conversational"
    await save_user_data(user_id, new_data, style)
    await state.clear()
    await message.answer(
        get_message(style, "welcome") + "\nБюджет настроен! Используй /daily для ежедневной проверки.",
        reply_markup=main_keyboard(style)
    )

# ----- ДОБАВЛЕНИЕ РАСХОДА -----
@dp.message(Command("add"))
@dp.message(F.text == "📝 Добавить расход")
async def cmd_add(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await load_user_data(user_id)
    if not data:
        await message.answer("Сначала настрой бюджет через /start")
        return
    style = await get_user_style(user_id)
    await message.answer("Выбери категорию:", reply_markup=category_keyboard(style))
    await state.set_state(AddExpense.choosing_category)

@dp.callback_query(AddExpense.choosing_category, F.data.startswith("cat_"))
async def process_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data[4:]
    await state.update_data(category=category)
    await callback.message.edit_text(f"Выбрана категория. Введи сумму (можно '30к', '15000' и т.д.):")
    await callback.answer()
    await state.set_state(AddExpense.entering_amount)

@dp.message(AddExpense.entering_amount)
async def process_amount(message: Message, state: FSMContext):
    amount = parse_money(message.text)
    if amount is None:
        await message.answer("Не понял сумму. Попробуй ещё раз (например: 30к, 15000).")
        return
    await state.update_data(amount=amount)
    await message.answer("Добавь описание (или отправь 'нет'):")
    await state.set_state(AddExpense.entering_description)

@dp.message(AddExpense.entering_description)
async def process_description(message: Message, state: FSMContext):
    description = message.text if message.text.lower() != "нет" else ""
    data = await state.get_data()
    category = data['category']
    amount = data['amount']
    user_id = message.from_user.id

    user_data = await load_user_data(user_id)
    if not user_data:
        await message.answer("Ошибка: данные не найдены. Начни заново.")
        await state.clear()
        return

    style = await get_user_style(user_id)

    # Проверка лимита категории
    remaining_cat = user_data['expense_categories'][category]['remaining']
    if amount > remaining_cat:
        await message.answer(get_message(style, "category_warning", remaining=format_money(remaining_cat, style)))
        # Всё равно продолжаем, пользователь подтвердил, просто предупредили

    # Списываем
    user_data['expense_categories'][category]['spent'] += amount
    user_data['expense_categories'][category]['remaining'] -= amount
    user_data['remaining_budget'] -= amount

    # Сохраняем историю
    user_data['expense_history'].append({
        "date": datetime.now().isoformat(),
        "category": category,
        "amount": amount,
        "description": description
    })

    # Пересчёт дневного лимита
    if user_data['days_left'] > 0:
        user_data['daily_limit'] = calculate_daily_limit(user_data['remaining_budget'], user_data['days_left'])

    await save_user_data(user_id, user_data, style)

    cat_name = get_category_name(style, category)
    await message.answer(
        get_message(style, "expense_added", amount=format_money(amount, style), category=cat_name) +
        (f"\n{get_message(style, 'expense_description', description=description)}" if description else "")
    )
    # Совет
    daily_limit = user_data['daily_limit']
    if amount > daily_limit * 2:
        await message.answer(get_message(style, "advice_critical"))
    elif amount > daily_limit:
        over = amount - daily_limit
        await message.answer(get_message(style, "advice_over_limit", over=format_money(over, style)))
    elif amount > daily_limit * 0.7:
        await message.answer(get_message(style, "advice_normal"))
    else:
        saved = daily_limit - amount
        await message.answer(get_message(style, "advice_good", saved=format_money(saved, style)))

    await state.clear()

# ----- ЕЖЕДНЕВНАЯ ПРОВЕРКА -----
@dp.message(Command("daily"))
@dp.message(F.text == "🌅 Ежедневная проверка")
async def cmd_daily(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await load_user_data(user_id)
    if not data:
        await message.answer("Сначала настрой бюджет через /start")
        return
    style = await get_user_style(user_id)
    today_str = datetime.now().date().isoformat()
    if data.get('last_check_date') == today_str:
        await message.answer(get_message(style, "already_checked"))
        return

    limit = format_money(data['daily_limit'], style)
    remaining = format_money(data['remaining_budget'], style)

    text = get_message(style, "daily_check_start") + "\n"
    text += get_message(style, "daily_limit_info", limit=limit) + "\n"
    text += get_message(style, "remaining_budget", remaining=remaining) + "\n\n"
    text += "Как прошел день? (отправь цифру)\n"
    text += "1. 👍 Без трат\n2. 💸 Были траты\n3. ⏭️ Пропустить"

    await message.answer(text)
    await state.set_state(DailyCheck.waiting_for_choice)

@dp.message(DailyCheck.waiting_for_choice)
async def process_daily_choice(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await load_user_data(user_id)
    if not data:
        await message.answer("Ошибка, данные не найдены")
        await state.clear()
        return
    style = await get_user_style(user_id)
    choice = message.text.strip()

    if choice == '1':
        saved_today = data['daily_limit']
        data['saved_money'] = data.get('saved_money', 0) + saved_today
        data['remaining_budget'] -= saved_today
        data['days_left'] -= 1
        data['last_check_date'] = datetime.now().date().isoformat()
        await save_user_data(user_id, data, style)
        await message.answer(get_message(style, "no_expenses_today", saved=format_money(saved_today, style)))
        await state.clear()

    elif choice == '2':
        # Переход к добавлению расхода
        await state.clear()
        await cmd_add(message, state)  # вызовем добавление расхода

    elif choice == '3':
        await message.answer(get_message(style, "skip_check"))
        await state.clear()

    else:
        await message.answer("Не понял, выбери 1, 2 или 3.")

# ----- СТАТУС -----
@dp.message(Command("status"))
@dp.message(F.text == "📊 Статус")
async def cmd_status(message: Message):
    user_id = message.from_user.id
    data = await load_user_data(user_id)
    if not data:
        await message.answer("Сначала настрой бюджет через /start")
        return
    style = await get_user_style(user_id)

    fund = format_money(data['total_fund'], style)
    remaining = format_money(data['remaining_budget'], style)
    limit = format_money(data['daily_limit'], style)

    text = get_message(style, "status_title") + "\n\n"
    text += get_message(style, "total_fund", amount=fund) + "\n\n"
    if style == "official":
        text += f"📅 БЮДЖЕТ МЕСЯЦА:\n  💵 Остаток: {remaining} рублей\n  📆 Дней осталось: {data['days_left']}\n  🎯 Дневной лимит: {limit} рублей\n\n"
    else:
        text += f"📅 МЕСЯЦ:\n  💵 Остаток: {remaining}\n  📆 Осталось дней: {data['days_left']}\n  🎯 Можно тратить в день: {limit}\n\n"

    text += "📊 КАТЕГОРИИ:\n"
    for cat, cat_data in data['expense_categories'].items():
        emoji = get_category_emoji(cat)
        cat_title = get_category_name(style, cat)
        remaining_cat = format_money(cat_data['remaining'], style)
        planned = format_money(cat_data['planned'], style)
        if style == "official":
            percent = (cat_data['spent'] / cat_data['planned'] * 100) if cat_data['planned'] > 0 else 0
            text += f"{emoji} {cat_title}: план {planned}, потрачено {format_money(cat_data['spent'], style)} ({percent:.1f}%), остаток {remaining_cat}\n"
        else:
            text += f"{emoji} {cat_title}: осталось {remaining_cat} из {planned}\n"

    saved = data.get('saved_money', 0)
    if saved > 0:
        text += f"\n💰 Накопил за месяц: {format_money(saved, style)}"

    await message.answer(text)

# ----- ОБЩИЙ ФОНД -----
@dp.message(Command("fund"))
@dp.message(F.text == "💰 Общий фонд")
async def cmd_fund(message: Message):
    user_id = message.from_user.id
    data = await load_user_data(user_id)
    if not data:
        await message.answer("Сначала настрой бюджет через /start")
        return
    style = await get_user_style(user_id)
    fund = format_money(data['total_fund'], style)
    await message.answer(get_message(style, "total_fund", amount=fund))

# ----- ИСТОРИЯ -----
@dp.message(Command("history"))
@dp.message(F.text == "📈 История")
async def cmd_history(message: Message):
    user_id = message.from_user.id
    data = await load_user_data(user_id)
    if not data or not data.get('monthly_summary'):
        await message.answer("История пока пуста.")
        return
    style = await get_user_style(user_id)
    text = get_message(style, "history_title") + "\n"
    for month, summary in data['monthly_summary'].items():
        saved = format_money(summary['saved'], style)
        fund = format_money(summary['total_fund'], style)
        text += get_message(style, "history_item", month=month, saved=saved, fund=fund) + "\n"
    await message.answer(text)

# ----- СМЕНА СТИЛЯ -----
@dp.message(Command("style"))
@dp.message(F.text == "🗣️ Стиль")
async def cmd_style(message: Message):
    user_id = message.from_user.id
    style = await get_user_style(user_id)
    await message.answer(get_message(style, "style_menu"), reply_markup=style_keyboard())

@dp.callback_query(F.data.startswith("style_"))
async def process_style_change(callback: CallbackQuery):
    new_style = callback.data[6:]  # style_official -> official
    user_id = callback.from_user.id
    await update_user_style(user_id, new_style)
    style_names = {"official": "официальный", "conversational": "разговорный", "humorous": "с юмором"}
    await callback.message.edit_text(
        get_message(new_style, "style_changed", style_ru=style_names[new_style])
    )
    await callback.answer()

# ----- ОТМЕНА -----
@dp.message(Command("cancel"))
@dp.message(F.text.lower() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    style = await get_user_style(user_id)
    await message.answer("Действие отменено.", reply_markup=main_keyboard(style))

# ================== ЗАПУСК ==================
async def main():
    if BOT_TOKEN == "ТВОЙ_ТОКЕН":
        print("ОШИБКА: Вставьте свой токен в переменную BOT_TOKEN")
        return
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())