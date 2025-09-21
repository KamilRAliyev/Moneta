"""
Implementation of formula commands for transaction processing
"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Union, Optional

try:
    import dateinfer
except ImportError:
    dateinfer = None

try:
    from dateutil import parser as dateutil_parser
except ImportError:
    dateutil_parser = None

from .base import BaseCommand, CommandMetadata, CommandParameter, DataType


class DateInferCommand(BaseCommand):
    """Command to infer and parse date/datetime strings using multiple parsing methods"""
    
    def _get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="date_infer",
            description="Automatically infer date/datetime format and parse date or datetime string",
            category="date",
            parameters=[
                CommandParameter(
                    name="date_string",
                    data_type=DataType.STRING,
                    description="String containing date or datetime to parse",
                    required=True
                )
            ],
            return_type=DataType.DATE,
            examples=[
                "date_infer('2024-01-15')",
                "date_infer('01/15/2024 14:30:00')", 
                "date_infer('15-Jan-2024 2:30 PM')",
                "date_infer('2024-12-31T23:59:59')",
                "date_infer('Mon, 15 Jan 2024 14:30:00')"
            ]
        )
    
    def _execute_impl(self, date_string: str) -> Optional[datetime]:
        """Parse date string using multiple parsing methods"""
        if not date_string or not isinstance(date_string, str):
            return None
        
        date_str = date_string.strip()
        if not date_str:
            return None
            
        # Try dateinfer first if available
        if dateinfer is not None:
            try:
                inferred_format = dateinfer.infer([date_str])
                parsed_date = datetime.strptime(date_str, inferred_format)
                return parsed_date
            except (ValueError, TypeError, Exception):
                pass  # Fall through to next method
        
        # Try dateutil parser if available
        if dateutil_parser is not None:
            try:
                parsed_date = dateutil_parser.parse(date_str)
                return parsed_date
            except (ValueError, TypeError, Exception):
                pass  # Fall through to next method
        
        # Manual fallback for common formats
        common_formats = [
            # Date only formats
            '%Y-%m-%d',          # 2024-01-15
            '%m/%d/%Y',          # 01/15/2024
            '%d-%b-%Y',          # 15-Jan-2024
            '%m/%d/%y',          # 01/15/24
            '%d/%m/%Y',          # 15/01/2024
            '%Y/%m/%d',          # 2024/01/15
            '%d.%m.%Y',          # 15.01.2024
            '%b %d, %Y',         # Jan 15, 2024
            '%B %d, %Y',         # January 15, 2024
            
            # DateTime formats
            '%Y-%m-%d %H:%M:%S',     # 2024-01-15 12:30:45
            '%Y-%m-%dT%H:%M:%S',     # 2024-01-15T12:30:45 (ISO format)
            '%Y-%m-%dT%H:%M:%SZ',    # 2024-01-15T12:30:45Z (ISO with Z)
            '%Y-%m-%d %H:%M',        # 2024-01-15 12:30
            '%m/%d/%Y %H:%M:%S',     # 01/15/2024 12:30:45
            '%m/%d/%Y %H:%M',        # 01/15/2024 12:30
            '%d-%b-%Y %H:%M:%S',     # 15-Jan-2024 12:30:45
            '%d-%b-%Y %H:%M',        # 15-Jan-2024 12:30
            
            # 12-hour formats with AM/PM
            '%Y-%m-%d %I:%M:%S %p',  # 2024-01-15 02:30:45 PM
            '%Y-%m-%d %I:%M %p',     # 2024-01-15 02:30 PM
            '%m/%d/%Y %I:%M:%S %p',  # 01/15/2024 02:30:45 PM
            '%m/%d/%Y %I:%M %p',     # 01/15/2024 02:30 PM
            '%d-%b-%Y %I:%M:%S %p',  # 15-Jan-2024 02:30:45 PM
            '%d-%b-%Y %I:%M %p',     # 15-Jan-2024 02:30 PM
            
            # RFC 2822 format
            '%a, %d %b %Y %H:%M:%S', # Mon, 15 Jan 2024 14:30:00
        ]
        
        for fmt in common_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date
            except ValueError:
                continue
                
        return None


class AmountToFloatCommand(BaseCommand):
    """Command to convert amount strings to float values"""
    
    def _get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="amount_to_float",
            description="Convert amount string to float, handling currency symbols and formatting",
            category="numeric",
            parameters=[
                CommandParameter(
                    name="amount_string",
                    data_type=DataType.ANY,
                    description="Amount string to convert (can be string or numeric)",
                    required=True
                )
            ],
            return_type=DataType.FLOAT,
            examples=[
                "amount_to_float('$123.45')",
                "amount_to_float('1,234.56')",
                "amount_to_float('-$50.00')",
                "amount_to_float('(100.00)')",  # Parentheses for negative
                "amount_to_float('$(243)')",    # Dollar outside parentheses
                "amount_to_float('($243)')"     # Dollar inside parentheses
            ]
        )
    
    def _execute_impl(self, amount_string: Union[str, int, float]) -> Optional[float]:
        """Convert amount to float with robust parsing"""
        if amount_string is None:
            return None
            
        # If already numeric, convert directly
        if isinstance(amount_string, (int, float)):
            return float(amount_string)
            
        if not isinstance(amount_string, str):
            return None
            
        # Clean the string
        cleaned = str(amount_string).strip()
        if not cleaned:
            return None
            
        try:
            # Handle parentheses as negative (accounting format) - check before removing currency symbols
            # Support both $(amount) and ($amount) formats
            is_negative = (cleaned.startswith('(') and cleaned.endswith(')')) or \
                         (cleaned.startswith('$(') and cleaned.endswith(')'))
            
            if is_negative:
                # Remove parentheses and any leading currency symbol
                if cleaned.startswith('$('):
                    cleaned = cleaned[2:-1].strip()  # Remove $( and )
                else:
                    cleaned = cleaned[1:-1].strip()  # Remove ( and )
                
            # Remove currency symbols, spaces, and other non-numeric characters
            # Keep digits, decimal points, commas, and minus signs
            cleaned = re.sub(r'[^\d.,\-+]', '', cleaned)
            
            # Handle negative signs
            if cleaned.startswith('-'):
                is_negative = True
                cleaned = cleaned[1:]
            elif cleaned.startswith('+'):
                cleaned = cleaned[1:]
            
            # Remove commas (thousand separators)
            cleaned = cleaned.replace(',', '')
            
            if not cleaned or cleaned == '.':
                return None
                
            # Convert to float
            result = float(cleaned)
            return -result if is_negative else result
            
        except (ValueError, InvalidOperation):
            return None


class AddCommand(BaseCommand):
    """Addition operation for numeric values"""
    
    def _get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="add",
            description="Add two numeric values",
            category="math",
            parameters=[
                CommandParameter(name="left", data_type=DataType.FLOAT, description="Left operand", required=True),
                CommandParameter(name="right", data_type=DataType.FLOAT, description="Right operand", required=True)
            ],
            return_type=DataType.FLOAT,
            examples=["add(10.5, 20.3)", "add(amount_to_float(money_in), amount_to_float(fee))"]
        )
    
    def _execute_impl(self, left: Union[int, float], right: Union[int, float]) -> Optional[float]:
        """Add two numbers"""
        try:
            if left is None or right is None:
                return None
            return float(left) + float(right)
        except (ValueError, TypeError):
            return None


class SubtractCommand(BaseCommand):
    """Subtraction operation for numeric values"""
    
    def _get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="subtract",
            description="Subtract second value from first value",
            category="math",
            parameters=[
                CommandParameter(name="left", data_type=DataType.FLOAT, description="Value to subtract from", required=True),
                CommandParameter(name="right", data_type=DataType.FLOAT, description="Value to subtract", required=True)
            ],
            return_type=DataType.FLOAT,
            examples=["subtract(100.0, 25.5)", "subtract(amount_to_float(money_in), amount_to_float(money_out))"]
        )
    
    def _execute_impl(self, left: Union[int, float], right: Union[int, float]) -> Optional[float]:
        """Subtract right from left"""
        try:
            if left is None or right is None:
                return None
            return float(left) - float(right)
        except (ValueError, TypeError):
            return None


class MultiplyCommand(BaseCommand):
    """Multiplication operation for numeric values"""
    
    def _get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="multiply",
            description="Multiply two numeric values",
            category="math",
            parameters=[
                CommandParameter(name="left", data_type=DataType.FLOAT, description="First value", required=True),
                CommandParameter(name="right", data_type=DataType.FLOAT, description="Second value", required=True)
            ],
            return_type=DataType.FLOAT,
            examples=["multiply(10.0, 1.5)", "multiply(amount_to_float(base), 0.1)"]
        )
    
    def _execute_impl(self, left: Union[int, float], right: Union[int, float]) -> Optional[float]:
        """Multiply two numbers"""
        try:
            if left is None or right is None:
                return None
            return float(left) * float(right)
        except (ValueError, TypeError):
            return None


class DivideCommand(BaseCommand):
    """Division operation for numeric values"""
    
    def _get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="divide",
            description="Divide first value by second value",
            category="math",
            parameters=[
                CommandParameter(name="dividend", data_type=DataType.FLOAT, description="Value to be divided", required=True),
                CommandParameter(name="divisor", data_type=DataType.FLOAT, description="Value to divide by", required=True)
            ],
            return_type=DataType.FLOAT,
            examples=["divide(100.0, 4.0)", "divide(amount_to_float(total), 12)"]
        )
    
    def _execute_impl(self, dividend: Union[int, float], divisor: Union[int, float]) -> Optional[float]:
        """Divide dividend by divisor"""
        if dividend is None or divisor is None:
            return None
        if float(divisor) == 0:
            raise ValueError("Division by zero")
        return float(dividend) / float(divisor)
