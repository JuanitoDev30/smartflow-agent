"""Configuración de la aplicación"""


from functools import lru_cache
from typing import Literal

from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    #Proveedor de LLM. El nucleo del agente no conoce estos valores
    llm_provider: str = "anthropic"  # openai, anthropic, cohere, llama2, local
    llm_model: str = "claude-opus-5"  
    llm_max_tokens: int = 8000
    

     #Solo para anthropic
    llm_effort: Literal["low", "medium", "high", "xhigh", "max"] = "medium"
    anthropic_api_key: str | None = None 
    
    # Para compatible con openAi  (nvidia NIM, vLLM, Ollama )
    llm_base_url: str | None = None
    llm_api_key: str | None = Field(
        default = None,
        validation_alias = AliasChoices(
            "LLM_API_KEY", "NVIDIA_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "TOGETHER_API_KEY"
        )
    )
    
    
    # Backend de datos: memory (fakes sin dependencias) o api
    
    repository_backend: Literal["memory", "api"] = "memory"
    api_base_url: str = "http://localhost:3001/api"
    api_token: str | None = None
    api_timeout_seconds: int = 15  # segundos
    
    # Cuenta de servicio del agente para acceder a la API de datos
    api_email: str | None = None
    api_password: str | None = None
    api_login_path: str = "/auth/login"
    api_token : str | None = None
    
    
    # Base propia del agente. Distinta del negocio
    
    agent_database_url: str = ""
    conversation_ttl_hours: int = 72
    conversation_max_messages: int = 80
    conversation_sweep_minutes: int = 60
    
    
    #Exposicion al frontend
    
    allowed_origins: str = "http://localhost:3000"
    
    session_secret: str =""
    session_ttl_hour: int = 72
    #limite por conversacion y por ip
    rate_limit_per_conversation: int = 20
    rate_limit_per_ip: int = 60
    rate_limit_window_seconds: int = 60
    
    #Activar solo si el agente esta detras de un proxy de confianza
    trust_forwarded_for: bool = False
    
    # Agente
    
    agent_max_iterations: int = 8
    business_name: str = "Asistente de pedidos"
    
    @property
    def origins(self) -> list[str]:
        """Devuelve la lista de orígenes permitidos para CORS"""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
    
@lru_cache()
def get_settings() -> Settings:
    """Obtiene la configuración de la aplicación desde variables de entorno o archivo .env"""
    return Settings()    
