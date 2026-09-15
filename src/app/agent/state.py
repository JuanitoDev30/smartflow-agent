"""Estado de la conversacion y su puerto de persistencia.

Vive fuera del proceso (Postgres) para que el endpoint REST sea sin estado y para
que el mismo nucleo sirva despues en WhatsApp, donde no hay sesion HTTP.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

from app.domain.models import Customer, DraftOrder, DraftReservation
from app.llm.base import LLMMessage, Usage


@dataclass(slots=True)
class ConversationState:
    conversation_id: str
    channel: str = "web"
    customer: Customer = field(default_factory=Customer)
    draft: DraftOrder = field(default_factory=DraftOrder)
    # La reserva de mesa es un flujo aparte del pedido: un cliente puede
    # reservar sin pedir, pedir sin reservar, o las dos cosas en la misma
    # conversacion. Por eso son dos borradores y no uno con campos opcionales.
    reservation: DraftReservation = field(default_factory=DraftReservation)
    messages: list[LLMMessage] = field(default_factory=list)
    # Lo que lleva gastado la conversacion entera, no solo el ultimo turno. Es la
    # unica cifra que permite comparar: un turno caro no dice nada, y el total de
    # la cuenta al final de mes no dice de donde salio. Se persiste con el estado
    # para que sobreviva al reinicio, igual que el historial.
    usage: Usage = field(default_factory=Usage)
    turns: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    # Version de la fila de la que se cargo este estado. 0 = nunca se guardo.
    # Viaja con el estado para detectar escrituras concurrentes al guardar.
    version: int = 0

    def trim(self, max_messages: int = 80) -> None:
        """Tope duro al tamano de la fila, en numero de mensajes.

        Es la red de seguridad del almacenamiento, no la politica de contexto:
        de cuanto historial se le manda al modelo se encarga `app.agent.budget`,
        que mide en tokens, que es la unidad en la que llega la factura.

        El recorte es en tandas y no continuo: al cruzar el tope se baja de golpe
        a `_TRIM_RELIEF` del tope. Recortar de a un mensaje por turno cambiaria
        el principio del historial en cada peticion, y como la cache del modelo
        es coincidencia de prefijo, eso invalidaria la conversacion entera cada
        vez. Un corte grande de vez en cuando cuesta un fallo; uno chico cada
        turno cuesta todos.
        """
        if len(self.messages) <= max_messages:
            return
        self.messages = _cut(self.messages, int(max_messages * _TRIM_RELIEF))


# A que fraccion del tope se baja cuando se cruza. Ver ConversationState.trim.
_TRIM_RELIEF = 0.7


def _cut(messages: list[LLMMessage], limit: int) -> list[LLMMessage]:
    """Ultimos `limit` mensajes, sin dejar huerfano un resultado de herramienta.

    Un tool_result sin su tool_use hace que la API rechace la peticion entera,
    asi que el corte se desplaza hasta caer en un limite valido.
    """
    if len(messages) <= limit:
        return list(messages)
    cut = messages[-limit:]
    while cut and cut[0].tool_results:
        cut = cut[1:]
    return cut


class ConversationConflict(RuntimeError):
    """Otro proceso escribio esta conversacion mientras se procesaba el turno.

    Vive aqui, junto al puerto, y no en el adaptador de Postgres: quien consume
    el puerto tiene que poder capturarlo sin importar quien lo implemente.
    """


class ConversationRepository(Protocol):
    async def load(self, conversation_id: str) -> ConversationState | None: ...

    async def save(self, state: ConversationState) -> None: ...

    async def find_by_reservation(self, reservation_id: str) -> str | None:
        """Conversacion que registro esa reserva, si sigue viva.

        Es de mejor esfuerzo: la conversacion expira a las 72 horas y la reserva
        puede confirmarse despues. Quien lo llame tiene que aguantar un None.
        """
        ...
