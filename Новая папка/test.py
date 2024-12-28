import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import matplotlib.pyplot as plt

TOKEN = '7460982002:AAGrOuS6H9g2Mx2ga0jzLRBQodsJvJTTL-4'
bot = telebot.TeleBot(TOKEN)

# Викторины
quizzes = {
    "Природа": [
        {"question": "Какой самый большой океан на Земле?", "options": ["Тихий", "Атлантический", "Индийский", "Северный Ледовитый"], "answer": "Тихий"},
        {"question": "Какое самое высокое дерево?", "options": ["Баобаб", "Секвойя", "Кедр", "Дуб"], "answer": "Секвойя"},
    ],
    "История": [
        {"question": "Кто написал 'Война и мир'?", "options": ["Толстой", "Достоевский", "Пушкин", "Чехов"], "answer": "Толстой"},
        {"question": "Какое событие началось в 1939 году?", "options": ["Первая мировая", "Вторая мировая", "Октябрьская революция", "Космическая гонка"], "answer": "Вторая мировая"},
    ]
}

# Хранение данных
user_data = {}  # Для личных викторин
games = {}      # Для групповых викторин

@bot.message_handler(commands=['start'])
def start_command(message):
    if message.chat.type == "private":
        user_data[message.chat.id] = {"score": 0, "quiz_name": None, "question_index": 0, "total_questions": 0, "answers": []}
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        for quiz_name in quizzes.keys():
            markup.add(KeyboardButton(quiz_name))
        bot.send_message(message.chat.id, "Привет! Выбери викторину, чтобы начать:", reply_markup=markup)
    else:
        bot.send_message(
            message.chat.id,
            "Привет! Вот как использовать бота в группе:\n"
            "1. Создайте викторину с помощью команды /createparty.\n"
            "2. Участники могут присоединиться с помощью команды /joinparty.\n"
            "3. Запустите викторину с помощью команды /startparty.\n\n"
            "Создатель викторины также участвует в игре!"
        )

@bot.message_handler(commands=['createparty'])
def create_party(message):
    if message.chat.type != "private":
        chat_id = message.chat.id
        if chat_id not in games:
            games[chat_id] = {
                "creator": message.from_user.id,
                "players": {message.from_user.id: {"score": 0, "answers": []}},
                "quiz_name": None,
                "current_question": 0,
                "state": "waiting",
                "answered": set()
            }
            bot.reply_to(message, "Викторина создана! Другие участники могут присоединиться с помощью команды /joinparty.")
        else:
            bot.reply_to(message, "Викторина уже создана.")
    else:
        bot.reply_to(message, "Эта команда доступна только в группах.")

@bot.message_handler(commands=['joinparty'])
def join_party(message):
    if message.chat.type != "private":
        chat_id = message.chat.id
        if chat_id in games and games[chat_id]["state"] == "waiting":
            user_id = message.from_user.id
            if user_id not in games[chat_id]["players"]:
                games[chat_id]["players"][user_id] = {"score": 0, "answers": []}
                bot.reply_to(message, f"{message.from_user.first_name} присоединился к викторине!")
            else:
                bot.reply_to(message, "Вы уже присоединились.")
        else:
            bot.reply_to(message, "Викторина не создана или уже началась.")
    else:
        bot.reply_to(message, "Эта команда доступна только в группах.")

@bot.message_handler(commands=['startparty'])
def start_party(message):
    if message.chat.type != "private":
        chat_id = message.chat.id
        user_id = message.from_user.id

        if chat_id not in games:
            bot.reply_to(message, "Викторина не создана. Сначала используйте /createparty.")
            return

        game = games[chat_id]

        if game["state"] != "waiting":
            bot.reply_to(message, "Викторина уже началась!")
            return

        if game["creator"] != user_id:
            bot.reply_to(message, "Только создатель викторины может её начать.")
            return

        if len(game["players"]) < 2:
            bot.reply_to(message, "Недостаточно игроков. Присоединитесь с помощью /joinparty.")
            return

        bot.send_message(chat_id, "Викторина начинается!")
        game["state"] = "active"
        game["quiz_name"] = "Природа"
        game["current_question"] = 0
        ask_group_question(chat_id)
    else:
        bot.reply_to(message, "Эта команда доступна только в группах.")

def ask_group_question(chat_id):
    game = games[chat_id]
    quiz_name = game["quiz_name"]
    current_question = game["current_question"]

    if current_question < len(quizzes[quiz_name]):
        question = quizzes[quiz_name][current_question]
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for option in question["options"]:
            markup.add(KeyboardButton(option))

        game["answered"] = set()  # Очистить список ответивших игроков
        bot.send_message(chat_id, question["question"], reply_markup=markup)
        game["current_question"] += 1
    else:
        finish_group_quiz(chat_id)

@bot.message_handler(func=lambda message: message.chat.type != "private" and message.chat.id in games and games[message.chat.id]["state"] == "active")
def check_group_answer(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    game = games[chat_id]

    if user_id not in game["players"]:
        bot.reply_to(message, "Вы не участвуете в викторине. Присоединитесь с помощью /joinparty.")
        return

    if user_id in game["answered"]:
        bot.reply_to(message, "Вы уже ответили на этот вопрос.")
        return

    quiz_name = game["quiz_name"]
    current_question = game["current_question"] - 1
    selected_answer = message.text
    correct_answer = quizzes[quiz_name][current_question]["answer"]

    game["answered"].add(user_id)  # Добавить игрока в список ответивших

    if selected_answer == correct_answer:
        game["players"][user_id]["score"] += 1
        bot.send_message(chat_id, f"{message.from_user.first_name} ответил правильно!")
    else:
        bot.send_message(chat_id, f"{message.from_user.first_name} ошибся. Правильный ответ: {correct_answer}")

    if len(game["answered"]) == len(game["players"]):
        ask_group_question(chat_id)

def finish_group_quiz(chat_id):
    game = games[chat_id]
    results = [(player_id, data["score"]) for player_id, data in game["players"].items()]
    results.sort(key=lambda x: x[1], reverse=True)

    result_message = "Результаты викторины:\n"
    for rank, (player_id, score) in enumerate(results, start=1):
        player_name = bot.get_chat_member(chat_id, player_id).user.first_name
        result_message += f"{rank}. {player_name}: {score} баллов\n"

    bot.send_message(chat_id, result_message)
    del games[chat_id]

bot.polling()
