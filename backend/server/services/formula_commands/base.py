from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Type
from pydantic import BaseModel, Field
from enum import Enum
import inspect


class DataType(Enum):
    """Supported data types for command inputs/outputs"""
    STRING = "string"
    FLOAT = "float" 
    INTEGER = "integer"
    DATE = "date"
    BOOLEAN = "boolean"
    ANY = "any"


class CommandParameter(BaseModel):
    """Definition of a command parameter"""
    name: str
    data_type: DataType
    description: str
    required: bool = True
    default_value: Optional[Any] = None


class CommandMetadata(BaseModel):
    """Metadata describing a command"""
    name: str
    description: str
    category: str
    parameters: List[CommandParameter]
    return_type: DataType
    examples: List[str] = Field(default_factory=list)


class CommandResult(BaseModel):
    """Result of command execution"""
    success: bool
    value: Any = None
    error: Optional[str] = None


class BaseCommand(ABC):
    """Base class for all formula commands"""
    
    def __init__(self):
        self._metadata = self._get_metadata()
        self._validate_implementation()
    
    @property
    def metadata(self) -> CommandMetadata:
        """Get command metadata"""
        return self._metadata
    
    @abstractmethod
    def _get_metadata(self) -> CommandMetadata:
        """Return metadata describing this command"""
        pass
    
    @abstractmethod
    def _execute_impl(self, *args, **kwargs) -> Any:
        """Execute the command logic"""
        pass
    
    def execute(self, *args, **kwargs) -> CommandResult:
        """Execute command with error handling and validation"""
        try:
            # Validate arguments
            self._validate_args(args, kwargs)
            
            # Execute the command
            result = self._execute_impl(*args, **kwargs)
            
            return CommandResult(success=True, value=result)
            
        except Exception as e:
            return CommandResult(success=False, error=str(e))
    
    def _validate_args(self, args: tuple, kwargs: dict):
        """Validate command arguments against metadata"""
        provided_args = len(args) + len(kwargs)
        required_params = [p for p in self.metadata.parameters if p.required]
        
        if provided_args < len(required_params):
            param_names = [p.name for p in required_params]
            raise ValueError(f"Missing required parameters: {param_names}")
    
    def _validate_implementation(self):
        """Validate that command implementation matches metadata"""
        sig = inspect.signature(self._execute_impl)
        params = list(sig.parameters.keys())
        
        # Remove 'self' if present
        if params and params[0] == 'self':
            params = params[1:]
        
        metadata_params = [p.name for p in self.metadata.parameters]
        
        if len(params) != len(metadata_params):
            raise ValueError(f"Command {self.metadata.name}: Implementation parameters {params} don't match metadata parameters {metadata_params}")


class CommandRegistry:
    """Registry for managing available commands"""
    
    def __init__(self):
        self._commands: Dict[str, BaseCommand] = {}
    
    def register(self, command_class: Type[BaseCommand]) -> None:
        """Register a new command"""
        command = command_class()
        self._commands[command.metadata.name] = command
    
    def get_command(self, name: str) -> Optional[BaseCommand]:
        """Get a command by name"""
        return self._commands.get(name)
    
    def list_commands(self) -> List[CommandMetadata]:
        """List all available commands"""
        return [cmd.metadata for cmd in self._commands.values()]
    
    def get_commands_by_category(self, category: str) -> List[CommandMetadata]:
        """Get commands filtered by category"""
        return [cmd.metadata for cmd in self._commands.values() 
                if cmd.metadata.category == category]


# Global command registry instance
command_registry = CommandRegistry()