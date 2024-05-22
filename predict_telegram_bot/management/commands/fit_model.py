from django.core.management.base import BaseCommand

from predict_telegram_bot.predict_model.classifier_model import run


class Command(BaseCommand):
    help = 'Обучение модели'

    def handle(self, *args, **options):
        file_path = ''
        if options['path']:
            file_path = options['path']
        try:
            with open(file_path, 'r') as file:
                self.stdout.write(self.style.SUCCESS(f'Файл найден'))
                run(file_path)
                self.stdout.write(self.style.SUCCESS(f'Модель обучена'))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'Ошибка: Файл {file_path} не найден'))
        else:
            try:
                run(file_path)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Ошибка: {e}'))

    def add_arguments(self, parser):
        parser.add_argument(
            '-p',
            '--path',
            type=str,
            help='Путь к файлу для чтения данных для обучения'
        )
