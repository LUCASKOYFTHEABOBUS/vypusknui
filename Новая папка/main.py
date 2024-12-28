import telebot
import matplotlib.pyplot as plt

TOKEN = '7460982002:AAGrOuS6H9g2Mx2ga0jzLRBQodsJvJTTL-4'
bot = telebot.TeleBot(TOKEN)

# Вопросы для викторин
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

# Хранение данных пользователя
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Инициализация данных пользователя
    user_data[message.chat.id] = {"score": 0, "quiz_name": None, "question_index": 0, "total_questions": 0, "answers": []}
    
    # Создаем клавиатуру с кнопками для выбора викторины
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for quiz_name in quizzes.keys():
        markup.add(telebot.types.KeyboardButton(quiz_name))
    
    bot.send_message(
        message.chat.id,
        "Привет! Выбери викторину, чтобы начать:\n- Природа\n- История",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text in quizzes.keys())
def select_quiz(message):
    quiz_name = message.text
    user_data[message.chat.id]["quiz_name"] = quiz_name
    user_data[message.chat.id]["total_questions"] = len(quizzes[quiz_name])
    user_data[message.chat.id]["question_index"] = 0
    user_data[message.chat.id]["score"] = 0
    user_data[message.chat.id]["answers"] = []

    bot.send_message(
        message.chat.id,
        f"Ты выбрал викторину: {quiz_name}! Сейчас начнем...",
    )
    ask_question(message.chat.id)

def ask_question(chat_id):
    user = user_data[chat_id]
    quiz_name = user["quiz_name"]
    question_index = user["question_index"]
    
    if question_index < len(quizzes[quiz_name]):
        question = quizzes[quiz_name][question_index]
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for option in question["options"]:
            markup.add(telebot.types.KeyboardButton(option))
        
        bot.send_message(chat_id, question["question"], reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(chat_id, check_answer)
    else:
        send_statistics(chat_id)
        user_data[chat_id] = {"score": 0, "quiz_name": None, "question_index": 0, "total_questions": 0, "answers": []}

def check_answer(message):
    chat_id = message.chat.id
    user = user_data[chat_id]
    quiz_name = user["quiz_name"]
    question_index = user["question_index"]
    
    selected_answer = message.text
    correct_answer = quizzes[quiz_name][question_index]["answer"]
    
    if selected_answer == correct_answer:
        user["score"] += 1
        user["answers"].append(1)  # Правильный ответ
        bot.send_message(chat_id, "Правильно!")
    else:
        user["answers"].append(0)  # Неправильный ответ
        bot.send_message(chat_id, f"Неправильно. Правильный ответ: {correct_answer}")
    
    user["question_index"] += 1
    ask_question(chat_id)

def send_statistics(chat_id):
    user = user_data[chat_id]
    score = user["score"]
    total_questions = user["total_questions"]
    answers = user["answers"]

    # Создаем линейную диаграмму
    plt.figure(figsize=(8, 4))
    plt.plot(range(1, total_questions + 1), answers, marker='o', linestyle='-', color='blue')
    plt.ylim(-0.1, 1.1)
    plt.xticks(range(1, total_questions + 1))
    plt.yticks([0, 1], ["Неправильно", "Правильно"])
    plt.xlabel("Вопрос")
    plt.ylabel("Результат")
    plt.title("Результаты викторины")
    plt.grid(True)

    # Сохраняем изображение и отправляем его пользователю
    image_path = f"statistics_{chat_id}.png"
    plt.savefig(image_path)
    plt.close()
    
    performance = (score / total_questions) * 100
    if performance == 100:
        feedback = "Отличный результат! Ты ответил на все вопросы правильно!"
    elif performance >= 70:
        feedback = "Отлично! Ты справился с большинством вопросов!"
    elif performance >= 50:
        feedback = "Неплохо! Но есть куда расти!"
    else:
        feedback = "Не расстраивайся! Попробуй снова, чтобы улучшить результат."

    with open(image_path, 'rb') as image_file:
        bot.send_photo(chat_id, image_file)
    
    bot.send_message(chat_id, f"Викторина завершена! Ты набрал {score} из {total_questions}.\n{feedback}")

bot.polling()
