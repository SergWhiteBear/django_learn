from django.db import models
from .validate import validate_global_group, validate_local_group


class DirectionOfStudy(models.Model):
    direction_of_study = models.CharField(
        verbose_name='Направление',
        max_length=50,
        primary_key=True
    )  # Направление

    def __str__(self):
        return self.direction_of_study

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
        max_length=10,
        default='КН-',
        validators=[validate_local_group]
    )  # Внутреннее название (пр-р: КН-304)
    global_name = models.CharField(
        verbose_name='Внешнее название',
        max_length=10,
        default='МЕН-',
        validators=[validate_global_group],
        primary_key=True
    )  # Внешнее название (пр-р: МЕН-310204)

    def __str__(self):
        return self.global_name

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
    olympiad = models.CharField(
        verbose_name='Участие/неучастие в олимпиадах',
        max_length=100,
        choices=olympiad_сhoice,
        default='Не выбрано'
    )  # Участие/неучастие в олимпиадах

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'


class SchoolExam(models.Model):
    stud_id = models.ForeignKey(
        Student,
        verbose_name='Студент',
        on_delete=models.CASCADE,
        related_name='SchoolExam'
    )  # Ф. И. О.
    exam_name = models.CharField(
        max_length=15,
        verbose_name='Название экзамена'
    )
    exam_score = models.FloatField(
        default=0,
        verbose_name='Балл'
    )

    def __str__(self):
        return self.exam_name

    class Meta:
        unique_together = ['exam_name', 'stud_id']
        verbose_name = 'Школьный экзамен'
        verbose_name_plural = 'Школьные экзамены'


class StudySubject(models.Model):
    subject_name = models.CharField(
        max_length=10,
        verbose_name='Название предмета'
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
        editable=False,
        default=0
    )

    def __str__(self):
        return f'{self.name_exam}'

    class Meta:
        verbose_name = 'Экзамен'
        verbose_name_plural = 'Экзамены'


class PointsPerSemester(models.Model):
    stud_id = models.ForeignKey(
        Student,
        verbose_name='Студент',
        on_delete=models.CASCADE,
        to_field='id',
        default=None,
        editable=False
    )  # Ф. И. О.
    name_subject = models.ForeignKey(
        StudySubject,
        verbose_name='Предмет',
        on_delete=models.CASCADE,
        editable=False
    )
    subject_score = models.FloatField(verbose_name='Балл за предмет', default=0)
    attending_classes = models.FloatField(verbose_name='Посещение', default=0)

    def __str__(self):
        return f'{self.name_subject}'

    class Meta:
        verbose_name = 'Баллы в семестре'
        verbose_name_plural = 'Баллы в семестре'


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
