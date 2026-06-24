from datetime import datetime as dt
from datetime import timezone as tz

from phonenumbers import PhoneNumberFormat as phFormat
from phonenumbers import format_number as fmt
from phonenumbers import parse as parse_ph
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db

# Constants
DESCRIPTION_LENGTH = 200
NAME_LENGTH = 50
FINGERPRINT_LENGTH = 255
PHONE_NUM_LENGTH = 20
MISSIONARY_TYPE_LENGTH = 10


class Person(db.Model):
    """Person: Person[id, phone_num, f_name, l_name]"""

    __tablename__ = "person"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_num: Mapped[str] = mapped_column(String(PHONE_NUM_LENGTH))
    f_name: Mapped[str] = mapped_column(String(NAME_LENGTH))
    l_name: Mapped[str] = mapped_column(String(NAME_LENGTH))
    events: Mapped[list["Events"]] = relationship(back_populates="person")

    def to_dict(self) -> dict[str, int | str]:
        return {
            "id": self.id,
            "phone_num": self.phone_num,
            "f_name": self.f_name,
            "l_name": self.l_name,
        }

    def __repr__(self) -> str:
        return f"<Person {self.id}>"


class Fingerprints(db.Model):
    """Device Fingerprint: Fingerprints[id, fingerprint, created_at]"""

    __tablename__ = "fingerprints"

    id: Mapped[int] = mapped_column(primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(FINGERPRINT_LENGTH), unique=True)
    created_at: Mapped[dt] = mapped_column(DateTime, default=lambda: dt.now(tz.utc))

    def to_dict(self) -> dict[str, int | str | None]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Fingerprints {self.id}>"


class Events(db.Model):
    """Event: Events[id, person_id, fingerprint_id, description, time, missionary_type]"""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("person.id"))
    fingerprint_id: Mapped[int] = mapped_column(ForeignKey("fingerprints.id"))
    description: Mapped[str | None] = mapped_column(String(DESCRIPTION_LENGTH))
    time: Mapped[dt] = mapped_column(DateTime)
    missionary_type: Mapped[str] = mapped_column(String(MISSIONARY_TYPE_LENGTH))
    person: Mapped[Person] = relationship(lazy="joined")
    fingerprint: Mapped[Fingerprints] = relationship(lazy="joined")

    def to_dict(self) -> dict[str, int | str | None]:
        return {
            "id": self.id,
            "person_id": self.person_id,
            "f_name": self.person.f_name,
            "l_name": self.person.l_name,
            "phone_num": fmt(parse_ph(self.person.phone_num, "AU"), phFormat.NATIONAL),
            "description": self.description,
            "time": self.time.isoformat(),
            "missionary_type": self.missionary_type,
        }

    def __repr__(self) -> str:
        return f"<Events {self.id}>"
