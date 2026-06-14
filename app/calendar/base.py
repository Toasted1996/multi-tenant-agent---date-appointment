from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TimeSlot:
    start: datetime
    end: datetime
    available: bool
    event_id: Optional[str] = None

    @property
    def duration_minutes(self) -> int:
        return int((self.end - self.start).total_seconds() / 60)


@dataclass
class CalendarEvent:
    title: str
    start: datetime
    end: datetime
    description: Optional[str] = None
    event_id: Optional[str] = None
    attendee_name: Optional[str] = None
    attendee_email: Optional[str] = None


class BaseCalendar(ABC):
    @abstractmethod
    def check_availability(self, start: datetime, end: datetime) -> TimeSlot:
        """Verificar si un rango horario está disponible."""

    @abstractmethod
    def create_event(self, event: CalendarEvent) -> str:
        """Crear un evento y retornar su ID externo."""

    @abstractmethod
    def delete_event(self, event_id: str) -> None:
        """Eliminar o cancelar un evento por su ID."""
