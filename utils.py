from datetime import datetime, timedelta
import random


def generate_sample_data():
    """Генерация тестовых данных для демонстрации"""
    from database import Session, User, Schedule, Event, Payment, Grade, Boost, ShopItem
    from datetime import datetime, timedelta

    session = Session()

    # Создаем тестового ученика
    student = User(
        telegram_id=0,
        role="student",
        username="student1",
        password="123",
        full_name="Иванов Иван"
    )
    session.add(student)
    session.commit()

    # Создаем расписание
    now = datetime.now()
    schedule_items = [
        Schedule(lesson_name="Математика", date_time=now.replace(hour=9), location="Каб. 101", teacher="Петрова М.И.",
                 student_id=student.id),
        Schedule(lesson_name="Русский язык", date_time=now.replace(hour=11), location="Каб. 102",
                 teacher="Сидорова А.В.", student_id=student.id),
        Schedule(lesson_name="Программирование", date_time=now.replace(hour=14), location="Каб. 201",
                 teacher="Иванов С.П.", student_id=student.id),
    ]
    for item in schedule_items:
        session.add(item)

    # Создаем мероприятия
    events = [
        Event(title="День открытых дверей", description="Приходите познакомиться со школой",
              date=now + timedelta(days=5)),
        Event(title="Конкурс проектов", description="Покажи свой проект", date=now + timedelta(days=10)),
        Event(title="Спортивный праздник", description="Веселые старты", date=now + timedelta(days=15)),
    ]
    for event in events:
        session.add(event)

    # Создаем платежи
    payments = [
        Payment(user_id=student.id, amount=15000, date=now - timedelta(days=30), status="paid"),
        Payment(user_id=student.id, amount=15000, date=now, status="debt"),
    ]
    for payment in payments:
        session.add(payment)

    # Создаем оценки
    grades = [
        Grade(student_id=student.id, subject="Математика", grade=4.5,
              teacher_feedback="Хорошо, но есть над чем работать"),
        Grade(student_id=student.id, subject="Русский язык", grade=5.0, teacher_feedback="Отлично!"),
        Grade(student_id=student.id, subject="Программирование", grade=4.0, teacher_feedback="Нужно больше практики"),
    ]
    for grade in grades:
        session.add(grade)

    # Создаем бусты
    boost = Boost(user_id=student.id, amount=150)
    session.add(boost)

    # Создаем магазин
    shop_items = [
        ShopItem(name="Movavi ручка", description="Брендированная ручка", price=50),
        ShopItem(name="Movavi блокнот", description="Блокнот с логотипом", price=100),
        ShopItem(name="Movavi футболка", description="Футболка с принтом", price=300),
        ShopItem(name="Скидка на обучение 10%", description="Скидка на следующий месяц", price=500),
    ]
    for item in shop_items:
        session.add(item)

    session.commit()
    session.close()