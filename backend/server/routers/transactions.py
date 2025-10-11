from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import String
from typing import List, Optional
from datetime import datetime

from server.models.main import Transaction, Statement, TransactionMetadata
from server.services.database import get_db

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("/")
async def list_transactions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100000, description="Maximum number of records to return"),
    statement_id: Optional[str] = Query(None, description="Filter by statement ID"),
    db: Session = Depends(lambda: get_db("main"))
):
    """
    List transactions with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        statement_id: Optional statement ID to filter by
        db: Database session
    
    Returns:
        List of transactions with pagination info
    """
    try:
        query = db.query(Transaction).options(joinedload(Transaction.statement))
        
        if statement_id:
            query = query.filter(Transaction.statement_id == statement_id)
        
        total = query.count()
        transactions = query.offset(skip).limit(limit).all()
        
        return {
            "transactions": [
                {
                    "id": t.id,
                    "statement_id": t.statement_id,
                    "ingested_content": t.ingested_content,
                    "ingested_content_hash": t.ingested_content_hash,
                    "ingested_at": t.ingested_at.isoformat(),
                    "created_at": t.created_at.isoformat(),
                    "computed_content": t.computed_content,
                    "computed_content_hash": t.computed_content_hash,
                    "computed_at": t.computed_at.isoformat() if t.computed_at else None,
                    "statement": {
                        "id": t.statement.id,
                        "filename": t.statement.filename,
                        "mime_type": t.statement.mime_type,
                        "processed": t.statement.processed,
                        "columns": t.statement.columns,
                        "created_at": t.statement.created_at.isoformat()
                    }
                }
                for t in transactions
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/")
async def delete_all_transactions(
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Delete all transactions from the database.
    
    WARNING: This action cannot be undone!
    
    Args:
        db: Database session
    
    Returns:
        Confirmation message with count of deleted transactions
    """
    try:
        # Count transactions before deletion
        total_count = db.query(Transaction).count()
        
        if total_count == 0:
            return {
                "message": "No transactions found to delete",
                "removed_count": 0
            }
        
        # Delete all transactions
        db.query(Transaction).delete()
        db.commit()
        
        return {
            "message": f"Successfully deleted {total_count} transactions",
            "removed_count": total_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete transactions: {str(e)}")

@router.get("/metadata")
async def get_transaction_metadata(db: Session = Depends(lambda: get_db("main"))):
    """
    Get the metadata for all transactions (singleton pattern).
    
    Args:
        db: Database session
    
    Returns:
        Metadata for all transactions
    """
    try:
        # Try to get the singleton metadata record
        meta = db.query(TransactionMetadata).first()
        
        if not meta:
            # Create the singleton record if it doesn't exist
            meta = TransactionMetadata(
                id="1",
                ingested_columns={},
                computed_columns={}
            )
            db.add(meta)
            db.commit()
            db.refresh(meta)
        
        # Regenerate metadata from all existing transactions on each call
        all_ingested_columns = set()
        all_computed_columns = set()
        
        # Get all transactions and collect unique columns
        transactions = db.query(Transaction).all()
        for transaction in transactions:
            if transaction.ingested_content:
                all_ingested_columns.update(transaction.ingested_content.keys())
            if transaction.computed_content:
                all_computed_columns.update(transaction.computed_content.keys())
        
        # Detect currency fields
        currency_fields = []
        currency_patterns = ['currency', 'curr', 'ccy', 'crncy']
        common_currencies = {'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY', 'INR', 'RUB'}
        currency_symbols = {'$', '€', '£', '¥', '₹', '₽', 'R$', '₩', 'kr', 'zł', '฿', 'Rp', 'RM', '₱', 'R', '₺'}
        
        # Check column names for currency patterns
        all_columns = list(all_ingested_columns) + list(all_computed_columns)
        for col in all_columns:
            col_lower = col.lower()
            if any(pattern in col_lower for pattern in currency_patterns):
                currency_fields.append(col)
                continue
            
            # Check if column values contain currency codes or symbols
            has_currency_values = False
            for transaction in transactions[:100]:  # Sample first 100 transactions
                content = {**(transaction.ingested_content or {}), **(transaction.computed_content or {})}
                value = content.get(col)
                if value and isinstance(value, str):
                    # Check for currency codes or symbols
                    if value.upper() in common_currencies or value in currency_symbols:
                        has_currency_values = True
                        break
            
            if has_currency_values:
                currency_fields.append(col)
        
        # Update metadata with collected columns
        meta.ingested_columns = {col: True for col in all_ingested_columns}
        meta.computed_columns = {col: True for col in all_computed_columns}
        meta.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "ingested_columns": meta.ingested_columns or {},
            "computed_columns": meta.computed_columns or {},
            "currency_fields": currency_fields,
            "updated_at": meta.updated_at.isoformat() if meta.updated_at else None,
            "created_at": meta.created_at.isoformat() if meta.created_at else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve transaction metadata: {str(e)}")

@router.get("/filtered")
async def get_filtered_transactions(
    request: Request,
    columns: Optional[str] = Query(None, description="Comma-separated list of columns to include"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="General search across all transaction content"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    statement_id: Optional[str] = Query(None, description="Filter by statement ID"),
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Get transactions filtered by specific columns with advanced filtering and pagination.
    
    Args:
        columns: Comma-separated list of columns to include in response
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: General search across all transaction content
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        statement_id: Filter by statement ID
        db: Database session
    
    Returns:
        List of transactions with filtering applied
    """
    try:
        from sqlalchemy import or_, and_, desc, asc, text, Float
        from urllib.parse import parse_qs, urlparse
        from fastapi import Request
        import json
        
        query = db.query(Transaction).options(joinedload(Transaction.statement))
        
        # Apply statement filter
        if statement_id:
            query = query.filter(Transaction.statement_id == statement_id)
        
        # Apply general search
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Transaction.ingested_content.contains(search),
                    Transaction.computed_content.contains(search)
                )
            )
        
        # Implement field-specific filtering
        query_params = dict(request.query_params)
        filter_params = {}
        for key, value in query_params.items():
            if key.startswith('filter_') and '_' in key[7:]:
                parts = key.split('_')
                if len(parts) >= 3:
                    filter_index = parts[1]
                    filter_type = parts[2]
                    
                    if filter_index not in filter_params:
                        filter_params[filter_index] = {}
                    filter_params[filter_index][filter_type] = value
        
        if filter_params:
            print(f"DEBUG: Filter parameters received: {filter_params}")
            
            # Apply field filters
            for filter_index, filter_data in filter_params.items():
                if 'field' in filter_data and 'operator' in filter_data and 'value' in filter_data:
                    field = filter_data['field']
                    operator = filter_data['operator']
                    value = filter_data['value']
                    
                    if not field or not value:
                        continue
                    
                    # Convert value to appropriate type for numeric comparisons
                    try:
                        # Try to convert to float for numeric fields
                        numeric_value = float(value)
                        is_numeric = True
                    except (ValueError, TypeError):
                        is_numeric = False
                    
                    # Apply filter based on operator using raw SQL for JSON field access
                    if operator == 'equals':
                        if is_numeric:
                            query = query.filter(
                                or_(
                                    text(f"json_extract(ingested_content, '$.{field}') = :value"),
                                    text(f"json_extract(computed_content, '$.{field}') = :value")
                                )
                            ).params(value=value)
                        else:
                            query = query.filter(
                                or_(
                                    text(f"json_extract(ingested_content, '$.{field}') LIKE :value"),
                                    text(f"json_extract(computed_content, '$.{field}') LIKE :value")
                                )
                            ).params(value=f"%{value}%")
                    elif operator == 'contains':
                        query = query.filter(
                            or_(
                                text(f"json_extract(ingested_content, '$.{field}') LIKE :value"),
                                text(f"json_extract(computed_content, '$.{field}') LIKE :value")
                            )
                        ).params(value=f"%{value}%")
                    elif operator == 'startswith':
                        query = query.filter(
                            or_(
                                text(f"json_extract(ingested_content, '$.{field}') LIKE :value"),
                                text(f"json_extract(computed_content, '$.{field}') LIKE :value")
                            )
                        ).params(value=f"{value}%")
                    elif operator == 'endswith':
                        query = query.filter(
                            or_(
                                text(f"json_extract(ingested_content, '$.{field}') LIKE :value"),
                                text(f"json_extract(computed_content, '$.{field}') LIKE :value")
                            )
                        ).params(value=f"%{value}")
                    elif operator == 'not_equals':
                        if is_numeric:
                            query = query.filter(
                                and_(
                                    text(f"json_extract(ingested_content, '$.{field}') != :value"),
                                    text(f"json_extract(computed_content, '$.{field}') != :value")
                                )
                            ).params(value=value)
                        else:
                            query = query.filter(
                                and_(
                                    ~text(f"json_extract(ingested_content, '$.{field}') LIKE :value"),
                                    ~text(f"json_extract(computed_content, '$.{field}') LIKE :value")
                                )
                            ).params(value=f"%{value}%")
                    elif operator in ['gt', 'gte', 'lt', 'lte'] and is_numeric:
                        # Numeric comparisons
                        if operator == 'gt':
                            query = query.filter(
                                or_(
                                    text(f"CAST(json_extract(ingested_content, '$.{field}') AS REAL) > :value"),
                                    text(f"CAST(json_extract(computed_content, '$.{field}') AS REAL) > :value")
                                )
                            ).params(value=numeric_value)
                        elif operator == 'gte':
                            query = query.filter(
                                or_(
                                    text(f"CAST(json_extract(ingested_content, '$.{field}') AS REAL) >= :value"),
                                    text(f"CAST(json_extract(computed_content, '$.{field}') AS REAL) >= :value")
                                )
                            ).params(value=numeric_value)
                        elif operator == 'lt':
                            query = query.filter(
                                or_(
                                    text(f"CAST(json_extract(ingested_content, '$.{field}') AS REAL) < :value"),
                                    text(f"CAST(json_extract(computed_content, '$.{field}') AS REAL) < :value")
                                )
                            ).params(value=numeric_value)
                        elif operator == 'lte':
                            query = query.filter(
                                or_(
                                    text(f"CAST(json_extract(ingested_content, '$.{field}') AS REAL) <= :value"),
                                    text(f"CAST(json_extract(computed_content, '$.{field}') AS REAL) <= :value")
                                )
                            ).params(value=numeric_value)
        
        # Apply sorting
        if sort_by:
            if sort_by in ['id', 'statement_id', 'created_at', 'ingested_at', 'computed_at']:
                # Sort by direct table columns
                column = getattr(Transaction, sort_by)
                if sort_order.lower() == 'desc':
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
            else:
                # Sort by JSON fields (ingested_content or computed_content)
                # This is more complex and might need custom SQL
                pass
        
        # Get total count before applying pagination
        total = query.count()
        
        # Apply pagination
        transactions = query.offset(skip).limit(limit).all()
        
        # Parse columns filter
        selected_columns = None
        if columns:
            selected_columns = [col.strip() for col in columns.split(',')]
        
        result_transactions = []
        for t in transactions:
            transaction_data = {
                "id": t.id,
                "statement_id": t.statement_id,
                "created_at": t.created_at.isoformat(),
                "ingested_at": t.ingested_at.isoformat(),
                "computed_at": t.computed_at.isoformat() if t.computed_at else None
            }
            
            # Add ingested content (filtered by columns if specified)
            if t.ingested_content:
                if selected_columns:
                    transaction_data["ingested_content"] = {
                        col: t.ingested_content[col] 
                        for col in selected_columns 
                        if col in t.ingested_content
                    }
                else:
                    transaction_data["ingested_content"] = t.ingested_content
            
            # Add computed content (filtered by columns if specified)
            if t.computed_content:
                if selected_columns:
                    transaction_data["computed_content"] = {
                        col: t.computed_content[col] 
                        for col in selected_columns 
                        if col in t.computed_content
                    }
                else:
                    transaction_data["computed_content"] = t.computed_content
            
            # Add statement info
            transaction_data["statement"] = {
                "id": t.statement.id,
                "filename": t.statement.filename,
                "mime_type": t.statement.mime_type,
                "processed": t.statement.processed,
                "created_at": t.statement.created_at.isoformat()
            }
            
            result_transactions.append(transaction_data)
        
        return {
            "transactions": result_transactions,
            "total": total,
            "skip": skip,
            "limit": limit,
            "columns_filter": selected_columns
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/")
async def delete_all_transactions(
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Delete all transactions from the database.
    
    WARNING: This action cannot be undone!
    
    Args:
        db: Database session
    
    Returns:
        Confirmation message with count of deleted transactions
    """
    try:
        # Count transactions before deletion
        total_count = db.query(Transaction).count()
        
        if total_count == 0:
            return {
                "message": "No transactions found to delete",
                "removed_count": 0
            }
        
        # Delete all transactions
        db.query(Transaction).delete()
        db.commit()
        
        return {
            "message": f"Successfully deleted {total_count} transactions",
            "removed_count": total_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete transactions: {str(e)}")

@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Get a specific transaction by ID.
    
    Args:
        transaction_id: The transaction ID
        db: Database session
    
    Returns:
        Transaction details
    """
    try:
        transaction = db.query(Transaction).options(joinedload(Transaction.statement)).filter(Transaction.id == transaction_id).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return {
            "id": transaction.id,
            "statement_id": transaction.statement_id,
            "created_at": transaction.created_at.isoformat(),
            "statement": {
                "id": transaction.statement.id,
                "filename": transaction.statement.filename,
                "mime_type": transaction.statement.mime_type,
                "processed": transaction.statement.processed,
                "created_at": transaction.statement.created_at.isoformat()
            },
            "ingested_content_hash": transaction.ingested_content_hash,
            "ingested_content": transaction.ingested_content,
            "ingested_at": transaction.ingested_at.isoformat(),
            "computed_content": transaction.computed_content,
            "computed_content_hash": transaction.computed_content_hash,
            "computed_at": transaction.computed_at.isoformat() if transaction.computed_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/")
async def delete_all_transactions(
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Delete all transactions from the database.
    
    WARNING: This action cannot be undone!
    
    Args:
        db: Database session
    
    Returns:
        Confirmation message with count of deleted transactions
    """
    try:
        # Count transactions before deletion
        total_count = db.query(Transaction).count()
        
        if total_count == 0:
            return {
                "message": "No transactions found to delete",
                "removed_count": 0
            }
        
        # Delete all transactions
        db.query(Transaction).delete()
        db.commit()
        
        return {
            "message": f"Successfully deleted {total_count} transactions",
            "removed_count": total_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete transactions: {str(e)}")

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Delete a transaction.
    
    Args:
        transaction_id: The transaction ID
        db: Database session
    
    Returns:
        Success message
    """
    try:
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        db.delete(transaction)
        db.commit()
        
        return {"message": "Transaction deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/")
async def delete_all_transactions(
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Delete all transactions from the database.
    
    WARNING: This action cannot be undone!
    
    Args:
        db: Database session
    
    Returns:
        Confirmation message with count of deleted transactions
    """
    try:
        # Count transactions before deletion
        total_count = db.query(Transaction).count()
        
        if total_count == 0:
            return {
                "message": "No transactions found to delete",
                "removed_count": 0
            }
        
        # Delete all transactions
        db.query(Transaction).delete()
        db.commit()
        
        return {
            "message": f"Successfully deleted {total_count} transactions",
            "removed_count": total_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete transactions: {str(e)}")

@router.get("/statement/{statement_id}")
async def get_transactions_by_statement(
    statement_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100000, description="Maximum number of records to return"),
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Get all transactions for a specific statement.
    
    Args:
        statement_id: The statement ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
    
    Returns:
        List of transactions for the statement
    """
    try:
        # Check if statement exists
        statement = db.query(Statement).filter(Statement.id == statement_id).first()
        if not statement:
            raise HTTPException(status_code=404, detail="Statement not found")
        
        query = db.query(Transaction).filter(Transaction.statement_id == statement_id)
        total = query.count()
        transactions = query.offset(skip).limit(limit).all()
        
        return {
            "statement_id": statement_id,
            "statement": {
                "id": statement.id,
                "filename": statement.filename,
                "mime_type": statement.mime_type,
                "processed": statement.processed,
                "created_at": statement.created_at.isoformat()
            },
            "transactions": [
                {
                    "id": t.id,
                    "ingested_content": t.ingested_content,
                    "ingested_content_hash": t.ingested_content_hash,
                    "ingested_at": t.ingested_at.isoformat(),
                    "created_at": t.created_at.isoformat(),
                    "computed_content": t.computed_content,
                    "computed_content_hash": t.computed_content_hash,
                    "computed_at": t.computed_at.isoformat() if t.computed_at else None
                }
                for t in transactions
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/")
async def delete_all_transactions(
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Delete all transactions from the database.
    
    WARNING: This action cannot be undone!
    
    Args:
        db: Database session
    
    Returns:
        Confirmation message with count of deleted transactions
    """
    try:
        # Count transactions before deletion
        total_count = db.query(Transaction).count()
        
        if total_count == 0:
            return {
                "message": "No transactions found to delete",
                "removed_count": 0
            }
        
        # Delete all transactions
        db.query(Transaction).delete()
        db.commit()
        
        return {
            "message": f"Successfully deleted {total_count} transactions",
            "removed_count": total_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete transactions: {str(e)}")

@router.get("/search/content")
async def search_transactions_by_content(
    q: str = Query(..., description="Search query for transaction content"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100000, description="Maximum number of records to return"),
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Search transactions by content using JSON field search.
    
    Args:
        q: Search query
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
    
    Returns:
        List of matching transactions
    """
    try:
        # Simple text search in the JSON content
        # This is a basic implementation - for production, consider using full-text search
        query = db.query(Transaction).options(joinedload(Transaction.statement)).filter(
            Transaction.ingested_content.cast(String).contains(q)
        )
        
        total = query.count()
        transactions = query.offset(skip).limit(limit).all()
        
        return {
            "query": q,
            "transactions": [
                {
                    "id": t.id,
                    "statement_id": t.statement_id,
                    "statement": {
                        "id": t.statement.id,
                        "filename": t.statement.filename,
                        "mime_type": t.statement.mime_type,
                        "processed": t.statement.processed,
                        "columns": t.statement.columns,
                        "created_at": t.statement.created_at.isoformat()
                    },
                    "ingested_content": t.ingested_content,
                    "ingested_content_hash": t.ingested_content_hash,
                    "ingested_at": t.ingested_at.isoformat(),
                    "created_at": t.created_at.isoformat(),
                    "computed_content": t.computed_content,
                    "computed_content_hash": t.computed_content_hash,
                    "computed_at": t.computed_at.isoformat() if t.computed_at else None
                }
                for t in transactions
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/")
async def delete_all_transactions(
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Delete all transactions from the database.
    
    WARNING: This action cannot be undone!
    
    Args:
        db: Database session
    
    Returns:
        Confirmation message with count of deleted transactions
    """
    try:
        # Count transactions before deletion
        total_count = db.query(Transaction).count()
        
        if total_count == 0:
            return {
                "message": "No transactions found to delete",
                "removed_count": 0
            }
        
        # Delete all transactions
        db.query(Transaction).delete()
        db.commit()
        
        return {
            "message": f"Successfully deleted {total_count} transactions",
            "removed_count": total_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete transactions: {str(e)}")
