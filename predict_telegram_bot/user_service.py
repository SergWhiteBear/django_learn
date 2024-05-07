import telebot
from django.db import transaction
from .models import *


class TelegramUserManager:
    @staticmethod
    def check_auth(chat_id):
        try:
            user = TelegramUsers.objects.get(tg_id=chat_id)
            return user
        except TelegramUsers.DoesNotExist:
            return False

    @staticmethod
    def register_user(chat_id, username, registration_data):
        try:
            user_info = f'{registration_data[chat_id]["stud_id"]}\n{registration_data[chat_id]["name"]}\n{registration_data[chat_id]["group"]}'
            TelegramUsers.objects.create(
                tg_username=username,
                tg_id=chat_id,
                user_info=user_info,
                status='W',
                check_application=False
            )
        except Exception as e:
            print(e)

    @staticmethod
    def get_student_info(chat_id):
        user = TelegramUserManager.check_auth(chat_id)
        if user:
            student_id = user.user_info.splitlines()[0]
            student = Student.objects.get(id=student_id)
            return {
                'stud_id': student.id,
                'name': student.full_name,
                'group': student.group_name.global_name
            }
        else:
            return False

    @staticmethod
    def get_student_points(chat_id):
        student = TelegramUserManager.get_student_info(chat_id)
        if student:
            points = PointsPerSemester.objects.filter(stud_id=student['stud_id'])
            points_list = [{'subject': point.name_subject.subject_name, 'score': point.subject_score,
                            'attending': point.attending_classes, 'points_predict': point.predict_points} for point in
                           points]
            return points_list
        else:
            return False

    @staticmethod
    def get_student_exam_results(chat_id):
        student = TelegramUserManager.get_student_info(chat_id)
        if student:
            exams = StudyExam.objects.filter(stud_id=student['stud_id'])
            exam_list = [{'subject': exam.name_exam.subject_name, 'final_score': exam.final_score,
                          'exam_predict': exam.exam_predict} for exam in exams]
            return exam_list
        else:
            return None

    @staticmethod
    def get_subjects_by_specialty(chat_id):
        try:
            student = TelegramUserManager.get_student_info(chat_id)
            direction = Group.objects.get(global_name=student['group']).direction_of_study
            subjects = StudySubject.objects.filter(direction_of_study=direction)
            return subjects
        except DirectionOfStudy.DoesNotExist:
            return False
