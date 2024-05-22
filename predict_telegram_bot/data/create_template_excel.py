import xlsxwriter


def create_template():
    # Создание нового рабочего книги
    wb = xlsxwriter.Workbook('template_with_formulas.xlsx')

    # Выбор активной листа
    ws = wb.add_worksheet()

    # Запись заголовков в первую строку
    headers = [
        "ФИО",
        "stud_id",
        "ЕГЭ(всего)",
        "total_score",
        "exam_math",
        "exam_inf",
        "exam_physic",
        "exam_rus",
        "extra_score",
        "phy_or_inf",
        "суммРейтинг",
        "Рейтинг"
    ]

    for col_num, header in enumerate(headers, start=0):
        ws.write(0, col_num, header)

    # Сохранение файла
    wb.close()


def run():
    create_template()
