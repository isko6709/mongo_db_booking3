from pymongo import AsyncMongoClient
from mysite.config import settings

mongo_client: AsyncMongoClient | None = None
mongo_database = None


async def connect_mongodb():
    global mongo_client, mongo_database

    mongo_client = AsyncMongoClient(
        settings.mongodb_url,
        serverSelectionTimeoutMS=5000,
        tz_aware=True
    )

    await mongo_client.admin.command('ping')

    mongo_database = mongo_client[
        settings.mongodb_db_name
    ]


async def close_mongodb():
    global mongo_client, mongo_database

    if mongo_client is not None:
        await mongo_client.close()

    mongo_client = None
    mongo_database = None

async def get_database():
    if mongo_database is None:
        raise RuntimeWarning('Подключение болгон жок')
    return mongo_database


async def get_booking_collections():
    database = await get_database()
    return database['bookings']