
"""Reglas de negocio del pedido.

Aqui vive lo que No puede quedar en manos del modelo: Validacion de stock,
precios, telefono, y el orden correcto de las llamadas al sistema de pedidos.
Las herramientas del agente son una capa delgada sobre este servicio

"""


import logging
import unicodedata

from app.agent.state import ConversationState
from app.domain.errors import (
    EmptyOrder,
    IncompleteOrderData,
    InsufficientStock,
    InvalidPhone,
    OrderNotCancellable,
    OrderNotEditable,
    OrderNotFound,
    ProductNotAvailable,
    ProductNotFound,
)
from app.domain.models import (
    Order,
    OrderLine,
    Product,
    normalize_phone,
)
from app.domain.ports import CatalogRepository, CustomerRepository, OrderRepository

logger = logging.getLogger(__name__)


def _fold(text: str) -> str:
    """Minusculas sin tildes, para buscar 'cafe' y encontrar 'Café'."""
    normalized = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")

class OrderService:
    def __init__(
        self,
        catalog: CatalogRepository,
        orders: OrderRepository,
        customers: CustomerRepository,
    ) -> None:
        self._catalog = catalog
        self._orders = orders
        self._customers = customers
        
        
    async def find_products(
        self,
        query: str | None = None,
        category_id: str | None = None,
        only_available: bool = True,
        limit: int =15,
        
    ) -> list[Product]:
        
        """Busca en el catalogo"""
        products = await self._catalog.list_products(category_id)
        if only_available:
            products = [p for p in products if p.sellable]

        if query:
            needle = _fold(query)
            terms = [t for t in needle.split() if t]
            products = [
                p
                for p in products
                if all(
                    term in _fold(f"{p.name} {p.description or ''} {p.code or ''}")
                    for term in terms
                )
            ]
        return products[:limit]
    
    
    # Borrador del pedido