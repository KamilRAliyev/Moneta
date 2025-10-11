from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import logging

from server.models.main import Report, Transaction
from server.services.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


# Pydantic models for request/response
class ReportCreate(BaseModel):
    name: str
    widgets: List[Dict[str, Any]] = []
    filters: Optional[Dict[str, Any]] = None


class ReportUpdate(BaseModel):
    name: Optional[str] = None
    widgets: Optional[List[Dict[str, Any]]] = None
    filters: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    id: str
    name: str
    user_id: Optional[str]
    widgets: List[Dict[str, Any]]
    filters: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# CRUD Endpoints
@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(lambda: get_db("main"))
):
    """
    List all reports with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
    
    Returns:
        List of reports
    """
    try:
        reports = db.query(Report).offset(skip).limit(limit).all()
        return [
            ReportResponse(
                id=r.id,
                name=r.name,
                user_id=r.user_id,
                widgets=r.widgets if isinstance(r.widgets, list) else [],
                filters=r.filters if r.filters else {},
                created_at=r.created_at.isoformat(),
                updated_at=r.updated_at.isoformat()
            )
            for r in reports
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")


@router.get("/{report_id}/", response_model=ReportResponse)
async def get_report(
    report_id: str,
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Get a specific report by ID.
    
    Args:
        report_id: Report ID
        db: Database session
    
    Returns:
        Report details
    """
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return ReportResponse(
            id=report.id,
            name=report.name,
            user_id=report.user_id,
            widgets=report.widgets if isinstance(report.widgets, list) else [],
            filters=report.filters if isinstance(report.filters, dict) else {},
            created_at=report.created_at.isoformat(),
            updated_at=report.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@router.post("/", response_model=ReportResponse)
async def create_report(
    report: ReportCreate,
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Create a new report.
    
    Args:
        report: Report data
        db: Database session
    
    Returns:
        Created report
    """
    try:
        new_report = Report(
            name=report.name,
            widgets=report.widgets,
            filters=report.filters or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        return ReportResponse(
            id=new_report.id,
            name=new_report.name,
            user_id=new_report.user_id,
            widgets=new_report.widgets if isinstance(new_report.widgets, list) else [],
            filters=new_report.filters if isinstance(new_report.filters, dict) else {},
            created_at=new_report.created_at.isoformat(),
            updated_at=new_report.updated_at.isoformat()
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create report: {str(e)}")


@router.put("/{report_id}/", response_model=ReportResponse)
async def update_report(
    report_id: str,
    report_update: ReportUpdate,
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Update an existing report.
    
    Args:
        report_id: Report ID
        report_update: Updated report data
        db: Database session
    
    Returns:
        Updated report
    """
    try:
        logger.info("=== UPDATE REPORT DEBUG ===")
        logger.info(f"Report ID: {report_id}")
        logger.info(f"Report update data: {report_update}")
        logger.info(f"Filters in request: {report_update.filters}")
        
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        if report_update.name is not None:
            report.name = report_update.name
            logger.info(f"✅ Updated name to: {report.name}")
        if report_update.widgets is not None:
            report.widgets = report_update.widgets
            logger.info(f"✅ Updated widgets (count: {len(report.widgets)})")
        if report_update.filters is not None:
            logger.info(f"✅ Setting filters to: {report_update.filters}")
            report.filters = report_update.filters
            logger.info(f"✅ Report.filters is now: {report.filters}")
        else:
            logger.warning(f"⚠️ Filters is None, not updating")
        
        report.updated_at = datetime.utcnow()
        
        logger.info(f"Before commit - report.filters: {report.filters}")
        db.commit()
        db.refresh(report)
        logger.info(f"After commit - report.filters: {report.filters}")
        
        return ReportResponse(
            id=report.id,
            name=report.name,
            user_id=report.user_id,
            widgets=report.widgets if isinstance(report.widgets, list) else [],
            filters=report.filters if isinstance(report.filters, dict) else {},
            created_at=report.created_at.isoformat(),
            updated_at=report.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update report: {str(e)}")


@router.delete("/{report_id}/")
async def delete_report(
    report_id: str,
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Delete a report.
    
    Args:
        report_id: Report ID
        db: Database session
    
    Returns:
        Success message
    """
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        db.delete(report)
        db.commit()
        
        return {"message": "Report deleted successfully", "id": report_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")


# Data Aggregation Endpoint
@router.get("/data/aggregated/")
async def get_aggregated_data(
    x_field: str = Query(..., description="Field to group by (x-axis)"),
    y_field: str = Query(..., description="Field to aggregate (y-axis)"),
    aggregation: str = Query("sum", description="Aggregation method: sum, avg, count"),
    date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[str] = Query(None, description="End date (ISO format)"),
    date_field: str = Query("date", description="Field name to use for date filtering"),
    currency_field: Optional[str] = Query(None, description="Currency field name for grouping"),
    split_by_currency: bool = Query(False, description="Split data into separate series by currency"),
    db: Session = Depends(lambda: get_db("main"))
):
    """
    Get aggregated transaction data for charts.
    
    Args:
        x_field: Field to group by (e.g., 'date', 'category', 'description')
        y_field: Field to aggregate (e.g., 'amount')
        aggregation: Aggregation method (sum, avg, count)
        date_from: Optional start date filter
        date_to: Optional end date filter
        date_field: Field name to use for date filtering (default: 'date')
        db: Database session
    
    Returns:
        Aggregated data with labels and values
    """
    try:
        import json
        from collections import defaultdict
        
        # Build base query
        query = db.query(Transaction)
        
        # Get all transactions
        transactions = query.all()
        
        # Aggregate data in Python (since JSON field querying is complex)
        # Structure: aggregated[x_value][currency] = [values...]
        if split_by_currency and currency_field:
            aggregated = defaultdict(lambda: defaultdict(list))
        else:
            aggregated = defaultdict(list)
        
        for txn in transactions:
            # Merge ingested and computed content
            content = {**(txn.ingested_content or {}), **(txn.computed_content or {})}
            
            # Apply date filters on the transaction's date field (from content, NOT created_at)
            if date_from or date_to:
                txn_date_str = content.get(date_field)
                if txn_date_str:
                    try:
                        # Parse transaction date
                        if isinstance(txn_date_str, str):
                            # Try multiple date formats
                            txn_date = None
                            date_formats = [
                                '%Y-%m-%d',  # ISO format
                                '%m/%d/%Y',  # MM/DD/YYYY
                                '%d/%m/%Y',  # DD/MM/YYYY
                                '%Y/%m/%d',  # YYYY/MM/DD
                            ]
                            
                            # Try ISO format first (handles YYYY-MM-DDTHH:MM:SS)
                            try:
                                txn_date = datetime.fromisoformat(txn_date_str.split('T')[0])
                            except ValueError:
                                # Try other formats
                                for fmt in date_formats:
                                    try:
                                        txn_date = datetime.strptime(txn_date_str, fmt)
                                        break
                                    except ValueError:
                                        continue
                            
                            if txn_date is None:
                                continue
                        else:
                            continue  # Skip if not a string
                        
                        # Check date range
                        if date_from:
                            date_from_dt = datetime.fromisoformat(date_from)
                            if txn_date.date() < date_from_dt.date():
                                continue  # Skip transaction outside range
                        
                        if date_to:
                            date_to_dt = datetime.fromisoformat(date_to)
                            if txn_date.date() > date_to_dt.date():
                                continue  # Skip transaction outside range
                    except (ValueError, AttributeError):
                        # Skip transactions with invalid dates
                        continue
                else:
                    # Skip transactions without a date field when filtering by date
                    if date_from or date_to:
                        continue
            
            # Extract x-axis value
            x_value = None
            if x_field == 'date':
                # Use the actual transaction date from content, not created_at
                x_value = content.get(date_field, '').split('T')[0] if content.get(date_field) else None
            elif x_field in content:
                x_value = str(content[x_field])
            else:
                # Try to find field in nested structures (case-insensitive)
                for key, val in content.items():
                    if key.lower() == x_field.lower():
                        x_value = str(val)
                        break
            
            if x_value is None:
                continue
            
            # Extract y-axis value
            y_value = None
            if y_field in content:
                try:
                    y_value = float(content[y_field])
                except (ValueError, TypeError):
                    continue
            else:
                # Try to find field in nested structures (case-insensitive)
                for key, val in content.items():
                    if key.lower() == y_field.lower():
                        try:
                            y_value = float(val)
                            break
                        except (ValueError, TypeError):
                            continue
            
            if y_value is not None:
                # Handle currency grouping
                if split_by_currency and currency_field:
                    # Extract currency code or symbol
                    currency = content.get(currency_field, 'UNKNOWN')
                    if isinstance(currency, str):
                        # Map common symbols to codes for consistency
                        symbol_to_code = {
                            '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY',
                            '₹': 'INR', '₽': 'RUB', 'R$': 'BRL', '₩': 'KRW',
                            'kr': 'NOK', 'zł': 'PLN', '฿': 'THB', 'Rp': 'IDR',
                            'RM': 'MYR', '₱': 'PHP', 'R': 'ZAR', '₺': 'TRY'
                        }
                        currency = symbol_to_code.get(currency, currency.upper())
                    aggregated[x_value][currency].append(y_value)
                else:
                    aggregated[x_value].append(y_value)
        
        # Apply aggregation
        if split_by_currency and currency_field:
            # Build multi-currency response
            labels = sorted(aggregated.keys())
            
            # Collect all currencies
            all_currencies = set()
            for label in labels:
                all_currencies.update(aggregated[label].keys())
            all_currencies = sorted(all_currencies)
            
            # Build values by currency
            values_by_currency = {}
            for currency in all_currencies:
                currency_values = []
                for label in labels:
                    data_points = aggregated[label].get(currency, [])
                    
                    if aggregation == 'sum':
                        value = sum(data_points)
                    elif aggregation == 'avg':
                        value = sum(data_points) / len(data_points) if data_points else 0
                    elif aggregation == 'count':
                        value = len(data_points)
                    else:
                        value = sum(data_points)
                    
                    currency_values.append(round(value, 2))
                
                values_by_currency[currency] = currency_values
            
            return {
                "labels": labels,
                "values_by_currency": values_by_currency,
                "currencies": all_currencies,
                "x_field": x_field,
                "y_field": y_field,
                "aggregation": aggregation,
                "split_by_currency": True,
                "total_records": len(transactions)
            }
        else:
            # Single series response
            labels = []
            values = []
            
            for label in sorted(aggregated.keys()):
                data_points = aggregated[label]
                
                if aggregation == 'sum':
                    value = sum(data_points)
                elif aggregation == 'avg':
                    value = sum(data_points) / len(data_points) if data_points else 0
                elif aggregation == 'count':
                    value = len(data_points)
                else:
                    value = sum(data_points)  # default to sum
                
                labels.append(label)
                values.append(round(value, 2))
            
            return {
                "labels": labels,
                "values": values,
                "x_field": x_field,
                "y_field": y_field,
                "aggregation": aggregation,
                "split_by_currency": False,
                "total_records": len(transactions),
                "filtered_records": sum(len(v) for v in aggregated.values())
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to aggregate data: {str(e)}")
