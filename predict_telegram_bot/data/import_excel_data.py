import pandas as pd

from predict_telegram_bot.models import Student, DirectionOfStudy, Group, SchoolExam, StudentRating

file_path_standart = 'predict_telegram_bot/data/БаллыЕГЭ.xlsx'


def import_data(file_path=file_path_standart):
    for sheet_name in pd.ExcelFile(file_path).sheet_names:
        direction = DirectionOfStudy(
            direction_of_study=sheet_name
        )
        group = Group(
            direction_of_study=direction,
            local_name=f'ГР-{direction}',
            global_name=f'МЕН-{direction}'
        )
        direction.save()
        group.save()

        df = pd.read_excel(file_path, sheet_name=sheet_name)
        for index, row in df.iterrows():
            try:
                student = Student(
                    id=row['stud_id'],
                    full_name=row['full_name'],
                    group_name=group
                )
                school_exam = SchoolExam(
                    stud_id=student,
                    exam_rus=row['exam_rus'] if pd.notna(row['exam_rus']) else 0,
                    exam_math=row['exam_math'] if pd.notna(row['exam_math']) else 0,
                    exam_physic=row['exam_physic'] if pd.notna(row['exam_physic']) else 0,
                    exam_inf=row['exam_inf'] if pd.notna(row['exam_inf']) else 0,
                    extra_score=row['extra_score'] if pd.notna(row['extra_score']) else 0
                )
                rating = StudentRating(
                    stud_id=student,
                    sumRate=row['суммРейтинг'],
                    rate=row['Рейтинг'],
                    predict_academic_success='w'
                )
                student.save()
                school_exam.save()
                rating.save()
            except Exception as e:
                print(e)


def run(file_path=file_path_standart):
    import_data(file_path)
