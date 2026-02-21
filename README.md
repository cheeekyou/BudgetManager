import json
import os
import math
import random
from datetime import datetime
import calendar
from typing import Dict, Optional

DATA_FILE = "budget_data.json"
HUMOR_FILE = "humor_phrases.json"

class BudgetManager:
    def __init__(self):
        self.humor_phrases = self.load_humor_phrases()
        self.speech_style = "conversational"
        self.data = self.load_data()

    # ---------- ЗАГРУЗКА ШУТОК ----------
    def load_humor_phrases(self) -> Dict:
        if os.path.exists(HUMOR_FILE):
            try:
                with open(HUMOR_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print("⚠️ Ошибка загрузки humor_phrases.json, используются встроенные фразы")
                return self.get_default_humor_phrases()
        else:
            print("⚠️ Файл humor_phrases.json не найден, используются встроенные фразы")
            return self.get_default_humor_phrases()

    def get_default_humor_phrases(self) -> Dict:
        # Минимальный набор, если файл отсутствует
        return {
            "greeting": ["Привет!"],
            "goodbye": ["Пока!"],
            "no_expenses": ["Нет трат!"],
            "over_limit_critical": ["Критично!"],
            "over_limit": ["Превышение!"],
            "good_saving": ["Экономия!"],
            "category_warning": ["Предупреждение!"],
            "month_result_great": ["Отлично!"],
            "month_result_good": ["Хорошо!"],
            "month_result_ok": ["Неплохо!"],
            "month_result_bad": ["Плохо!"],
            "daily_check": ["Проверка!"],
            "fun_fact": ["Факт!"]
        }

    # ---------- СТИЛЬ ОБЩЕНИЯ ----------
    def set_speech_style(self, style: str):
        if style in ["official", "conversational", "humorous"]:
            self.speech_style = style
            self.save_data()
            welcome_messages = {
                "official": "Стиль общения изменен на официальный.",
                "conversational": "Ок, теперь буду по-человечески разговаривать.",
                "humorous": "🃏 Включаю режим балагура! Сейчас будут приколы!"
            }
            print(welcome_messages.get(style, ""))

    # ---------- ПОЛУЧЕНИЕ СЛУЧАЙНОЙ ФРАЗЫ ----------
    def get_random_humor(self, key: str, **kwargs) -> str:
        phrases = self.humor_phrases.get(key, [])
        if not phrases:
            return ""
        phrase = random.choice(phrases)
        try:
            return phrase.format(**kwargs)
        except KeyError:
            return phrase

    # ---------- ГЛАВНЫЙ МЕТОД ПОЛУЧЕНИЯ СООБЩЕНИЙ ----------
    def get_message(self, message_key: str, **kwargs) -> str:
        messages = {
            # Приветствия и прощания
            "welcome": {
                "official": "Добро пожаловать в Персональный Финансовый Помощник!",
                "conversational": "Привет! Давай разберемся с твоими финансами.",
                "humorous": None
            },
            "goodbye": {
                "official": "До свидания! Желаем успехов в накоплении капитала!",
                "conversational": "Пока! Будут вопросы - заходи, разберемся.",
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
                "humorous": "жизненно необходимые (без них никак)"
            },
            "category_temporary": {
                "official": "Временные расходы",
                "conversational": "текущие",
                "humorous": "хотелки и прихоти"
            },
            "category_unexpected": {
                "official": "Непредвиденные расходы",
                "conversational": "внезапные",
                "humorous": "сюрпризы судьбы (не всегда приятные)"
            },
            "category_estimated": {
                "official": "Предположительные расходы",
                "conversational": "плановые",
                "humorous": "запланированные удовольствия"
            },
            "category_daily": {
                "official": "Ежедневные покупки",
                "conversational": "повседневные",
                "humorous": "кофе-пирожки и прочая радость"
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
                "humorous": "Инструкция для чайников (в хорошем смысле):"
            },
            "style_changed": {
                "official": "Стиль общения изменен на {style_ru}.",
                "conversational": "Ок, теперь буду {style_ru}.",
                "humorous": "🃏 Врубаю {style_ru} режим! Погнали!"
            }
        }

        if self.speech_style == "humorous":
            if message_key in self.humor_phrases:
                return self.get_random_humor(message_key, **kwargs)
            msg_dict = messages.get(message_key, {})
            template = msg_dict.get("humorous")
            if template is not None:
                try:
                    return template.format(**kwargs)
                except KeyError:
                    return template

        msg_dict = messages.get(message_key, {})
        template = msg_dict.get(self.speech_style) or msg_dict.get("conversational", "")
        if not template:
            return ""
        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    # ---------- ФОРМАТИРОВАНИЕ ДЕНЕГ ----------
    def format_money(self, amount: int) -> str:
        if self.speech_style in ["conversational", "humorous"]:
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

    # ---------- ПАРСИНГ ДЕНЕГ ----------
    def parse_money(self, text: str) -> int:
        text = text.lower().strip().replace(" ", "")
        if text.endswith('к'):
            number = float(text[:-1]) * 1000
            return int(number)
        if 'тыс' in text:
            text = text.replace('тыс', '')
            number = float(text) * 1000
            return int(number)
        if '.' in text:
            number = float(text)
            return math.ceil(number)
        return int(float(text))

    # ---------- ЗАГРУЗКА ДАННЫХ ----------
    def load_data(self) -> Dict:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.speech_style = data.get('speech_style', 'conversational')
                    return data
            except (json.JSONDecodeError, IOError):
                print("⚠️ Ошибка чтения файла. Создаю новый профиль.")
                return self.setup_initial_budget()
        else:
            return self.setup_initial_budget()

    # ---------- СОХРАНЕНИЕ ДАННЫХ ----------
    def save_data(self):
        self.data['speech_style'] = self.speech_style
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
        print("✅ Данные сохранены")

    # ---------- НАЧАЛЬНАЯ НАСТРОЙКА ----------
    def setup_initial_budget(self) -> Dict:
        print("\n" + "="*60)
        print(self.get_message("welcome"))
        print("="*60)

        print("\n" + self.get_message("style_menu"))
        print(f"1. {self.get_message('style_official')}")
        print(f"2. {self.get_message('style_conversational')}")
        print(f"3. {self.get_message('style_humorous')}")

        style_choice = input("Ваш выбор (1/2/3): ").strip()
        if style_choice == "1":
            self.speech_style = "official"
        elif style_choice == "2":
            self.speech_style = "conversational"
        else:
            self.speech_style = "humorous"

        print(self.get_message("style_changed", style_ru=self.get_message(f"style_{self.speech_style}")))

        print("\n" + self.get_message("money_hint"))
        print("   • 30к = 30 000 рублей")
        print("   • 15 тыс = 15 000 рублей")
        print("   • 234.60 = 235 рублей (округляем вверх!)")
        print("="*60)

        try:
            income_text = input("\n💰 Введите ваш доход за этот месяц: ")
            income = self.parse_money(income_text)

            fund_text = input("🏦 Введите ваш общий фонд денег: ")
            total_fund = self.parse_money(fund_text)

            print("\n📊 Введите ваши расходы на этот месяц (по категориям):")
            print("-" * 40)

            fixed_text = input("🏠 Постоянные (аренда, коммуналка): ")
            fixed = self.parse_money(fixed_text)

            temp_text = input("🛍️ Временные (развлечения, одежда): ")
            temporary = self.parse_money(temp_text)

            unexp_text = input("🚨 Непредвиденные (на случай ЧП): ")
            unexpected = self.parse_money(unexp_text)

            est_text = input("📝 Предположительные (планы): ")
            estimated = self.parse_money(est_text)

            daily_text = input("☕ Ежедневные покупки (кофе, продукты): ")
            daily = self.parse_money(daily_text)

            today = datetime.now()
            days_in_month = calendar.monthrange(today.year, today.month)[1]
            days_left = days_in_month - today.day + 1

            total_expenses = fixed + temporary + unexpected + estimated + daily
            remaining_budget = income - total_expenses

            data = {
                "start_date": today.isoformat(),
                "current_month": today.strftime("%Y-%m"),
                "initial_income": income,
                "total_fund": total_fund,
                "remaining_budget": remaining_budget,
                "days_left": days_left,
                "daily_limit": self.calculate_daily_limit(remaining_budget, days_left),
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
                "monthly_summary": {},
                "speech_style": self.speech_style
            }

            self.show_initial_summary(data)
            return data

        except ValueError as e:
            print(f"❌ Ошибка: {e}")
            return self.setup_initial_budget()

    # ---------- ПОКАЗ НАЧАЛЬНОЙ СВОДКИ ----------
    def show_initial_summary(self, data: Dict):
        print("\n" + "="*60)
        print(self.get_message("status_title"))
        print("="*60)

        income_formatted = self.format_money(data['initial_income'])
        fund_formatted = self.format_money(data['total_fund'])
        remaining_formatted = self.format_money(data['remaining_budget'])
        limit_formatted = self.format_money(data['daily_limit'])

        if self.speech_style == "official":
            print(f"💰 Доход: {income_formatted} рублей")
            print(f"🏦 Общий фонд: {fund_formatted} рублей")
            total_expenses = sum(cat['planned'] for cat in data['expense_categories'].values())
            print(f"📊 Всего расходов: {self.format_money(total_expenses)} рублей")
            print(f"💵 Остаток на месяц: {remaining_formatted} рублей")
            print(f"📅 Дней в месяце осталось: {data['days_left']}")
            print(f"🎯 Дневной лимит: {limit_formatted} рублей в день")
        else:
            print(f"💰 Доход: {income_formatted}")
            print(f"🏦 Всего накоплено: {fund_formatted}")
            total_expenses = sum(cat['planned'] for cat in data['expense_categories'].values())
            print(f"📊 Запланировано расходов: {self.format_money(total_expenses)}")
            print(f"💵 Останется после расходов: {remaining_formatted}")
            print(f"📆 Дней до конца месяца: {data['days_left']}")
            print(f"🎯 Можно тратить в день: {limit_formatted}")

            if self.speech_style == "humorous" and data['remaining_budget'] < 0:
                print("\n😱 Ой, кажется, ты уже в минусе! Может, пересмотришь планы?")

        if data['remaining_budget'] < 0 and self.speech_style != "humorous":
            if self.speech_style == "official":
                print("\n⚠️ ВНИМАНИЕ: Расходы превышают доходы!")
                print("Рекомендуем пересмотреть временные и предположительные расходы.")
            else:
                print("\n⚠️ Ой! Расходы больше доходов. Давай урежем хотелки.")

    # ---------- РАСЧЕТ ДНЕВНОГО ЛИМИТА ----------
    def calculate_daily_limit(self, remaining_budget: int, days_left: int) -> int:
        if days_left <= 0:
            return 0
        return math.ceil(remaining_budget / days_left)

    # ---------- НАЗВАНИЕ КАТЕГОРИИ ----------
    def get_category_name(self, category: str) -> str:
        names = {
            "fixed": self.get_message("category_fixed"),
            "temporary": self.get_message("category_temporary"),
            "unexpected": self.get_message("category_unexpected"),
            "estimated": self.get_message("category_estimated"),
            "daily": self.get_message("category_daily")
        }
        return names.get(category, category)

    # ---------- ФИНАНСОВЫЙ СОВЕТ ----------
    def give_financial_advice(self, expense: int, daily_limit: int, category: str = None):
        print()
        if expense == 0:
            print(self.get_message("advice_good", saved=self.format_money(daily_limit)))
            return

        over_amount = expense - daily_limit
        over_formatted = self.format_money(over_amount)

        if expense > daily_limit * 2:
            print(self.get_message("advice_critical"))
        elif expense > daily_limit:
            print(self.get_message("advice_over_limit", over=over_formatted))
        elif expense > daily_limit * 0.7:
            print(self.get_message("advice_normal"))
        else:
            print(self.get_message("advice_good", saved=self.format_money(daily_limit - expense)))

        if self.speech_style == "humorous" and random.random() > 0.7:
            print(f"\n💡 {self.get_random_humor('fun_fact')}")

    # ---------- ДОБАВЛЕНИЕ РАСХОДА ----------
    def add_expense(self):
        print("\n" + "="*60)
        print(self.get_message("daily_check_start"))
        print("="*60)

        print("\n📊 Остатки по категориям:")
        for cat_name, cat_data in self.data['expense_categories'].items():
            emoji = self.get_category_emoji(cat_name)
            cat_title = self.get_category_name(cat_name)
            remaining = self.format_money(cat_data['remaining'])
            if self.speech_style == "official":
                print(f"  {emoji} {cat_title}: {remaining} рублей")
            else:
                print(f"  {emoji} {cat_title}: {remaining}")

        print("\n💡 Подсказка: можно вводить '30к', '234.60' (округлится)")

        print("\nВыберите категорию расхода:")
        print("1. 🏠 " + self.get_category_name("fixed"))
        print("2. 🛍️ " + self.get_category_name("temporary"))
        print("3. 🚨 " + self.get_category_name("unexpected"))
        print("4. 📝 " + self.get_category_name("estimated"))
        print("5. ☕ " + self.get_category_name("daily"))

        try:
            choice = input("Ваш выбор (1-5): ").strip()
            categories = ["fixed", "temporary", "unexpected", "estimated", "daily"]
            cat_index = int(choice) - 1

            if 0 <= cat_index < len(categories):
                category = categories[cat_index]

                amount_text = input(f"Введите сумму расхода: ")
                amount = self.parse_money(amount_text)

                amount_formatted = self.format_money(amount)
                if self.speech_style == "official":
                    print(f"💰 Сумма с округлением: {amount_formatted} рублей")
                else:
                    print(f"💰 Итого: {amount_formatted}")

                # Проверка лимита категории
                if amount > self.data['expense_categories'][category]['remaining']:
                    remaining = self.data['expense_categories'][category]['remaining']
                    remaining_formatted = self.format_money(remaining)
                    print(self.get_message("category_warning", remaining=remaining_formatted))
                    confirm = input("Продолжить? (да/нет): ").strip().lower()
                    if confirm != 'да':
                        print(self.get_message("goodbye"))
                        return

                # Обновляем данные
                self.data['expense_categories'][category]['spent'] += amount
                self.data['expense_categories'][category]['remaining'] -= amount
                self.data['remaining_budget'] -= amount

                description = input("Описание траты: ")

                cat_name_rus = self.get_category_name(category)
                print(self.get_message("expense_added", amount=amount_formatted, category=cat_name_rus))
                if description:
                    print(self.get_message("expense_description", description=description))

                self.data['expense_history'].append({
                    "date": datetime.now().isoformat(),
                    "category": category,
                    "amount": amount,
                    "description": description
                })

                # Пересчет дневного лимита
                if self.data['days_left'] > 0:
                    self.data['daily_limit'] = self.calculate_daily_limit(
                        self.data['remaining_budget'],
                        self.data['days_left']
                    )

                self.give_financial_advice(amount, self.data['daily_limit'], category)
                self.save_data()
                self.show_current_status()
            else:
                print("❌ Неверный выбор категории")

        except ValueError:
            print("❌ Ошибка: Введите корректное число")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

    def get_category_emoji(self, category: str) -> str:
        emojis = {
            "fixed": "🏠",
            "temporary": "🛍️",
            "unexpected": "🚨",
            "estimated": "📝",
            "daily": "☕"
        }
        return emojis.get(category, "📊")

    # ---------- ЕЖЕДНЕВНАЯ ПРОВЕРКА ----------
    def daily_check(self):
        today = datetime.now().date()
        today_str = today.isoformat()

        print("\n" + "="*60)
        print(self.get_message("daily_check_start"))
        print("="*60)

        if self.data.get('last_check_date') == today_str:
            print(self.get_message("already_checked"))
            return

        limit_formatted = self.format_money(self.data['daily_limit'])
        remaining_formatted = self.format_money(self.data['remaining_budget'])

        print(self.get_message("daily_limit_info", limit=limit_formatted))
        print(self.get_message("remaining_budget", remaining=remaining_formatted))

        print("\nКак прошел день?")
        print("1. 👍 Без трат")
        print("2. 💸 Были траты")
        print("3. ⏭️ Пропустить")

        choice = input("Ваш выбор (1-3): ").strip()

        if choice == '1':
            saved_today = self.data['daily_limit']
            self.data['saved_money'] = self.data.get('saved_money', 0) + saved_today
            self.data['remaining_budget'] -= saved_today

            saved_formatted = self.format_money(saved_today)
            print(self.get_message("no_expenses_today", saved=saved_formatted))

        elif choice == '2':
            self.add_expense()

        elif choice == '3':
            print(self.get_message("skip_check"))
            return
        else:
            print("❌ Неверный выбор")
            return

        self.data['days_left'] -= 1
        self.data['last_check_date'] = today_str
        self.save_data()

        if self.data['days_left'] <= 0:
            self.end_of_month()

    # ---------- КОНЕЦ МЕСЯЦА ----------
    def end_of_month(self):
        print("\n" + "="*60)

        unused_fixed = self.data['expense_categories']['fixed']['remaining']
        unused_temporary = self.data['expense_categories']['temporary']['remaining']
        unused_unexpected = self.data['expense_categories']['unexpected']['remaining']
        unused_estimated = self.data['expense_categories']['estimated']['remaining']
        unused_daily = self.data['expense_categories']['daily']['remaining']

        total_saved = (unused_fixed + unused_temporary + unused_unexpected +
                       unused_estimated + unused_daily + self.data.get('saved_money', 0))

        old_fund = self.data['total_fund']
        self.data['total_fund'] += total_saved

        budget_formatted = self.format_money(self.data['initial_income'])
        saved_formatted = self.format_money(total_saved)
        fund_formatted = self.format_money(self.data['total_fund'])

        if total_saved > old_fund * 0.2:
            encouragement_key = "encouragement_great"
        elif total_saved > old_fund * 0.1:
            encouragement_key = "encouragement_good"
        elif total_saved > 0:
            encouragement_key = "encouragement_ok"
        else:
            encouragement_key = "encouragement_bad"

        if self.speech_style == "humorous":
            encouragement = self.get_message(encouragement_key, saved=saved_formatted)
            print(encouragement)
        else:
            print(self.get_message("month_summary",
                  budget=budget_formatted,
                  saved=saved_formatted,
                  encouragement=self.get_message(encouragement_key)))

        if self.speech_style == "official":
            print(f"\n📊 Детализация экономии:")
            print(f"  🏠 Постоянные: {self.format_money(unused_fixed)} рублей")
            print(f"  🛍️ Временные: {self.format_money(unused_temporary)} рублей")
            print(f"  🚨 Непредвиденные: {self.format_money(unused_unexpected)} рублей")
            print(f"  📝 Предположительные: {self.format_money(unused_estimated)} рублей")
            print(f"  ☕ Ежедневные: {self.format_money(unused_daily)} рублей")
            print(f"  🌟 Ежедневная экономия: {self.format_money(self.data.get('saved_money', 0))} рублей")
            print(f"\n🏦 Общий фонд теперь: {fund_formatted} рублей")
        elif self.speech_style == "conversational":
            print(f"\n📊 По категориям сэкономил:")
            print(f"  🏠 Обязательные: {self.format_money(unused_fixed)}")
            print(f"  🛍️ Текущие: {self.format_money(unused_temporary)}")
            print(f"  🚨 Внезапные: {self.format_money(unused_unexpected)}")
            print(f"  📝 Плановые: {self.format_money(unused_estimated)}")
            print(f"  ☕ Ежедневные: {self.format_money(unused_daily)}")
            print(f"  🌟 С повседневных: {self.format_money(self.data.get('saved_money', 0))}")
            print(f"\n🏦 Всего накоплено: {fund_formatted}")
        else:
            print(f"\n📊 Куда ушли деньги (точнее, не ушли):")
            print(f"  🏠 На обязаловке сэкономил: {self.format_money(unused_fixed)}")
            print(f"  🛍️ Хотелки недокупил: {self.format_money(unused_temporary)}")
            print(f"  🚨 Форс-мажор не случился: {self.format_money(unused_unexpected)}")
            print(f"  📝 Планы перенес: {self.format_money(unused_estimated)}")
            print(f"  ☕ Кофе не допил: {self.format_money(unused_daily)}")
            print(f"  🌟 В ежедневке накопил: {self.format_money(self.data.get('saved_money', 0))}")
            print(f"\n🏦 Итого в кубышке: {fund_formatted}")

            if total_saved > 0:
                print(f"\n🎉 Плюс {saved_formatted} к пенсии! Так держать!")

        month_key = self.data['current_month']
        self.data['monthly_summary'][month_key] = {
            "saved": total_saved,
            "total_fund": self.data['total_fund']
        }

        print("\n🔄 Хотите настроить новый месяц?")
        choice = input("(да/нет): ").strip().lower()

        if choice == 'да':
            self.save_data()
            self.data = self.setup_initial_budget()
        else:
            print(self.get_message("goodbye"))

    # ---------- ПОКАЗ ТЕКУЩЕГО СТАТУСА ----------
    def show_current_status(self):
        print("\n" + "="*60)
        print(self.get_message("status_title"))
        print("="*60)

        fund_formatted = self.format_money(self.data['total_fund'])
        print(self.get_message("total_fund", amount=fund_formatted))

        remaining_formatted = self.format_money(self.data['remaining_budget'])
        limit_formatted = self.format_money(self.data['daily_limit'])

        if self.speech_style == "official":
            print(f"\n📅 БЮДЖЕТ МЕСЯЦА:")
            print(f"  💵 Остаток: {remaining_formatted} рублей")
            print(f"  📆 Дней осталось: {self.data['days_left']}")
            print(f"  🎯 Дневной лимит: {limit_formatted} рублей")
        else:
            print(f"\n📅 МЕСЯЦ:")
            print(f"  💵 Остаток: {remaining_formatted}")
            print(f"  📆 Осталось дней: {self.data['days_left']}")
            print(f"  🎯 Можно тратить в день: {limit_formatted}")

        print(f"\n📊 КАТЕГОРИИ:")
        for cat_name, cat_data in self.data['expense_categories'].items():
            emoji = self.get_category_emoji(cat_name)
            cat_title = self.get_category_name(cat_name)

            if self.speech_style == "official":
                percent = (cat_data['spent'] / cat_data['planned'] * 100) if cat_data['planned'] > 0 else 0
                planned_f = self.format_money(cat_data['planned'])
                spent_f = self.format_money(cat_data['spent'])
                remaining_f = self.format_money(cat_data['remaining'])
                print(self.get_message("category_status",
                      category=f"{emoji} {cat_title}",
                      planned=planned_f,
                      spent=spent_f,
                      percent=f"{percent:.1f}",
                      remaining=remaining_f))
            else:
                remaining_f = self.format_money(cat_data['remaining'])
                planned_f = self.format_money(cat_data['planned'])
                print(self.get_message("category_status",
                      category=f"{emoji} {cat_title}",
                      remaining=remaining_f,
                      planned=planned_f))

        saved = self.data.get('saved_money', 0)
        if saved > 0:
            saved_formatted = self.format_money(saved)
            if self.speech_style == "official":
                print(f"\n💰 НАКОПЛЕНО ЗА МЕСЯЦ: {saved_formatted} рублей")
            else:
                print(f"\n💰 Накопил за месяц: {saved_formatted}")

        if self.data['expense_history']:
            if self.speech_style == "official":
                print(f"\n📋 ПОСЛЕДНИЕ ОПЕРАЦИИ:")
            else:
                print(f"\n📋 ПОСЛЕДНИЕ ТРАТЫ:")

            for expense in self.data['expense_history'][-3:]:
                date = datetime.fromisoformat(expense['date']).strftime("%d.%m")
                emoji = self.get_category_emoji(expense['category'])
                amount_f = self.format_money(expense['amount'])

                if self.speech_style == "official":
                    print(f"  {date} {emoji} {amount_f} руб. - {expense['description']}")
                else:
                    print(f"  {date} {emoji} {amount_f} - {expense['description']}")

    # ---------- ГЛАВНЫЙ ЦИКЛ ----------
    def run(self):
        print("\n" + "="*60)
        print(self.get_message("welcome"))
        print("="*60)

        while True:
            print("\n📌 ГЛАВНОЕ МЕНЮ:")
            print("1. 🌅 Ежедневная проверка")
            print("2. 📝 Добавить расход")
            print("3. 📊 Показать текущее состояние")
            print("4. 💰 Показать общий фонд")
            print("5. 📈 История по месяцам")
            print("6. 🗣️ Сменить стиль общения")
            print("7. ❌ Выход")

            choice = input("\nВаш выбор: ").strip()

            if choice == '1':
                self.daily_check()
            elif choice == '2':
                self.add_expense()
            elif choice == '3':
                self.show_current_status()
            elif choice == '4':
                fund_formatted = self.format_money(self.data['total_fund'])
                print(self.get_message("total_fund", amount=fund_formatted))
            elif choice == '5':
                print("\n" + "="*60)
                print(self.get_message("history_title"))
                print("="*60)
                for month, summary in self.data['monthly_summary'].items():
                    saved_f = self.format_money(summary['saved'])
                    fund_f = self.format_money(summary['total_fund'])
                    print(self.get_message("history_item",
                          month=month,
                          saved=saved_f,
                          fund=fund_f))
            elif choice == '6':
                print("\n" + self.get_message("style_menu"))
                print(f"1. {self.get_message('style_official')}")
                print(f"2. {self.get_message('style_conversational')}")
                print(f"3. {self.get_message('style_humorous')}")
                style_choice = input("Ваш выбор (1/2/3): ").strip()
                if style_choice == "1":
                    self.set_speech_style("official")
                elif style_choice == "2":
                    self.set_speech_style("conversational")
                elif style_choice == "3":
                    self.set_speech_style("humorous")
                else:
                    print("❌ Неверный выбор")
            elif choice == '7':
                print(self.get_message("goodbye"))
                self.save_data()
                break
            else:
                print("❌ Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    manager = BudgetManager()
    manager.run()
