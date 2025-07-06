# Flight booking agent
from fetchai.ledger.api import LedgerApi
from fetchai.ledger.contract import Contract
from fetchai.ledger.crypto import Entity

class FlightAgent:
    def __init__(self, entity: Entity, contract: Contract):
        self.entity = entity
        self.contract = contract
        self.api = LedgerApi('127.0.0.1', 8000)
    
    def search_flights(self, origin, destination, date):
        """Query the smart contract for available flights"""
        query = self.contract.query(
            self.api, 'availableFlights',
            origin=origin, destination=destination, date=date
        )
        return query
    
    def book_flight(self, flight_id, passenger_info):
        """Book a flight using the smart contract"""
        self.contract.action(
            self.api, 'bookFlight',
            self.entity, flight_id=flight_id, passenger_info=passenger_info
        )
        return True