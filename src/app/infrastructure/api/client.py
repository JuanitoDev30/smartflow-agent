


"""
Cliente HTTP compartido contra el backend de negocio

concentra en un solo lugar la url base, la autenticacion, los timeouts y la traduccion de fallos http a errores de dominio

El backend utiliza jwt que expira. Un token fijo en la configuracion funciona el primer dia, y falla el segundo.
Por ende el cliente se autentica solo con las credenciales de su propia cuenta de servicio y renueva el token cuando el backend responde 401


"""

import asyncio
import logging
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from app.domain.errors import BackendUnvailable, DomainError


logger = logging.getLogger(__name__)


class BackendRejected(DomainError):
  """El backend rechazo la operacion por una razon de negocio"""
  
  def __init__(self, detail: str) -> None:
    super().__init__(f"El backend rechazo la operacion: {detail}")
    self.detail = detail
    
class AuthenticationFailed(BackendUnvailable):
  """Las credenciales del agente no sirven para autenticarse contra el backend"""
  def __init__(self, detail: str) -> None:
    super().__init__(detail)
    logger.error(f"Autenticacion fallida: {detail}")
    
    
class BackendClient:
  def __init__(
    self,
    base_url: str,
    *,
    token: str | None = None,
    email: str | None = None,
    password: str | None = None,
    login_path: str = "auth/login",
    timeout: float = 15.0,
    client: httpx.AsyncClient | None = None
  ) -> None:
    self._base = base_url.rstrip("/")
    self._login_path = login_path
    self._email = email
    self._password = password
    
    # Las credenciales ganan sobre un token fijo
    
    if email and password and token:
      logger.warning(
        "Hay API_TOKEN y API_EMAIL/API_PASSWORD configurados a la vez"
        "Se usan las credenciales y se ignora el token porque no se puede renovar"
      )
      token = None
      
      
      self._static_token = token
      self._token: str | None = token
      self._auth_lock = asyncio.Lock()
      self._client = client or httpx.AsyncClient(timeout=timeout, headers={"Accept": "application/json"})
      
  @property
  def authenticates(self) -> bool:
      return bool(self._email and self._password)
    
  @property
  def auth_mode(self) -> str:
    if self.authenticates:
      return "credentials"
    if self._static_token:
      return "token fijo"
    return "sin autenticacion"   
  
  async def login(self) -> None:
    """Obtiene un token nuevo"""    
    