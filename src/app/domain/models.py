"""Modelos del dominio.

Son estructuras puras: no saben nada de SQL, de HTTP ni del LLM. Los adaptadores
de infraestructura traducen desde/hacia el contrato real del backend.

Los nombres y valores siguen el contrato que ya existe (estados del pedido,
metodos de pago, telefono de 10 digitos) para no inventar una traduccion que
haya que mantener en dos lados.

Regla: el dinero es Decimal, nunca float. Los precios SIEMPRE vienen del
catalogo, nunca de lo que el modelo escriba en una tool.
"""

import re
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

PHONE_DIGITS = 10
# Indicativo del pais. Los clientes escriben su numero indistintamente con o sin
# el, y el modelo tiende a normalizar a formato internacional por su cuenta.
COUNTRY_CODE = "57"


class OrderStatus(StrEnum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADO = "CONFIRMADO"
    EN_PREPARACION = "EN_PREPARACION"
    EN_CAMINO = "EN_CAMINO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"

    @property
    def is_cancellable(self) -> bool:
        """Solo se cancela antes de que el pedido entre a preparacion."""
        return self in {OrderStatus.PENDIENTE, OrderStatus.CONFIRMADO}

    @property
    def is_editable(self) -> bool:
        return self in {OrderStatus.PENDIENTE, OrderStatus.CONFIRMADO}

    @property
    def label(self) -> str:
        return {
            OrderStatus.PENDIENTE: "pendiente de confirmacion",
            OrderStatus.CONFIRMADO: "confirmado",
            OrderStatus.EN_PREPARACION: "en preparacion",
            OrderStatus.EN_CAMINO: "en camino",
            OrderStatus.ENTREGADO: "entregado",
            OrderStatus.CANCELADO: "cancelado",
        }[self]


class PaymentMethod(StrEnum):
    EFECTIVO = "EFECTIVO"
    TARJETA = "TARJETA"
    TRANSFERENCIA = "TRANSFERENCIA"


class ProductStatus(StrEnum):
    ACTIVE = "active"
    LOW_STOCK = "low_stock"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"

    @property
    def sellable(self) -> bool:
        return self in {ProductStatus.ACTIVE, ProductStatus.LOW_STOCK}


def normalize_phone(raw: str | int | None) -> str | None:
    """Deja solo digitos y quita el indicativo de pais si lo trae.

    "+57 300 123 4567", "300-123-4567" y 3001234567 son el mismo numero.
    """
    if raw is None or raw == "":
        return None
    digits = re.sub(r"\D", "", str(raw))
    if len(digits) == len(COUNTRY_CODE) + PHONE_DIGITS and digits.startswith(COUNTRY_CODE):
        digits = digits[len(COUNTRY_CODE) :]
    return digits or None


def is_valid_phone(raw: str | None) -> bool:
    digits = normalize_phone(raw)
    return digits is not None and len(digits) == PHONE_DIGITS


class Category(BaseModel):
    id: str
    name: str


class Product(BaseModel):
    id: str
    # Codigo corto del producto ("1002"). El cliente suele nombrarlo asi, y es
    # mas facil de decir por chat que un UUID.
    code: str | None = None
    name: str
    description: str | None = None
    category_id: str | None = None
    category_name: str | None = None
    unit_price: Decimal
    stock: int = 0
    status: ProductStatus = ProductStatus.ACTIVE
    # El catalogo usa borrado logico; un producto archivado no se vende aunque
    # su status siga diciendo "active".
    deleted: bool = False

    @property
    def sellable(self) -> bool:
        return not self.deleted and self.status.sellable and self.stock > 0

    @property
    def availability_note(self) -> str | None:
        """Aviso de escasez, para que el agente pueda mencionarlo sin inventarlo."""
        if self.status is ProductStatus.LOW_STOCK:
            return f"quedan pocas unidades ({self.stock})"
        return None


class Customer(BaseModel):
    """Datos del cliente. `default_address` es la direccion guardada como
    principal; la direccion de entrega de un pedido puntual vive en el borrador."""

    id: str | None = None
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    default_address: str | None = None

    def normalized_phone(self) -> str | None:
        return normalize_phone(self.phone)


class OrderLine(BaseModel):
    product_id: str
    name: str
    quantity: int = Field(gt=0)
    unit_price: Decimal

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


class DraftOrder(BaseModel):
    """Pedido en construccion. Vive en NUESTRO lado, no en el sistema de pedidos.

    Solo se envia al backend cuando el cliente confirma. `placed_order_id` actua
    como llave de idempotencia: si ya tiene valor, el pedido ya fue creado y un
    segundo intento no debe duplicarlo.
    """

    lines: list[OrderLine] = Field(default_factory=list)
    delivery_address: str | None = None
    payment_method: PaymentMethod | None = None
    notes: str | None = None
    # None = todavia no se le pregunto al cliente. Es distinto de False.
    save_address_as_default: bool | None = None
    placed_order_id: str | None = None

    @property
    def total(self) -> Decimal:
        return sum((line.subtotal for line in self.lines), Decimal("0"))

    @property
    def is_empty(self) -> bool:
        return not self.lines

    def find(self, product_id: str) -> OrderLine | None:
        return next((line for line in self.lines if line.product_id == product_id), None)

    def upsert(self, line: OrderLine) -> None:
        existing = self.find(line.product_id)
        if existing is None:
            self.lines.append(line)
        else:
            existing.quantity = line.quantity
            existing.unit_price = line.unit_price

    def remove(self, product_id: str) -> bool:
        before = len(self.lines)
        self.lines = [line for line in self.lines if line.product_id != product_id]
        return len(self.lines) != before

    def clear(self) -> None:
        self.lines = []

    def missing_fields(self, customer: Customer) -> list[str]:
        """Que falta para poder registrar el pedido, en lenguaje para el cliente."""
        missing: list[str] = []
        if not customer.full_name:
            missing.append("nombre")
        if not is_valid_phone(customer.phone):
            missing.append(f"telefono de {PHONE_DIGITS} digitos")
        if not self.delivery_address:
            missing.append("direccion de entrega")
        if self.payment_method is None:
            missing.append("metodo de pago (EFECTIVO, TARJETA o TRANSFERENCIA)")
        if self.save_address_as_default is None:
            missing.append("si desea guardar la direccion como principal")
        return missing


class Order(BaseModel):
    """Pedido tal como existe en el sistema de pedidos."""

    id: str
    status: OrderStatus
    customer_id: str | None = None
    lines: list[OrderLine]
    total: Decimal
    delivery_address: str | None = None
    payment_method: PaymentMethod | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    @property
    def short_code(self) -> str:
        """Los ids son UUID; al cliente se le muestran los primeros 8 caracteres."""
        return self.id[:8]


# --- Reservas ---------------------------------------------------------------
#
# El backend de reservas es un modulo aparte del de pedidos: tiene sus propios
# estados, sus propias transiciones y su propio recurso escaso (la mesa, que no
# se puede vender dos veces en la misma franja). Se modela aparte por eso, no
# por simetria.

# Duracion que asume el backend cuando no se le manda ninguna.
DEFAULT_DURATION_MINUTES = 90
MIN_DURATION_MINUTES = 30
MAX_DURATION_MINUTES = 480
MAX_PARTY_SIZE = 50


class ReservationStatus(StrEnum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    SENTADA = "SENTADA"
    COMPLETADA = "COMPLETADA"
    CANCELADA = "CANCELADA"
    NO_ASISTIO = "NO_ASISTIO"

    @property
    def is_open(self) -> bool:
        """La reserva sigue viva y ocupando la mesa."""
        return self in {
            ReservationStatus.PENDIENTE,
            ReservationStatus.CONFIRMADA,
            ReservationStatus.SENTADA,
        }

    @property
    def is_cancellable(self) -> bool:
        """Espejo de TRANSICIONES_VALIDAS del backend: una reserva ya sentada se
        completa, no se cancela."""
        return self in {ReservationStatus.PENDIENTE, ReservationStatus.CONFIRMADA}

    @property
    def is_editable(self) -> bool:
        return self.is_open

    @property
    def label(self) -> str:
        return {
            ReservationStatus.PENDIENTE: "pendiente de confirmacion",
            ReservationStatus.CONFIRMADA: "confirmada",
            ReservationStatus.SENTADA: "en mesa",
            ReservationStatus.COMPLETADA: "completada",
            ReservationStatus.CANCELADA: "cancelada",
            ReservationStatus.NO_ASISTIO: "marcada como no asistio",
        }[self]


class TableZone(StrEnum):
    INTERIOR = "INTERIOR"
    TERRAZA = "TERRAZA"
    BARRA = "BARRA"
    VIP = "VIP"
    PRIVADO = "PRIVADO"

    @property
    def label(self) -> str:
        return {
            TableZone.INTERIOR: "interior",
            TableZone.TERRAZA: "terraza",
            TableZone.BARRA: "barra",
            TableZone.VIP: "zona VIP",
            TableZone.PRIVADO: "salon privado",
        }[self]


class Table(BaseModel):
    id: str
    number: int
    capacity: int
    zone: TableZone = TableZone.INTERIOR
    # Una mesa inactiva existe y conserva su historial, pero no se reserva.
    active: bool = True
    description: str | None = None

    @property
    def label(self) -> str:
        return f"mesa {self.number} ({self.zone.label})"


class TableOption(BaseModel):
    """Una mesa evaluada para una franja concreta. `reason` viene del backend y
    explica por que no sirve, cuando no sirve."""

    table: Table
    available: bool
    reason: str | None = None


class Availability(BaseModel):
    starts_at: datetime
    ends_at: datetime
    tables: list[TableOption] = Field(default_factory=list)

    @property
    def free(self) -> list[Table]:
        return [option.table for option in self.tables if option.available]

    def free_in_zone(self, zone: TableZone | None) -> list[Table]:
        tables = self.free
        if zone is None:
            return tables
        return [table for table in tables if table.zone is zone]

    @property
    def has_space(self) -> bool:
        return bool(self.free)


class DraftReservation(BaseModel):
    """Reserva en construccion. Igual que el borrador del pedido, vive de este
    lado y no llega al backend hasta que el cliente confirma.

    `placed_reservation_id` es la llave de idempotencia: con valor, la reserva ya
    existe y un segundo intento no debe crear otra.
    """

    starts_at: datetime | None = None
    duration_minutes: int = DEFAULT_DURATION_MINUTES
    party_size: int | None = None
    # Solo se fijan si el cliente pidio una zona concreta; vacios significan que
    # la mesa la elige el backend, que para eso conoce la ocupacion completa.
    table_id: str | None = None
    table_zone: TableZone | None = None
    notes: str | None = None
    placed_reservation_id: str | None = None

    @property
    def is_empty(self) -> bool:
        return self.starts_at is None and self.party_size is None

    @property
    def ends_at(self) -> datetime | None:
        if self.starts_at is None:
            return None
        return self.starts_at + timedelta(minutes=self.duration_minutes)

    def clear(self) -> None:
        """Vacia la reserva en construccion sin perder la ya registrada."""
        self.starts_at = None
        self.duration_minutes = DEFAULT_DURATION_MINUTES
        self.party_size = None
        self.table_id = None
        self.table_zone = None
        self.notes = None

    def missing_fields(self, customer: Customer) -> list[str]:
        """Que falta para poder registrar la reserva, en lenguaje para el cliente."""
        missing: list[str] = []
        if not customer.full_name:
            missing.append("nombre")
        if not is_valid_phone(customer.phone):
            missing.append(f"telefono de {PHONE_DIGITS} digitos")
        if self.starts_at is None:
            missing.append("fecha y hora")
        if self.party_size is None:
            missing.append("numero de personas")
        return missing


class Reservation(BaseModel):
    """Reserva tal como existe en el sistema."""

    id: str
    status: ReservationStatus
    starts_at: datetime
    duration_minutes: int = DEFAULT_DURATION_MINUTES
    party_size: int
    table: Table | None = None
    customer_id: str | None = None
    customer_name: str | None = None
    customer_phone: str | None = None
    origin: str | None = None
    notes: str | None = None
    cancellation_reason: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    @property
    def short_code(self) -> str:
        return self.id[:8]

    @property
    def ends_at(self) -> datetime:
        return self.starts_at + timedelta(minutes=self.duration_minutes)
