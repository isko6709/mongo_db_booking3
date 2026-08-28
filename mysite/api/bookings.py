import asyncio
from fastapi import APIRouter, Depends, HTTPException
from mysite.schemas.booking import BookingResponseSchema, BookingCreateSchema, BookingStatus
from mysite.database.mongodb import get_booking_collections
from mysite.database.mapper import booking_document_to_responce
from .dependencies import get_current_user
from typing import Annotated, List
from mysite.clients.hotel_service import get_hotel, get_room
from datetime import datetime, time, timezone

booking_router = APIRouter(prefix='/bookings', tags=['Bookings'])


@booking_router.get('/', response_model=List[BookingResponseSchema])
async def booking_list(current_user: Annotated[dict, Depends(get_current_user)]):
    collection = await get_booking_collections()
    cursor = collection.find({'user_id': current_user['id']}).sort('created_date', -1)

    bookings = []
    async for i in cursor:
        bookings.append(booking_document_to_responce(i))

    return bookings


@booking_router.post('/', response_model=BookingResponseSchema)
async def booking_create(booking: BookingCreateSchema, current_user: Annotated[dict, Depends(get_current_user)]):
    hotel, room = await asyncio.gather(get_hotel(booking.hotel_id), get_room(booking.room_id))

    if booking.hotel_id != room['hotel']['id']:
        raise HTTPException(status_code=400, detail='Комната не относится к выбранному отелю')

    check_in_datetime = datetime.combine(booking.check_in, time.min, tzinfo=timezone.utc)
    check_out_datetime = datetime.combine(booking.check_out, time.min, tzinfo=timezone.utc)

    collection = await get_booking_collections()

    nights = (booking.check_out - booking.check_in).days
    total_price = room['price'] * nights

    booking_document = {
        'user_id': current_user['id'],
        'hotel_id': booking.hotel_id,
        'hotel_name': hotel['hotel_name'],
        'room_id': booking.room_id,
        'room_number': room['room_number'],
        'check_in': check_in_datetime,
        'check_out': check_out_datetime,
        'nights': nights,
        'guests': booking.guests,
        'price': room['price'],
        'total_price': total_price,
        'status': BookingStatus.confirmed.value,
        'created_date': datetime.now(timezone.utc),
        'updated_date': datetime.now(timezone.utc),
    }

    result = await collection.insert_one(booking_document)
    booking_document['_id'] = result.inserted_id

    return booking_document_to_responce(booking_document)