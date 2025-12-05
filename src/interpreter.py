"""
Interpreter and execution context for the build system.

This module provides the Interpreter class which traverses and executes the AST,
and the Context class which manages the execution environment including variables,
functions, and modules.
"""

# pylint: disable=too-many-public-methods

import os
import re
import subprocess
from typing import Any, List, Dict, Callable
from src.types import (
    Program,
    FunctionCall,
    Literal,
    Identifier,
    VariableDeref,
    PropertyAccess,
    ASTNode,
    SymbolType,
    Flag,
    Executable,
)
from src.protocols import InterpreterProtocol, ContextProtocol


class Context(ContextProtocol):
    """
    Holds the execution context (symbols, functions, modules) for the interpreter.

    Attributes
    ----------
    symbols : Dict[str, Any]
        Dictionary of variable names and their values.
    functions : Dict[str, Callable]
        Dictionary of registered function names and their implementations.
    modules : Dict[str, Any]
        Dictionary of loaded modules.
    """

    def __init__(self):
        self._symbols: Dict[str, Any] = {}  # name -> value
        self._functions: Dict[str, Callable] = {}  # name -> callable
        self._modules: Dict[str, Any] = {}  # name -> module object

    @property
    def symbols(self) -> Dict[str, Any]:
        """
        Returns the dictionary of symbols.
        """
        return self._symbols

    @property
    def functions(self) -> Dict[str, Callable]:
        """
        Returns the dictionary of functions.
        """
        return self._functions

    @property
    def modules(self) -> Dict[str, Any]:
        """
        Returns the dictionary of modules.
        """
        return self._modules

    def get(self, name: str) -> Any:
        """
        Retrieves a symbol's value by name.

        Parameters
        ----------
        name : str
            The symbol name.

        Returns
        -------
        Any
            The symbol's value, or None if not found.
        """
        return self._symbols.get(name)

    def set(self, name: str, value: Any) -> None:
        """
        Sets a symbol's value.

        Parameters
        ----------
        name : str
            The symbol name.
        value : Any
            The value to set.
        """
        self._symbols[name] = value

    def register_function(self, name: str, func: Callable) -> None:
        """
        Registers a function in the context.

        Parameters
        ----------
        name : str
            The function name.
        func : Callable
            The function implementation.
        """
        self._functions[name] = func

    def call_function(
        self, name: str, args: List[Any], interpreter: InterpreterProtocol
    ) -> Any:
        """
        Calls a registered function.

        Parameters
        ----------
        name : str
            The name of the function to call.
        args : List[Any]
            The arguments to pass to the function.
        interpreter : InterpreterProtocol
            The interpreter instance.

        Returns
        -------
        Any
            The return value of the function.

        Raises
        ------
        Exception
            If the function is not found or callable.
        """
        if name in self._functions:
            return self._functions[name](args, interpreter)

        # Check if name is a Variable that calls a Flag (Mechanism 1)
        val = self.get(name)
        if val is not None:
            eval_args = interpreter.evaluate_args(args)

            # Case: Variable(Flag) -> Flag(Variable)
            if len(eval_args) == 1 and isinstance(eval_args[0], Flag):
                flag = eval_args[0]
                return flag.apply([val])

            # Case: Flag(Args...)
            if isinstance(val, Flag):
                return val.apply(eval_args)

        raise RuntimeError(f"Unknown function or callable: {name}")


class Interpreter(InterpreterProtocol):
    """
    AST Interpreter/Visitor implementation.

    Attributes
    ----------
    plugin_visitors : Dict[Any, Any]
        Static registry for plugins to register visitors.
    context : Context
        The execution context.
    visitors : Dict[Any, Callable]
        Dictionary of AST node types to visitor functions.
    dry_run : bool
        If True, executes in dry-run mode (printing instead of executing commands).
    """

    plugin_visitors: Dict[Any, Any] = (
        {}
    )  # Static registry for plugins to register visitors

    def __init__(self, dry_run: bool = False):
        self._context = Context()
        self.visitors: Dict[Any, Callable] = {}  # type -> fn
        self._dry_run: bool = dry_run
        self.setup_core_functions()
        self.register_core_visitors()
        # Register plugin visitors
        self.visitors.update(Interpreter.plugin_visitors)

    @property
    def context(self) -> ContextProtocol:
        """
        Returns the interpreter's context.
        """
        return self._context

    @property
    def dry_run(self) -> bool:
        return self._dry_run

    def register_visitor(self, node_type: Any, handler: Any) -> None:
        """
        Registers a visitor function for a specific AST node type.

        Parameters
        ----------
        node_type : Any
            The class of the AST node.
        handler : Any
            The visitor function.
        """
        self.visitors[node_type] = handler

    def visit(self, node: ASTNode) -> Any:
        """
        Visits an AST node using the registered visitor.

        Parameters
        ----------
        node : ASTNode
            The node to visit.

        Returns
        -------
        Any
            The result of the visit.

        Raises
        ------
        Exception
            If no visitor is registered for the node type.
        """
        handler = self.visitors.get(type(node))
        if handler:
            return handler(self, node)  # Handler signature: (interpreter, node)
        raise RuntimeError(f"No visitor registered for node type: {type(node)}")

    def register_core_visitors(self) -> None:
        """
        Registers visitors for core AST nodes.
        """
        self.register_visitor(Program, self.visit_program_node)
        self.register_visitor(FunctionCall, self.visit_function_call_node)
        self.register_visitor(Literal, lambda i, n: n.value)
        self.register_visitor(Identifier, self.visit_identifier_node)
        self.register_visitor(VariableDeref, self.visit_variable_deref_node)
        self.register_visitor(PropertyAccess, self.visit_property_access)

    def setup_core_functions(self) -> None:
        """
        Registers core functions in the context.
        """
        self.context.register_function("IMPORT", self.func_import)
        self.context.register_function("USING", self.func_using)
        self.context.register_function("DECLARE", self.func_declare)
        self.context.register_function("SET", self.func_set)
        self.context.register_function("EXECUTE", self.func_execute)
        self.context.register_function("IF", self.func_if)
        self.context.register_function("IFANY", self.func_ifany)
        self.context.register_function("ECHO", self.func_echo)
        self.context.register_function("BUILTIN", self.func_builtin)

        # New ARRAY function
        self.context.register_function("ARRAY", self.func_array)

        # Logical/Helper functions
        self.context.register_function("NOT", self.func_not)
        self.context.register_function("NEQ", self.func_neq)
        self.context.register_function("EXISTS", self.func_exists)

    # --- Core Visitor Implementations ---

    def visit_program_node(
        self, interpreter: InterpreterProtocol, node: Program
    ) -> Any:
        """
        Visits a Program node.
        """
        result = None
        for stmt in node.statements:
            result = interpreter.visit(stmt)
        return result

    def visit_function_call_node(
        self, interpreter: InterpreterProtocol, node: FunctionCall
    ) -> Any:
        """
        Visits a FunctionCall node.
        """
        func_name = node.name.name
        return interpreter.context.call_function(func_name, node.args, interpreter)  # type: ignore

    def visit_identifier_node(
        self, interpreter: InterpreterProtocol, node: Identifier
    ) -> Any:
        """
        Visits an Identifier node.
        """
        val = interpreter.context.get(node.name)
        if val is not None:
            return val
        return node.name

    def visit_variable_deref_node(
        self, interpreter: InterpreterProtocol, node: VariableDeref
    ) -> Any:
        """
        Visits a VariableDeref node.
        """
        target = node.target
        if isinstance(target, Identifier):
            return interpreter.context.get(target.name)
        elif isinstance(target, FunctionCall):
            return interpreter.visit(target)
        elif isinstance(target, Literal):
            if isinstance(target.value, str):
                return interpreter.interpolate_string(target.value)
            return target.value
        return interpreter.visit(target)

    def visit_property_access(
        self, interpreter: InterpreterProtocol, node: PropertyAccess
    ) -> Any:
        """
        Visits a PropertyAccess node.
        """
        obj = interpreter.visit(node.target)
        prop = node.property_name.name

        if hasattr(obj, "get"):
            return obj.get(prop)
        if hasattr(obj, prop):
            return getattr(obj, prop)
        if isinstance(obj, dict):
            return obj.get(prop)
        return None

    def interpolate_string(self, s: str) -> str:
        """
        Interpolates variables in a string (e.g. "$VAR").

        Parameters
        ----------
        s : str
            The string to interpolate.

        Returns
        -------
        str
            The interpolated string.
        """

        def replace(match):
            name = match.group(1)
            val = self.context.get(name)
            return str(val) if val is not None else match.group(0)

        return re.sub(r"\$([a-zA-Z_]\w*)", replace, s)

    def evaluate_args(self, args_nodes: List[ASTNode]) -> List[Any]:
        """
        Evaluates a list of argument nodes.

        Parameters
        ----------
        args_nodes : List[ASTNode]
            The argument nodes.

        Returns
        -------
        List[Any]
            The evaluated arguments.
        """
        return [self.visit(arg) for arg in args_nodes]

    # --- Core Functions ---

    def func_array(
        self, args: List[ASTNode], interpreter: InterpreterProtocol
    ) -> List[Any]:
        """
        Creates an array from arguments.

        Parameters
        ----------
        args : List[ASTNode]
            The argument nodes to convert into an array.
        interpreter : InterpreterProtocol
            The interpreter instance.

        Returns
        -------
        List[Any]
            A list containing the evaluated arguments.
        """
        # ARRAY(item1, item2, ...) -> Returns list
        return interpreter.evaluate_args(args)

    def func_import(
        self, args: List[ASTNode], interpreter: InterpreterProtocol
    ) -> None:
        """
        Imports a module.

        Parameters
        ----------
        args : List[ASTNode]
            The import arguments (module name, etc.).
        interpreter : InterpreterProtocol
            The interpreter instance.
        """
        _ = interpreter.evaluate_args(args)
        # Assuming args[0] handles the import side-effect logic (like BUILTIN)

    def func_using(self, args: List[ASTNode], interpreter: InterpreterProtocol) -> None:
        """
        Brings module symbols into the current scope.

        Parameters
        ----------
        args : List[ASTNode]
            The module name or module object to import symbols from.
        interpreter : InterpreterProtocol
            The interpreter instance.

        Notes
        -----
        If the module is not found, a warning is printed but execution continues.
        """
        evaluated_args = interpreter.evaluate_args(args)
        module_or_name = evaluated_args[0]
        module = module_or_name
        if isinstance(module, str):
            module = interpreter.context.modules.get(module)

        if isinstance(module, dict):
            for key, val in module.items():
                interpreter.context.register_function(key, val)
        else:
            print(f"Warning: Module {module_or_name} not found or invalid.")

    def func_builtin(
        self, args: List[ASTNode], interpreter: InterpreterProtocol
    ) -> Any:
        """
        Loads a builtin module.

        Parameters
        ----------
        args : List[ASTNode]
            The builtin module name to load.
        interpreter : InterpreterProtocol
            The interpreter instance.

        Returns
        -------
        Any
            The loaded module object, or None if the module is not recognized.

        Notes
        -----
        Currently supports 'FILESTAT' and 'BUILDCACHE' builtin modules.
        """
        # pylint: disable=import-outside-toplevel
        evaluated_args = interpreter.evaluate_args(args)
        name = evaluated_args[0]
        if name == "FILESTAT":
            from modules.filestat import get_module

            mod = get_module()
            interpreter.context.modules["FILESTAT"] = mod
            return mod
        if name == "BUILDCACHE":
            from modules.buildcache import get_module

            mod = get_module()
            interpreter.context.modules["BUILDCACHE"] = mod
            return mod
        return None

    def func_declare(
        self, args: List[ASTNode], interpreter: InterpreterProtocol
    ) -> None:
        """
        Declares a symbol (VARIABLE, FLAGS, EXECUTABLE).

        Parameters
        ----------
        args : List[ASTNode]
            Arguments: [type, name, value(s)...]
            - args[0]: Symbol type (VARIABLE, FLAGS, or EXECUTABLE)
            - args[1]: Symbol name
            - args[2+]: Values depending on the type
        interpreter : InterpreterProtocol
            The interpreter instance.

        Notes
        -----
        - VARIABLE requires one value
        - FLAGS requires a template string
        - EXECUTABLE requires description, source, and path
        """
        type_node = args[0]
        name_node = args[1]
        decl_type = interpreter.visit(type_node)  # Should resolve to string or value

        if isinstance(name_node, Identifier):
            name = name_node.name
        else:
            name = str(interpreter.visit(name_node))

        vals = interpreter.evaluate_args(args[2:])

        if decl_type == SymbolType.VARIABLE.value or decl_type == "VARIABLE":
            interpreter.context.set(name, vals[0])
        elif decl_type == SymbolType.FLAGS.value or decl_type == "FLAGS":
            interpreter.context.set(name, Flag(name, vals[0]))
        elif decl_type == SymbolType.EXECUTABLE.value or decl_type == "EXECUTABLE":
            interpreter.context.set(name, Executable(name, vals[0], vals[1], vals[2]))

    def func_set(self, args: List[ASTNode], interpreter: InterpreterProtocol) -> None:
        """
        Sets an existing variable's value.

        Parameters
        ----------
        args : List[ASTNode]
            Arguments: [name, value]
            - args[0]: Variable name
            - args[1]: New value
        interpreter : InterpreterProtocol
            The interpreter instance.
        """
        name_node = args[0]
        if isinstance(name_node, Identifier):
            name = name_node.name
        else:
            name = str(interpreter.visit(name_node))
        val = interpreter.visit(args[1])
        interpreter.context.set(name, val)

    def func_execute(
        self, args: List[ASTNode], interpreter: InterpreterProtocol
    ) -> None:
        """
        Executes a command.

        Parameters
        ----------
        args : List[ASTNode]
            Arguments: [executable, arg1, arg2, ...]
            - args[0]: Executable or Executable object
            - args[1+]: Command arguments (may include Flag objects)
        interpreter : InterpreterProtocol
            The interpreter instance.

        Notes
        -----
        Flag objects in arguments are expanded by collecting the required
        number of preceding arguments based on the flag's arity.
        In dry-run mode, the command is printed but not executed.

        Raises
        ------
        Exception
            If a flag does not have enough preceding arguments for its arity.
        """
        evaluated_args = []
        for arg in args:
            evaluated_args.append(interpreter.visit(arg))

        exe = evaluated_args[0]
        cmd_args = evaluated_args[1:]

        final_args = []
        i = 0
        while i < len(cmd_args):
            arg = cmd_args[i]
            if isinstance(arg, Flag):
                arity = arg.arity
                if len(final_args) < arity:
                    raise ValueError(
                        f"Not enough arguments for flag {arg.name} (arity {arity})"
                    )
                flag_inputs = []
                for _ in range(arity):
                    flag_inputs.insert(0, final_args.pop())
                res = arg.apply(flag_inputs)
                final_args.extend(res.split())
            else:
                final_args.append(arg)
            i += 1

        exe_name = exe
        if isinstance(exe, Executable):
            exe_name = exe.path if exe.path else exe.name

        flat_args = []
        for a in final_args:
            if isinstance(a, list):
                flat_args.extend(map(str, a))
            else:
                flat_args.append(str(a))

        command = [str(exe_name)] + flat_args

        # Dry Run Check
        if interpreter.dry_run:
            print(f"EXECUTE (DRY): {' '.join(command)}")
            return  # Skip subprocess.run

        print(f"EXECUTE: {' '.join(command)}")
        try:
            subprocess.run(command, check=True)
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Execution failed: {e}")

    def func_if(self, args: List[ASTNode], interpreter: InterpreterProtocol) -> None:
        """
        Conditional execution (if/then/else).

        Parameters
        ----------
        args : List[ASTNode]
            Arguments: [condition, then_branch, else_branch?]
            - args[0]: Condition to evaluate
            - args[1]: Expression to execute if condition is true
            - args[2]: (Optional) Expression to execute if condition is false
        interpreter : InterpreterProtocol
            The interpreter instance.
        """
        cond = interpreter.visit(args[0])
        if cond:
            interpreter.visit(args[1])
        elif len(args) > 2:
            interpreter.visit(args[2])

    def func_ifany(self, args: List[ASTNode], interpreter: InterpreterProtocol) -> None:
        """
        Executes actions if any condition is met.

        Parameters
        ----------
        args : List[ASTNode]
            A mix of condition function calls and action expressions.
            Conditions are tested in order; once one is true, subsequent
            non-condition expressions are executed.
        interpreter : InterpreterProtocol
            The interpreter instance.

        Notes
        -----
        Recognized condition functions: NOT, EXISTS, NEQ, EQ, AND, OR, IS_PRIME.
        Once a condition evaluates to True, all following non-condition
        expressions are executed.
        """
        triggered = False
        for arg in args:
            if isinstance(arg, FunctionCall):
                name = arg.name.name
                if name in ["NOT", "EXISTS", "NEQ", "EQ", "AND", "OR", "IS_PRIME"]:
                    if not triggered:
                        res = interpreter.visit(arg)
                        if res is True:
                            triggered = True
                else:
                    if triggered:
                        interpreter.visit(arg)
            else:
                if triggered:
                    interpreter.visit(arg)

    def func_echo(self, args: List[ASTNode], interpreter: InterpreterProtocol) -> bool:
        """
        Prints arguments to stdout.

        Parameters
        ----------
        args : List[ASTNode]
            The expressions to print.
        interpreter : InterpreterProtocol
            The interpreter instance.

        Returns
        -------
        bool
            Always returns True.

        Notes
        -----
        ECHO is executed even in dry-run mode.
        """
        vals = interpreter.evaluate_args(args)
        # ECHO is executed even in dry-run?
        # "Exception: Dry-run may execute ECHO commands, not anything else."
        print(" ".join(map(str, vals)))
        return True

    def func_not(self, args: List[ASTNode], interpreter: InterpreterProtocol) -> bool:
        """
        Logical NOT.

        Parameters
        ----------
        args : List[ASTNode]
            Arguments: [expression]
        interpreter : InterpreterProtocol
            The interpreter instance.

        Returns
        -------
        bool
            The logical negation of the argument.
        """
        return not interpreter.visit(args[0])

    def func_neq(self, args: List[ASTNode], interpreter: InterpreterProtocol) -> bool:
        """
        Logical NEQ (Not Equal).

        Parameters
        ----------
        args : List[ASTNode]
            Arguments: [value1, value2]
        interpreter : InterpreterProtocol
            The interpreter instance.

        Returns
        -------
        bool
            True if the values are not equal, False otherwise.
        """
        vals = interpreter.evaluate_args(args)
        return vals[0] != vals[1]

    def func_exists(
        self, args: List[ASTNode], interpreter: InterpreterProtocol
    ) -> bool:
        """
        Checks if a file exists.

        Parameters
        ----------
        args : List[ASTNode]
            Arguments: [path]
        interpreter : InterpreterProtocol
            The interpreter instance.

        Returns
        -------
        bool
            True if the file exists, False otherwise.
        """
        path = interpreter.visit(args[0])
        return os.path.exists(str(path))
