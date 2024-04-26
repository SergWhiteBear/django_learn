import asyncio

from telebot import types
from telebot.async_telebot import AsyncTeleBot

from django.conf import settings

from predict_telegram_bot.user_service import TelegramUserManager

from predict_telegram_bot.log.bot_log import BotLogger

bot = AsyncTeleBot(settings.TELEGRAM_TOKEN, parse_mode='HTML')

# Хранилище для данных регистрации и состояний
registration_data = {}
user_states = {}
sent_messages = []  # для удаления сообщений (в процессе)
msgs = {}
logger = BotLogger('bot.log')


@bot.message_handler(commands=['start'])
async def send_welcome(message):
    start_msg = await bot.reply_to(message, f"""\
    Welcome, {message.from_user.username}! Я PredictBot. 
Я нужен для формирования прогноза по твоей учебе. 
Можешь ознакомится с тем, что я умею /help """)
    user_states[message.from_user.id] = "start"
    markup = types.InlineKeyboardMarkup()
    choice_button1 = types.InlineKeyboardButton('Смешарик', callback_data='choice')
    choice_button2 = types.InlineKeyboardButton('Новичёк', callback_data='choice')
    markup.add(choice_button2, choice_button1)
    await bot.send_message(message.from_user.id, f'Ты новенький или уже смешарик?', reply_markup=markup)
    print(message.chat.id, message.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data == 'choice')
async def get_status_user(message):
    user = await TelegramUserManager.check_auth(message.from_user.id)
    if user is False:
        status_msg = await bot.send_message(message.from_user.id, f"""\
    Так как ты не зарегистрирован, мне нужно собрать информацию о тебе.
    Эта информация отправится на обработку администратору.
    После подтверждения информации о тебе, ты сможешь пользоваться всем моим функционалом.
                        """)
        regist_msg = await bot.send_message(message.from_user.id, f"""Приступим к регистрации. 
    Для начала сообщи мне номер студенческого билета.""")
        user_states[message.chat.id] = "stud_id"
    elif user and user.status == 'W':
        start_msg = await bot.send_message(message.from_user.id, "Ожидайте подтверждения")
        sent_messages.append(start_msg)
        return
    else:
        start_msg = await bot.send_message(message.from_user.id,
                                           "Вы уже зарегистрированы. Ознакомьтесь с командами /help")
        sent_messages.append(start_msg)
        return


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'stud_id')
async def get_stud_id(message):
    registration_data[message.from_user.id] = {"stud_id": message.text}
    dialog_msg = await bot.send_message(message.from_user.id, f"""Я тебя запомнил!""")
    logger.log_info(f"Пользователь ввел номер студ.")
    user_states[message.from_user.id] = "name"
    regist_msg = await bot.send_message(message.chat.id, f"""Отправьте ваше Ф.И.О""")


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'name')
async def get_full_name(message):
    registration_data[message.chat.id]["name"] = message.text
    dialog_msg = await bot.send_message(message.from_user.id, f"""Ага! Это ты значит! Понял, понял""")
    logger.log_info(f"Пользователь ввел Ф.И.О")
    user_states[message.chat.id] = "group"
    regist_msg = await bot.send_message(message.from_user.id, f"""Отправьте название группы""")


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'group')
async def get_group_name(message):
    registration_data[message.from_user.id]["group"] = message.text
    dialog_msg = await bot.send_message(message.from_user.id,
                                        f"""Дак ты то самый {message.from_user.username}! ХААХХААХХАХАХ""")
    logger.log_info(f"Пользователь ввел группу")
    user_states[message.from_user.id] = None  # сброс состояния
    final_msg = await bot.send_message(message.from_user.id, f"""Усё! Давай беги от сюдава""")
    await TelegramUserManager.register_user(message.from_user.id, message.from_user.username, registration_data)
    await bot.send_message(
        message.chat.id,
        f"Спасибо! Регистрация завершена. Ваша информация:\n"
        f"Номер студенческого билета: {registration_data[message.from_user.id]['stud_id']}\n"
        f"Ф.И.О: {registration_data[message.from_user.id]['name']}\n"
        f"Группа: {registration_data[message.from_user.id]['group']}")
    logger.log_info(f"Регистрация прошла успешно")


@bot.message_handler(commands=['me'])
async def send_info_about_user(message):
    print("Команда /me вызвана")
    chat_id = message.chat.id
    user_info = registration_data.get(chat_id, {})
    await bot.send_message(
        message.chat.id,
        f"Номер студенческого билета: {user_info.get('stud_id', 'Не указан')}\n"
        f"Ф.И.О: {user_info.get('name', 'Не указан')}\n"
        f"Группа: {user_info.get('group', 'Не указан')}")
    markup = types.InlineKeyboardMarkup()
    get_predicts_button = types.InlineKeyboardButton("Предсказания", callback_data='get_predicts')
    get_study_points = types.InlineKeyboardButton("Предметы и баллы", callback_data='get_points_subjects')
    markup.add(get_predicts_button, get_study_points)
    await bot.send_message(chat_id, 'Тест кнопок', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_points_subjects')
async def get_predicts(call):
    markup = types.InlineKeyboardMarkup()
    get_points_button = types.InlineKeyboardButton("Баллы за предметы", callback_data='get_points_subject')
    get_study_exam = types.InlineKeyboardButton("Баллы за экзамены", callback_data='get_points_exam')
    get_study_subject = types.InlineKeyboardButton("Предметы", callback_data='get_subject')
    markup.add(get_points_button, get_study_subject, get_study_exam)
    message = call.message
    chat_id = message.chat.id
    await bot.send_message(chat_id, f'Данные отправлены: get_predict_exam', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_predicts')
async def get_predicts(call):
    markup = types.InlineKeyboardMarkup()
    get_predict_exam_button = types.InlineKeyboardButton("Предсказание по экзамену", callback_data='get_predict_exam')
    get_predict_points_button = types.InlineKeyboardButton("Предсказание по баллам", callback_data='get_predict_points')
    markup.add(get_predict_exam_button, get_predict_points_button)
    message = call.message
    chat_id = message.chat.id
    await bot.send_message(chat_id, f'Данные отправлены: get_predict_exam', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_predict_exam')
async def get_predict_exam(call):
    message = call.message
    chat_id = message.chat.id
    await bot.send_message(chat_id, f'Данные отправлены: get_predict_exam')


@bot.callback_query_handler(func=lambda call: call.data == 'get_predict_points')
async def get_predict_points(call):
    message = call.message
    chat_id = message.chat.id
    await bot.send_message(chat_id, f'Данные отправлены: get_predict_points')


@bot.callback_query_handler(func=lambda call: call.data == 'get_points_subject')
async def get_points_subject(call):
    message = call.message
    chat_id = message.chat.id
    await bot.send_message(chat_id, f'Данные отправлены: get_points_subject')


@bot.callback_query_handler(func=lambda call: call.data == 'get_points_exam')
async def get_points_exam(call):
    message = call.message
    chat_id = message.chat.id
    await bot.send_message(chat_id, f'Данные отправлены: get_points_exam')


@bot.callback_query_handler(func=lambda call: call.data == 'get_subject')
async def get_subject(call):
    message = call.message
    chat_id = message.chat.id
    await bot.send_message(chat_id, f'Данные отправлены: get_subject')


@bot.message_handler(commands=['help'])
async def send_help(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    support_button = types.InlineKeyboardButton("Поддержка", callback_data='call_support')
    markup.add(support_button)
    await bot.send_message(chat_id, 'Список команд: \n /me \n /start', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'call_support')
async def get_subject(call):
    message = call.message
    chat_id = message.chat.id
    await bot.send_message(chat_id, f'Отправил данные в поддержку', )
