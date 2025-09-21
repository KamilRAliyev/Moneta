from fastapi import APIRouter, HTTPException, Depends, Query
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
        
        # Update metadata with collected columns
        meta.ingested_columns = {col: True for col in all_ingested_columns}
        meta.computed_columns = {col: True for col in all_computed_columns}
        meta.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "ingested_columns": meta.ingested_columns or {},
            "computed_columns": meta.computed_columns or {},
            "updated_at": meta.updated_at.isoformat() if meta.updated_at else None,
            "created_at": meta.created_at.isoformat() if meta.created_at else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve transaction metadata: {str(e)}")

@router.get("/filtered")
async def get_filtered_transactions(
    columns: Optional[str] = Query(None, description="Comma-separated list of columns to include"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100000, description="Maximum number of records to return"),
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Get transactions filtered by specific columns with pagination.
    
    Args:
        columns: Comma-separated list of columns to include in response
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
    
    Returns:
        List of transactions with only specified columns
    """
    try:
        query = db.query(Transaction).options(joinedload(Transaction.statement))
        
        total = query.count()
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
