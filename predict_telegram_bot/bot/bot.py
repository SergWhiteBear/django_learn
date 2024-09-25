import telebot
from telebot import types
from telebot.handler_backends import State, StatesGroup
from django.conf import settings
from predict_telegram_bot.user_service import TelegramUserManager
from predict_telegram_bot.log.bot_log import BotLogger

bot = telebot.TeleBot(settings.TELEGRAM_TOKEN, parse_mode='HTML')
logger = BotLogger('bot.log')


# Определение состояний
class UserRegistrationState(StatesGroup):
    stud_id = State()
    name = State()
    group = State()


# Хранилище данных регистрации
registration_data = {}


# Вспомогательная функция для отправки сообщений
def send_custom_message(chat_id, text, markup=None):
    bot.send_message(chat_id, text, reply_markup=markup)


# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        logger.log_info(f"Команда /start вызвана пользователем {message.from_user.username}")
        send_custom_message(message.chat.id, f"""
Добро пожаловать, {message.from_user.username}! Я PredictBot. 
Я здесь, чтобы помочь вам с прогнозированием вашей учебы. 
Вы можете узнать, что я умею, с помощью команды /help.
""")
        bot.set_state(message.from_user.id, None)  # сброс состояния
        get_status_user(message)
    except Exception as e:
        logger.log_error(f"Ошибка при выполнении команды /start: {str(e)}")
        send_custom_message(message.chat.id, "Произошла ошибка. Попробуйте еще раз.")


# Команда /status
@bot.message_handler(commands=['status'])
def get_status_user(message):
    try:
        user = TelegramUserManager.check_auth(message.from_user.id)
        if not user:
            send_custom_message(message.chat.id, """
Поскольку вы не зарегистрированы, мне нужно собрать некоторую информацию о вас.
Эта информация будет отправлена администратору для обработки.
После подтверждения вашей информации вы сможете воспользоваться всей моей функциональностью.
""")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Да!", callback_data='get_confirm'),
                       types.InlineKeyboardButton("Нет:(", callback_data='get_cancel'))
            send_custom_message(message.chat.id, 'Приступим к регистрации?', markup)
        elif user.status == 'W':
            send_custom_message(message.chat.id, "Ожидайте подтверждения")
        else:
            send_custom_message(message.chat.id, "Вы уже зарегистрированы. Ознакомьтесь с командами с помощью /help")
    except Exception as e:
        logger.log_error(f"Ошибка при обработке команды /status: {str(e)}")
        send_custom_message(message.chat.id, "Произошла ошибка. Попробуйте еще раз.")


# Обработка нажатия кнопки "Да" для регистрации
@bot.callback_query_handler(func=lambda call: call.data == 'get_confirm')
def get_confirm(call):
    try:
        user = TelegramUserManager.check_auth(call.from_user.id)
        if user and user.status == 'R':
            send_custom_message(call.message.chat.id, "Вы уже зарегистрированы.")
        elif user and user.status == 'W':
            send_custom_message(call.message.chat.id, "Ожидайте проверки.")
        else:
            send_custom_message(call.message.chat.id,
                                "Начнем регистрацию. Пожалуйста, отправьте мне свой студенческий номер.")
            bot.set_state(call.from_user.id, UserRegistrationState.stud_id, call.message.chat.id)
    except Exception as e:
        logger.log_error(f"Ошибка при обработке регистрации: {str(e)}")
        send_custom_message(call.message.chat.id, "Произошла ошибка. Попробуйте еще раз.")


# Обработка нажатия кнопки "Нет"
@bot.callback_query_handler(func=lambda call: call.data == 'get_cancel')
def get_cancel(call):
    send_custom_message(call.message.chat.id, "Жаль. Если передумаете, можете начать регистрацию снова.")


# Получение студенческого номера
@bot.message_handler(state=UserRegistrationState.stud_id)
def get_stud_id(message):
    try:
        if not message.text.isdigit():
            send_custom_message(message.chat.id, "Пожалуйста, введите корректный студенческий номер.")
            return
        registration_data[message.from_user.id] = {"stud_id": message.text}
        send_custom_message(message.chat.id, "Понял! Пожалуйста, отправьте мне свое полное имя.")
        bot.set_state(message.from_user.id, UserRegistrationState.name, message.chat.id)
    except Exception as e:
        logger.log_error(f"Ошибка при вводе студенческого номера: {str(e)}")
        send_custom_message(message.chat.id, "Произошла ошибка. Попробуйте еще раз.")


# Получение полного имени
@bot.message_handler(state=UserRegistrationState.name)
def get_full_name(message):
    try:
        registration_data[message.chat.id]["name"] = message.text
        send_custom_message(message.chat.id, "Понял! Отправьте мне название вашей группы.")
        bot.set_state(message.from_user.id, UserRegistrationState.group, message.chat.id)
    except Exception as e:
        logger.log_error(f"Ошибка при вводе полного имени: {str(e)}")
        send_custom_message(message.chat.id, "Произошла ошибка. Попробуйте еще раз.")


# Получение названия группы
@bot.message_handler(state=UserRegistrationState.group)
def get_group_name(message):
    try:
        registration_data[message.from_user.id]["group"] = message.text
        send_custom_message(message.chat.id, f"Регистрация завершена! Вы {message.from_user.username}.")
        TelegramUserManager.register_user(
            message.from_user.id,
            message.from_user.username,
            registration_data[message.from_user.id]
        )
        send_custom_message(message.chat.id, f"""
Спасибо за регистрацию. Ваша информация:
Студенческий номер: {registration_data[message.from_user.id]['stud_id']}
Полное Имя: {registration_data[message.from_user.id]['name']}
Группа: {registration_data[message.from_user.id]['group']}
""")
        logger.log_info(f"Пользователь {message.from_user.username} успешно зарегистрирован.")
        bot.set_state(message.from_user.id, None, message.chat.id)  # сброс состояния
    except Exception as e:
        logger.log_error(f"Ошибка при завершении регистрации: {str(e)}")
        send_custom_message(message.chat.id, "Произошла ошибка. Попробуйте еще раз.")


# Команда /me - информация о пользователе
@bot.message_handler(commands=['me'])
def send_info_about_user(message):
    try:
        logger.log_info(f"Команда /me вызвана пользователем {message.from_user.username}")
        chat_id = message.chat.id
        info = TelegramUserManager.get_student_info(chat_id)
        if info:
            response = f"""
Информация о пользователе:
Студенческий билет: {info['stud_id']}
Полное имя: {info['name']}
Группа: {info['group']}
"""
            send_custom_message(chat_id, response)
        else:
            send_custom_message(chat_id, "К сожалению, нет информации о пользователе.")

        # Клавиатура для дополнительной информации
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Предсказания", callback_data='get_predicts'),
                   types.InlineKeyboardButton("Предметы и Баллы", callback_data='get_points_subjects'))
        send_custom_message(chat_id, 'Выберите информацию:', markup)
    except Exception as e:
        logger.log_error(f"Ошибка при выполнении команды /me: {str(e)}")
        send_custom_message(message.chat.id, "Произошла ошибка. Попробуйте еще раз.")

# Команда /help
@bot.message_handler(commands=['help'])
def send_help(message):
    try:
        logger.log_info(f"Команда /help вызвана пользователем {message.from_user.username}")
        help_text = """
Я PredictBot, и вот что я умею:

/start - Начать работу с ботом
/help - Показать это сообщение
/status - Проверить статус вашей регистрации
/me - Показать вашу информацию
"""
        send_custom_message(message.chat.id, help_text)
    except Exception as e:
        logger.log_error(f"Ошибка при выполнении команды /help: {str(e)}")
        send_custom_message(message.chat.id, "Произошла ошибка. Попробуйте еще раз.")
