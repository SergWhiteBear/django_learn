import pickle
import pandas as pd
from django.contrib import admin
from django.db import transaction
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed
from admincharts.admin import AdminChartMixin
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from .models import *

# !!! Поправить пути для файлов, если создавать модель через консоль путь отличается
best_logistic_regression_model = pickle.load(open('predict_telegram_bot/predict_model/best_gradient_boosting_model.pkl', 'rb'))
scaler = pickle.load(open('predict_telegram_bot/predict_model/scaler_fit.pkl', 'rb'))


@admin.register(DirectionOfStudy)
class DirectionOfStudyAdmin(admin.ModelAdmin):
    search_fields = ('direction_of_study__startswith',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'view_group_link', 'view_school_exam_link')
    list_filter = ('group_name',)
    search_fields = ('full_name__startswith', 'id__startswith')
    raw_id_fields = ('group_name',)

    def view_group_link(self, obj):  # Функция для перехода на таблицу "Группы" из "Студенты"
        url = (
                reverse("admin:predict_telegram_bot_group_changelist")
                + "?"
                + urlencode({"global_name": f"{obj.group_name}"})
        )
        return format_html('<a href="{}">{}</a>', url, obj.group_name)

    def view_school_exam_link(self, obj):  # Функция для перехода на таблицу "Экзамены" из "Студенты"
        url = (
                reverse("admin:predict_telegram_bot_studyexam_changelist")
                + "?"
                + urlencode({"stud_id": f"{obj.id}"})
        )
        return format_html('<a href="{}">Экзамены</a>', url, obj.id)

    def get_form(self, request, obj=None, **kwargs):
        form = super(StudentAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['group_name'].widget.attrs['style'] = 'width: 200px;'
        return form

    view_group_link.short_description = "Группа"
    view_school_exam_link.short_description = "Экзамены"


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('global_name', 'local_name', 'direction_of_study', 'view_count_student')
    list_filter = ('global_name', 'local_name', 'direction_of_study')
    raw_id_fields = ['direction_of_study', ]

    def view_count_student(self, obj):  # Функция подсчёта студентов в группе
        count = obj.student_set.count()
        return count

    def get_form(self, request, obj=None, **kwargs):
        form = super(GroupAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['direction_of_study'].widget.attrs['style'] = 'width: 280px;'
        return form

    view_count_student.short_description = "Кол-во студентов"


@admin.register(SchoolExam)
class SchoolExamAdmin(admin.ModelAdmin):
    list_display = ('stud_id', 'exam_rus', 'exam_math', 'exam_physic', 'exam_inf',)
    list_filter = ('stud_id__group_name',)
    raw_id_fields = ['stud_id', ]


@admin.action(description='Выполнить прогноз для студента/ов')
def make_predict(modelname, request, queryset):
    # Сбор данных о студентах
    data = []
    for obj in queryset:
        # Получение данных из базы данных или других источников
        school_exam = SchoolExam.objects.get(stud_id=obj.stud_id)
        features = [
            obj.stud_id,
            school_exam.exam_score,
            school_exam.exam_math,
            max(school_exam.exam_physic, school_exam.exam_inf),
            school_exam.exam_rus,
            school_exam.extra_score
        ]
        data.append(features)

    # Создание DataFrame
    df = pd.DataFrame(data, columns=['stud_id', 'exam_score', 'exam_math', 'phy_or_inf', 'exam_rus', 'extra_score'])
    features = ['exam_score', 'exam_math', 'phy_or_inf', 'exam_rus', 'extra_score']
    # Добавление новых признаков
    df['avg_exam_score'] = df[['exam_math', 'phy_or_inf', 'exam_rus']].mean(axis=1)
    threshold_score = 70
    df['exams_above_threshold'] = (df[['exam_math', 'phy_or_inf', 'exam_rus']] > threshold_score).sum(axis=1)
    features += ['avg_exam_score', 'exams_above_threshold']
    # Стандартизация данных
    x = df[features]

    # Стандартизация данных
    x = scaler.transform(x)

    # Предсказание
    predictions = best_logistic_regression_model.predict(x)
    print(predictions)
    predictions_mapped = ['s' if pred else 'n' for pred in predictions]
    for stud_id, prediction in zip(df['stud_id'], predictions_mapped):
        StudentRating.objects.filter(stud_id=stud_id).update(predict_academic_success=prediction)
    y_true = [StudentRating.objects.get(stud_id=obj.stud_id).rate > 60 for obj in queryset]
    print(f'Точность: {accuracy_score(predictions, y_true)}')
    print(classification_report(predictions, y_true))
    print(confusion_matrix(predictions, y_true))


@admin.register(StudentRating)
class StudentRatingAdmin(admin.ModelAdmin):
    list_display = ('stud_id', 'sumRate', 'rate', 'predict_academic_success')
    list_filter = ('stud_id__group_name',)
    actions = [make_predict]
    raw_id_fields = ('stud_id',)

    list_chart_type = "pie"  # Тип графика
    list_chart_data = {'rate', 'stud_id__group_name'}  # Данные для графика
    list_chart_options = {"colors": ["#3366cc"]}  # Цвета для графика
    list_chart_config = None  # Переопределение общих настроек


@admin.register(StudySubject)
class StudySubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_name', 'get_related_objects')
    list_filter = ('direction_of_study',)
    search_fields = ('subject_name__startswith',)
    filter_horizontal = ('direction_of_study',)

    def get_related_objects(self, obj):  # Функция для отображения направлений
        return ", ".join([str(related_object) for related_object in obj.direction_of_study.all()])

    get_related_objects.short_description = 'Направления'


@admin.register(StudyExam)
class StudyExamAdmin(AdminChartMixin, admin.ModelAdmin):
    list_display = ('name_exam', 'stud_id', 'final_score', 'exam_predict')
    search_fields = ('name_exam__subject_name__startswith', 'stud_id__full_name__startswith',)
    raw_id_fields = ['name_exam', 'stud_id', ]
    list_filter = ('name_exam', 'stud_id__group_name')


@admin.register(PointsPerSemester)
class PointsPerSemesterAdmin(admin.ModelAdmin):
    list_display = ('stud_id', 'name_subject', 'subject_score', 'attending_classes', 'predict_points')
    list_filter = ('name_subject', 'stud_id__group_name')
    raw_id_fields = ['stud_id', 'name_subject', ]


@admin.register(TelegramUsers)
class TelegramUsersAdmin(admin.ModelAdmin):
    list_display = ('tg_username', 'tg_id', 'status', 'check_application')


"""
Триггеры 1) create_related_object_student - после создания студента, создает записи в таблицах 'Экзамены' и 'Баллы 
в семестре' 
2) create_related_student - после подтверждения данных в TelegramUsers, создает запись студента 
3) create_study_exams - при добавлении нового предмета добавляет запись с этим предметом в 'Экзамены' для всех студентов 
связанных с указанной специальностью
"""


@receiver(post_save, sender=Student)
def create_related_object_student(sender, instance, created, **kwargs):
    if created:
        try:
            with transaction.atomic():
                subjects = StudySubject.objects.filter(direction_of_study=instance.group_name.direction_of_study)
                for subject in subjects:
                    # Создаем объект StudyExam для каждого объекта StudySubject
                    StudyExam.objects.create(stud_id=instance, name_exam=subject)
                    PointsPerSemester.objects.create(stud_id=instance, name_subject=subject)
        except Exception as e:
            print(f"Ошибка при создании студента: {e}")


@receiver(post_save, sender=TelegramUsers)
def create_related_student(sender, instance, created, **kwargs):
    if not created and instance.status == 'R' and instance.check_application is True:
        try:
            stud_id, full_name, group = instance.user_info.splitlines()
            check_exist = Student.objects.filter(id=stud_id).exists()
            if not check_exist:
                with transaction.atomic():  # Использую транзакцию для обеспечения целостности данных
                    group_instance = Group.objects.get(global_name=group)
                    Student.objects.create(
                        id=int(stud_id),
                        full_name=full_name,
                        group_name=group_instance
                    )
            else:
                instance.status = 'C'
                instance.save()
        except Exception as e:
            print(f"Ошибка при создании студента: {e}")


# Сигнал для создания экзаменов при создании нового предмета
@receiver(post_save, sender=StudySubject)
def create_study_exams(sender, instance, created, **kwargs):
    if created:
        create_exams_for_directions(instance)


# Сигнал для создания экзаменов при изменении направлений обучения у существующего предмета
@receiver(m2m_changed, sender=StudySubject.direction_of_study.through)
def update_records_for_subject(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'post_add':
        added_directions = DirectionOfStudy.objects.filter(pk__in=pk_set)
        # Обновляем записи экзаменов для предмета
        update_exams_for_subject(instance, added_directions)
        # Обновляем записи баллов в семестре для предмета
        update_points_for_subject(instance, added_directions)
    elif action == 'post_remove':
        removed_directions = DirectionOfStudy.objects.filter(pk__in=pk_set)
        delete_exams_for_subject(instance, removed_directions)
        delete_points_for_subject(instance, removed_directions)


def update_points_for_subject(subject, directions):
    for direction in directions:
        groups = Group.objects.filter(direction_of_study=direction)
        students = Student.objects.filter(group_name__in=groups)
        existing_points = PointsPerSemester.objects.filter(name_subject=subject, stud_id__in=students)

        # Создаем записи баллов в семестре только для студентов, у которых их еще нет
        students_with_existing_points = existing_points.values_list('stud_id', flat=True)
        students_without_existing_points = students.exclude(id__in=students_with_existing_points)
        for student in students_without_existing_points:
            PointsPerSemester.objects.create(name_subject=subject, stud_id=student)


def delete_points_for_subject(subject, directions):
    for direction in directions:
        groups = Group.objects.filter(direction_of_study=direction)
        students = Student.objects.filter(group_name__in=groups)
        PointsPerSemester.objects.filter(name_subject=subject, stud_id__in=students).delete()


def update_exams_for_subject(subject, directions):
    for direction in directions:
        groups = Group.objects.filter(direction_of_study=direction)
        students = Student.objects.filter(group_name__in=groups)
        existing_exams = StudyExam.objects.filter(name_exam=subject, stud_id__in=students)

        # Создаем записи экзаменов только для студентов, у которых их еще нет
        students_with_existing_exams = existing_exams.values_list('stud_id', flat=True)
        students_without_existing_exams = students.exclude(id__in=students_with_existing_exams)
        for student in students_without_existing_exams:
            StudyExam.objects.create(name_exam=subject, stud_id=student)


def delete_exams_for_subject(subject, directions):
    for direction in directions:
        groups = Group.objects.filter(direction_of_study=direction)
        students = Student.objects.filter(group_name__in=groups)
        StudyExam.objects.filter(name_exam=subject, stud_id__in=students).delete()


def create_exams_for_directions(subject):
    # Получаем все связанные направления обучения для данного предмета
    directions = subject.direction_of_study.all()

    # Проходимся по каждому направлению обучения
    for direction in directions:
        # Получаем все группы, связанные с текущим направлением обучения
        groups = Group.objects.filter(direction_of_study=direction)

        # Проходимся по каждой группе
        for group in groups:
            # Получаем всех студентов в текущей группе
            students = Student.objects.filter(group_name=group)

            # Создаем запись экзамена для каждого студента
            for student in students:
                StudyExam.objects.create(name_exam=subject, stud_id=student)
