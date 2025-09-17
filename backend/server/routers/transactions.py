from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import String
from typing import List, Optional
from datetime import datetime

from server.models.main import Transaction, Statement
from server.services.database import get_db

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("/")
async def list_transactions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
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
                    "statement": {
                        "id": t.statement.id,
                        "filename": t.statement.filename,
                        "mime_type": t.statement.mime_type,
                        "processed": t.statement.processed,
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
            "computed_content_hash": transaction.computed_content_hash,
            "computed_content": transaction.computed_content,
            "computed_at": transaction.computed_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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

@router.get("/statement/{statement_id}")
async def get_transactions_by_statement(
    statement_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
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
                    "computed_at": t.computed_at.isoformat()
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

@router.get("/search/content")
async def search_transactions_by_content(
    q: str = Query(..., description="Search query for transaction content"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
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
                        "file_path": t.statement.file_path,
                        "file_hash": t.statement.file_hash,
                        "mime_type": t.statement.mime_type,
                        "processed": t.statement.processed,
                        "created_at": t.statement.created_at.isoformat()
                    }
                    "ingested_content": t.ingested_content,
                    "ingested_content_hash": t.ingested_content_hash,
                    "ingested_at": t.ingested_at.isoformat(),
                    "created_at": t.created_at.isoformat(),
                    "computed_content": t.computed_content,
                    "computed_content_hash": t.computed_content_hash,
                    "computed_at": t.computed_at.isoformat()
                }
                for t in transactions
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
