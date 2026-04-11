from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()
engine = create_engine('sqlite:///movavik.db', connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

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

class Schedule(Base):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)
    lesson_name = Column(String)
    date_time = Column(DateTime)
    location = Column(String)
    teacher = Column(String)
    student_id = Column(Integer, ForeignKey('users.id'))

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    date = Column(DateTime)
    registered_users = Column(Text, default="")

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Integer)
    reason = Column(String)
    date = Column(DateTime, default=datetime.now)

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)
    date = Column(DateTime)
    status = Column(String)   # 'paid' | 'debt'

class Grade(Base):
    __tablename__ = 'grades'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('users.id'))
    subject = Column(String)
    grade = Column(Float)
    teacher_feedback = Column(String)
    date = Column(DateTime, default=datetime.now)

class Boost(Base):
    __tablename__ = 'boosts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Integer, default=0)

class ShopItem(Base):
    __tablename__ = 'shop_items'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    price = Column(Integer)
    image_url = Column(String, nullable=True)

class News(Base):
    __tablename__ = 'news'
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    date = Column(DateTime, default=datetime.now)

# init

def init_db():
    Base.metadata.create_all(engine)
    _seed_demo_data()

def get_session():
    return Session()

# users

def get_user(telegram_id: int):
    s = Session()
    u = s.query(User).filter_by(telegram_id=telegram_id).first()
    s.close()
    return u

def get_user_by_credentials(username: str, password: str):
    s = Session()
    u = s.query(User).filter_by(username=username, password=password).first()
    s.close()
    return u

def create_user(telegram_id, role, username, password, full_name):
    s = Session()
    u = User(telegram_id=telegram_id, role=role,
             username=username, password=password, full_name=full_name)
    s.add(u)
    s.commit()
    s.close()

def update_user_telegram_id(user_id: int, telegram_id: int):
    s = Session()
    u = s.query(User).get(user_id)
    if u:
        u.telegram_id = telegram_id
        s.commit()
    s.close()

def update_user_role(telegram_id: int, role: str):
    s = Session()
    u = s.query(User).filter_by(telegram_id=telegram_id).first()
    if u:
        u.role = role
        s.commit()
    s.close()

def logout_user(telegram_id: int):
    s = Session()
    u = s.query(User).filter_by(telegram_id=telegram_id).first()
    if u:
        u.telegram_id = None
        s.commit()
    s.close()

def get_all_users():
    s = Session()
    users = s.query(User).filter(User.telegram_id.isnot(None)).all()
    s.close()
    return users

# schedule

def get_schedule(student_id: int, limit_days: int = 1):
    from datetime import timedelta
    s = Session()
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = today + timedelta(days=limit_days)
    rows = (s.query(Schedule)
            .filter(Schedule.student_id == student_id,
                    Schedule.date_time >= today,
                    Schedule.date_time <= end)
            .order_by(Schedule.date_time).all())
    s.close()
    return rows

def get_full_schedule(student_id: int):
    s = Session()
    rows = s.query(Schedule).filter_by(student_id=student_id).order_by(Schedule.date_time).all()
    s.close()
    return rows

def add_schedule(lesson_name, date_time, location, teacher, student_id):
    s = Session()
    s.add(Schedule(lesson_name=lesson_name, date_time=date_time,
                   location=location, teacher=teacher, student_id=student_id))
    s.commit()
    s.close()

# events

def get_events():
    s = Session()
    rows = s.query(Event).filter(Event.date >= datetime.now()).order_by(Event.date).all()
    s.close()
    return rows

def get_event(event_id: int):
    s = Session()
    e = s.query(Event).get(event_id)
    s.close()
    return e

def add_event(title, description, date):
    s = Session()
    s.add(Event(title=title, description=description, date=date))
    s.commit()
    s.close()

def register_for_event(user_id: int, event_id: int) -> bool:
    s = Session()
    e = s.query(Event).get(event_id)
    if e:
        registered = e.registered_users.split(",") if e.registered_users else []
        if str(user_id) not in registered:
            registered.append(str(user_id))
            e.registered_users = ",".join(registered)
            s.commit()
            s.close()
            return True
    s.close()
    return False

def is_registered_for_event(user_id: int, event_id: int) -> bool:
    e = get_event(event_id)
    if e:
        return str(user_id) in (e.registered_users.split(",") if e.registered_users else [])
    return False

def get_user_events(user_id: int):
    s = Session()
    events = s.query(Event).all()
    result = [e for e in events
              if str(user_id) in (e.registered_users.split(",") if e.registered_users else [])]
    s.close()
    return result

# boosts

def get_boost(user_id: int) -> int:
    s = Session()
    b = s.query(Boost).filter_by(user_id=user_id).first()
    if not b:
        b = Boost(user_id=user_id, amount=0)
        s.add(b)
        s.commit()
    result = b.amount
    s.close()
    return result

def add_boost(user_id: int, amount: int, reason: str):
    s = Session()
    b = s.query(Boost).filter_by(user_id=user_id).first()
    if not b:
        b = Boost(user_id=user_id, amount=0)
        s.add(b)
    b.amount += amount
    s.add(Transaction(user_id=user_id, amount=amount, reason=reason))
    s.commit()
    s.close()

def spend_boost(user_id: int, amount: int) -> bool:
    s = Session()
    b = s.query(Boost).filter_by(user_id=user_id).first()
    if b and b.amount >= amount:
        b.amount -= amount
        s.add(Transaction(user_id=user_id, amount=-amount, reason="Покупка в магазине"))
        s.commit()
        s.close()
        return True
    s.close()
    return False

def get_transactions(user_id: int):
    s = Session()
    rows = (s.query(Transaction).filter_by(user_id=user_id)
            .order_by(Transaction.date.desc()).limit(10).all())
    s.close()
    return rows

# shop

def get_shop_items():
    s = Session()
    items = s.query(ShopItem).all()
    s.close()
    return items

def get_shop_item(item_id: int):
    s = Session()
    item = s.query(ShopItem).get(item_id)
    s.close()
    return item

def add_shop_item(name, description, price, image_url=None):
    s = Session()
    s.add(ShopItem(name=name, description=description, price=price, image_url=image_url))
    s.commit()
    s.close()

# finance

def get_debts(user_id: int):
    s = Session()
    rows = s.query(Payment).filter_by(user_id=user_id, status='debt').all()
    s.close()
    return rows

def get_payments_history(user_id: int):
    s = Session()
    rows = (s.query(Payment).filter_by(user_id=user_id)
            .order_by(Payment.date.desc()).limit(10).all())
    s.close()
    return rows

def add_payment(user_id, amount, status):
    s = Session()
    s.add(Payment(user_id=user_id, amount=amount, date=datetime.now(), status=status))
    s.commit()
    s.close()

# grades

def get_grades(student_id: int):
    s = Session()
    rows = s.query(Grade).filter_by(student_id=student_id).order_by(Grade.date.desc()).all()
    s.close()
    return rows

def add_grade(student_id, subject, grade, teacher_feedback):
    s = Session()
    s.add(Grade(student_id=student_id, subject=subject, grade=grade,
                teacher_feedback=teacher_feedback))
    s.commit()
    s.close()

def calculate_average_grade(student_id: int) -> float:
    grades = get_grades(student_id)
    return round(sum(g.grade for g in grades) / len(grades), 2) if grades else 0.0

# news

def add_news(text: str):
    s = Session()
    s.add(News(text=text))
    s.commit()
    s.close()

def get_recent_news(limit: int = 5):
    s = Session()
    rows = s.query(News).order_by(News.date.desc()).limit(limit).all()
    s.close()
    return rows

def _seed_demo_data():
    s = Session()
    if s.query(User).count() > 0:
        s.close()
        return

    from datetime import timedelta
    now = datetime.now()

    # Тестовый ученик
    student = User(telegram_id=None, role="student",
                   username="student", password="123", full_name="Иванов Иван Иванович")
    s.add(student)
    s.flush()
    parent = User(telegram_id=None, role="parent",
                  username="parent", password="123",
                  full_name="Иванова Мария Петровна", student_id=student.id)
    s.add(parent)
    s.flush()
    schedule_data = [
        (0, "Курс Python",              "10:00", "Каб. 201", "Иванов С.П."),
        (0, "Курс Roblox Studio",       "12:00", "Каб. 103", "Смирнов А.К."),
        (1, "Курс Кибербезопасность",   "09:00", "Каб. 305", "Фёдоров Д.В."),
        (1, "Курс Python",              "11:00", "Каб. 201", "Иванов С.П."),
        (2, "Курс Minecraft",           "10:00", "Каб. 104", "Орлова Е.Н."),
        (2, "Курс Roblox Studio",       "13:00", "Каб. 103", "Смирнов А.К."),
        (3, "Курс Кибербезопасность",   "09:00", "Каб. 305", "Фёдоров Д.В."),
        (3, "Курс Minecraft",           "11:00", "Каб. 104", "Орлова Е.Н."),
        (4, "Курс Python",              "10:00", "Каб. 201", "Иванов С.П."),
        (4, "Курс Roblox Studio",       "14:00", "Каб. 103", "Смирнов А.К."),
    ]
    for day_offset, name, t, loc, teacher in schedule_data:
        h, m = map(int, t.split(":"))
        base = (now + timedelta(days=day_offset)).replace(hour=h, minute=m, second=0, microsecond=0)
        s.add(Schedule(lesson_name=name, date_time=base,
                       location=loc, teacher=teacher, student_id=student.id))

    # Мероприятия
    for i, (title, desc, days) in enumerate([
        ("День открытых дверей", "Знакомство со школой Movavi", 5),
        ("Конкурс IT-проектов", "Покажи свой проект жюри", 12),
        ("Спортивный праздник", "Весёлые старты для всех", 20),
    ]):
        s.add(Event(title=title, description=desc, date=now + timedelta(days=days)))

    # Платежи
    s.add(Payment(user_id=student.id, amount=15000, date=now - timedelta(days=30), status="paid"))
    s.add(Payment(user_id=student.id, amount=15000, date=now, status="debt"))

    # Оценки
    for subj, g, fb in [
        ("Курс Python",            5.0, "Отличный код! Алгоритмы написаны верно, проект сдан вовремя."),
        ("Курс Roblox Studio",     4.5, "Хорошая работа, следлай более четкие модели персонажей."),
        ("Курс Minecraft",         4.0, "Неплохо, но больше практикуйся в pvp режимах."),
        ("Курс Кибербезопасность", 3.5, "Нужно лучше разобрать тему сетевых атак — повтори материал."),
    ]:
        s.add(Grade(student_id=student.id, subject=subj, grade=g, teacher_feedback=fb,
                    date=now - timedelta(days=10)))
    # Бусты
    s.add(Boost(user_id=student.id, amount=400))
    s.add(Transaction(user_id=student.id, amount=400, reason="Приветственные бусты",
                      date=now - timedelta(days=30)))

    # Магазин
    for name, desc, price in [
        ("Movavi ручка",          "Брендированная ручка Movavi", 50),
        ("Movavi блокнот",        "Блокнот с логотипом Movavi", 100),
        ("Movavi шопер",          "Фирменная сумка-шопер Movavi", 250),
        ("Сладкий подарок",       "Вкусный сладкий набор", 150),
        ("Movavi футболка",       "Футболка с принтом Movavi", 300),
        ("Скидка на обучение 10%","Скидка на следующий месяц обучения", 500),
    ]:
        s.add(ShopItem(name=name, description=desc, price=price))

    # Новости
    s.add(News(text="🎉 Добро пожаловать в Movavik — бот IT Школы Movavi!\n\nЗдесь вы найдёте расписание, оценки, мероприятия и многое другое."))

    s.commit()
    s.close()
    print("✅ Демо-данные успешно загружены!")
