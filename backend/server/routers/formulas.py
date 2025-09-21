"""
Formula Commands API Router

Provides endpoints for managing and executing formula commands
for transaction processing.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from server.services.formula_commands import command_registry, CommandResult, DataType
from server.services.database import get_db
from server.models.main import TransactionMetadata

router = APIRouter(prefix="/formulas", tags=["formulas"])


class CommandInfo(BaseModel):
    """Response model for command information"""
    name: str
    description: str
    category: str
    parameters: List[Dict[str, Any]]
    return_type: str
    examples: List[str]


class CommandExecuteRequest(BaseModel):
    """Request model for executing a command"""
    args: List[Any] = Field(default_factory=list)
    kwargs: Dict[str, Any] = Field(default_factory=dict)


class CommandExecuteResponse(BaseModel):
    """Response model for command execution"""
    success: bool
    value: Any = None
    error: Optional[str] = None


class FormulaTestRequest(BaseModel):
    """Request model for testing formulas against sample data"""
    formula: str
    sample_data: Dict[str, Any]


class FormulaTestResponse(BaseModel):
    """Response model for formula testing"""
    success: bool
    result: Any = None
    error: Optional[str] = None


@router.get("/commands", response_model=List[CommandInfo])
async def list_commands():
    """
    List all available formula commands
    
    Returns a list of all registered commands with their metadata,
    including parameters, descriptions, and usage examples.
    """
    try:
        commands = command_registry.list_commands()
        
        return [
            CommandInfo(
                name=cmd.name,
                description=cmd.description,
                category=cmd.category,
                parameters=[
                    {
                        "name": param.name,
                        "data_type": param.data_type.value,
                        "description": param.description,
                        "required": param.required,
                        "default_value": param.default_value
                    }
                    for param in cmd.parameters
                ],
                return_type=cmd.return_type.value,
                examples=cmd.examples
            )
            for cmd in commands
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing commands: {str(e)}")


@router.get("/commands/categories")
async def list_command_categories():
    """
    List all available command categories
    
    Returns a list of unique categories for organizing commands in the UI.
    """
    try:
        commands = command_registry.list_commands()
        categories = list(set(cmd.category for cmd in commands))
        
        return {
            "categories": sorted(categories),
            "commands_by_category": {
                category: [
                    cmd.name for cmd in commands if cmd.category == category
                ]
                for category in categories
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing categories: {str(e)}")


@router.get("/commands/{command_name}", response_model=CommandInfo)
async def get_command_details(command_name: str):
    """
    Get detailed information about a specific command
    
    Args:
        command_name: Name of the command to get details for
        
    Returns:
        Detailed command information including parameters and examples
    """
    try:
        command = command_registry.get_command(command_name)
        if not command:
            raise HTTPException(status_code=404, detail=f"Command '{command_name}' not found")
        
        cmd = command.metadata
        return CommandInfo(
            name=cmd.name,
            description=cmd.description,
            category=cmd.category,
            parameters=[
                {
                    "name": param.name,
                    "data_type": param.data_type.value,
                    "description": param.description,
                    "required": param.required,
                    "default_value": param.default_value
                }
                for param in cmd.parameters
            ],
            return_type=cmd.return_type.value,
            examples=cmd.examples
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting command details: {str(e)}")


@router.post("/commands/{command_name}/execute", response_model=CommandExecuteResponse)
async def execute_command(command_name: str, request: CommandExecuteRequest):
    """
    Execute a specific command with provided arguments
    
    Args:
        command_name: Name of the command to execute
        request: Command execution request with arguments
        
    Returns:
        Command execution result
    """
    try:
        command = command_registry.get_command(command_name)
        if not command:
            raise HTTPException(status_code=404, detail=f"Command '{command_name}' not found")
        
        # Execute the command
        result = command.execute(*request.args, **request.kwargs)
        
        return CommandExecuteResponse(
            success=result.success,
            value=result.value,
            error=result.error
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing command: {str(e)}")


@router.post("/test", response_model=FormulaTestResponse)
async def test_formula(request: FormulaTestRequest):
    """
    Test a formula expression against sample transaction data
    
    Args:
        request: Formula test request with formula and sample data
        
    Returns:
        Formula evaluation result
    """
    try:
        # This is a simplified test endpoint
        # In a full implementation, you'd want a proper expression parser
        # For now, return a placeholder response
        return FormulaTestResponse(
            success=True,
            result=None,
            error="Formula testing not fully implemented yet - use individual command execution for now"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing formula: {str(e)}")


@router.get("/fields")
async def get_available_fields(db: Session = Depends(lambda: get_db("main"))):
    """
    Get available transaction fields for formula building
    
    Returns transaction metadata showing available ingested and computed fields
    that can be used in formulas.
    """
    try:
        # Get transaction metadata
        metadata = db.query(TransactionMetadata).first()
        
        if not metadata:
            return {
                "ingested_fields": [],
                "computed_fields": [],
                "message": "No transaction metadata found"
            }
        
        # Format field information for UI
        ingested_fields = [
            {
                "name": field_name,
                "type": "ingested",
                "sample_values": field_info.get("sample_values", []) if isinstance(field_info, dict) else [],
                "description": f"Ingested field: {field_name}"
            }
            for field_name, field_info in metadata.ingested_columns.items()
        ]
        
        computed_fields = [
            {
                "name": field_name,
                "type": "computed", 
                "sample_values": field_info.get("sample_values", []) if isinstance(field_info, dict) else [],
                "description": f"Computed field: {field_name}"
            }
            for field_name, field_info in metadata.computed_columns.items()
        ]
        
        return {
            "ingested_fields": ingested_fields,
            "computed_fields": computed_fields,
            "total_fields": len(ingested_fields) + len(computed_fields)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting fields: {str(e)}")
