from datetime import datetime
from decimal import Decimal
import uuid
from sqlalchemy import (
    MetaData, String, Integer, Boolean, DateTime, ForeignKey, CheckConstraint, 
    Numeric, Text, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from server.settings import alembic_convention

metadata = MetaData(naming_convention=alembic_convention)
class Base(DeclarativeBase):
    metadata = metadata

RULE_TYPES = {
    "formula": "Formula Expression",
    "model_mapping": "Model Object Mapping",
    "value_assignment": "Direct Value Assignment"
}

class ComputedFieldRule(Base):
    __tablename__ = "computed_field_rules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Core rule components
    target_field: Mapped[str] = mapped_column(String(255), nullable=False)  # computed field name
    condition: Mapped[str] = mapped_column(Text, nullable=True)  # optional condition expression
    action: Mapped[str] = mapped_column(Text, nullable=False)  # formula or mapping expression
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)  # formula, model_mapping, value_assignment
    
    # Rule execution
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)  # lower = higher priority
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("length(id) >= 1", name="cfr_id_nonempty"),
        CheckConstraint("length(name) >= 1", name="cfr_name_nonempty"),
        CheckConstraint("length(target_field) >= 1", name="cfr_target_field_nonempty"),
        CheckConstraint("length(action) >= 1", name="cfr_action_nonempty"),
        CheckConstraint("rule_type IN ('formula', 'model_mapping', 'value_assignment')", name="cfr_rule_type_check"),
        CheckConstraint("priority >= 0", name="cfr_priority_positive"),
        Index("idx_cfr_target_priority", "target_field", "priority"),  # for efficient rule ordering
        Index("idx_cfr_active_priority", "active", "priority"),  # for active rule queries
    )