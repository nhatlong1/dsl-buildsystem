import os
import subprocess
import sys
from typing import Any, List, Dict, Callable
from src.ast_nodes import Program, FunctionCall, Literal, Identifier, VariableDeref, PropertyAccess, ASTNode

class SymbolType:
    VARIABLE = 'VARIABLE'
    FLAGS = 'FLAGS'
    EXECUTABLE = 'EXECUTABLE'
    MACRO = 'MACRO'

class Flag:
    def __init__(self, name, template):
        self.name = name
        self.template = template
        # Determine arity by finding max $N
        self.arity = 0
        import re
        matches = re.findall(r'\$(\d+)', template)
        if matches:
            self.arity = max(map(int, matches))

    def apply(self, args):
        if len(args) != self.arity:
            raise Exception(f"Flag {self.name} expects {self.arity} arguments, got {len(args)}")

        result = self.template
        for i, arg in enumerate(args):
            result = result.replace(f"${i+1}", str(arg))
        return result

    def __repr__(self):
        return f"<Flag {self.name} arity={self.arity}>"

class Executable:
    def __init__(self, name, description, source, path):
        self.name = name
        self.description = description
        self.source = source
        self.path = path

class Context:
    def __init__(self):
        self.symbols = {} # name -> value (Variable, Flag, Executable, or generic value)
        self.functions = {} # name -> callable
        self.modules = {} # name -> module object

    def get(self, name):
        return self.symbols.get(name)

    def set(self, name, value):
        self.symbols[name] = value

    def register_function(self, name, func):
        self.functions[name] = func

    def call_function(self, name, args, interpreter):
        if name in self.functions:
            return self.functions[name](args, interpreter)

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

        raise Exception(f"Unknown function or callable: {name}")

class Interpreter:
    plugin_visitors = {} # Static registry for plugins to register visitors

    def __init__(self):
        self.context = Context()
        self.visitors = {} # type -> fn
        self.setup_core_functions()
        self.register_core_visitors()
        # Register plugin visitors
        self.visitors.update(Interpreter.plugin_visitors)

    def register_visitor(self, node_type, handler):
        self.visitors[node_type] = handler

    def visit(self, node: ASTNode) -> Any:
        handler = self.visitors.get(type(node))
        if handler:
            return handler(self, self, node)
        raise Exception(f"No visitor registered for node type: {type(node)}")

    def register_core_visitors(self):
        self.register_visitor(Program, self.visit_Program)
        self.register_visitor(FunctionCall, self.visit_FunctionCall)
        self.register_visitor(Literal, lambda i, n: n.value)
        self.register_visitor(Identifier, self.visit_Identifier)
        self.register_visitor(VariableDeref, self.visit_VariableDeref)
        self.register_visitor(PropertyAccess, self.visit_PropertyAccess)

    def setup_core_functions(self):
        self.context.register_function('IMPORT', self.func_import)
        self.context.register_function('USING', self.func_using)
        self.context.register_function('DECLARE', self.func_declare)
        self.context.register_function('SET', self.func_set)
        self.context.register_function('EXECUTE', self.func_execute)
        self.context.register_function('IF', self.func_if)
        self.context.register_function('IFANY', self.func_ifany)
        self.context.register_function('ECHO', self.func_echo)
        self.context.register_function('BUILTIN', self.func_builtin)

        # New ARRAY function
        self.context.register_function('ARRAY', self.func_array)

        # Logical/Helper functions
        self.context.register_function('NOT', self.func_not)
        self.context.register_function('NEQ', self.func_neq)
        self.context.register_function('EXISTS', self.func_exists)

    # --- Core Visitor Implementations ---

    def visit_Program(self, interpreter, node: Program):
        result = None
        for stmt in node.statements:
            result = interpreter.visit(stmt)
        return result

    def visit_FunctionCall(self, interpreter, node: FunctionCall):
        func_name = node.name.name
        return interpreter.context.call_function(func_name, node.args, interpreter)

    def visit_Identifier(self, interpreter, node: Identifier):
        val = interpreter.context.get(node.name)
        if val is not None:
            return val
        return node.name

    def visit_VariableDeref(self, interpreter, node: VariableDeref):
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

    def visit_PropertyAccess(self, interpreter, node: PropertyAccess):
        obj = interpreter.visit(node.target)
        prop = node.property_name.name

        if hasattr(obj, 'get'):
            return obj.get(prop)
        if hasattr(obj, prop):
            return getattr(obj, prop)
        if isinstance(obj, dict):
             return obj.get(prop)
        return None

    def interpolate_string(self, s):
        import re
        def replace(match):
            name = match.group(1)
            val = self.context.get(name)
            return str(val) if val is not None else match.group(0)
        return re.sub(r'\$([a-zA-Z_]\w*)', replace, s)

    def evaluate_args(self, args_nodes):
        return [self.visit(arg) for arg in args_nodes]

    # --- Core Functions ---

    def func_array(self, args, interpreter):
        # ARRAY(item1, item2, ...) -> Returns list
        return interpreter.evaluate_args(args)

    def func_import(self, args, interpreter):
        evaluated_args = interpreter.evaluate_args(args)
        # Assuming args[0] handles the import side-effect logic (like BUILTIN)
        pass

    def func_using(self, args, interpreter):
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

    def func_builtin(self, args, interpreter):
        evaluated_args = interpreter.evaluate_args(args)
        name = evaluated_args[0]
        if name == 'FILESTAT':
            from modules.filestat import get_module
            mod = get_module()
            interpreter.context.modules['FILESTAT'] = mod
            return mod
        elif name == 'BUILDCACHE':
            from modules.buildcache import get_module
            mod = get_module()
            interpreter.context.modules['BUILDCACHE'] = mod
            return mod
        return None

    def func_declare(self, args, interpreter):
        type_node = args[0]
        name_node = args[1]
        decl_type = interpreter.visit(type_node)

        if isinstance(name_node, Identifier):
            name = name_node.name
        else:
            name = str(interpreter.visit(name_node))

        vals = interpreter.evaluate_args(args[2:])

        if decl_type == 'VARIABLE':
            interpreter.context.set(name, vals[0])
        elif decl_type == 'FLAGS':
            interpreter.context.set(name, Flag(name, vals[0]))
        elif decl_type == 'EXECUTABLE':
            interpreter.context.set(name, Executable(name, vals[0], vals[1], vals[2]))

    def func_set(self, args, interpreter):
        name_node = args[0]
        if isinstance(name_node, Identifier):
            name = name_node.name
        else:
            name = str(interpreter.visit(name_node))
        val = interpreter.visit(args[1])
        interpreter.context.set(name, val)

    def func_execute(self, args, interpreter):
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
                    raise Exception(f"Not enough arguments for flag {arg.name} (arity {arity})")
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
            exe_name = exe.name

        flat_args = []
        for a in final_args:
             if isinstance(a, list):
                 flat_args.extend(map(str, a))
             else:
                 flat_args.append(str(a))

        command = [str(exe_name)] + flat_args
        print(f"EXECUTE: {' '.join(command)}")
        try:
            subprocess.run(command, check=True)
        except Exception as e:
            print(f"Execution failed: {e}")

    def func_if(self, args, interpreter):
        cond = interpreter.visit(args[0])
        if cond:
            interpreter.visit(args[1])
        elif len(args) > 2:
            interpreter.visit(args[2])

    def func_ifany(self, args, interpreter):
        triggered = False
        for arg in args:
            if isinstance(arg, FunctionCall):
                name = arg.name.name
                if name in ['NOT', 'EXISTS', 'NEQ', 'EQ', 'AND', 'OR', 'IS_PRIME']:
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

    def func_echo(self, args, interpreter):
        vals = interpreter.evaluate_args(args)
        print(" ".join(map(str, vals)))
        return True

    def func_not(self, args, interpreter):
        return not interpreter.visit(args[0])

    def func_neq(self, args, interpreter):
        vals = interpreter.evaluate_args(args)
        return vals[0] != vals[1]

    def func_exists(self, args, interpreter):
        path = interpreter.visit(args[0])
        return os.path.exists(str(path))
