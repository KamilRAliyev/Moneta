"""
Rule Engine Service

Handles safe evaluation of rule conditions and actions using the formula command system.
Supports formula expressions, model mappings, and value assignments.
"""

import re
import ast
import operator
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from server.services.formula_commands import command_registry, CommandResult
from server.models.configurations import ComputedFieldRule


@dataclass
class RuleEvaluationResult:
    """Result of evaluating a single rule"""
    success: bool
    condition_matched: bool
    target_field: str
    computed_value: Any = None
    error: Optional[str] = None


@dataclass
class RuleExecutionContext:
    """Context for rule execution containing transaction data and metadata"""
    transaction_data: Dict[str, Any]  # ingested_content + computed_content
    ingested_fields: List[str]
    computed_fields: List[str]
    available_commands: List[str]


class SafeExpressionEvaluator:
    """Safe evaluator for rule expressions using AST parsing and formula commands"""
    
    # Safe operators for condition evaluation
    SAFE_OPERATORS = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.In: lambda x, y: x in y,
        ast.NotIn: lambda x, y: x not in y,
        ast.And: operator.and_,
        ast.Or: operator.or_,
        ast.Not: operator.not_,
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
    }
    
    def __init__(self, context: RuleExecutionContext):
        self.context = context
        
    def evaluate_condition(self, condition_expr: str) -> Tuple[bool, Optional[str]]:
        """
        Safely evaluate a condition expression
        
        Args:
            condition_expr: Expression like "merchant == 'Amazon'" or "amount > 100"
            
        Returns:
            (condition_result, error_message)
        """
        if not condition_expr or not condition_expr.strip():
            return True, None  # Empty condition always matches
            
        try:
            # Parse the expression into AST
            tree = ast.parse(condition_expr.strip(), mode='eval')
            result = self._evaluate_ast_node(tree.body)
            return bool(result), None
            
        except Exception as e:
            return False, f"Condition evaluation error: {str(e)}"
    
    def evaluate_action(self, action_expr: str, rule_type: str) -> Tuple[Any, Optional[str]]:
        """
        Safely evaluate an action expression
        
        Args:
            action_expr: Expression like "amount_to_float(amount)" or "Account('Cash')"
            rule_type: Type of rule (formula, model_mapping, value_assignment)
            
        Returns:
            (computed_value, error_message)
        """
        try:
            if rule_type == "value_assignment":
                # Direct value assignment - parse as literal
                return self._parse_literal_value(action_expr)
                
            elif rule_type == "model_mapping":
                # Model mapping like Account('Cash') - handle specially
                return self._evaluate_model_mapping(action_expr)
                
            elif rule_type == "formula":
                # Formula expression using commands
                return self._evaluate_formula_expression(action_expr)
                
            else:
                return None, f"Unknown rule type: {rule_type}"
                
        except Exception as e:
            return None, f"Action evaluation error: {str(e)}"
    
    def _evaluate_ast_node(self, node: ast.AST) -> Any:
        """Recursively evaluate AST nodes safely"""
        if isinstance(node, ast.Constant):
            return node.value
            
        elif isinstance(node, ast.Name):
            # Variable lookup in transaction data
            var_name = node.id
            if var_name in self.context.transaction_data:
                return self.context.transaction_data[var_name]
            else:
                raise ValueError(f"Unknown variable: {var_name}")
                
        elif isinstance(node, ast.Compare):
            left = self._evaluate_ast_node(node.left)
            result = left
            
            for i, (op, comparator) in enumerate(zip(node.ops, node.comparators)):
                right = self._evaluate_ast_node(comparator)
                if type(op) not in self.SAFE_OPERATORS:
                    raise ValueError(f"Unsupported operator: {type(op).__name__}")
                result = self.SAFE_OPERATORS[type(op)](result, right)
                if not result:
                    break
            return result
            
        elif isinstance(node, ast.BoolOp):
            op = node.op
            if type(op) not in self.SAFE_OPERATORS:
                raise ValueError(f"Unsupported boolean operator: {type(op).__name__}")
                
            if isinstance(op, ast.And):
                return all(self._evaluate_ast_node(value) for value in node.values)
            elif isinstance(op, ast.Or):
                return any(self._evaluate_ast_node(value) for value in node.values)
                
        elif isinstance(node, ast.UnaryOp):
            operand = self._evaluate_ast_node(node.operand)
            if type(node.op) not in self.SAFE_OPERATORS:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return self.SAFE_OPERATORS[type(node.op)](operand)
            
        elif isinstance(node, ast.BinOp):
            left = self._evaluate_ast_node(node.left)
            right = self._evaluate_ast_node(node.right)
            if type(node.op) not in self.SAFE_OPERATORS:
                raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
            return self.SAFE_OPERATORS[type(node.op)](left, right)
            
        elif isinstance(node, ast.Call):
            # Handle safe method calls like string.contains(), string.startswith(), etc.
            return self._evaluate_method_call(node)
            
        elif isinstance(node, ast.Attribute):
            # Handle attribute access like field.attribute
            value = self._evaluate_ast_node(node.value)
            attr_name = node.attr
            
            # For now, just return the attribute name - it will be used in method calls
            return getattr(value, attr_name, None)
            
        else:
            raise ValueError(f"Unsupported AST node type: {type(node).__name__}")
    
    def _evaluate_method_call(self, node: ast.Call) -> Any:
        """Evaluate safe method calls"""
        if isinstance(node.func, ast.Attribute):
            # Method call like obj.method()
            obj = self._evaluate_ast_node(node.func.value)
            method_name = node.func.attr
            args = [self._evaluate_ast_node(arg) for arg in node.args]
            
            # Whitelist of safe string methods
            safe_string_methods = {
                'contains': lambda s, substr: str(substr).lower() in str(s).lower(),
                'startswith': lambda s, prefix: str(s).lower().startswith(str(prefix).lower()),
                'endswith': lambda s, suffix: str(s).lower().endswith(str(suffix).lower()),
                'lower': lambda s: str(s).lower(),
                'upper': lambda s: str(s).upper(),
                'strip': lambda s: str(s).strip(),
            }
            
            if method_name in safe_string_methods:
                return safe_string_methods[method_name](obj, *args)
            else:
                raise ValueError(f"Unsupported method: {method_name}")
        elif isinstance(node.func, ast.Name):
            # Function call like function_name()
            func_name = node.func.id
            args = [self._evaluate_ast_node(arg) for arg in node.args]
            
            # Support formula commands in conditions
            if func_name in self.context.available_commands:
                from server.services.formula_commands import command_registry
                command_instance = command_registry.get_command(func_name)
                if command_instance:
                    result = command_instance.execute(*args)
                    if result.success:
                        return result.value
                    else:
                        raise ValueError(f"Formula command error: {result.error}")
                else:
                    raise ValueError(f"Formula command not found: {func_name}")
            else:
                raise ValueError(f"Function not supported in conditions: {func_name}")
        else:
            # Other function call types not supported
            raise ValueError("Complex function calls not supported in conditions")
    
    def _parse_literal_value(self, value_expr: str) -> Tuple[Any, Optional[str]]:
        """Parse a literal value for direct assignment"""
        value_expr = value_expr.strip()
        
        try:
            # Try to parse as Python literal
            tree = ast.parse(value_expr, mode='eval')
            if isinstance(tree.body, ast.Constant):
                return tree.body.value, None
            else:
                return value_expr, None  # Return as string if not a literal
                
        except:
            return value_expr, None  # Return as string if parsing fails
    
    def _evaluate_model_mapping(self, mapping_expr: str) -> Tuple[Any, Optional[str]]:
        """Evaluate model mapping expression like Account('Cash')"""
        # For now, return the expression as-is for model mapping
        # In a full implementation, you'd instantiate actual model objects
        return mapping_expr.strip(), None
    
    def _evaluate_formula_expression(self, formula_expr: str) -> Tuple[Any, Optional[str]]:
        """Evaluate formula expression using command registry"""
        try:
            # Use AST parsing to handle nested function calls properly
            parsed = ast.parse(formula_expr.strip(), mode='eval')
            result = self._evaluate_ast_node(parsed.body)
            return result, None
                    
        except Exception as e:
            return None, f"Formula evaluation error: {str(e)}"
    
    def _parse_command_args(self, args_str: str) -> List[Any]:
        """Parse command arguments from string"""
        if not args_str.strip():
            return []
        
        # Simple argument parsing - split by comma and resolve variables/literals
        args = []
        for arg in args_str.split(','):
            arg = arg.strip()
            
            # Check if it's a variable from transaction data
            if arg in self.context.transaction_data:
                args.append(self.context.transaction_data[arg])
            else:
                # Try to parse as literal
                try:
                    tree = ast.parse(arg, mode='eval')
                    if isinstance(tree.body, ast.Constant):
                        args.append(tree.body.value)
                    else:
                        args.append(arg)  # Keep as string
                except:
                    args.append(arg)  # Keep as string
                    
        return args


class RuleEngine:
    """Main rule engine for evaluating and executing rules"""
    
    def __init__(self):
        self.evaluator = None
    
    def evaluate_rule(
        self, 
        rule: ComputedFieldRule, 
        context: RuleExecutionContext
    ) -> RuleEvaluationResult:
        """
        Evaluate a single rule against transaction context
        
        Args:
            rule: The rule to evaluate
            context: Transaction context with data and metadata
            
        Returns:
            Rule evaluation result
        """
        if not rule.active:
            return RuleEvaluationResult(
                success=False,
                condition_matched=False,
                target_field=rule.target_field,
                error="Rule is not active"
            )
        
        evaluator = SafeExpressionEvaluator(context)
        
        # Evaluate condition
        condition_matched, condition_error = evaluator.evaluate_condition(rule.condition)
        
        if condition_error:
            return RuleEvaluationResult(
                success=False,
                condition_matched=False,
                target_field=rule.target_field,
                error=f"Condition error: {condition_error}"
            )
        
        if not condition_matched:
            return RuleEvaluationResult(
                success=True,
                condition_matched=False,
                target_field=rule.target_field
            )
        
        # Condition matched, evaluate action
        computed_value, action_error = evaluator.evaluate_action(rule.action, rule.rule_type)
        
        if action_error:
            return RuleEvaluationResult(
                success=False,
                condition_matched=True,
                target_field=rule.target_field,
                error=f"Action error: {action_error}"
            )
        
        return RuleEvaluationResult(
            success=True,
            condition_matched=True,
            target_field=rule.target_field,
            computed_value=computed_value
        )
    
    def execute_rules_for_transaction(
        self,
        rules: List[ComputedFieldRule],
        transaction_data: Dict[str, Any],
        ingested_fields: List[str],
        computed_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Execute rules for a single transaction
        
        Args:
            rules: List of rules sorted by priority
            transaction_data: Combined ingested_content + computed_content
            ingested_fields: Available ingested field names
            computed_fields: Available computed field names
            
        Returns:
            Dictionary of computed field values
        """
        context = RuleExecutionContext(
            transaction_data=transaction_data,
            ingested_fields=ingested_fields,
            computed_fields=computed_fields,
            available_commands=[cmd.name for cmd in command_registry.list_commands()]
        )
        
        computed_results = {}
        processed_targets = set()  # Track which target fields have been computed
        
        # Process rules in priority order (already sorted)
        for rule in rules:
            # Skip if we've already computed this target field (first successful rule wins)
            if rule.target_field in processed_targets:
                continue
            
            result = self.evaluate_rule(rule, context)
            
            if result.success and result.condition_matched:
                # Rule matched and executed successfully
                computed_results[rule.target_field] = result.computed_value
                processed_targets.add(rule.target_field)
                
                # Update context with newly computed value for subsequent rules
                context.transaction_data[rule.target_field] = result.computed_value
        
        return computed_results


# Global rule engine instance
rule_engine = RuleEngine()
