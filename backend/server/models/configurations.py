from datetime import datetime
from decimal import Decimal
import uuid
from sqlalchemy import (
    MetaData, String, Integer, Boolean, DateTime, ForeignKey, CheckConstraint, 
    Numeric, Text, JSON, UniqueConstraint, Index, Choice
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from server.settings import alembic_convention

metadata = MetaData(naming_convention=alembic_convention)
class Base(DeclarativeBase):
    metadata = metadata

RULE_TYPES = {
    "model": "Model Mapping",
    "formula": "Formula Based Mapping",
}

class ComputedFieldRules(Base):
    __tablename__ = "computed_field_rules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_type: Mapped[str] = mapped_column(Choice(RULE_TYPES.keys()), nullable=False)
    rule_definition: Mapped[str] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("length(id) >= 1", name="computed_field_rules_id_nonempty"),
        CheckConstraint("length(description) >= 1", name="computed_field_rules_description_nonempty"),
        CheckConstraint("length(field_name) >= 1", name="computed_field_rules_field_name_nonempty"),
        CheckConstraint("rule_type IN ('model', 'formula')", name="computed_field_rules_rule_type_check"),
    )