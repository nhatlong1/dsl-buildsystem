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
             # Evaluate arguments first?
             # Wait, args passed here are raw AST nodes (Expressions).
             # We must evaluate them to check if they are flags.

             # But if we evaluate `SDL3_INCLUDE`, it returns the Identifier name if not resolved?
             # No, visit(Identifier) tries to resolve it.

             eval_args = interpreter.evaluate_args(args)

             # Case: Variable(Flag) -> Flag(Variable)
             if len(eval_args) == 1 and isinstance(eval_args[0], Flag):
                 flag = eval_args[0]
                 # flag.apply expects list of values.
                 return flag.apply([val])

             # Case: Flag(Args...)
             if isinstance(val, Flag):
                 return val.apply(eval_args)

        raise Exception(f"Unknown function or callable: {name}")

class Interpreter:
    def __init__(self):
        self.context = Context()
        self.setup_core_functions()

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

        # Logical/Helper functions
        self.context.register_function('NOT', self.func_not)
        self.context.register_function('NEQ', self.func_neq)
        self.context.register_function('EXISTS', self.func_exists) # Often provided by FILESTAT, but core might need a fallback or it's imported

    def visit(self, node: ASTNode) -> Any:
        if isinstance(node, Program):
            return self.visit_Program(node)
        elif isinstance(node, FunctionCall):
            return self.visit_FunctionCall(node)
        elif isinstance(node, Literal):
            return node.value
        elif isinstance(node, Identifier):
            # Identifiers as atoms usually mean their string name unless they resolve to a symbol
            # But in `args`, `SDL3_INCLUDE` is passed as an identifier.
            # We should probably check if it resolves to a symbol in the context, if so return that value?
            # Or return the identifier name?
            # In `DECLARE(VARIABLE, NAME, ...)` NAME is an identifier.
            # In `SDL3_INCLUDE_PATH(SDL3_INCLUDE)`, SDL3_INCLUDE is an identifier that refers to a FLAG.
            # So we should try to resolve it.
            val = self.context.get(node.name)
            if val is not None:
                return val
            return node.name
        elif isinstance(node, VariableDeref):
            return self.visit_VariableDeref(node)
        elif isinstance(node, PropertyAccess):
            return self.visit_PropertyAccess(node)
        else:
            raise Exception(f"Unknown node type: {type(node)}")

    def visit_Program(self, node: Program):
        result = None
        for stmt in node.statements:
            result = self.visit(stmt)
        return result

    def visit_FunctionCall(self, node: FunctionCall):
        func_name = node.name.name
        # Evaluate arguments
        # Special case: Some functions might want raw AST (like IF/MACRO)?
        # IF(cond, then, else) -> we should evaluate cond. If true, eval then.
        # But `args` in FunctionCall are expressions.
        # If we evaluate all args eagerly, we break IF logic (both branches execute).
        # So `visit_FunctionCall` delegates to the function handler, passing raw nodes?
        # Or we use a lambda/lazy evaluation?

        # Standard approach: Pass raw nodes to handler, let handler evaluate.
        # But `args` in `FunctionCall` are `Expression` nodes.

        # Let's change `call_function` signature to take `args` (AST nodes) and `interpreter`.
        # The handler is responsible for visiting args.

        return self.context.call_function(func_name, node.args, self)

    def evaluate_args(self, args_nodes):
        return [self.visit(arg) for arg in args_nodes]

    # --- Core Functions ---

    def func_import(self, args, interpreter):
        # IMPORT(Module)
        evaluated_args = interpreter.evaluate_args(args)
        module = evaluated_args[0]
        # logic to add module to context?
        # sample: IMPORT(BUILTIN(FILESTAT))
        # BUILTIN returns a module object.
        # So we just ignore? Or store it?
        pass

    def func_using(self, args, interpreter):
        # USING(Module, *)
        # In sample: USING(FILESTAT, *)

        # args[0] might be an Identifier node. We need to resolve it.
        # visit() on Identifier returns the value from context if it exists, or the name string.
        # If BUILTIN(FILESTAT) was called inside IMPORT, what happened?
        # func_builtin returns the module dict.
        # func_import takes that dict. But what does it do with it?

        # Re-check func_import. It does pass.
        # So IMPORT(BUILTIN(...)) evaluates BUILTIN, gets a dict. IMPORT ignores it.
        # So the module is NOT in context under 'FILESTAT'.
        # But `USING(FILESTAT, *)` implies `FILESTAT` refers to something.

        # If BUILTIN assigns to context modules, then we are good?
        # My func_builtin impl: interpreter.context.modules['FILESTAT'] = mod
        # So `interpreter.context.modules` has it.
        # But `USING` first argument evaluation:
        # If args[0] is Identifier(FILESTAT), visit(Identifier) checks context.symbols.
        # It's not in symbols, it's in modules.
        # So visit returns "FILESTAT" (string).

        evaluated_args = interpreter.evaluate_args(args)
        module_or_name = evaluated_args[0]

        module = module_or_name
        if isinstance(module, str):
            module = interpreter.context.modules.get(module)

        if isinstance(module, dict):
            # Copy all module exports to context
            for key, val in module.items():
                interpreter.context.register_function(key, val) # Register as function/callable
                # Also set as symbol if needed?
                # The modules return lambdas (args, interp).
                # These are functions.
        else:
             print(f"Warning: Module {module_or_name} not found or invalid.")

    def func_builtin(self, args, interpreter):
        # BUILTIN(NAME)
        # Returns a module dictionary/object
        evaluated_args = interpreter.evaluate_args(args)
        name = evaluated_args[0]

        # Load builtin module
        # For now, hardcode or dynamic load
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
        # DECLARE(Type, Name, ...)
        # We need the name as a string, so we shouldn't evaluate the identifier deeply if it's the name being declared.
        # args[1] is the identifier for the name.

        type_node = args[0] # EXECUTABLE, FLAGS, VARIABLE
        name_node = args[1]

        decl_type = interpreter.visit(type_node)

        # Special handling: name_node might be Identifier. visit() might resolve it if it exists.
        # We want the name string.
        if isinstance(name_node, Identifier):
            name = name_node.name
        else:
            name = str(interpreter.visit(name_node))

        vals = interpreter.evaluate_args(args[2:])

        if decl_type == 'VARIABLE':
            # DECLARE(VARIABLE, Name, Value)
            interpreter.context.set(name, vals[0])
        elif decl_type == 'FLAGS':
            # DECLARE(FLAGS, Name, Template)
            interpreter.context.set(name, Flag(name, vals[0]))
        elif decl_type == 'EXECUTABLE':
            # DECLARE(EXECUTABLE, Name, Desc, Source, Path)
            interpreter.context.set(name, Executable(name, vals[0], vals[1], vals[2]))

    def func_set(self, args, interpreter):
        # SET(Name, Value)
        name_node = args[0]
        if isinstance(name_node, Identifier):
            name = name_node.name
        else:
            name = str(interpreter.visit(name_node))

        val = interpreter.visit(args[1])
        interpreter.context.set(name, val)

    def func_execute(self, args, interpreter):
        # EXECUTE(ExeName, Args...)
        # Handle @Flag mechanism here.

        evaluated_args = []
        for arg in args:
            evaluated_args.append(interpreter.visit(arg))

        exe = evaluated_args[0]
        cmd_args = evaluated_args[1:]

        # Process Flag popping
        final_args = []
        i = 0
        while i < len(cmd_args):
            arg = cmd_args[i]
            if isinstance(arg, Flag):
                # Pop previous args
                arity = arg.arity
                if len(final_args) < arity:
                    raise Exception(f"Not enough arguments for flag {arg.name} (arity {arity})")

                flag_inputs = []
                for _ in range(arity):
                    flag_inputs.insert(0, final_args.pop())

                res = arg.apply(flag_inputs)
                # res is string like "-c file.c". Need to split?
                # Sample: "-Wall ...".
                # Shell execute usually expects list of args.
                # If res is a string with spaces, we might need to split it unless it's a single argument.
                # But "-c file.c" are multiple arguments to gcc.
                # So we split by space?
                # What if quoted?
                # "libs/sdl3-vendor/include" might have spaces?
                # Simple split might be dangerous.
                # But let's assume standard space separation for flags.
                final_args.extend(res.split())
            else:
                final_args.append(arg)
            i += 1

        # Execute
        # exe might be Executable object or string
        exe_name = exe
        if isinstance(exe, Executable):
            exe_name = exe.name # Or path? sample says 'gcc', 'mkdir'

        # Flatten final_args (some might be strings, some lists?)
        flat_args = []
        for a in final_args:
             if isinstance(a, list):
                 flat_args.extend(map(str, a))
             else:
                 flat_args.append(str(a))

        command = [str(exe_name)] + flat_args
        print(f"EXECUTE: {' '.join(command)}")
        # Real execution:
        # subprocess.run(command, check=True)
        # For now, just print or maybe run real commands if simple?
        # User said: "Should the system actually execute shell commands... Yes"
        # I'll try to run them.
        try:
            subprocess.run(command, check=True)
        except Exception as e:
            print(f"Execution failed: {e}")

    def func_if(self, args, interpreter):
        # IF(Cond, Then, [Else])
        cond = interpreter.visit(args[0])
        if cond:
            interpreter.visit(args[1])
        elif len(args) > 2:
            interpreter.visit(args[2])

    def func_ifany(self, args, interpreter):
        # IFANY(Cond1, Cond2, ..., ThenBody)
        # Wait, sample:
        # IFANY(
        #    NOT(EXISTS(MAIN_OBJ)),
        #    NEQ(...),
        #    ...
        #    /* Rebuild main.o */ (Comment)
        #    ECHO(...),
        #    EXECUTE(...)
        # )
        # It seems IFANY takes N conditions. If ANY is true, it executes the REST of the arguments?
        # Or where is the split between conditions and body?
        # "Rebuild main.o" comments are interleaved.
        # But the parser sees a list of expressions.
        # `ECHO` is an expression (FunctionCall).
        # `EXECUTE` is an expression.
        # `NOT(EXISTS)` is an expression (returns boolean).

        # How do we distinguish condition from action?
        # Maybe conditions return booleans, and actions return None/True?
        # Or maybe IFANY assumes everything that returns boolean is a condition, and once we hit something that executes/returns void/string, that's the body?
        # Or maybe it evaluates ALL arguments. If ANY of them (presumably the checks) are true...
        # But `EXECUTE` should only run if the check is true.
        # So it can't evaluate all eagerly.

        # Logic: Iterate args. Evaluate. If result is Boolean, treat as condition.
        # If any condition is True, then we are in "Triggered" mode.
        # But wait, if we evaluate `EXECUTE(...)`, it executes!
        # So we cannot evaluate potential actions unless we know we are triggered.

        # But we don't know which args are conditions and which are actions just by looking at AST (they are all FunctionCalls).
        # `NOT` returns bool. `EXECUTE` returns None?

        # Heuristic:
        # Evaluate args one by one.
        # If it's a condition (returns bool):
        #    If True, mark "Triggered".
        #    If False, continue.
        # If it's an action (and we are Triggered):
        #    Execute it.
        # If it's an action (and NOT Triggered):
        #    Skip it?

        # Problem: How do we know `NOT(...)` is a condition without evaluating it? We have to evaluate it.
        # So we evaluate. If it returns True, we flag `triggered = True`.
        # Then we continue to next arg.
        # If next arg is `NEQ(...)`, we evaluate it. It returns Bool.
        # If `triggered` is already True, does `NEQ` matter? Maybe not.
        # But if `triggered` is False, we check `NEQ`.
        # When do we stop treating things as conditions?
        # When we encounter an action like `ECHO` or `EXECUTE`.
        # But `ECHO` is called. We can't prevent it from running if we call `visit`.

        # Unless... `ECHO` and `EXECUTE` are wrapped or we check the function name?
        # Checking function name is fragile but effective for this DSL.
        # "Conditions" are likely: NOT, EXISTS, NEQ, OR, AND, EQ.
        # "Actions" are: EXECUTE, ECHO, SET, ...

        # Let's try to peek at the function name of the call.

        triggered = False

        for arg in args:
            if isinstance(arg, FunctionCall):
                name = arg.name.name
                if name in ['NOT', 'EXISTS', 'NEQ', 'EQ', 'AND', 'OR', 'IS_PRIME']: # Condition-like
                    if not triggered:
                        res = interpreter.visit(arg)
                        if res is True:
                            triggered = True
                else:
                    # Action-like
                    if triggered:
                        interpreter.visit(arg)
            else:
                # Literal or Identifier?
                # Probably ignore or evaluate if triggered?
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
        # Check if file exists.
        # Maybe check if `FILESTAT` module provides it, or impl here.
        # Sample uses `EXISTS(@BUILD_DIR)`.
        path = interpreter.visit(args[0])
        return os.path.exists(str(path))

    def visit_VariableDeref(self, node: VariableDeref):
        # Target can be Identifier, FunctionCall (returning string name?), or Literal (string template).
        # Sample: `@BUILD_DIR` (ID), `@STAT(...)` (Call), `@"String"` (Literal)

        target = node.target

        if isinstance(target, Identifier):
             # @VAR -> Get value of VAR
             return self.context.get(target.name)
        elif isinstance(target, FunctionCall):
             # @STAT(...) -> Evaluate call, then what?
             # Sample: `@STAT(MAIN_SRC).LASTMODIFIEDDATE`
             # So `@` might just mean "Evaluate this and return the object so we can access properties"?
             # If `STAT` returns an object, we don't need `@` if `visit_FunctionCall` returns the object.
             # But the sample implies `@` is needed.
             # Maybe `STAT` returns a handle/struct, and without `@` it does something else?
             # Or maybe `@` is just sugar and `STAT` returns the object anyway.
             # I'll just evaluate the target.
             return self.visit(target)
        elif isinstance(target, Literal):
             # @"String with $VAR" -> Interpolate
             if isinstance(target.value, str):
                 return self.interpolate_string(target.value)
             return target.value

        return self.visit(target)

    def interpolate_string(self, s):
        # Replace $VAR with value
        # This is simple regex replacement looking up in context.
        import re
        def replace(match):
            name = match.group(1)
            val = self.context.get(name)
            return str(val) if val is not None else match.group(0)

        return re.sub(r'\$([a-zA-Z_]\w*)', replace, s)

    def visit_PropertyAccess(self, node: PropertyAccess):
        obj = self.visit(node.target)
        prop = node.property_name.name

        # If obj is a dict (Module or Stat object)
        if hasattr(obj, 'get'):
            return obj.get(prop)
        if hasattr(obj, prop):
            return getattr(obj, prop)
        if isinstance(obj, dict):
             return obj.get(prop)

        # Hack for STAT object if it's a named tuple or custom class
        return None
