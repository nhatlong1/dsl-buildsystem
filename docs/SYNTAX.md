# Syntax Documentation

## Overview

The build system language is **expression-based** and **function-call-driven**. A program is a sequence of top-level expressions, most of which are function calls. The language is extensible through dynamically loaded plugins that introduce new syntax forms (e.g., `FOR` loops, `REPEAT`, array literals).

## Grammar (Core)

```ebnf
program       ::= { expression }
expression    ::= prefix { infix }
prefix        ::= identifier
                 | literal
                 | "@" expression          (* variable dereference *)
                 | "(" expression ")"      (* grouped expression *)
                 | "*"                     (* wildcard identifier *)
infix         ::= "(" [ arg_list ] ")"    (* function call *)
                 | "." identifier          (* property access *)
                 | "+" expression          (* string concatenation *)
arg_list      ::= expression { "," expression }
```

### Precedence (lowest to highest)

| Level | Operator | Description           |
| ----- | -------- | --------------------- |
| 0     | (lowest) | Top-level expressions |
| 20    | `+`      | String concatenation  |
| 30    | `.`      | Property access       |
| 40    | `@`      | Dereference (prefix)  |
| 50    | `()`     | Function call         |

## Types

| Type       | Syntax        | Examples                    |
| ---------- | ------------- | --------------------------- |
| String     | `"text"`      | `"hello"`, `"src/main.cpp"` |
| Number     | digits        | `0`, `42`, `100`            |
| Boolean    | keyword       | `TRUE`, `FALSE`             |
| Null       | keyword       | `NULL`                      |
| Identifier | unquoted name | `gpp`, `VARIABLE`, `my_var` |

## Variable Dereference (`@`)

The `@` operator dereferences a variable, retrieving its runtime value. Without `@`, an identifier is treated as a literal name.

```
DECLARE(VARIABLE, name, "world")
ECHO(name)               /* prints: name */
ECHO(@name)              /* prints: world */
```

When applied to a string literal, `@` triggers **string interpolation** using `$variable` syntax:

```
DECLARE(VARIABLE, dir, "build")
ECHO(@"output is $dir")  /* prints: output is build */
```

## Property Access (`.`)

Access properties of objects returned by module functions.

```
STAT("main.cpp").LASTMODIFIEDDATE
```

## String Concatenation (`+`)

The `+` operator concatenates two values as strings.

```
ECHO("hello" + " " + "world")  /* prints: hello world */
```

## Comments

Block comments use `/* ... */`. Comments may not be nested.

```
/* This is a comment */
```

---

## Core Functions

### Declaration & Assignment

#### `DECLARE(Type, Name, ...)`

Declares a named symbol.

| Type         | Description                            | Extra Arguments           |
| ------------ | -------------------------------------- | ------------------------- |
| `VARIABLE`   | Simple value                           | Initial value             |
| `FLAGS`      | Template string with `$N` placeholders | Template string           |
| `EXECUTABLE` | External command                       | Description, Source, Path |

```
DECLARE(VARIABLE, src, "main.cpp")
DECLARE(FLAGS, cxx_flags, "-std=c++17 -Wall")
DECLARE(FLAGS, output_flag, "-o $1")
DECLARE(EXECUTABLE, gpp, "GNU C++ Compiler", "System", "g++")
```

**FLAGS templates**: Use `$1`, `$2`, etc. as placeholders. When a `FLAGS` value appears as an argument, it can be called with arguments to fill the template:

```
DECLARE(FLAGS, output_flag, "-o $1")
EXECUTE(@gpp, "main.cpp", @output_flag("main"))
/* Produces: g++ main.cpp -o main */
```

#### `SET(Name, Value)`

Updates an existing variable's value.

```
SET(src, "other.cpp")
```

### Execution

#### `EXECUTE(Executable, Args...)`

Runs an external command. Supports automatic flag template substitution.

```
EXECUTE(@gpp, @cxx_flags, "main.cpp", @output_flag("main"))
```

When a `FLAGS` argument is encountered during evaluation, it consumes preceding arguments to fill its `$N` placeholders. List arguments are automatically flattened.

### Control Flow

#### `IF(Condition, Then [, Else])`

Conditional execution. Evaluates `Condition`; if truthy, executes `Then`, otherwise executes `Else` (if provided).

```
IF(EXISTS("main.cpp"),
    ECHO("Found"),
    ECHO("Not found")
)
```

### Output

#### `ECHO(Args...)`

Prints arguments to stdout, space-separated, followed by a newline.

```
ECHO("Building", @target)
```

### Collections

#### `ARRAY(Item...)`

Creates a list from its arguments.

```
DECLARE(VARIABLE, files, ARRAY("a.cpp", "b.cpp"))
```

### Logical & Comparison Functions

| Function       | Description                                         |
| -------------- | --------------------------------------------------- |
| `EQ(A, B)`     | Returns `TRUE` if A equals B (same type and value)  |
| `NEQ(A, B)`    | Returns `TRUE` if A does not equal B                |
| `NOT(Cond)`    | Logical negation                                    |
| `EXISTS(Path)` | Returns `TRUE` if the file/directory exists on disk |

### Platform Detection

#### `PLATFORM([Property])`

Compile-time constant function. Returns platform information baked in when the builder binary is compiled. Called with no arguments, it returns the OS name.

| Property       | Returns                                       |
| -------------- | --------------------------------------------- |
| *(none)*       | `"windows"` \| `"linux"` \| `"macos"`         |
| `"os"`         | Same as above                                 |
| `"arch"`       | `"x86_64"` \| `"x86"` \| `"arm64"` \| `"arm"` |
| `"shared_ext"` | `"dll"` \| `"so"` \| `"dylib"`                |
| `"exe_ext"`    | `".exe"` \| `""`                              |
| `"is_windows"` | `TRUE` \| `FALSE`                             |
| `"is_linux"`   | `TRUE` \| `FALSE`                             |
| `"is_macos"`   | `TRUE` \| `FALSE`                             |

```
DECLARE(VARIABLE, ext, PLATFORM("shared_ext"))

IF(PLATFORM("is_windows"),
    SET(link_flags, "")
)
```

`PLATFORM()` is a function call, not a magic variable. When you see `()`, you know it's a query.

### Module Management

#### `IMPORT(Module)`

Imports a built-in module.

```
IMPORT(BUILTIN(FILESTAT))
```

#### `USING(Module, Pattern)`

Brings module symbols into the current scope.

```
USING(FILESTAT, *)
```

#### `LOAD_PLUGIN(Path)`

Dynamically loads a compiled plugin (`.dll` or `.so`) at runtime. This enables the build script to compile and then immediately load its own plugins.

```
LOAD_PLUGIN(@"bin/plugins/loop.dll")
```

---

## CLI Options

```
builder [options] <file.mybuild>
```

| Option         | Description                                   |
| -------------- | --------------------------------------------- |
| `--dry-run`    | Print execution commands without running them |
| `--parse-only` | Parse input, print the AST tree, and exit     |
| `--help`       | Show help message                             |
