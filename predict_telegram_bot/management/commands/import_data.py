from django.core.management.base import BaseCommand

import pandas as pd
from predict_telegram_bot.data.import_excel_data import run

class Command(BaseCommand):
    help = 'Запуск импорта'

    def handle(self, *args, **options):
        try:
            run()
        except Exception as e:
            print(e)