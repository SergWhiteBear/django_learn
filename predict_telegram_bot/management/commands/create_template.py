from django.core.management.base import BaseCommand

from predict_telegram_bot.data.create_template_excel import run


class Command(BaseCommand):
    help = 'Создание шаблона для заполнения'

    def handle(self, *args, **options):
        run()
