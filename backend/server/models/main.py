from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    MetaData, String, Integer, Boolean, DateTime, ForeignKey, CheckConstraint, 
    Numeric, Text, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import uuid

from server.settings import alembic_convention
metadata = MetaData(naming_convention=alembic_convention)

class Base(DeclarativeBase):
    metadata = metadata

class Statement(Base):
    __tablename__ = "statements"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="statement", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("length(id) >= 1", name="statement_id_nonempty"),
        CheckConstraint("length(filename) >= 1", name="statement_filename_nonempty"),
        CheckConstraint("length(file_path) >= 1", name="statement_filepath_nonempty"),
    )


