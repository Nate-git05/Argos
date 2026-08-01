from datetime import datetime  # type for the registered_at column

from sqlalchemy import DateTime, String, func  # column types + func.now() for the DB-side timestamp
from sqlalchemy.orm import Mapped, mapped_column  # SQLAlchemy 2.0 typed column declaration

from application.server.web.models import Base  # shared declarative base


class RegisteredUser(Base):  # one row per person who submitted the registration modal
    __tablename__ = "registered_users"  # actual Postgres table name

    id: Mapped[int] = mapped_column(primary_key=True)  # auto-incrementing primary key
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)  # from the modal's "First name" field
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)  # from the modal's "Last name" field
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)  # one registration per email
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )  # audit column -- set by Postgres itself when the row is inserted, not the app server's clock
