# Syntax Documentation

## Core Concepts

The build system language is based on **Function Calls**. Most statements are function calls.

```ebnf
program ::= { statement }
statement ::= function_call
function_call ::= identifier "(" [ arg_list ] ")"
```

### Expressions and Types

Arguments to functions can be:
- **Literals**: Strings (`"text"`), Numbers (`123`), Booleans (`TRUE`/`FALSE`), `NULL`.
- **Identifiers**: References to variables or symbols.
- **Function Calls**: Nested calls.
- **Variable Dereference (`@`)**: Accessing the value of a variable or macro.
- **Property Access (`.`)**: Accessing properties of an object (e.g., file stats).

### Variable Dereference (`@`)
The `@` symbol is used to explicitly dereference a variable or invoke a macro/variable in an expression context where it might otherwise be treated as a literal identifier.

Example:
```
ECHO(@"Current dir: $BUILD_DIR")  // String interpolation
EXISTS(@BUILD_DIR)                // Access variable value
```

### Property Access (`.`)
Use `.` to access properties of objects returned by functions (like `STAT` or `CACHE`).

Example:
```
STAT(MAIN_SRC).LASTMODIFIEDDATE
```

## Core Functions

### `IMPORT(Module)`
Imports a module.
```
IMPORT(BUILTIN(FILESTAT))
```

### `USING(Module, Pattern)`
Brings module symbols into the current scope.
```
USING(FILESTAT, *)
```

### `DECLARE(Type, Name, ...)`
Declares a new symbol.
Types:
- `VARIABLE`: Simple value storage.
- `FLAGS`: Template strings for compiler flags.
- `EXECUTABLE`: External command definition.

### `SET(Name, Value)`
Updates a variable's value.

### `EXECUTE(Executable, Args...)`
Runs an external command.
Supports flag substitution. If an argument is a `FLAGS` object, it pops preceding arguments to fill its template.

### `IF(Condition, Then, [Else])`
Conditional execution.

### `IFANY(Cond1, Cond2, ..., Action1, Action2...)`
Executes actions if *any* of the conditions are true.
(Note: Heuristic-based separation of conditions and actions).

### `ECHO(Args...)`
Prints to stdout.

### `ARRAY(Item...)`
Creates an array (list) of items.
```
DECLARE(VARIABLE, MY_LIST, ARRAY(1, 2, 3))
```

### Logical Functions
- `NOT(Cond)`: Returns logical negation.
- `NEQ(A, B)`: Returns true if A is not equal to B.
- `EXISTS(Path)`: Returns true if the path exists.

## Builtin Modules

### FILESTAT
Provides file status information.
- `STAT(Path)`: Returns a `FileStat` object.
    - `.LASTMODIFIEDDATE`: The last modification timestamp.
- `EXISTS(Path)`: Checks existence (alias to core `EXISTS`).

### BUILDCACHE
Provides a simple caching mechanism for build artifacts.
- `CACHE(Path)`: Returns a `CacheEntry` object from the cache.
    - `.LASTMODIFIEDDATE`: The recorded timestamp in the cache.
- `WRITEBUILDCACHE()`: Saves the current cache state to disk (`.buildcache`).
