from fastapi import FastAPI, HTTPException
import uvicorn
from pymongo.errors import PyMongoError
from mysite.database.mongodb import close_mongodb, connect_mongodb, get_database
from contextlib import asynccontextmanager
from mysite.api import bookings

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await connect_mongodb()
        print('Mongodb: подключение успешно')
        yield
    finally:
        await close_mongodb()
        print('Mongodb: соединение закрыто')

booking_app = FastAPI(title='Booking Service', lifespan=lifespan)
booking_app.include_router(bookings.booking_router)

# @booking_app.get('/')
# async def test_info():
#     return {"message": 'Все работает'}

@booking_app.get('/check/database')
async def check_database():
    try:
        database = await get_database()
        await database.command('ping')

        return {'status': 'ok',
                'database': database.name,
                'connection': 'active'}

    except PyMongoError:
        raise HTTPException(status_code=500, detail='Mongodb не доступен')



if __name__ == '__main__':
    uvicorn.run(booking_app, host='127.0.0.1', port=8002)