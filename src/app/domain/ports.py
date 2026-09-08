"""Puertos: los contratos que el dominio le exige a la infraestructura y a la capa de aplicación.

Se usa Protocol en vez de clases bases abstractas, para que un adaptador no tenga que heredar de nada nuestro

El puerto conversacional no vive aqui. Guarda mensajes del LLM que es un concepto alejado al dominio
"""



from typing import Protocol

from app.domain.models import Category, Product, Order, PaymentMethod, Customer

class CatalogRepository(Protocol):
  """Lectura del catalogo: categorias e inventario"""
  
  