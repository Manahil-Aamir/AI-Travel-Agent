# Shopping agent
from fetchai.ledger.api import LedgerApi
from fetchai.ledger.contract import Contract
from fetchai.ledger.crypto import Entity

class ShoppingAgent:
    def __init__(self, entity: Entity, contract: Contract):
        self.entity = entity
        self.contract = contract
        self.api = LedgerApi('127.0.0.1', 8000)
    
    def search_products(self, query, platform="ebay"):
        """Search for products across platforms"""
        query = self.contract.query(
            self.api, 'searchProducts',
            query=query, platform=platform
        )
        return query
    
    def purchase_product(self, product_id, shipping_info, payment):
        """Purchase a product using the smart contract"""
        self.contract.action(
            self.api, 'purchaseProduct',
            self.entity, product_id=product_id,
            shipping_info=shipping_info, payment=payment
        )
        return True
    
    def track_order(self, order_id):
        """Track an existing order"""
        query = self.contract.query(
            self.api, 'trackOrder',
            order_id=order_id
        )
        return query