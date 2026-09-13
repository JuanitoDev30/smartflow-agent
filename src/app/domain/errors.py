"""Errores del dominio

Se distinguen los errores tecnicos.
El agente puede explicarle al cliente en lenguaje natural que hubo un error tecnico y que vuelva a intentar mas tarde.
"""



class DomainError(Exception):
    """Base de todos los errores de negocio."""


class ProductNotFound(DomainError):
    def __init__(self, product_id: str) -> None:
        super().__init__(f"No existe un producto con id '{product_id}'.")
        self.product_id = product_id


class ProductNotAvailable(DomainError):
    def __init__(self, name: str) -> None:
        super().__init__(f"'{name}' no esta disponible en este momento.")
        self.name = name


class InsufficientStock(DomainError):
    def __init__(self, name: str, requested: int, available: int) -> None:
        super().__init__(
            f"De '{name}' se pidieron {requested} y solo hay {available} disponibles."
        )
        self.name = name
        self.requested = requested
        self.available = available


class OrderNotFound(DomainError):
    def __init__(self, reference: str) -> None:
        super().__init__(f"No se encontro el pedido '{reference}'.")
        self.reference = reference


class OrderNotCancellable(DomainError):
    def __init__(self, reference: str, status: str) -> None:
        super().__init__(
            f"El pedido '{reference}' esta en estado '{status}'. "
            "Solo se puede cancelar cuando esta PENDIENTE o CONFIRMADO."
        )
        self.reference = reference
        self.status = status


class OrderNotEditable(DomainError):
    def __init__(self, reference: str, status: str) -> None:
        super().__init__(
            f"El pedido '{reference}' esta en estado '{status}' y ya no se puede modificar."
        )
        self.reference = reference
        self.status = status


class IncompleteOrderData(DomainError):
    def __init__(self, missing: list[str]) -> None:
        super().__init__("Faltan datos para registrar el pedido: " + ", ".join(missing))
        self.missing = missing


class InvalidPhone(DomainError):
    def __init__(self, digits: int) -> None:
        super().__init__(
            f"El telefono debe tener exactamente 10 digitos; se recibieron {digits}."
        )
        self.digits = digits


class EmptyOrder(DomainError):
    def __init__(self) -> None:
        super().__init__("El pedido no tiene productos.")


class BackendUnavailable(DomainError):
    """El sistema de pedidos no respondio. Es tecnico, pero el agente necesita
    poder decirselo al cliente sin exponer detalles."""

    def __init__(self, detail: str = "") -> None:
        super().__init__("El sistema no esta respondiendo en este momento.")
        self.detail = detail
