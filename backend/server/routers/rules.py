"""
Rules Engine API Router

Provides endpoints for managing computed field rules and executing 
them against transaction data.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from server.services.database import get_db
from server.models.configurations import ComputedFieldRule, RULE_TYPES
from server.services.rule_engine import rule_engine, RuleExecutionContext
from server.models.main import Transaction, TransactionMetadata

router = APIRouter(prefix="/rules", tags=["rules"])


class RuleCreate(BaseModel):
    """Request model for creating a rule"""
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable rule name")
    description: Optional[str] = Field(None, description="Optional detailed description")
    target_field: str = Field(..., min_length=1, max_length=255, description="Target computed field name")
    condition: Optional[str] = Field(None, description="Optional condition expression (when to apply rule)")
    action: str = Field(..., min_length=1, description="Action expression (formula or mapping)")
    rule_type: str = Field(..., description="Rule type: formula, model_mapping, or value_assignment")
    priority: int = Field(100, ge=0, description="Rule priority (lower = higher priority)")
    active: bool = Field(True, description="Whether rule is active")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Amazon Transactions Amount",
                "description": "Convert amount to float for Amazon transactions",
                "target_field": "amount",
                "condition": "merchant == 'Amazon'",
                "action": "amount_to_float(amount)",
                "rule_type": "formula",
                "priority": 10,
                "active": True
            }
        }


class RuleUpdate(BaseModel):
    """Request model for updating a rule"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_field: Optional[str] = Field(None, min_length=1, max_length=255)
    condition: Optional[str] = None
    action: Optional[str] = Field(None, min_length=1)
    rule_type: Optional[str] = None
    priority: Optional[int] = Field(None, ge=0)
    active: Optional[bool] = None


class RuleResponse(BaseModel):
    """Response model for rule data"""
    id: str
    name: str
    description: Optional[str]
    target_field: str
    condition: Optional[str]
    action: str
    rule_type: str
    priority: int
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RuleExecuteRequest(BaseModel):
    """Request model for executing rules"""
    transaction_ids: Optional[List[str]] = Field(None, description="Specific transaction IDs to process")
    target_fields: Optional[List[str]] = Field(None, description="Only process rules for these fields")
    rule_ids: Optional[List[str]] = Field(None, description="Only execute these specific rules")
    dry_run: bool = Field(False, description="If true, don't save results, just return what would be computed")
    force_reprocess: bool = Field(False, description="If true, reprocess all fields even if they already have values")


class RuleExecuteResponse(BaseModel):
    """Response model for rule execution results"""
    success: bool
    processed_transactions: int
    updated_fields: Dict[str, int]  # field_name -> count of transactions updated
    errors: List[str] = []
    dry_run_results: Optional[Dict[str, Any]] = None


class RuleTestRequest(BaseModel):
    """Request model for testing a single rule against sample data"""
    rule: RuleCreate
    sample_transaction: Dict[str, Any]


class RuleTestResponse(BaseModel):
    """Response model for rule testing"""
    success: bool
    condition_matched: bool
    result_value: Any = None
    error: Optional[str] = None


@router.post("/", response_model=RuleResponse)
async def create_rule(rule: RuleCreate, db: Session = Depends(lambda: get_db("configurations"))):
    """
    Create a new computed field rule
    
    Creates a new rule for computing transaction fields based on conditions
    and formulas. Rules are executed in priority order.
    """
    try:
        # Validate rule_type
        if rule.rule_type not in RULE_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid rule_type. Must be one of: {list(RULE_TYPES.keys())}"
            )
        
        # Create new rule
        db_rule = ComputedFieldRule(
            name=rule.name,
            description=rule.description,
            target_field=rule.target_field,
            condition=rule.condition,
            action=rule.action,
            rule_type=rule.rule_type,
            priority=rule.priority,
            active=rule.active,
            updated_at=datetime.utcnow()
        )
        
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        
        return RuleResponse.from_orm(db_rule)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating rule: {str(e)}")


@router.get("/", response_model=List[RuleResponse])
async def list_rules(
    target_field: Optional[str] = Query(None, description="Filter by target field"),
    rule_type: Optional[str] = Query(None, description="Filter by rule type"),
    active_only: bool = Query(False, description="Only return active rules"),
    db: Session = Depends(lambda: get_db("configurations"))
):
    """
    List all computed field rules with optional filters
    
    Returns rules sorted by priority (ascending = higher priority first).
    """
    try:
        query = db.query(ComputedFieldRule)
        
        # Apply filters
        if target_field:
            query = query.filter(ComputedFieldRule.target_field == target_field)
        
        if rule_type:
            query = query.filter(ComputedFieldRule.rule_type == rule_type)
            
        if active_only:
            query = query.filter(ComputedFieldRule.active == True)
        
        # Sort by priority (lower = higher priority)
        query = query.order_by(ComputedFieldRule.priority, ComputedFieldRule.created_at)
        
        rules = query.all()
        return [RuleResponse.from_orm(rule) for rule in rules]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing rules: {str(e)}")


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: str, db: Session = Depends(lambda: get_db("configurations"))):
    """Get a specific rule by ID"""
    try:
        rule = db.query(ComputedFieldRule).filter(ComputedFieldRule.id == rule_id).first()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
            
        return RuleResponse.from_orm(rule)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting rule: {str(e)}")


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: str, 
    rule_update: RuleUpdate, 
    db: Session = Depends(lambda: get_db("configurations"))
):
    """Update an existing rule"""
    try:
        db_rule = db.query(ComputedFieldRule).filter(ComputedFieldRule.id == rule_id).first()
        
        if not db_rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        # Validate rule_type if provided
        if rule_update.rule_type and rule_update.rule_type not in RULE_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid rule_type. Must be one of: {list(RULE_TYPES.keys())}"
            )
        
        # Update fields
        update_data = rule_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_rule, field, value)
            
        db_rule.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_rule)
        
        return RuleResponse.from_orm(db_rule)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating rule: {str(e)}")


@router.delete("/{rule_id}")
async def delete_rule(rule_id: str, db: Session = Depends(lambda: get_db("configurations"))):
    """Delete a rule"""
    try:
        db_rule = db.query(ComputedFieldRule).filter(ComputedFieldRule.id == rule_id).first()
        
        if not db_rule:
            raise HTTPException(status_code=404, detail="Rule not found")
            
        db.delete(db_rule)
        db.commit()
        
        return {"message": "Rule deleted successfully", "id": rule_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting rule: {str(e)}")


@router.get("/fields/targets")
async def get_target_fields(db: Session = Depends(lambda: get_db("configurations"))):
    """Get all available target fields (computed fields) from existing rules"""
    try:
        # Get unique target fields from existing rules
        target_fields = db.query(ComputedFieldRule.target_field).distinct().all()
        target_fields = [field[0] for field in target_fields]
        
        # You might also want to get computed fields from TransactionMetadata
        # This would require importing and querying from the main database
        
        return {
            "target_fields": sorted(target_fields),
            "rule_types": RULE_TYPES,
            "total_rules": db.query(ComputedFieldRule).count()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting target fields: {str(e)}")


@router.post("/test", response_model=RuleTestResponse)
async def test_rule(request: RuleTestRequest):
    """
    Test a rule against sample transaction data
    
    This is a dry-run endpoint to test rule logic before saving.
    """
    try:
        # Create a temporary rule object for testing
        temp_rule = ComputedFieldRule(
            id="test",
            name=request.rule.name,
            description=request.rule.description,
            target_field=request.rule.target_field,
            condition=request.rule.condition,
            action=request.rule.action,
            rule_type=request.rule.rule_type,
            priority=request.rule.priority,
            active=request.rule.active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Create execution context
        from server.services.formula_commands import command_registry
        commands = command_registry.list_commands()
        context = RuleExecutionContext(
            transaction_data=request.sample_transaction,
            ingested_fields=list(request.sample_transaction.keys()),
            computed_fields=[],
            available_commands=[cmd.name for cmd in commands]
        )
        
        # Evaluate the rule
        result = rule_engine.evaluate_rule(temp_rule, context)
        
        return RuleTestResponse(
            success=result.success,
            condition_matched=result.condition_matched,
            result_value=result.computed_value,
            error=result.error
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing rule: {str(e)}")


@router.get("/test/transactions")
async def get_test_transactions(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of transactions to return"),
    skip: int = Query(0, ge=0, description="Number of transactions to skip"),
    main_db: Session = Depends(lambda: get_db("main"))
):
    """
    Get a list of transactions for testing rules against real data
    
    Returns a simplified list of transactions with basic info for selection
    """
    try:
        from server.models.main import Transaction
        
        # Get transactions with basic info
        query = main_db.query(Transaction).options(joinedload(Transaction.statement))
        total = query.count()
        transactions = query.offset(skip).limit(limit).all()
        
        return {
            "transactions": [
                {
                    "id": t.id,
                    "ingested_content": t.ingested_content,
                    "computed_content": t.computed_content,
                    "statement": {
                        "id": t.statement.id,
                        "filename": t.statement.filename,
                        "created_at": t.statement.created_at.isoformat()
                    },
                    "created_at": t.created_at.isoformat(),
                    "ingested_at": t.ingested_at.isoformat()
                }
                for t in transactions
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching transactions: {str(e)}")


@router.get("/test/transactions/{transaction_id}")
async def get_test_transaction(
    transaction_id: str,
    main_db: Session = Depends(lambda: get_db("main"))
):
    """
    Get a specific transaction for testing rules
    
    Returns the full transaction data in a format suitable for rule testing
    """
    try:
        from server.models.main import Transaction
        
        transaction = main_db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Return the transaction data in the format expected by rule testing
        return {
            "id": transaction.id,
            "ingested_content": transaction.ingested_content,
            "computed_content": transaction.computed_content,
            "statement": {
                "id": transaction.statement.id,
                "filename": transaction.statement.filename,
                "created_at": transaction.statement.created_at.isoformat()
            },
            "created_at": transaction.created_at.isoformat(),
            "ingested_at": transaction.ingested_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching transaction: {str(e)}")


@router.post("/execute", response_model=RuleExecuteResponse)
async def execute_rules(
    request: RuleExecuteRequest,
    config_db: Session = Depends(lambda: get_db("configurations")),
    main_db: Session = Depends(lambda: get_db("main"))
):
    """
    Execute rules against transaction data
    
    Processes transactions through the rules engine to compute field values.
    Rules are executed in priority order, with first successful rule winning for each field.
    """
    try:
        errors = []
        updated_fields = {}
        
        # 1. Load applicable rules from configurations database
        rules_query = config_db.query(ComputedFieldRule).filter(ComputedFieldRule.active == True)
        
        if request.target_fields:
            rules_query = rules_query.filter(ComputedFieldRule.target_field.in_(request.target_fields))
        
        if request.rule_ids:
            rules_query = rules_query.filter(ComputedFieldRule.id.in_(request.rule_ids))
        
        # Sort by priority (lower = higher priority)
        rules = rules_query.order_by(ComputedFieldRule.priority, ComputedFieldRule.created_at).all()
        
        if not rules:
            return RuleExecuteResponse(
                success=True,
                processed_transactions=0,
                updated_fields={},
                errors=["No active rules found matching criteria"]
            )
        
        # 2. Load transactions from main database
        transactions_query = main_db.query(Transaction)
        
        if request.transaction_ids:
            transactions_query = transactions_query.filter(Transaction.id.in_(request.transaction_ids))
        
        transactions = transactions_query.all()
        
        if not transactions:
            return RuleExecuteResponse(
                success=True,
                processed_transactions=0,
                updated_fields={},
                errors=["No transactions found matching criteria"]
            )
        
        # 3. Get transaction metadata for field information
        metadata = main_db.query(TransactionMetadata).first()
        ingested_fields = list(metadata.ingested_columns.keys()) if metadata else []
        computed_fields = list(metadata.computed_columns.keys()) if metadata else []
        
        processed_count = 0
        dry_run_results = {} if request.dry_run else None
        
        # 4. Process each transaction
        for transaction in transactions:
            try:
                # Combine ingested and computed content
                transaction_data = dict(transaction.ingested_content)
                if transaction.computed_content:
                    transaction_data.update(transaction.computed_content)
                
                # Execute rules for this transaction
                computed_results = rule_engine.execute_rules_for_transaction(
                    rules=rules,
                    transaction_data=transaction_data,
                    ingested_fields=ingested_fields,
                    computed_fields=computed_fields,
                    force_reprocess=request.force_reprocess
                )
                
                if computed_results:
                    print(f"DEBUG: Transaction {transaction.id} has computed results: {computed_results}")
                    # Track updated fields
                    for field_name in computed_results.keys():
                        updated_fields[field_name] = updated_fields.get(field_name, 0) + 1
                    
                    # Serialize datetime objects to ISO format strings for JSON storage
                    serialized_results = {}
                    for key, value in computed_results.items():
                        if isinstance(value, datetime):
                            serialized_results[key] = value.isoformat()
                        else:
                            serialized_results[key] = value
                    print(f"DEBUG: Serialized results: {serialized_results}")
                    
                    if request.dry_run:
                        # Store dry run results
                        dry_run_results[transaction.id] = serialized_results
                    else:
                        # Update transaction with computed results
                        # Create a new dict to ensure SQLAlchemy detects the change
                        if transaction.computed_content:
                            new_computed_content = dict(transaction.computed_content)
                            new_computed_content.update(serialized_results)
                            transaction.computed_content = new_computed_content
                        else:
                            transaction.computed_content = serialized_results
                        
                        transaction.computed_at = datetime.utcnow()
                        # Force flush to ensure changes are written to database
                        main_db.flush()
                        # You might want to update computed_content_hash here too
                
                processed_count += 1
                
            except Exception as e:
                errors.append(f"Error processing transaction {transaction.id}: {str(e)}")
                continue
        
        # 5. Commit changes if not dry run
        if not request.dry_run and processed_count > 0:
            print(f"DEBUG: About to commit {processed_count} transactions")
            try:
                main_db.commit()
                print(f"DEBUG: Commit successful")
            except Exception as e:
                print(f"DEBUG: Commit failed: {e}")
                errors.append(f"Database commit failed: {str(e)}")
                main_db.rollback()
        
        return RuleExecuteResponse(
            success=len(errors) == 0,
            processed_transactions=processed_count,
            updated_fields=updated_fields,
            errors=errors,
            dry_run_results=dry_run_results
        )
        
    except Exception as e:
        print(f"DEBUG: Exception caught: {e}")
        if not request.dry_run:
            main_db.rollback()
        raise HTTPException(status_code=500, detail=f"Error executing rules: {str(e)}")


@router.post("/test-db-update")
async def test_db_update(main_db: Session = Depends(lambda: get_db("main"))):
    """Test endpoint to verify database updates work"""
    try:
        # Get a transaction
        transaction = main_db.query(Transaction).first()
        if not transaction:
            return {"error": "No transactions found"}
        
        # Update computed_content
        if transaction.computed_content:
            transaction.computed_content["test_field"] = "test_value"
        else:
            transaction.computed_content = {"test_field": "test_value"}
        
        # Commit
        main_db.commit()
        
        # Verify update
        main_db.refresh(transaction)
        
        return {
            "success": True,
            "transaction_id": transaction.id,
            "computed_content": transaction.computed_content
        }
    except Exception as e:
        main_db.rollback()
        return {"error": str(e)}
