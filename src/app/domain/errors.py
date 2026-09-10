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
    
    
    
    