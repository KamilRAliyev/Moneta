"""
Formula Commands Module

This module provides a command-based system for processing transaction data
with mathematical operations, data parsing, and other utility functions.
"""

from .base import command_registry, BaseCommand, CommandMetadata, CommandResult, DataType
from .commands import (
    DateInferCommand,
    AmountToFloatCommand, 
    AddCommand,
    SubtractCommand,
    MultiplyCommand,
    DivideCommand,
    RegexCommand,
    DefaultIfNoneCommand,
    EqualsCommand,
    DateMonthCommand,
    DateWeekCommand,
    DateWeekdayCommand
)

# Register all available commands
def _register_commands():
    """Register all built-in commands"""
    commands = [
        DateInferCommand,
        AmountToFloatCommand,
        AddCommand,
        SubtractCommand, 
        MultiplyCommand,
        DivideCommand,
        RegexCommand,
        DefaultIfNoneCommand,
        EqualsCommand,
        DateMonthCommand,
        DateWeekCommand,
        DateWeekdayCommand
    ]
    
    for command_class in commands:
        command_registry.register(command_class)

# Initialize commands on module import
_register_commands()

# Export main interface
__all__ = [
    'command_registry',
    'BaseCommand',
    'CommandMetadata', 
    'CommandResult',
    'DataType'
]
