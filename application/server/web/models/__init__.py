from sqlalchemy.orm import DeclarativeBase  # SQLAlchemy 2.0 base class for ORM models


class Base(DeclarativeBase):  # shared base every table model inherits from
    pass
