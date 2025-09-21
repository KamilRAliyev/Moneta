"""
Test suite for formula commands system
"""
import sys
import os
# Add the backend directory to Python path so we can import server modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime
from server.services.formula_commands import command_registry
from server.services.formula_commands.base import DataType


class TestFormulaCommands:
    """Test all formula commands functionality"""
    
    def test_command_registry_initialization(self):
        """Test that command registry is properly initialized with commands"""
        commands = command_registry.list_commands()
        command_names = [cmd.name for cmd in commands]
        
        # Check all expected commands are registered
        expected_commands = [
            'date_infer', 
            'amount_to_float', 
            'add', 
            'subtract', 
            'multiply', 
            'divide'
        ]
        
        for expected_cmd in expected_commands:
            assert expected_cmd in command_names, f"Command {expected_cmd} not found in registry"
    
    def test_date_infer_command(self):
        """Test date_infer command with various date formats"""
        command = command_registry.get_command('date_infer')
        assert command is not None
        
        test_cases = [
            # Date only formats
            ('2024-01-15', datetime(2024, 1, 15)),
            ('01/15/2024', datetime(2024, 1, 15)),
            ('15-Jan-2024', datetime(2024, 1, 15)),
            ('2024-12-31', datetime(2024, 12, 31)),
            ('12/31/2024', datetime(2024, 12, 31)),
            
            # DateTime formats
            ('2024-01-15 14:30:00', datetime(2024, 1, 15, 14, 30, 0)),
            ('01/15/2024 14:30:00', datetime(2024, 1, 15, 14, 30, 0)),
            ('2024-01-15T14:30:00', datetime(2024, 1, 15, 14, 30, 0)),
            ('2024-01-15 02:30 PM', datetime(2024, 1, 15, 14, 30, 0)),
            ('01/15/2024 02:30:45 PM', datetime(2024, 1, 15, 14, 30, 45)),
            
            # Edge cases
            ('', None),  # Empty string
            (None, None),  # None input
        ]
        
        for input_date, expected in test_cases:
            result = command.execute(input_date)
            if expected is None:
                assert result.value is None
            else:
                assert result.success == True, f"Expected success for '{input_date}', got error: {result.error}"
                assert isinstance(result.value, datetime)
                assert result.value.year == expected.year
                assert result.value.month == expected.month
                assert result.value.day == expected.day
                assert result.value.hour == expected.hour
                assert result.value.minute == expected.minute
                assert result.value.second == expected.second
    
    def test_amount_to_float_command(self):
        """Test amount_to_float command with various amount formats"""
        command = command_registry.get_command('amount_to_float')
        assert command is not None
        
        test_cases = [
            # Basic formats
            ('123.45', 123.45),
            ('$123.45', 123.45),
            ('1,234.56', 1234.56),
            ('-50.00', -50.00),
            ('-$50.00', -50.00),
            ('(100.00)', -100.00),  # Parentheses for negative
            
            # Currency symbols
            ('€123.45', 123.45),
            ('£456.78', 456.78),
            ('¥1000', 1000.0),
            
            # Spaces and formatting
            (' $123.45 ', 123.45),
            ('USD 1,500.00', 1500.00),
            
            # Already numeric
            (123.45, 123.45),
            (100, 100.0),
            
            # Edge cases
            ('', None),
            (None, None),
            ('abc', None),
            ('$', None),
        ]
        
        for input_amount, expected in test_cases:
            result = command.execute(input_amount)
            if expected is None:
                assert result.value is None or not result.success
            else:
                assert result.success == True
                assert abs(result.value - expected) < 0.001, f"Expected {expected}, got {result.value} for input '{input_amount}'"
    
    def test_add_command(self):
        """Test add command"""
        command = command_registry.get_command('add')
        assert command is not None
        
        test_cases = [
            (10.5, 20.3, 30.8),
            (0, 5, 5),
            (-10, 5, -5),
            (100, 0.5, 100.5),
            (None, 5, None),
            (5, None, None),
        ]
        
        for left, right, expected in test_cases:
            result = command.execute(left, right)
            if expected is None:
                assert result.value is None or not result.success
            else:
                assert result.success == True
                assert abs(result.value - expected) < 0.001
    
    def test_subtract_command(self):
        """Test subtract command"""
        command = command_registry.get_command('subtract')
        assert command is not None
        
        test_cases = [
            (100.0, 25.5, 74.5),
            (50, 50, 0),
            (10, 20, -10),
            (0, 5, -5),
            (None, 5, None),
            (5, None, None),
        ]
        
        for left, right, expected in test_cases:
            result = command.execute(left, right)
            if expected is None:
                assert result.value is None or not result.success
            else:
                assert result.success == True
                assert abs(result.value - expected) < 0.001
    
    def test_multiply_command(self):
        """Test multiply command"""
        command = command_registry.get_command('multiply')
        assert command is not None
        
        test_cases = [
            (10.0, 1.5, 15.0),
            (5, 0, 0),
            (-10, 3, -30),
            (2.5, 4, 10.0),
            (None, 5, None),
            (5, None, None),
        ]
        
        for left, right, expected in test_cases:
            result = command.execute(left, right)
            if expected is None:
                assert result.value is None or not result.success
            else:
                assert result.success == True
                assert abs(result.value - expected) < 0.001
    
    def test_divide_command(self):
        """Test divide command"""
        command = command_registry.get_command('divide')
        assert command is not None
        
        test_cases = [
            (100.0, 4.0, 25.0),
            (15, 3, 5.0),
            (7, 2, 3.5),
            (0, 5, 0.0),
            (None, 5, None),
            (5, None, None),
        ]
        
        for dividend, divisor, expected in test_cases:
            result = command.execute(dividend, divisor)
            if expected is None:
                assert result.value is None or not result.success
            else:
                assert result.success == True
                assert abs(result.value - expected) < 0.001
        
        # Test division by zero
        result = command.execute(10, 0)
        assert not result.success
        assert "Division by zero" in result.error
    
    def test_command_metadata(self):
        """Test that all commands have proper metadata"""
        commands = command_registry.list_commands()
        
        for cmd in commands:
            # Check required metadata fields
            assert cmd.name is not None and cmd.name != ""
            assert cmd.description is not None and cmd.description != ""
            assert cmd.category is not None and cmd.category != ""
            assert isinstance(cmd.parameters, list)
            assert cmd.return_type in DataType
            assert isinstance(cmd.examples, list)
            
            # Check parameters have required fields
            for param in cmd.parameters:
                assert param.name is not None and param.name != ""
                assert param.data_type in DataType
                assert param.description is not None and param.description != ""
                assert isinstance(param.required, bool)
    
    def test_command_categories(self):
        """Test command categories are properly set"""
        commands = command_registry.list_commands()
        categories = {cmd.category for cmd in commands}
        
        expected_categories = {'date', 'numeric', 'math'}
        assert expected_categories.issubset(categories)
    
    def test_command_execution_error_handling(self):
        """Test command error handling with invalid inputs"""
        # Test with non-existent command
        command = command_registry.get_command('nonexistent')
        assert command is None
        
        # Test date_infer with invalid date
        date_cmd = command_registry.get_command('date_infer')
        result = date_cmd.execute('invalid-date-string')
        # Should handle gracefully and return None
        assert result.value is None or not result.success


def test_run_all_commands():
    """Integration test running a sequence of commands like a real formula"""
    # Test a realistic scenario: processing transaction amounts
    
    # Get commands
    amount_to_float = command_registry.get_command('amount_to_float')
    add = command_registry.get_command('add')
    subtract = command_registry.get_command('subtract')
    
    # Simulate transaction data
    money_in_str = "$1,500.00"
    money_out_str = "$200.50"
    fee_str = "$5.95"
    
    # Convert to floats
    money_in = amount_to_float.execute(money_in_str).value
    money_out = amount_to_float.execute(money_out_str).value
    fee = amount_to_float.execute(fee_str).value
    
    assert money_in == 1500.0
    assert money_out == 200.5
    assert fee == 5.95
    
    # Calculate net amount: money_in - money_out - fee
    temp_result = subtract.execute(money_in, money_out).value  # 1299.5
    final_amount = subtract.execute(temp_result, fee).value    # 1293.55
    
    assert abs(final_amount - 1293.55) < 0.001
    
    print(f"✓ Integration test passed: ${money_in_str} - ${money_out_str} - ${fee_str} = ${final_amount}")


if __name__ == "__main__":
    # Run tests directly
    test_instance = TestFormulaCommands()
    
    print("Running Formula Commands Tests...")
    
    try:
        test_instance.test_command_registry_initialization()
        print("✓ Command registry initialization test passed")
        
        test_instance.test_date_infer_command()
        print("✓ Date infer command test passed")
        
        test_instance.test_amount_to_float_command()
        print("✓ Amount to float command test passed")
        
        test_instance.test_add_command()
        print("✓ Add command test passed")
        
        test_instance.test_subtract_command()
        print("✓ Subtract command test passed")
        
        test_instance.test_multiply_command()
        print("✓ Multiply command test passed")
        
        test_instance.test_divide_command()
        print("✓ Divide command test passed")
        
        test_instance.test_command_metadata()
        print("✓ Command metadata test passed")
        
        test_instance.test_command_categories()
        print("✓ Command categories test passed")
        
        test_instance.test_command_execution_error_handling()
        print("✓ Error handling test passed")
        
        test_run_all_commands()
        print("✓ Integration test passed")
        
        print("\n🎉 All tests passed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
