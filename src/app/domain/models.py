"""Modelos del dominio de la aplicación.

  - No saben nada de SQL, de HTTP ni del LLM. Los adaptadores de infraestructura traducen desde/hacia el contrato real del backend
  

"""



import re
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

PHONE_DIGITS = 10


class OrderStatus(StrEnum):
    """Estado de un pedido"""

    PENDIENTE = "PENDIENTE"
    CONFIRMADO = "CONFIRMADO"
    EN_PREPARACION = "EN_PREPARACION"
    EN_CAMINO = "EN_CAMINO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"
    
    @property
    def is_cancellable(self) -> bool :
      """Solo se cancela antes de que el pedido entre en preparación"""
      return self in (OrderStatus.PENDIENTE, OrderStatus.CONFIRMADO)
    
    
    @property
    def is_editable(self) -> bool:
      """Solo se puede editar antes de que el pedido entre en preparación"""
      return self in (OrderStatus.PENDIENTE, OrderStatus.CONFIRMADO)
    
    
    @property
    def label(self) -> str:
      return {
        OrderStatus.PENDIENTE: "pendiente de confirmacion",
        OrderStatus.CONFIRMADO: "confirmado",
        OrderStatus.EN_PREPARACION: "en preparacion",
        OrderStatus.EN_CAMINO: "en camino",
        OrderStatus.ENTREGADO: "entregado",
        OrderStatus.CANCELADO: "cancelado",
      }[self]
      
      
class PaymentMethod(StrEnum):
        """Método de pago"""
        EFECTIVO = "EFECTIVO"
        TARJETA = "TARJETA"
        TRANSFERENCIA = "TRANSFERENCIA"
        
        
class ProductStatus(StrEnum):
        """Estado de un producto"""
        ACTIVE = "active"
        LOW_STOCK = "low_stock"
        INACTIVE = "inactive"
        OUT_OF_STOCK = "out_of_stock"
        
        @property
        def sellable(self) -> bool:
            """Indica si el producto se puede vender"""
            return self in (ProductStatus.ACTIVE, ProductStatus.LOW_STOCK)
          
def normalize_phone(phone: str | None) -> str | None:
    """Normaliza un número de teléfono a 10 dígitos, eliminando caracteres no numéricos y el código de país si es necesario."""
    if phone is None:
        return None
    # Eliminar todos los caracteres que no sean dígitos
    digits = re.sub(r"\D", "", phone)
    # Si el número tiene más de 10 dígitos, eliminar el código de país (asumiendo que es un prefijo de 1 dígito)
    if len(digits) > PHONE_DIGITS:
        digits = digits[-PHONE_DIGITS:]
    return digits if len(digits) == PHONE_DIGITS else None
  
def is_valid_phone(phone: str | None) -> bool:
    """Valida si un número de teléfono es válido (10 dígitos)."""
    normalized = normalize_phone(phone)
    return normalized is not None and len(normalized) == PHONE_DIGITS 

class Category(BaseModel):
    """Modelo de categoría de producto"""
    id: int
    name: str
    
    
class Product(BaseModel):
    """Modelo de producto"""
    id: int
    name: str
    description: str | None = None
    category_id: int | None = None
    category_name: str | None = None
    unit_price: Decimal
    stock: int
    status: ProductStatus = ProductStatus.ACTIVE
   
   