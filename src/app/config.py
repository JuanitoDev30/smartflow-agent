"""Configuracion de la aplicacion, leida del entorno (12-factor)."""

from decimal import Decimal
from functools import lru_cache
from typing import TYPE_CHECKING, Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from app.llm.pricing import ModelPrice


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Proveedor de LLM. El nucleo del agente no conoce estos valores;
    # solo la factory de app/llm los interpreta.
    llm_provider: str = "anthropic"
    llm_model: str = "claude-opus-5"
    llm_max_tokens: int = 8000
    # Solo para los adaptadores de Claude (API directa y Bedrock). Ojo: los
    # modelos de Bedrock van una version atras y rechazan "xhigh" con un 400.
    llm_effort: Literal["low", "medium", "high", "xhigh", "max"] = "medium"
    anthropic_api_key: str | None = None
    # Solo para el adaptador de Bedrock. Si no se cargan, el SDK resuelve las
    # credenciales como cualquier cliente de AWS: entorno, perfil, o el rol de
    # la instancia (lo preferible en produccion: no hay secreto que rotar).
    aws_region: str = "us-east-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None
    # Solo para el adaptador compatible con OpenAI (NVIDIA NIM, vLLM, Ollama...).
    llm_base_url: str | None = None
    # Se aceptan los nombres de variable habituales de cada proveedor, para no
    # obligar a renombrar una key que ya esta exportada en el entorno.
    llm_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "LLM_API_KEY", "NVIDIA_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "TOGETHER_API_KEY"
        ),
    )

    # Backend de datos: memory (fakes, sin dependencias) o api (backend real).
    repository_backend: Literal["memory", "api"] = "memory"
    api_base_url: str = "http://localhost:3001/api"
    api_timeout_seconds: float = 15.0
    # Cuenta de servicio del agente. Debe ser propia, con los permisos minimos:
    # leer catalogo, y crear/consultar pedidos y clientes. Nada mas.
    api_email: str | None = None
    api_password: str | None = None
    api_login_path: str = "/auth/login"
    # Alternativa a email/password si el backend emite tokens de larga duracion.
    # Un token fijo no se renueva: cuando expire, el agente deja de funcionar.
    api_token: str | None = None

    # Base propia del agente (conversaciones). Distinta de la del negocio: el
    # agente nunca debe poder migrar ni tocar tablas administrativas.
    agent_database_url: str = ""
    conversation_ttl_hours: int = 72
    conversation_max_messages: int = 80
    conversation_sweep_minutes: int = 60

    # --- Exposicion al frontend ---------------------------------------------
    # Origenes permitidos, separados por coma. En produccion NUNCA "*": el chat
    # devuelve datos personales del cliente (nombre, telefono, direccion).
    allowed_origins: str = "http://localhost:3000"
    # Clave para firmar los tokens de conversacion. Si cambia, las sesiones
    # abiertas dejan de valer y los clientes empiezan una conversacion nueva.
    session_secret: str = ""
    session_ttl_hours: int = 72
    # Limite por conversacion y por IP, en una ventana de un minuto.
    rate_limit_per_conversation: int = 20
    rate_limit_per_ip: int = 60
    rate_limit_window_seconds: int = 60
    # Activar SOLO si el agente esta detras de un proxy de confianza (el de
    # Next.js, un nginx). Sin proxy, cualquiera falsifica X-Forwarded-For y se
    # salta el limite por IP; con proxy y sin esto, todos los visitantes
    # comparten la cuota del servidor que reenvia.
    trust_forwarded_for: bool = False

    # Agente
    agent_max_iterations: int = 8
    business_name: str = "Mi Negocio"

    # --- Costo de tokens ------------------------------------------------------
    # Todo lo de esta seccion es politica de contexto, y vale para cualquier
    # modelo: son decisiones sobre que se envia, no sobre con quien se habla.
    #
    # Techo del historial que viaja al modelo. Es el numero que de verdad manda
    # en la factura de un agente: cada iteracion del bucle reenvia el historial
    # entero, asi que un techo alto se paga multiplicado por iteracion y por
    # turno. 12k deja sitio de sobra para una conversacion de pedido.
    context_max_tokens: int = 12_000
    # A que fraccion del techo se baja cuando se cruza. Bajo a proposito: la
    # poda invalida la cache, asi que conviene podar poco seguido y mucho de
    # una vez. Subirlo a 0.9 multiplica los fallos de cache.
    context_relief_ratio: float = 0.55
    # Mensajes recientes con resultados de herramienta que se conservan enteros
    # al podar. Los anteriores se vacian: son busquedas de catalogo ya usadas.
    context_keep_tool_results: int = 4
    # Puntos de corte de cache al final del historial. 0 los apaga.
    context_cache_breakpoints: int = 3
    # Techo por resultado de herramienta. Un resultado entra una vez y se paga
    # en todos los turnos siguientes, asi que el tamano importa mas de lo que
    # parece. Muy bajo, el modelo se queda sin datos y vuelve a consultar.
    tool_result_max_chars: int = 6_000

    # Precio del modelo, en dolares por millon de tokens. Solo hace falta para
    # los modelos que no estan en la tabla de app/llm/pricing.py: los de NIM,
    # Groq, Together o uno propio en vLLM. Sin esto el agente sigue funcionando
    # igual; lo unico que no puede es decir cuanto costo el turno.
    llm_price_input: float | None = None
    llm_price_output: float | None = None
    llm_price_cache_read: float = 0.1
    llm_price_cache_write: float = 1.25

    # --- Reservas -----------------------------------------------------------
    # Zona horaria del negocio. Debe coincidir con la que asume el backend de
    # reservas (America/Bogota): si difieren, las reservas entran corridas.
    business_timezone: str = "America/Bogota"
    # Franjas de servicio, separadas por coma ("12:00-15:00,18:00-23:00"). El
    # backend NO guarda horarios: a las 4 de la manana toda mesa esta libre y la
    # reserva entraria. Vacio = no se valida, que es como se comportaba antes.
    reservation_hours: str = ""
    # Dias de cierre, por nombre o por numero ISO ("lunes" o "1").
    reservation_closed_days: str = ""
    # Tope de anticipacion. Protege de un "reserva para el 2030" por un dedazo
    # del cliente o del modelo al resolver una fecha relativa.
    reservation_max_days_ahead: int = 60

    # --- Avisos al cliente ---------------------------------------------------
    # Escuchar el socket de reservas del backend para encolar avisos cuando el
    # restaurante confirma o cancela. Apagado por defecto: mantiene una conexion
    # abierta contra otro proceso, y hoy NO hay canal que entregue esos avisos
    # (los acumula hasta que exista WhatsApp).
    reservation_watch_enabled: bool = False
    # Host del socket.io. El gateway NO lleva el prefijo /api que si llevan las
    # rutas REST, asi que por defecto se deriva quitandoselo a API_BASE_URL.
    backend_realtime_url: str = ""
    # Avisar solo de reservas creadas por el agente. Escribirle a alguien que
    # reservo por telefono desde el dashboard es un mensaje no solicitado.
    notify_only_own_reservations: bool = True

    @property
    def realtime_url(self) -> str:
        if self.backend_realtime_url:
            return self.backend_realtime_url.rstrip("/")
        base = self.api_base_url.rstrip("/")
        return base[: -len("/api")] if base.endswith("/api") else base

    @property
    def model_price(self) -> "ModelPrice | None":
        """Precio declarado por entorno, si lo hay. Gana sobre la tabla."""
        if self.llm_price_input is None or self.llm_price_output is None:
            return None
        from app.llm.pricing import ModelPrice

        return ModelPrice(
            input_per_mtok=Decimal(str(self.llm_price_input)),
            output_per_mtok=Decimal(str(self.llm_price_output)),
            cache_read_multiplier=Decimal(str(self.llm_price_cache_read)),
            cache_write_multiplier=Decimal(str(self.llm_price_cache_write)),
        )

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
