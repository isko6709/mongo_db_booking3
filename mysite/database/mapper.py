def booking_document_to_responce(document: dict):
    return {
        'id': str(document['_id']),
        "user_id": document['user_id'],
        "hotel_id": document['hotel_id'],
        "hotel_name": document['hotel_name'],
        "room_id": document['room_id'],
        "room_number": document['room_number'],
        "check_in": document['check_in'],
        "check_out": document['check_out'],
        "nights": document['nights'],
        "guests": document['guests'],
        "price": document['price'],
        "total_price": document['total_price'],
        "status": document['status'],
        "created_date": document['created_date'],
        "updated_date": document['created_date'],
    }
