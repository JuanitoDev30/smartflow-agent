"""Contexto que reciben las herramientas al ejecutarse.

Es inyeccion de dependencias explicita: una tool no busca sus colaboradores por
su cuenta ni importa modulos de infraestructura, los recibe aqui. Eso las hace
testeables con fakes y evita acoplarlas a la BD.
"""

from dataclasses import dataclass

from app.agent.state import ConversationState
from app.domain.ports import CatalogRepository, CustomerRepository, OrderRepository
from app.services.order_service import OrderService


@dataclass(slots=True)
class AgentContext:
    state: ConversationState
    catalog: CatalogRepository
    orders: OrderRepository
    customers: CustomerRepository
    order_service: OrderService
