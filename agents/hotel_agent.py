# Hotel booking agent
from fetchai.ledger.api import LedgerApi
from fetchai.ledger.contract import Contract
from fetchai.ledger.crypto import Entity

class HotelAgent:
    def __init__(self, entity: Entity, contract: Contract):
        self.entity = entity
        self.contract = contract
        self.api = LedgerApi('127.0.0.1', 8000)
    
    def search_hotels(self, location, checkin, checkout, guests):
        """Query the smart contract for available hotels"""
        query = self.contract.query(
            self.api, 'availableHotels',
            location=location, checkin=checkin, 
            checkout=checkout, guests=guests
        )
        return query
    
    def book_hotel(self, hotel_id, guest_info, payment):
        """Book a hotel using the smart contract"""
        self.contract.action(
            self.api, 'bookHotel',
            self.entity, hotel_id=hotel_id, 
            guest_info=guest_info, payment=payment
        )
        return True
    
    def cancel_booking(self, booking_id):
        """Cancel a hotel booking"""
        self.contract.action(
            self.api, 'cancelBooking',
            self.entity, booking_id=booking_id
        )
        return True