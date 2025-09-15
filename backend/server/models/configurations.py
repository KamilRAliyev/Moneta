from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    MetaData, String, Integer, Boolean, DateTime, ForeignKey, CheckConstraint, 
    Numeric, Text, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from server.settings import alembic_convention

metadata = MetaData(naming_convention=alembic_convention)
class Base(DeclarativeBase):
    metadata = metadata
