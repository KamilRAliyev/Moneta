import csv
import hashlib
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import logging

from server.models.main import Transaction, Statement
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

class CSVProcessor:
    """Service for processing CSV statement files and extracting transactions."""
    
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls']
    
    def process_statement(self, statement: Statement, db: Session) -> Dict[str, Any]:
        """
        Process a statement file and extract transactions.
        
        Args:
            statement: Statement object with file path
            db: Database session
            
        Returns:
            Dictionary with processing results
        """
        try:
            file_path = Path(statement.file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"Statement file not found: {file_path}")
            
            # Read the file based on its extension
            if file_path.suffix.lower() == '.csv':
                transactions_data = self._process_csv(file_path)
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                transactions_data = self._process_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
            
            if not transactions_data:
                return {
                    "success": False,
                    "message": "No transactions found in file",
                    "transactions_processed": 0,
                    "transactions_created": 0
                }
            
            # Process and save transactions
            created_count = self._save_transactions(statement, transactions_data, db)
            
            # Mark statement as processed
            statement.processed = True
            db.commit()
            
            return {
                "success": True,
                "message": f"Successfully processed {created_count} transactions",
                "transactions_processed": len(transactions_data),
                "transactions_created": created_count
            }
            
        except Exception as e:
            logger.error(f"Error processing statement {statement.id}: {str(e)}")
            return {
                "success": False,
                "message": f"Error processing statement: {str(e)}",
                "transactions_processed": 0,
                "transactions_created": 0
            }
    
    def _process_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process CSV file and extract transaction data."""
        transactions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Try to detect delimiter
                sample = file.read(1024)
                file.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(file, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 because header is row 1
                    try:
                        # Clean and process the row
                        processed_row = self._clean_row_data(row)
                        if processed_row:
                            transactions.append(processed_row)
                    except Exception as e:
                        logger.warning(f"Error processing row {row_num} in {file_path}: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {str(e)}")
            raise
        
        return transactions
    
    def _process_excel(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process Excel file and extract transaction data."""
        transactions = []
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Convert to list of dictionaries
            for row_num, (_, row) in enumerate(df.iterrows(), start=2):
                try:
                    # Convert pandas row to dict and clean
                    row_dict = row.to_dict()
                    processed_row = self._clean_row_data(row_dict)
                    if processed_row:
                        transactions.append(processed_row)
                except Exception as e:
                    logger.warning(f"Error processing row {row_num} in {file_path}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error reading Excel file {file_path}: {str(e)}")
            raise
        
        return transactions
    
    def _clean_row_data(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Clean and standardize row data."""
        # Remove empty rows
        if not any(str(value).strip() for value in row.values() if value is not None):
            return None
        
        # Clean the data
        cleaned_row = {}
        for key, value in row.items():
            if key is None:
                continue
                
            # Clean key name
            clean_key = str(key).strip().lower().replace(' ', '_').replace('-', '_')
            
            # Clean value
            if value is None or (isinstance(value, str) and not value.strip()):
                cleaned_row[clean_key] = None
            else:
                cleaned_row[clean_key] = str(value).strip()
        
        return cleaned_row
    
    def _save_transactions(self, statement: Statement, transactions_data: List[Dict[str, Any]], db: Session) -> int:
        """Save transactions to database."""
        created_count = 0
        
        for transaction_data in transactions_data:
            try:
                # Create hash of the transaction content
                content_hash = hashlib.sha256(
                    json.dumps(transaction_data, sort_keys=True).encode('utf-8')
                ).hexdigest()
                
                # Check if transaction already exists (application-level check for performance)
                existing_transaction = db.query(Transaction).filter(
                    Transaction.statement_id == statement.id,
                    Transaction.ingested_content_hash == content_hash
                ).first()
                
                if existing_transaction:
                    logger.info(f"Transaction already exists, skipping: {content_hash}")
                    continue
                
                # Create new transaction
                transaction = Transaction(
                    statement_id=statement.id,
                    ingested_content=transaction_data,
                    ingested_content_hash=content_hash,
                    ingested_at=datetime.utcnow()
                )
                
                db.add(transaction)
                db.flush()  # Flush to trigger database constraint check
                created_count += 1
                
            except IntegrityError as e:
                # Handle unique constraint violation at database level
                if "uq_transaction_statement_content" in str(e):
                    logger.info(f"Transaction already exists (database constraint), skipping: {content_hash}")
                    db.rollback()
                    continue
                else:
                    logger.error(f"Database integrity error: {str(e)}")
                    db.rollback()
                    continue
            except Exception as e:
                logger.error(f"Error saving transaction: {str(e)}")
                db.rollback()
                continue
        
        db.commit()
        return created_count
    
    def get_transaction_summary(self, statement_id: str, db: Session) -> Dict[str, Any]:
        """Get summary of transactions for a statement."""
        transactions = db.query(Transaction).filter(Transaction.statement_id == statement_id).all()
        
        return {
            "statement_id": statement_id,
            "total_transactions": len(transactions),
            "transactions": [
                {
                    "id": t.id,
                    "ingested_at": t.ingested_at.isoformat(),
                    "content_preview": {k: v for k, v in list(t.ingested_content.items())[:3]}
                }
                for t in transactions
            ]
        }
 