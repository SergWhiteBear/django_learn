from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from django.dispatch import receiver
from django.db.models.signals import post_save

from .models import DirectionOfStudy, Student, Group, SchoolExam, StudySubject, StudyExam, PointsPerSemester


@admin.register(DirectionOfStudy)
class DirectionOfStudyAdmin(admin.ModelAdmin):
    search_fields = ('direction_of_study__startswith',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'view_group_link', 'olympiad', 'view_school_exam_link')
    list_filter = ('group_name', 'olympiad')
    search_fields = ('full_name__startswith', 'id__startswith')

    def view_group_link(self, obj):  # Функция для перехода на таблицу "Группы" из "Студенты"
        url = (
                reverse("admin:telegramPredictBot_group_changelist")
                + "?"
                + urlencode({"global_name": f"{obj.group_name}"})
        )
        return format_html('<a href="{}">{}</a>', url, obj.group_name)

    def view_school_exam_link(self, obj):  # Функция для перехода на таблицу "Экзамены" из "Студенты"
        url = (
                reverse("admin:telegramPredictBot_studyexam_changelist")
                + "?"
                + urlencode({"stud_id": f"{obj.id}"})
        )
        return format_html('<a href="{}">Экзамены</a>', url, obj.id)

    view_group_link.short_description = "Группа"
    view_school_exam_link.short_description = "Экзамены"


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('global_name', 'local_name', 'direction_of_study', 'view_count_student')
    list_filter = ('global_name', 'local_name', 'direction_of_study')

    def view_count_student(self, obj):  # Функция подсчёта студентов в группе
        count = obj.student_set.count()
        url = (
                reverse("admin:telegramPredictBot_student_changelist")
                + "?"
                + urlencode({"group_name": f"{obj.global_name}"})
        )
        return format_html('<a href="{}">{}</a>', url, count)

    view_count_student.short_description = "Кол-во студентов"


@admin.register(SchoolExam)
class SchoolExamAdmin(admin.ModelAdmin):
    list_display = ('stud_id', 'exam_name', 'exam_score')
    list_filter = ('stud_id', 'exam_name', 'exam_score')


@admin.register(StudySubject)
class StudySubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_name', 'get_related_objects')
    list_filter = ('direction_of_study',)
    search_fields = ('subject_name__startswith',)

    def get_related_objects(self, obj):  # Функция для отображения связанных полей
        # Предположим, что у вас есть поле ManyToManyField с именем 'direction_of_study'
        return ", ".join([str(related_object) for related_object in obj.direction_of_study.all()])

    get_related_objects.short_description = 'Направления'


@admin.register(StudyExam)
class StudyExamAdmin(admin.ModelAdmin):
    list_display = ('name_exam', 'stud_id', 'final_score', 'exam_predict')
    search_fields = ('name_exam__subject_name__startswith', 'stud_id__full_name__startswith',)


@admin.register(PointsPerSemester)
class PointsPerSemesterAdmin(admin.ModelAdmin):
    list_display = ('stud_id', 'name_subject', 'subject_score', 'attending_classes')
    list_filter = ('name_subject',)

    def has_add_permission(self, request):
        return False


"""
    Триггеры
    1) create_related_object - после создания студента, создает записи в таблицах 'Экзамены' и 'Баллы в семестре'

"""


@receiver(post_save, sender=Student)
def create_related_object(sender, instance, created, **kwargs):
    if created:
        subjects = StudySubject.objects.filter(direction_of_study=instance.group_name.direction_of_study)
        for subject in subjects:
            # Создаем объект StudyExam для каждого объекта StudySubject
            StudyExam.objects.create(stud_id=instance, name_exam=subject)
            PointsPerSemester.objects.create(stud_id=instance, name_subject=subject)