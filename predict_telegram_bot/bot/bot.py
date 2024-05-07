import telebot
from telebot import types
from django.conf import settings
from predict_telegram_bot.user_service import TelegramUserManager
from predict_telegram_bot.log.bot_log import BotLogger

bot = telebot.TeleBot(settings.TELEGRAM_TOKEN, parse_mode='HTML')

# Хранилище для данных регистрации и состояний
registration_data = {}
user_states = {}
sent_messages = []  # для удаления сообщений (в процессе)
msgs = {}
logger = BotLogger('bot.log')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        logger.log_info(f"Команда /start вызвана пользователем {message.from_user.username}")
        start_msg = bot.reply_to(message, f"""\
Добро пожаловать, {message.from_user.username}! Я PredictBot. 
Я здесь, чтобы помочь вам с прогнозированием вашей учебы. 
Вы можете узнать, что я умею, с помощью команды /help.""")
        user_states[message.from_user.id] = "start"
        get_status_user(message)
    except Exception as e:
        logger.log_error(f"Произошла ошибка при выполнении команды /start: {str(e)}")


@bot.message_handler(commands=['status'])
def get_status_user(message):
    try:
        user = TelegramUserManager.check_auth(message.from_user.id)
        if user is False:
            status_msg = bot.send_message(message.from_user.id, f"""\
Поскольку вы не зарегистрированы, мне нужно собрать некоторую информацию о вас.
Эта информация будет отправлена администратору для обработки.
После подтверждения вашей информации вы сможете воспользоваться всей моей функциональностью.
            """)
            regist_msg = bot.send_message(message.from_user.id, f"""Начнем регистрацию. 
Пожалуйста, отправьте мне свой студенческий номер.""")
            user_states[message.chat.id] = "stud_id"
        elif user and user.status == 'W':
            start_msg = bot.send_message(message.from_user.id, "Ожидайте подтверждения")
            sent_messages.append(start_msg)
            return
        else:
            start_msg = bot.send_message(message.from_user.id,
                                         "Вы уже зарегистрированы. Ознакомьтесь с командами с помощью /help")
            sent_messages.append(start_msg)
            return
    except Exception as e:
        logger.log_error(f"Произошла ошибка при обработке команды /status: {str(e)}")


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'stud_id')
def get_stud_id(message):
    try:
        registration_data[message.from_user.id] = {
            "stud_id": message.text}  # Проверять чтобы записывался только номер без пробелов и тд
        dialog_msg = bot.send_message(message.from_user.id, f"""Понял!""")
        logger.log_info(f"Пользователь ввел студенческий номер.")
        user_states[message.from_user.id] = "name"
        regist_msg = bot.send_message(message.chat.id, f"""Пожалуйста, отправьте мне свое полное имя.""")
    except Exception as e:
        logger.log_error(f"Произошла ошибка при обработке сообщения о студенческом номере: {str(e)}")


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'name')
def get_full_name(message):
    try:
        registration_data[message.chat.id]["name"] = message.text
        dialog_msg = bot.send_message(message.from_user.id, f"""Понял!""")
        logger.log_info(f"Пользователь ввел полное имя.")
        user_states[message.from_user.id] = "group"
        regist_msg = bot.send_message(message.from_user.id, f"""Отправьте мне название вашей группы.""")
    except Exception as e:
        logger.log_error(f"Произошла ошибка при обработке сообщения о полном имени: {str(e)}")


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'group')
def get_group_name(message):
    try:
        registration_data[message.from_user.id]["group"] = message.text
        dialog_msg = bot.send_message(message.from_user.id,
                                      f"""Да! Вы {message.from_user.username}!""")
        logger.log_info(f"Пользователь ввел название группы.")
        user_states[message.from_user.id] = None  # сброс состояния
        final_msg = bot.send_message(message.from_user.id, f"""Все готово!""")
        TelegramUserManager.register_user(message.from_user.id, message.from_user.username, registration_data)
        bot.send_message(
            message.chat.id,
            f"Спасибо! Регистрация завершена. Ваша информация:\n"
            f"Студенческий номер: {registration_data[message.from_user.id]['stud_id']}\n"
            f"Полное Имя: {registration_data[message.from_user.id]['name']}\n"
            f"Группа: {registration_data[message.from_user.id]['group']}")
        logger.log_info(f"Регистрация успешно завершена.")
    except Exception as e:
        logger.log_error(f"Произошла ошибка при обработке сообщения о названии группы: {str(e)}")


@bot.message_handler(commands=['me'])
def send_info_about_user(message):
    try:  # доработать, если пользователь сразу вызвал /me после заполнения
        logger.log_info(f"Команда /me вызвана пользователем {message.from_user.username}")
        chat_id = message.chat.id
        info = TelegramUserManager.get_student_info(chat_id)
        if info:
            # Отправка информации о пользователе
            response = "Информация о пользователе:\n"
            response += f"Студенческий билет: {info['stud_id']}\n"
            response += f"Полное имя: {info['name']}\n"
            response += f"Группа: {info['group']}\n"

        else:
            response = "К сожалению, нет информации о пользователе."
        bot.send_message(chat_id, response)
        logger.log_info(f"Отправлена информация о пользователе: {response}")
        markup = types.InlineKeyboardMarkup()
        get_predicts_button = types.InlineKeyboardButton("Предсказания", callback_data='get_predicts')
        get_study_points = types.InlineKeyboardButton("Предметы и Баллы", callback_data='get_points_subjects')
        markup.add(get_predicts_button, get_study_points)
        bot.send_message(chat_id, 'Вы можете узнать следующую информацию', reply_markup=markup)
    except Exception as e:
        logger.log_error(f"Произошла ошибка при выполнении команды /me: {str(e)}")


@bot.callback_query_handler(func=lambda call: call.data == 'get_points_subjects')
def get_points_subjects(call):
    markup = types.InlineKeyboardMarkup()
    get_points_button = types.InlineKeyboardButton("Баллы за предметы", callback_data='get_points_subject')
    get_study_exam = types.InlineKeyboardButton("Баллы за экзамены", callback_data='get_points_exam')
    get_study_subject = types.InlineKeyboardButton("Предметы", callback_data='get_subject')
    markup.add(get_points_button, get_study_subject, get_study_exam)
    message = call.message
    chat_id = message.chat.id
    bot.send_message(chat_id, f'Вы можете получить следующую информацию', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_predicts')
def get_predicts(call):
    try:
        logger.log_info(f"Кнопка 'Предсказания' нажата пользователем {call.from_user.username}")
        chat_id = call.message.chat.id
        markup = types.InlineKeyboardMarkup()
        get_predict_exam_button = types.InlineKeyboardButton("Предсказание по экзамену",
                                                             callback_data='get_predict_exam')
        get_predict_points_button = types.InlineKeyboardButton("Предсказание по баллам",
                                                               callback_data='get_predict_points')
        markup.add(get_predict_exam_button, get_predict_points_button)
        bot.send_message(chat_id, f'Вы можете предсказать следующую информацию', reply_markup=markup)
    except Exception as e:
        logger.log_error(f"Произошла ошибка при обработке нажатия кнопки 'Предсказания': {str(e)}")


@bot.callback_query_handler(func=lambda call: call.data == 'get_predict_exam')
def get_predict_exam(call):
    try:
        logger.log_info(f"Кнопка 'Предсказание результатов экзаменов' нажата пользователем {call.from_user.username}")
        message = call.message
        chat_id = message.chat.id
        exam_info = TelegramUserManager.get_student_exam_results(chat_id)
        if exam_info:
            exam_response = "Предсказание результатов экзаменов:\n"
            for exam in exam_info:
                exam_response += f"Предмет: <b>{exam['subject']}</b>\n Предсказание: <b>{exam['exam_predict']}</b>\n "
        else:
            exam_response = "Нет данных о результатах экзаменов."
        bot.send_message(message.chat.id, exam_response)
    except Exception as e:
        logger.log_error(
            f"Произошла ошибка при обработке нажатия кнопки 'Предсказание результатов экзаменов': {str(e)}")


@bot.callback_query_handler(func=lambda call: call.data == 'get_predict_points')
def get_predict_points(call):
    try:
        logger.log_info(f"Кнопка 'Предсказание баллов за предметы' нажата пользователем {call.from_user.username}")
        message = call.message
        chat_id = message.chat.id
        points = TelegramUserManager.get_student_points(chat_id)
        if points:
            response = "Предсказание баллов за предметы:\n"
            for point in points:
                response += f"Предмет: <b>{point['subject']}</b>\n Предсказание: <b>{point['points_predict']}</b>\n"
        else:
            response = "Нет данных о баллах за предметы."
        bot.send_message(chat_id, response)
    except Exception as e:
        logger.log_error(f"Произошла ошибка при обработке нажатия кнопки 'Предсказание баллов за предметы': {str(e)}")


@bot.callback_query_handler(func=lambda call: call.data == 'get_points_subject')
def get_points_subject(call):
    try:
        logger.log_info(f"Кнопка 'Баллы за предметы' нажата пользователем {call.from_user.username}")
        message = call.message
        chat_id = message.chat.id
        points = TelegramUserManager.get_student_points(chat_id)
        if points:
            response = "Баллы за предметы:\n"
            for point in points:
                response += f"Предмет: <b>{point['subject']}</b>\n Балл: <b>{point['score']}</b>\n Посещение:" \
                            f"<b>{point['attending']}</b>\n"
        else:
            response = "Нет данных о баллах за предметы."
        bot.send_message(chat_id, response)
    except Exception as e:
        logger.log_error(f"Произошла ошибка при обработке нажатия кнопки 'Баллы за предметы': {str(e)}")


@bot.callback_query_handler(func=lambda call: call.data == 'get_points_exam')
def get_points_exam(call):
    try:
        logger.log_info(f"Кнопка 'Баллы за экзамены' нажата пользователем {call.from_user.username}")
        message = call.message
        chat_id = message.chat.id
        exam_info = TelegramUserManager.get_student_exam_results(chat_id)
        if exam_info:
            exam_response = "Результаты экзаменов:\n"
            for exam in exam_info:
                exam_response += f"Предмет: <b>{exam['subject']}</b>\n Итоговый балл: <b>{exam['final_score']}</b>\n "

        else:
            exam_response = "Нет данных о результатах экзаменов."
        bot.send_message(message.chat.id, exam_response)
    except Exception as e:
        logger.log_error(f"Произошла ошибка при обработке нажатия кнопки 'Баллы за экзамены': {str(e)}")


@bot.callback_query_handler(func=lambda call: call.data == 'get_subject')
def get_subject(call):
    try:
        logger.log_info(f"Кнопка 'Предметы' нажата пользователем {call.from_user.username}")
        message = call.message
        chat_id = message.chat.id
        subjects = TelegramUserManager.get_subjects_by_specialty(chat_id)
        if subjects:
            subject_list = "\n".join([subject.subject_name for subject in subjects])
            bot.send_message(chat_id, f"Предметы вашей специальности:\n{subject_list}")
        else:
            bot.send_message(chat_id, "Предметы вашей специальности не найдены.")
    except Exception as e:
        logger.log_error(f"Произошла ошибка при обработке нажатия кнопки 'Предметы': {str(e)}")


@bot.message_handler(commands=['help'])
def send_help(message):
    try:
        logger.log_info(f"Команда /help вызвана пользователем {message.from_user.username}")
        chat_id = message.chat.id
        markup = types.InlineKeyboardMarkup()
        support_button = types.InlineKeyboardButton("Поддержка", callback_data='call_support')
        markup.add(support_button)
        bot.send_message(chat_id, 'Список команд: \n /me \n /start \n /status', reply_markup=markup)
    except Exception as e:
        logger.log_error(f"Произошла ошибка при выполнении команды /help: {str(e)}")


@bot.callback_query_handler(func=lambda call: call.data == 'call_support')
def call_support(call):
    try:
        logger.log_info(f"Кнопка 'Поддержка' нажата пользователем {call.from_user.username}")
        message = call.message
        chat_id = message.chat.id
        bot.send_message(chat_id, f'Запрос в поддержку отправлен')
    except Exception as e:
        logger.log_error(f"Произошла ошибка при обработке нажатия кнопки 'Поддержка': {str(e)}")
