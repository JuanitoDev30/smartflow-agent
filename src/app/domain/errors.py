"""Errores del dominio

Se distinguen los errores tecnicos.
El agente puede explicarle al cliente en lenguaje natural que hubo un error tecnico y que vuelva a intentar mas tarde.
"""



class DomainError(Exception):
  """Error generico del dominio"""
  
  
class ProductNotFound(DomainError):
  """No se encontro el producto solicitado"""
  def __init__(self, product_id:str) -> None:
    super().__init__(f"Producto {product_id} no encontrado")
    self.product_id = product_id
    
    
class ProductNotAvailable(DomainError):
  """El producto solicitado no esta disponible"""
  def __init__(self, name:str) -> None:
    super().__init__(f"Producto {name} no disponible por el momento")
    self.name = name
    
class InsuficientStock(DomainError):
  """No hay suficiente stock del producto solicitado"""
  def __init__(self, name:str, requested:int, available:int) -> None:
    super().__init__(f"Producto {name} no tiene suficiente stock. Solicitado: {requested}, Disponible: {available}")
    self.name = name
    self.requested = requested
    self.available = available
    
    
class OrderNotFound(DomainError):
  """No se encontro la orden solicitada"""
  def __init__(self, reference:str) -> None:
    super().__init__(f"Orden {reference} no encontrada")
    self.reference = reference
    
    
class OrderNotCancellable(DomainError):
  """La orden solicitada no puede ser cancelada"""
  def __init__(self, reference:str, status:str) -> None:
    super().__init__(f"Orden {reference} no puede ser cancelada. Estado: {status}")
    self.reference = reference
    self.status = status
    
    
class IncompleteOrderData(DomainError):
  """La orden solicitada no tiene todos los datos necesarios para ser procesada"""
  def __init__(self, missing_fields:list[str]) -> None:
    super().__init__(f"Orden no tiene todos los datos necesarios para ser procesada. Campos faltantes: {missing_fields}")
    self.missing_fields = missing_fields
    
    
class InvalidPhoneNumber(DomainError):
  """El numero de telefono proporcionado no es valido"""
  def __init__(self, digits:str) -> None:
    super().__init__(f"El telefono debe tener exactamente 10 digitos. Se recibieron {digits}")
    self.digits = digits
    
    
class EmptyOrder(DomainError):
  """La orden solicitada no tiene productos"""
  def __init__(self) -> None:
    super().__init__(f"La orden no tiene productos")
    
    
class BackendUnvailable(DomainError):
  """El backend no esta disponible"""
  def __init__(self, detail: str = "") -> None:
    super().__init__(f"El sistema no esta respondiendo en este momento. {detail}")
    self.detail = detail