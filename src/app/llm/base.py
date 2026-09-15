"""
Puerto del LLM: tipos neutros y el contrato que cumple todo proveedor


Este modulo es la frontera. Nada por encima de el (agente, tools, dominio, API)
importa el SKD de ningun proveeodr. Cambiar de modelo o de vendedor significa escribir 
un adaptador nuevo que implemente LLMProvifer, y nada mas

"""



from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

Role = Literal['user', 'assistant']
StopReason = Literal['end_turn', 'tool_use', 'max_tokens', 'refusal']


@dataclass(frozen=True, slots=True)
class ToolSpec:
  """Descripcion de una herramienta en terminos neutros (JSON Schema)"""
  
  name: str
  description: str
  parameters: dict[str, Any]
  
@dataclass(frozen=True, slots=True)
class ToolCall:
  """Llamada a una herramienta, en terminos neutros (JSON)"""
  id: str
  name: str
  arguments: dict[str, Any]
  
  
@dataclass(frozen=True, slots=True)
class ToolResult:
  """Resultado de una herramienta, en terminos neutros (JSON)"""
  call_id: str
  content: str
  is_error: bool = False
  
  
@dataclass(slots=True)
class LLMMessage:
  
  """Un turno de la conversacion, independiente del proveedor
  
    -role="user"
    -role="assistant"
  """
  
  
  role: Role
  text: str = ""
  tool_calls: list[ToolCall] = field(default_factory=list)
  tool_results: list[ToolResult] = field(default_factory=list)
  provider: str | None = None
  provider_raw: Any | None = None
   # "Cachea el prefijo hasta aqui". Es intencion, no mecanismo: el agente sabe
    # que este mensaje es una frontera estable, y cada adaptador decide como se
    # expresa eso en su API (Anthropic: `cache_control`; los endpoints
    # compatibles con OpenAI cachean solos y lo ignoran). Por eso vive en el
    # puerto y no en un adaptador: la politica de contexto es una sola para
    # todos los proveedores. No se persiste: se decide en cada peticion.
  cache_hint: bool = False
  
  
  
@dataclass(frozen=True, slots=True)
class Usage:
  
  """Tokens de un turno, separados por como se facturan

   los tres se cobran a precios distintos: leer de cache sale ~10% de un token
   de entrada, y escribirlo ~125%. Sumar todo junto esconde de donde viene
   la factura, que es justo lo que hay que mirar para bajarla
  
  """
  
  input_tokens: int = 0
  output_tokens: int = 0
  cache_read_tokens: int = 0
  cache_write_tokens: int = 0
  
  def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            self.input_tokens + other.input_tokens,
            self.output_tokens + other.output_tokens,
            self.cache_read_tokens + other.cache_read_tokens,
            self.cache_write_tokens + other.cache_write_tokens,
        )
  
  


@dataclass(frozen=True, slots=True)
class LLMResponse:
  """Respuesta de un LLM, independiente del proveedor"""
  
  messages: LLMMessage
  stop_reason: StopReason
  usage: Usage = Usage()
  
  
class LLMProvider(Protocol):
  """Contrato unico que debe cumplir cualquier proveedor de modelo"""