"""Puertos: los contratos que el dominio le exige a la infraestructura y a la capa de aplicación.

Se usa Protocol en vez de clases bases abstractas, para que un adaptador no tenga que heredar de nada nuestro

El puerto conversacional no vive aqui. Guarda mensajes del LLM que es un concepto alejado al dominio
"""

from typing import Protocol

from app.domain.models import Category, Product, Order, PaymentMethod, Customer

class CatalogRepository(Protocol):
  """Lectura del catalogo: categorias e inventario"""
  async def list_categories(self) -> list[Category]: ...
  
  async def list_products(self, category_id:str | None  = None) -> list[Product]: ...
  
  async def get_product(self, product_id:str) -> Product | None: ...
  
  
class OrderRepository(Protocol):
  """Alta y gestion de pedidos""" 
  """create_order envia solo un producto y cantidad. El total y los precios los calcula el sistema de pedidos"""
  
  async def create_order(self, customer_id:str, items: list[tuple[str, int]], delivery_address:str, payment_method:PaymentMethod, notes: str | None = None) -> Order: ...
  
  async def get_order(self, order_id: str) -> Order | None: ...
  
  async def list_orders_for_customer(self, order_id: str) -> Order: ...
  
  async def update_delivery_address(self, order_id: str, address: str) -> Order: ...
  
class CustomerRepository(Protocol):
  """Gestion de clientes"""
  async def find_by_phone(self, phone:str) -> Customer | None: ...
  
  async def find_or_create(
    self, 
    full_name:str,
    phone:str,
    email:str | None = None,
    default_address:str | None = None
  ) -> Customer: ...
  
  async def update(self, customer_id:str, changes: dict[str, str | None]) -> Customer: ...