"""
Сидинг для Booking-сервиса (service3, FastAPI + MongoDB).

Идёт в обход HTTP API (не поднимает все 3 сервиса), а читает данные
НАПРЯМУЮ из БД других сервисов:
  - пользователей — из SQLite service1 (user.db)
  - отели/комнаты — из PostgreSQL service2 (booking_db)
и пишет тестовые бронирования напрямую в MongoDB коллекцию `bookings`,
повторяя структуру документа из mysite/database/mapper.py.

Нужны установленные пакеты: pymongo, psycopg2-binary (или psycopg2).
    pip install pymongo psycopg2-binary --break-system-packages

Настройки Mongo берутся из .env этого сервиса (MONGODB_URL, MONGODB_DB_NAME).
Настройки Postgres и путь к SQLite service1 — см. константы ниже или флаги CLI.

Запуск (из корня service3, там где лежит .env):
    python seed_data.py --sqlite ../service1/user.db
    python seed_data.py --sqlite ../service1/user.db --bookings 200

ВНИМАНИЕ: этот скрипт не проверялся на реальном Mongo Atlas кластере из
текущего окружения (нет доступа к внешним БД из песочницы) — логика
проверена вручную по вашей схеме (mapper.py/booking.py), но перед
использованием в проде рекомендую сначала прогнать на тестовой базе.
"""
import argparse
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "mongo_db")

# дефолты взяты из settings.py service2 (booking_app) — поменяйте, если у вас иначе
PG_DEFAULTS = dict(
    dbname="booking_db",
    user="postgres",
    password="adminadmin",
    host="localhost",
    port="5432",
)

BOOKING_STATUSES = ["pending", "cancelled", "confirmed"]


def fetch_users(sqlite_path: str):
    con = sqlite3.connect(sqlite_path)
    cur = con.cursor()
    cur.execute("SELECT id FROM profile")
    ids = [row[0] for row in cur.fetchall()]
    con.close()
    if not ids:
        raise RuntimeError(f"В {sqlite_path} не найдено ни одного пользователя — сначала запустите seed_data.py в service1")
    return ids


def fetch_hotels_and_rooms(pg_kwargs: dict):
    import psycopg2

    con = psycopg2.connect(**pg_kwargs)
    cur = con.cursor()
    cur.execute("SELECT id, hotel_name FROM booking_app_hotel")
    hotels = {row[0]: row[1] for row in cur.fetchall()}

    cur.execute("SELECT id, hotel_id, room_number, price FROM booking_app_room")
    rooms = [
        {"id": row[0], "hotel_id": row[1], "room_number": row[2], "price": row[3]}
        for row in cur.fetchall()
    ]
    con.close()

    if not hotels or not rooms:
        raise RuntimeError("В PostgreSQL нет отелей/комнат — сначала запустите `manage.py seed_data` в service2")

    return hotels, rooms


def build_booking(user_id: int, hotel_name: str, room: dict, now: datetime) -> dict:
    # часть броней в прошлом (завершённые), часть в будущем (актуальные)
    in_future = random.random() < 0.6
    if in_future:
        check_in = now + timedelta(days=random.randint(1, 90))
    else:
        check_in = now - timedelta(days=random.randint(1, 120))

    nights = random.randint(1, 14)
    check_out = check_in + timedelta(days=nights)
    guests = random.randint(1, 4)
    price = room["price"]
    total_price = price * nights

    status = random.choice(BOOKING_STATUSES)
    created_date = check_in - timedelta(days=random.randint(1, 30))
    if created_date > now:
        created_date = now - timedelta(days=random.randint(1, 5))

    return {
        "user_id": user_id,
        "hotel_id": room["hotel_id"],
        "hotel_name": hotel_name,
        "room_id": room["id"],
        "room_number": room["room_number"],
        "check_in": check_in,
        "check_out": check_out,
        "nights": nights,
        "guests": guests,
        "price": price,
        "total_price": total_price,
        "status": status,
        "created_date": created_date,
        "updated_date": created_date,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite", default="../service1/user.db", help="Путь к user.db сервиса auth")
    parser.add_argument("--pg-host", default=PG_DEFAULTS["host"])
    parser.add_argument("--pg-port", default=PG_DEFAULTS["port"])
    parser.add_argument("--pg-db", default=PG_DEFAULTS["dbname"])
    parser.add_argument("--pg-user", default=PG_DEFAULTS["user"])
    parser.add_argument("--pg-password", default=PG_DEFAULTS["password"])
    parser.add_argument("--bookings", type=int, default=200, help="Сколько бронирований создать")
    parser.add_argument("--flush", action="store_true", help="Очистить коллекцию bookings перед сидингом")
    args = parser.parse_args()

    from pymongo import MongoClient

    user_ids = fetch_users(args.sqlite)
    hotels, rooms = fetch_hotels_and_rooms(dict(
        dbname=args.pg_db, user=args.pg_user, password=args.pg_password,
        host=args.pg_host, port=args.pg_port,
    ))

    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[MONGODB_DB_NAME]
    collection = db["bookings"]

    if args.flush:
        collection.delete_many({})

    now = datetime.now(timezone.utc)
    documents = []
    for _ in range(args.bookings):
        room = random.choice(rooms)
        hotel_name = hotels[room["hotel_id"]]
        user_id = random.choice(user_ids)
        documents.append(build_booking(user_id, hotel_name, room, now))

    result = collection.insert_many(documents)
    print(f"Создано бронирований: {len(result.inserted_ids)}")

    client.close()


if __name__ == "__main__":
    main()
