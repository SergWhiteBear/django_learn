
from django.db import models


class DirectionOfStudy(models.Model):
    direction_of_study = models.CharField(
        verbose_name='Направление',
        max_length=50,
        primary_key=True
    )  # Направление

    def __str__(self):
        return f'{self.direction_of_study}'

    class Meta:
        verbose_name = 'Направление'
        verbose_name_plural = 'Направления'


class Group(models.Model):
    direction_of_study = models.ForeignKey(
        DirectionOfStudy,
        verbose_name='Направление',
        on_delete=models.CASCADE,
    )  # Направление обучения
    local_name = models.CharField(
        verbose_name='Внутреннее название',
        max_length=50,
        default='КН-',
        # validators=[validate_local_group]
    )  # Внутреннее название (пр-р: КН-304)
    global_name = models.CharField(
        verbose_name='Внешнее название',
        max_length=50,
        default='МЕН-',
        # validators=[validate_global_group],
        primary_key=True
    )  # Внешнее название (пр-р: МЕН-310204)

    def __str__(self):
        return f'{self.global_name}'

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'


class Student(models.Model):
    olympiad_сhoice = [
        ('Участвовал', 'Участвовал'),
        ('Не участвовал', 'Не участвовал'),
        ('Не выбрано', 'Не выбрано')
    ]  # Выбор для поля "Участие/неучастие в олимпиадах"
    id = models.PositiveBigIntegerField(
        verbose_name='Студенческий билет',
        primary_key=True
    )  # Номер студ. билета
    full_name = models.CharField(
        verbose_name='Ф.И.О',
        max_length=45,
        default='Не указано',
    )  # Ф. И. О.
    group_name = models.ForeignKey(
        Group,
        verbose_name='Группа',
        on_delete=models.CASCADE,
        to_field='global_name'
    )  # Название и номер группы

    def __str__(self):
        return f'{self.id}'

    class Meta:
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'


class SchoolExam(models.Model):
    stud_id = models.OneToOneField(
        Student,
        verbose_name='Студент',
        on_delete=models.CASCADE,
    )  # Ф. И. О.
    total_score = models.FloatField(
        verbose_name='Всего',
        default=0
    )
    exam_rus = models.FloatField(
        verbose_name='Русский язык',
        default=0
    )
    exam_math = models.FloatField(
        verbose_name='Математика',
        default=0
    )
    exam_physic = models.FloatField(
        verbose_name='Физика',
        default=0
    )
    exam_inf = models.FloatField(
        verbose_name='Информатика',
        default=0
    )
    extra_score = models.FloatField(
        verbose_name='Доп. баллы Егэ',
        default=0
    )

    def __str__(self):
        return f'{self.stud_id}'

    class Meta:
        verbose_name = 'Школьный экзамен'
        verbose_name_plural = 'Школьные экзамены'


class StudentRating(models.Model):
    STATUS_CHOICES = [
        ("s", "Успешный"),
        ("n", "Неуспешный"),
        ("w", "Нет прогноза"),
    ]
    stud_id = models.ForeignKey(
        Student,
        verbose_name='Студент',
        on_delete=models.CASCADE
    )
    sumRate = models.FloatField(
        verbose_name='sumRate',
        default=0
    )
    rate = models.FloatField(
        verbose_name='rate',
        default=0
    )
    predict_academic_success = models.CharField(
        verbose_name='Прогноз успеха в учебе',
        choices=STATUS_CHOICES,
        max_length=1,
        default='w'
    )

    def __str__(self):
        return f'{self.stud_id}'

    class Meta:
        verbose_name = 'Рейтинг'
        verbose_name_plural = 'Рейтинг'


class StudySubject(models.Model):
    subject_name = models.CharField(
        max_length=10,
        verbose_name='Название предмета',
    )
    direction_of_study = models.ManyToManyField(
        DirectionOfStudy,
        verbose_name='Направление',
        default=None
    )

    def __str__(self):
        return f'{self.subject_name}'

    class Meta:
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'


class StudyExam(models.Model):
    name_exam = models.ForeignKey(
        StudySubject,
        verbose_name='Предмет',
        on_delete=models.CASCADE
    )
    stud_id = models.ForeignKey(
        Student,
        verbose_name='Студент',
        on_delete=models.CASCADE,
        to_field='id',
        default=0
    )  # Ф. И. О.
    final_score = models.FloatField(
        verbose_name='Итоговый балл',
        default=0
    )
    exam_predict = models.FloatField(
        verbose_name='Предсказание',
        editable=False,
        default=0
    )

    def __str__(self):
        return f'{self.name_exam}'

    class Meta:
        verbose_name = 'Экзамен'
        verbose_name_plural = 'Экзамены'
        unique_together = (("name_exam", "stud_id"),)


class PointsPerSemester(models.Model):
    stud_id = models.ForeignKey(
        Student,
        verbose_name='Студент',
        on_delete=models.CASCADE,
        to_field='id',
        default=None,
    )  # Ф. И. О.
    name_subject = models.ForeignKey(
        StudySubject,
        verbose_name='Предмет',
        on_delete=models.CASCADE,
    )
    subject_score = models.FloatField(verbose_name='Балл за предмет', default=0)
    attending_classes = models.FloatField(verbose_name='Посещение', default=0)
    predict_points = models.FloatField(verbose_name='Предсказание', default=0, editable=False)

    def __str__(self):
        return f'{self.name_subject}'

    class Meta:
        verbose_name = 'Баллы в семестре'
        verbose_name_plural = 'Баллы в семестре'
        unique_together = (("name_subject", "stud_id"),)


#  Соответствие @username и номерам студ.
class TelegramUsers(models.Model):
    choice_status = [
        ('R', 'Зарегистрирован'),
        ('U', 'Не зарегистрирован'),
        ('W', 'Ожидает проверки'),
        ('C', 'Ошибка в информации пользователя')
    ]
    tg_username = models.CharField(
        verbose_name='Никнейм',
        max_length=35,
    )
    tg_id = models.PositiveBigIntegerField(
        verbose_name='Идентификатор',
        default=0,
    )
    user_info = models.TextField(verbose_name='Информация пользователя')
    status = models.CharField(
        verbose_name='Статус заявки',
        choices=choice_status,
        max_length=10,
        default='W',
    )
    check_application = models.BooleanField(verbose_name='Заявка просмотрена')

    def __str__(self):
        return f'{self.tg_username}'

    class Meta:
        verbose_name = 'Телеграмм'
        verbose_name_plural = 'Телеграмм'
