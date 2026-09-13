"""Estado de la conversacion y su puerto de persistencia.

Vive fuera del proceso (Postgres) para que el endpoint REST sea sin estado y para
que el mismo nucleo sirva despues en WhatsApp, donde no hay sesion HTTP.
"""



from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

from app.domain.models import Customer, DraftOrder
from app.llm.base import LLMMessage


@dataclass(slots=True)

class ConversationState:
    """Estado de la conversacion."""

    conversation_id: str
    channel: Customer = field(default_factory=Customer)
    draft: DraftOrder = field(default_factory=DraftOrder)
    messages: list[LLMMessage] = field(default_factory=list)
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    #Version de la fila de la que se cargo este estado. 0 = nunca se gaurdo
    # Viaja con el estado para detectar escrituras concurrentes al guardar
    version: int = 0
    
    
    def window(self, max_messages: int = 40) -> list[LLMMessage]:
      """Ventana reciente del historial, para enviarle al modelo. """
      return _cut(self.messages, max_messages)
    
    def trim(self, max_messages: int = 80) -> None:
      """Descarta lo mas viejo del historial
      `window` solo acota lo que se envia; sin esto la lista en si crece para siempre
      la conversacion ocupa cada vez mas memoria y la fila en la base cada vez mas espacio
      Se recorta mas largo que la ventana para conservar un poco de contexto y no perder la continuidad de la conversacion
      """
      
      self.messages = _cut(self.messages, max_messages)
      
      
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
  """Otro proceso escrivio esta conversacion mientras se procesaba el turno.
  Vive aqui, junto al puerto, y no en el adaptador de Postgres: quien consume el puerto 
  tiene que poder capturarlo sin importat quien lo implemente
  """
  
  
class ConversationRepository(Protocol):
  async def load(self, conversation_id: str) -> ConversationState | None: ...
  
  async def save(self, state: ConversationState) -> None: ...