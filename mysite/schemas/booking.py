from pydantic import BaseModel, Field, model_validator
from enum import Enum
from datetime import date, datetime


class BookingStatus(str, Enum):
    pending = 'pending'
    cancelled = 'cancelled'
    confirmed = 'confirmed'

class BookingCreateSchema(BaseModel):
    hotel_id: int = Field(gt=0)
    room_id: int = Field(gt=0)
    check_in: date
    check_out: date
    guests: int = Field(ge=1, le=20)

    @model_validator(mode='after')
    def validate_dates(self):
        if self.check_in < date.today():
            raise ValueError('Нельзя бронировать прошедшую дату')

        if self.check_out <= self.check_in:
            raise ValueError('Дата выезда должна быть позжу даты заезда')

        return self



class BookingUpdateCreate(BaseModel):
    check_in: date | None = None
    check_out: date | None = None
    guests: int | None = Field(default=None, ge=1, le=20)

class BookingResponseSchema(BaseModel):
    id: str
    user_id: int
    hotel_id: int
    hotel_name: str
    room_id: int
    room_number: int
    check_in: date
    check_out: date
    nights: int
    guests: int
    price: int
    total_price: int
    status: BookingStatus
    created_date: datetime
    updated_date: datetime
