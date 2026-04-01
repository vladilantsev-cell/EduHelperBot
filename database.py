from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()
engine = create_engine('sqlite:///eduhelper.db')
Session = sessionmaker(bind=engine)


# Модель пользователя
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    role = Column(String)
    username = Column(String)
    password = Column(String)
    full_name = Column(String)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    student = relationship("User", remote_side=[id])


# Модель расписания
class Schedule(Base):
    __tablename__ = 'schedule'

    id = Column(Integer, primary_key=True)
    lesson_name = Column(String)
    date_time = Column(DateTime)
    location = Column(String)
    teacher = Column(String)
    student_id = Column(Integer, ForeignKey('users.id'))


# Модель мероприятий
class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    date = Column(DateTime)
    registered_users = Column(Text, default="")


# Модель транзакций бустов
class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Integer)
    reason = Column(String)
    date = Column(DateTime, default=datetime.now)


# Модель платежей
class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)
    date = Column(DateTime)
    status = Column(String)


# Модель оценок
class Grade(Base):
    __tablename__ = 'grades'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('users.id'))
    subject = Column(String)
    grade = Column(Float)
    teacher_feedback = Column(String)
    date = Column(DateTime, default=datetime.now)


# Модель бустов
class Boost(Base):
    __tablename__ = 'boosts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Integer, default=0)


# Модель магазина
class ShopItem(Base):
    __tablename__ = 'shop_items'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    price = Column(Integer)
    image_url = Column(String, nullable=True)


def init_db():
    """Инициализация базы данных"""
    Base.metadata.create_all(engine)


def get_session():
    """Получить сессию"""
    return Session()


# ========== ФУНКЦИИ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ==========

def get_user(telegram_id):
    """Получить пользователя по telegram_id"""
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    session.close()
    return user


def create_user(telegram_id, role, username, password, full_name):
    """Создать нового пользователя"""
    session = Session()
    user = User(
        telegram_id=telegram_id,
        role=role,
        username=username,
        password=password,
        full_name=full_name
    )
    session.add(user)
    session.commit()
    session.close()
    return user


def update_user_student_id(telegram_id, student_id):
    """Обновить student_id у родителя"""
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.student_id = student_id
        session.commit()
    session.close()


# ========== ФУНКЦИИ ДЛЯ РАСПИСАНИЯ ==========

def get_schedule(student_id, limit_days=1):
    """Получить расписание на сегодня"""
    session = Session()
    from datetime import datetime, timedelta
    today = datetime.now().replace(hour=0, minute=0, second=0)
    end_date = today + timedelta(days=limit_days)

    schedule = session.query(Schedule).filter(
        Schedule.student_id == student_id,
        Schedule.date_time >= today,
        Schedule.date_time <= end_date
    ).order_by(Schedule.date_time).all()
    session.close()
    return schedule


def add_schedule(lesson_name, date_time, location, teacher, student_id):
    """Добавить занятие в расписание"""
    session = Session()
    lesson = Schedule(
        lesson_name=lesson_name,
        date_time=date_time,
        location=location,
        teacher=teacher,
        student_id=student_id
    )
    session.add(lesson)
    session.commit()
    session.close()


# ========== ФУНКЦИИ ДЛЯ МЕРОПРИЯТИЙ ==========

def get_events():
    """Получить все предстоящие мероприятия"""
    session = Session()
    events = session.query(Event).filter(Event.date >= datetime.now()).order_by(Event.date).all()
    session.close()
    return events


def get_event(event_id):
    """Получить мероприятие по ID"""
    session = Session()
    event = session.query(Event).get(event_id)
    session.close()
    return event


def register_for_event(user_id, event_id):
    """Зарегистрировать пользователя на мероприятие"""
    session = Session()
    event = session.query(Event).get(event_id)
    if event:
        registered = event.registered_users.split(",") if event.registered_users else []
        if str(user_id) not in registered:
            registered.append(str(user_id))
            event.registered_users = ",".join(registered)
            session.commit()
            session.close()
            return True
    session.close()
    return False


def get_user_events(user_id):
    """Получить мероприятия, на которые записан пользователь"""
    session = Session()
    events = session.query(Event).all()
    user_events = []
    for event in events:
        registered = event.registered_users.split(",") if event.registered_users else []
        if str(user_id) in registered:
            user_events.append(event)
    session.close()
    return user_events


def add_event(title, description, date):
    """Добавить новое мероприятие"""
    session = Session()
    event = Event(title=title, description=description, date=date)
    session.add(event)
    session.commit()
    session.close()


# ========== ФУНКЦИИ ДЛЯ БУСТОВ ==========

def get_boost(user_id):
    """Получить количество бустов пользователя"""
    session = Session()
    boost = session.query(Boost).filter_by(user_id=user_id).first()
    if not boost:
        boost = Boost(user_id=user_id, amount=0)
        session.add(boost)
        session.commit()
    result = boost.amount
    session.close()
    return result


def add_boost(user_id, amount, reason):
    """Добавить бусты пользователю"""
    session = Session()
    boost = session.query(Boost).filter_by(user_id=user_id).first()
    if not boost:
        boost = Boost(user_id=user_id, amount=0)
        session.add(boost)
    boost.amount += amount
    session.commit()

    transaction = Transaction(user_id=user_id, amount=amount, reason=reason)
    session.add(transaction)
    session.commit()
    session.close()


def spend_boost(user_id, amount):
    """Списать бусты"""
    session = Session()
    boost = session.query(Boost).filter_by(user_id=user_id).first()
    if boost and boost.amount >= amount:
        boost.amount -= amount
        session.commit()
        session.close()
        return True
    session.close()
    return False


def get_transactions(user_id):
    """Получить историю транзакций"""
    session = Session()
    transactions = session.query(Transaction).filter_by(user_id=user_id).order_by(Transaction.date.desc()).limit(
        10).all()
    session.close()
    return transactions


# ========== ФУНКЦИИ ДЛЯ МАГАЗИНА ==========

def get_shop_items():
    """Получить список товаров в магазине"""
    session = Session()
    items = session.query(ShopItem).all()
    session.close()
    return items


def get_shop_item(item_id):
    """Получить товар по ID"""
    session = Session()
    item = session.query(ShopItem).get(item_id)
    session.close()
    return item


def add_shop_item(name, description, price, image_url=None):
    """Добавить товар в магазин"""
    session = Session()
    item = ShopItem(name=name, description=description, price=price, image_url=image_url)
    session.add(item)
    session.commit()
    session.close()


# ========== ФУНКЦИИ ДЛЯ ФИНАНСОВ ==========

def get_debts(user_id):
    """Получить задолженности пользователя"""
    session = Session()
    debts = session.query(Payment).filter_by(user_id=user_id, status='debt').all()
    session.close()
    return debts


def get_payments_history(user_id):
    """Получить историю платежей"""
    session = Session()
    payments = session.query(Payment).filter_by(user_id=user_id).order_by(Payment.date.desc()).limit(10).all()
    session.close()
    return payments


def add_payment(user_id, amount, status):
    """Добавить платеж"""
    session = Session()
    payment = Payment(user_id=user_id, amount=amount, date=datetime.now(), status=status)
    session.add(payment)
    session.commit()
    session.close()


# ========== ФУНКЦИИ ДЛЯ ОЦЕНОК ==========

def get_grades(student_id):
    """Получить оценки ученика"""
    session = Session()
    grades = session.query(Grade).filter_by(student_id=student_id).order_by(Grade.date.desc()).all()
    session.close()
    return grades


def add_grade(student_id, subject, grade, teacher_feedback):
    """Добавить оценку"""
    session = Session()
    new_grade = Grade(
        student_id=student_id,
        subject=subject,
        grade=grade,
        teacher_feedback=teacher_feedback
    )
    session.add(new_grade)
    session.commit()
    session.close()


def calculate_average_grade(student_id):
    """Посчитать средний балл"""
    grades = get_grades(student_id)
    if grades:
        return sum(g.grade for g in grades) / len(grades)
    return 0


# ========== ФУНКЦИИ ДЛЯ ТЕСТОВЫХ ДАННЫХ ==========

def generate_test_data():
    """Создать тестовые данные"""
    session = Session()

    from datetime import datetime, timedelta

    # Создаем тестового ученика
    student = User(
        telegram_id=0,
        role="student",
        username="student",
        password="123",
        full_name="Иванов Иван"
    )
    session.add(student)
    session.commit()

    # Создаем расписание
    now = datetime.now()
    schedule_items = [
        Schedule(lesson_name="Математика", date_time=now.replace(hour=9, minute=0), location="Каб. 101",
                 teacher="Петрова М.И.", student_id=student.id),
        Schedule(lesson_name="Русский язык", date_time=now.replace(hour=11, minute=0), location="Каб. 102",
                 teacher="Сидорова А.В.", student_id=student.id),
        Schedule(lesson_name="Программирование", date_time=now.replace(hour=14, minute=0), location="Каб. 201",
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
    ]
    for item in shop_items:
        session.add(item)

    session.commit()
    session.close()
    print("✅ Тестовые данные созданы!")