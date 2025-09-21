"""
Implementation of formula commands for transaction processing
"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Union, Optional, List, Any

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


class RegexCommand(BaseCommand):
    """Command to apply regex pattern matching and extraction to text"""
    
    def _get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="regex",
            description="Apply regex pattern to text and return matches or extracted groups",
            category="text",
            parameters=[
                CommandParameter(
                    name="pattern",
                    data_type=DataType.STRING,
                    description="Regular expression pattern to match",
                    required=True
                ),
                CommandParameter(
                    name="text",
                    data_type=DataType.STRING,
                    description="Text to search in",
                    required=True
                ),
                CommandParameter(
                    name="return_all",
                    data_type=DataType.BOOLEAN,
                    description="If true, return all matches; if false, return first match only",
                    required=False,
                    default_value=False
                ),
                CommandParameter(
                    name="group_index",
                    data_type=DataType.INTEGER,
                    description="Index of capture group to return (0 for full match, 1+ for groups)",
                    required=False,
                    default_value=0
                )
            ],
            return_type=DataType.ANY,
            examples=[
                "regex(r'\\d+', 'Price: $123.45')",
                "regex(r'\\$(\\d+\\.\\d{2})', 'Total: $99.99', group_index=1)",
                "regex(r'\\b[A-Z]{2,}\\b', 'The USA and UK are countries', return_all=true)",
                "regex(r'(\\d{4})-(\\d{2})-(\\d{2})', 'Date: 2024-01-15', group_index=1)",
                "regex(r'[A-Za-z]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}', 'Contact: john@example.com')"
            ]
        )
    
    def _execute_impl(self, pattern: str, text: str, return_all: bool = False, group_index: int = 0) -> Optional[Union[str, List[str]]]:
        """Apply regex pattern to text and return matches"""
        if not pattern or not text:
            return None
            
        try:
            # Ensure group_index is an integer, default to 0 if empty or invalid
            if group_index is None or group_index == '':
                group_index = 0
            else:
                group_index = int(group_index)
            
            # Compile the regex pattern
            regex = re.compile(pattern)
            
            if return_all:
                # Find all matches
                matches = regex.findall(text)
                if not matches:
                    return []
                
                # If group_index is specified and we have groups, extract the specific group
                if group_index > 0 and matches and isinstance(matches[0], tuple):
                    return [match[group_index - 1] if group_index <= len(match) else None for match in matches]
                elif group_index > 0 and matches and not isinstance(matches[0], tuple):
                    # Single group case - findall returns list of strings
                    return [match for match in matches]
                else:
                    return matches
            else:
                # Find first match
                match = regex.search(text)
                if not match:
                    return None
                
                # Return specific group or full match
                if group_index == 0:
                    return match.group(0)  # Full match
                elif group_index <= match.lastindex:
                    return match.group(group_index)
                else:
                    return None
                    
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {str(e)}")
        except Exception as e:
            raise ValueError(f"Regex execution error: {str(e)}")


class EqualsCommand(BaseCommand):
    """Command to compare two values for equality"""
    
    def _get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="equals",
            description="Compare two values for equality (supports string, numeric, and boolean comparisons)",
            category="comparison",
            parameters=[
                CommandParameter(
                    name="left",
                    data_type=DataType.ANY,
                    description="Left value to compare",
                    required=True
                ),
                CommandParameter(
                    name="right",
                    data_type=DataType.ANY,
                    description="Right value to compare",
                    required=True
                ),
                CommandParameter(
                    name="case_sensitive",
                    data_type=DataType.BOOLEAN,
                    description="For string comparisons, whether to be case sensitive",
                    required=False,
                    default_value=True
                )
            ],
            return_type=DataType.BOOLEAN,
            examples=[
                "equals('hello', 'hello')",
                "equals('Hello', 'hello', case_sensitive=false)",
                "equals(123, 123)",
                "equals(amount_to_float(money_in), 1500.0)",
                "equals(statement_name, 'Chase Bank')",
                "equals(transaction_type, 'DEBIT')",
                "equals(description, 'ATM WITHDRAWAL', case_sensitive=false)"
            ]
        )
    
    def _execute_impl(self, left: Any, right: Any, case_sensitive: bool = True) -> bool:
        """Compare two values for equality"""
        if left is None and right is None:
            return True
        if left is None or right is None:
            return False
        
        # Handle string comparisons
        if isinstance(left, str) and isinstance(right, str):
            if case_sensitive:
                return left == right
            else:
                return left.lower() == right.lower()
        
        # Handle numeric comparisons
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return float(left) == float(right)
        
        # Handle mixed numeric comparisons (string number vs number)
        try:
            if isinstance(left, str) and isinstance(right, (int, float)):
                return float(left) == float(right)
            elif isinstance(left, (int, float)) and isinstance(right, str):
                return float(left) == float(right)
        except (ValueError, TypeError):
            pass
        
        # Handle boolean comparisons
        if isinstance(left, bool) and isinstance(right, bool):
            return left == right
        
        # Handle mixed boolean comparisons
        if isinstance(left, bool) and isinstance(right, (str, int, float)):
            if right in ('true', 'True', 'TRUE', '1', 1, 1.0):
                return left == True
            elif right in ('false', 'False', 'FALSE', '0', 0, 0.0):
                return left == False
            else:
                return False  # No other values should equal boolean
        elif isinstance(left, (str, int, float)) and isinstance(right, bool):
            if left in ('true', 'True', 'TRUE', '1', 1, 1.0):
                return right == True
            elif left in ('false', 'False', 'FALSE', '0', 0, 0.0):
                return right == False
            else:
                return False  # No other values should equal boolean
        
        # Default comparison
        return left == right
