import asyncio

from django.core.management.base import BaseCommand

from predict_telegram_bot.bot.bot import bot  # если тут ошибка, это норма


class Command(BaseCommand):
    help = 'Запуск бота'

    def handle(self, *args, **options):
        asyncio.run(bot.polling())
