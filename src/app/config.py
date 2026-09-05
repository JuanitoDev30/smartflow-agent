"""Configuración de la aplicación"""


from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    #Proveedor de LLM. El nucleo del agente no conoce estos valores
    llm_provider: str = "openai"  # openai, anthropic, cohere, llama2, local
    llm_model: str = "gpt-4o"  
    llm_max_tokens: int = 8000
    
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    
    
    # Backend de datos: memory (fakes sin dependencias) o api
    
    repository_backend: Literal["memory", "api"] = "memory"
    api_base_url: str = "http://localhost:3001/api"
    api_token: str | None = None
    api_timeout_seconds: int = 15  # segundos
    
    # Agente
    
    agent_max_iterations: int = 8
    business_name: str = "Asistente de pedidos"
    
@lru_cache()
def get_settings() -> Settings:
    """Obtiene la configuración de la aplicación desde variables de entorno o archivo .env"""
    return Settings()    
