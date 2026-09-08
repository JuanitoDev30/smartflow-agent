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
    
    @property
    def sellable(self) -> bool:
        """Indica si el producto se puede vender"""
        return self.status.sellable and self.stock > 0
      
      
    @property
    def availability_note(self) -> str | None:
      """Aviso de escases, para que el agente pueda mencionarlo sin inverntarlo"""  
      if self.status == ProductStatus.LOW_STOCK:
          return "Quedan pocas unidades"
      return None  
   
class Customer(BaseModel):
  """Datos del cliente"""
  id: str | None = None
  full_name: str | None = None
  phone: str | None = None
  email: str | None = None
  default_address: str | None = None
  
  def normalized_phone(self) -> str | None:
      """Devuelve el teléfono normalizado a 10 dígitos"""
      return normalize_phone(self.phone)
    
    
class OrderLine(BaseModel):
    """Línea de pedido"""
    product_id: str
    name: str
    quantity: int = Field(gt=0)
    unit_price: Decimal
    
    @property
    def subtotal(self) -> Decimal:
        """Crea una línea de pedido a partir de un producto y una cantidad"""
        return self.unit_price * self.quantity
    
class DraftOrder(BaseModel):
    """Pedido en construccion. Solo se envia al backend cuando el cliente confirma la compra"""
    
    lines: list[OrderLine] = Field(default_factory=list)
    delivery_address: str | None = None
    payment_method: PaymentMethod | None = None
    notes: str | None = None
    #None = todavia no se le pregunto al cliente
    save_address_as_default: bool | None = None
    placed_order_id: str | None = None  # ID del pedido confirmado, si ya se ha confirmado
    
    @property
    def is_empty(self) -> bool:
        """Indica si el pedido está vacío"""
        return not self.lines
    
    
    def find(self, product_id: str) -> OrderLine | None: 
        return next((line for line in self.lines if line.product_id == product_id), None)
    
    def upsert(self, line: OrderLine) -> None:
        """Agrega o actualiza una linea de pedido"""
        existing_line = self.find(line.product_id)
        if existing_line is None:
            self.lines.append(line)
        else:
            existing_line.quantity = line.quantity
            existing_line.unit_price = line.unit_price
            
            
    def remove(self, product_id: str) -> bool:
        """Elimina una línea de pedido. Devuelve True si se eliminó, False si no existía"""
        before = len(self.lines)
        self.lines = [line for line in self.lines if line.product_id != product_id]
        return len(self.lines) != before
    
    def missing_fields(self, customer: Customer) -> list[str]:
        """Que falta para poder registrar el pedido, en lenguaje para el cliente"""
        missing: list[str] = []
        if not customer.full_name:
            missing.append("nombre completo")
        if not is_valid_phone(customer.phone):
            missing.append(f"teléfono de  {PHONE_DIGITS} dígitos")
            
        if not self.delivery_address:
            missing.append("dirección de entrega")
        if self.payment_method is None:
            missing.append("método de pago (EFECTIVO, TARJETA o TRANSFERENCIA)")
        if self.save_address_as_default is None:
            missing.append("confirmar si desea guardar la dirección como predeterminada")
        return missing
    
    
class Order(BaseModel):
    """Pedido tal como existe en el sistema de pedidos"""
    
    id: str
    status: OrderStatus
    customer_id: str | None = None
    lines: list[OrderLine]
    total: Decimal
    delivery_address: str | None = None
    payment_method: PaymentMethod | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    
    @property
    def short_code(self) -> str:
        """Devuelve los primeros 6 caracteres del ID del pedido, para mostrar al cliente"""
        return self.id[6:]
            
            