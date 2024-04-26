from django.db import transaction

from .models import TelegramUsers, Student, Group

import telebot


class TelegramUserManager:

    @staticmethod
    async def check_auth(telegram_id):
        try:
            user = await TelegramUsers.objects.aget(tg_id=telegram_id)
            return user
        except TelegramUsers.DoesNotExist:
            return False

    @staticmethod
    async def register_user(chat_id, username, registration_data):
        try:
            user_info = f'{registration_data[chat_id]["stud_id"]}\n{registration_data[chat_id]["name"]}\n{registration_data[chat_id]["group"]}'
            await TelegramUsers.objects.acreate(
                tg_username=username,
                tg_id=chat_id,
                user_info=user_info,
                status='W',
                check_application=False
            )
        except Exception as e:
            print(e)
