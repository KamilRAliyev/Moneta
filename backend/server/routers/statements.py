from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import tempfile
import os
import shutil
from pathlib import Path
from datetime import datetime

from server.models.main import Statement
from server.services.database import get_db
from server.services.file_management import FileStorageService
from server.services.csv_processor import CSVProcessor
from server.settings import ALLOWED_FILE_EXTENSIONS

router = APIRouter(prefix="/statements", tags=["statements"])

# Initialize file storage service
file_storage = FileStorageService(base_dir=os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads"))

@router.post("/upload")
async def upload_statement(
    file: UploadFile = File(...),
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Upload a statement file and create a Statement record in the database.
    
    Args:
        file: The uploaded file
        db: Database session
    
    Returns:
        JSON response with statement details
    """
    try:
        # Validate file type
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_FILE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {ALLOWED_FILE_EXTENSIONS}"
            )
        
        # Create temporary file to store uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)
        
        try:
            # Move file to storage location
            sanitized_filename = file_storage.sanitize_filename(file.filename)
            today_date = file_storage.base_dir / "raw_data_dir" / datetime.utcnow().strftime("%Y-%m-%d")
            today_date.mkdir(parents=True, exist_ok=True)
            
            final_file_path = today_date / sanitized_filename
            shutil.move(str(temp_file_path), str(final_file_path))
            
            # Calculate file hash and get metadata
            file_hash = file_storage.calculate_file_hash(final_file_path)
            mime_type = file_storage.get_mime_type(final_file_path)
            
            # Check if statement with same hash already exists
            existing_statement = db.query(Statement).filter(Statement.file_hash == file_hash).first()
            if existing_statement:
                # Clean up the duplicate file
                final_file_path.unlink()
                return JSONResponse(
                    status_code=409,
                    content={
                        "message": "Statement with this file hash already exists",
                        "statement_id": existing_statement.id,
                        "filename": existing_statement.filename
                    }
                )
            
            # Create new statement record
            statement = Statement(
                filename=sanitized_filename,
                file_path=str(final_file_path),
                file_hash=file_hash,
                mime_type=mime_type,
                processed=False
            )
            
            db.add(statement)
            db.commit()
            db.refresh(statement)
            
            return JSONResponse(
                status_code=201,
                content={
                    "message": "Statement uploaded successfully",
                    "statement_id": statement.id,
                    "filename": statement.filename,
                    "file_hash": statement.file_hash,
                    "mime_type": statement.mime_type,
                    "created_at": statement.created_at.isoformat(),
                    "processed": statement.processed
                }
            )
            
        except Exception as e:
            # Clean up temporary file if something goes wrong
            if temp_file_path.exists():
                temp_file_path.unlink()
            raise e
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/upload-multiple")
async def upload_multiple_statements(
    files: List[UploadFile] = File(...),
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Upload multiple statement files and create Statement records in the database.
    
    Args:
        files: List of uploaded files
        db: Database session
    
    Returns:
        JSON response with upload results
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    if len(files) > 10:  # Limit to 10 files per request
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per request")
    
    results = {
        "successful_uploads": [],
        "failed_uploads": [],
        "duplicate_files": [],
        "total_files": len(files),
        "successful_count": 0,
        "failed_count": 0,
        "duplicate_count": 0
    }
    
    for file in files:
        try:
            # Validate file type
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in ALLOWED_FILE_EXTENSIONS:
                results["failed_uploads"].append({
                    "filename": file.filename,
                    "error": f"File type not allowed. Allowed types: {ALLOWED_FILE_EXTENSIONS}"
                })
                results["failed_count"] += 1
                continue
            
            # Create temporary file to store uploaded content
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = Path(temp_file.name)
            
            try:
                # Move file to storage location
                sanitized_filename = file_storage.sanitize_filename(file.filename)
                today_date = file_storage.base_dir / "raw_data_dir" / datetime.utcnow().strftime("%Y-%m-%d")
                today_date.mkdir(parents=True, exist_ok=True)
                
                final_file_path = today_date / sanitized_filename
                shutil.move(str(temp_file_path), str(final_file_path))
                
                # Calculate file hash and get metadata
                file_hash = file_storage.calculate_file_hash(final_file_path)
                mime_type = file_storage.get_mime_type(final_file_path)
                
                # Check if statement with same hash already exists
                existing_statement = db.query(Statement).filter(Statement.file_hash == file_hash).first()
                if existing_statement:
                    # Clean up the duplicate file
                    final_file_path.unlink()
                    results["duplicate_files"].append({
                        "filename": file.filename,
                        "statement_id": existing_statement.id,
                        "existing_filename": existing_statement.filename
                    })
                    results["duplicate_count"] += 1
                    continue
                
                # Create new statement record
                statement = Statement(
                    filename=sanitized_filename,
                    file_path=str(final_file_path),
                    file_hash=file_hash,
                    mime_type=mime_type,
                    processed=False
                )
                
                db.add(statement)
                db.commit()
                db.refresh(statement)
                
                results["successful_uploads"].append({
                    "filename": file.filename,
                    "statement_id": statement.id,
                    "file_hash": statement.file_hash,
                    "mime_type": statement.mime_type,
                    "created_at": statement.created_at.isoformat()
                })
                results["successful_count"] += 1
                
            except Exception as e:
                # Clean up temporary file if something goes wrong
                if temp_file_path.exists():
                    temp_file_path.unlink()
                results["failed_uploads"].append({
                    "filename": file.filename,
                    "error": str(e)
                })
                results["failed_count"] += 1
                
        except Exception as e:
            results["failed_uploads"].append({
                "filename": file.filename,
                "error": str(e)
            })
            results["failed_count"] += 1
    
    # Determine overall response status
    if results["successful_count"] > 0 and results["failed_count"] == 0 and results["duplicate_count"] == 0:
        status_code = 201
        message = f"All {results['successful_count']} files uploaded successfully"
    elif results["successful_count"] > 0:
        status_code = 207  # Multi-Status
        message = f"Partial success: {results['successful_count']} uploaded, {results['failed_count']} failed, {results['duplicate_count']} duplicates"
    else:
        status_code = 400
        message = "All files failed to upload"
    
    return JSONResponse(
        status_code=status_code,
        content={
            "message": message,
            "results": results
        }
    )

@router.post("/{statement_id}/process")
async def process_statement(
    statement_id: str,
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Process a statement file and extract transactions.
    
    Args:
        statement_id: The statement ID to process
        db: Database session
    
    Returns:
        JSON response with processing results
    """
    try:
        # Get the statement
        statement = db.query(Statement).filter(Statement.id == statement_id).first()
        
        if not statement:
            raise HTTPException(status_code=404, detail="Statement not found")
        
        # Check if file exists
        file_path = Path(statement.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Statement file not found")
        
        # Process the statement
        processor = CSVProcessor()
        result = processor.process_statement(statement, db)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "message": result["message"],
                    "statement_id": statement_id,
                    "transactions_processed": result["transactions_processed"],
                    "transactions_created": result["transactions_created"],
                    "processed": statement.processed
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "message": result["message"],
                    "statement_id": statement_id,
                    "transactions_processed": result["transactions_processed"],
                    "transactions_created": result["transactions_created"]
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{statement_id}/transactions")
async def get_statement_transactions(
    statement_id: str,
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Get transactions for a specific statement.
    
    Args:
        statement_id: The statement ID
        db: Database session
    
    Returns:
        List of transactions for the statement
    """
    try:
        # Check if statement exists
        statement = db.query(Statement).filter(Statement.id == statement_id).first()
        if not statement:
            raise HTTPException(status_code=404, detail="Statement not found")
        
        # Get transaction summary
        processor = CSVProcessor()
        result = processor.get_transaction_summary(statement_id, db)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/")
async def list_statements(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(lambda: get_db("main"))
):
    """
    List all statements with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
    
    Returns:
        List of statements
    """
    try:
        statements = db.query(Statement).offset(skip).limit(limit).all()
        
        return {
            "statements": [
                {
                    "id": stmt.id,
                    "filename": stmt.filename,
                    "file_hash": stmt.file_hash,
                    "mime_type": stmt.mime_type,
                    "processed": stmt.processed,
                    "columns": stmt.columns,
                    "created_at": stmt.created_at.isoformat()
                }
                for stmt in statements
            ],
            "total": db.query(Statement).count(),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{statement_id}")
async def get_statement(
    statement_id: str,
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Get a specific statement by ID.
    
    Args:
        statement_id: The statement ID
        db: Database session
    
    Returns:
        Statement details
    """
    try:
        statement = db.query(Statement).filter(Statement.id == statement_id).first()
        
        if not statement:
            raise HTTPException(status_code=404, detail="Statement not found")
        
        return {
            "id": statement.id,
            "filename": statement.filename,
            "file_path": statement.file_path,
            "file_hash": statement.file_hash,
            "mime_type": statement.mime_type,
            "processed": statement.processed,
            "columns": statement.columns,
            "created_at": statement.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/{statement_id}")
async def delete_statement(
    statement_id: str,
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Delete a statement and its associated file.
    
    Args:
        statement_id: The statement ID
        db: Database session
    
    Returns:
        Success message
    """
    try:
        statement = db.query(Statement).filter(Statement.id == statement_id).first()
        
        if not statement:
            raise HTTPException(status_code=404, detail="Statement not found")
        
        # Delete the file from storage
        file_path = Path(statement.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # Delete from database
        db.delete(statement)
        db.commit()
        
        return {"message": "Statement deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
