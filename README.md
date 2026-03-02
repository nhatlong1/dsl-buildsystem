# dsl-buildsystem

A domain-specific language for describing build processes. The builder compiles C++ projects using a declarative, function-call-driven script syntax — and is capable of building itself.

## Quick Start

### Prerequisites

- **g++** with C++17 support
- **Linux**: `libdl` (usually pre-installed)
- **Windows**: MinGW-w64 or similar g++ distribution

### Bootstrap

The builder must first be compiled from source using the bootstrap script:

**Linux / macOS / MSYS2:**
```bash
./bootstrap.sh
```

**Windows (manual):**
```
g++ -std=c++17 -Iinclude src/lexer.cpp src/parser.cpp src/interpreter.cpp src/plugin_loader.cpp src/main.cpp -o bin/builder.exe
g++ -std=c++17 -Iinclude -shared plugins/loop.cpp -o bin/plugins/loop.dll
g++ -std=c++17 -Iinclude -shared plugins/arrays.cpp -o bin/plugins/arrays.dll
g++ -std=c++17 -Iinclude -shared plugins/repeat.cpp -o bin/plugins/repeat.dll
g++ -std=c++17 -Iinclude -shared modules/filestat.cpp -o bin/modules/filestat.dll
g++ -std=c++17 -Iinclude -shared modules/buildcache.cpp -o bin/modules/buildcache.dll
```

This produces `bin/builder` (or `bin/builder.exe`), which can then run `.mybuild` scripts.

### Usage

```
bin/builder [options] <script.mybuild>
```

| Option         | Description                                    |
| -------------- | ---------------------------------------------- |
| `--dry-run`    | Print commands without executing them          |
| `--parse-only` | Parse the script, print the AST tree, and exit |
| `--help`       | Show help                                      |

### Example

```
bin/builder build.mybuild
```

## Language Overview

The language is expression-based. Nearly everything is a function call. There are no statements, blocks, or semicolons — just expressions separated by whitespace.

```
/* Declare a compiler */
DECLARE(EXECUTABLE, gpp, "GNU C++ Compiler", "System", "g++")
DECLARE(FLAGS, cxx_flags, "-std=c++17 -Wall")
DECLARE(FLAGS, output_flag, "-o $1")

/* Detect platform at compile time */
DECLARE(VARIABLE, ext, PLATFORM("shared_ext"))

/* Conditional based on platform */
IF(PLATFORM("is_windows"),
    ECHO("Building on Windows")
)

/* Build */
EXECUTE(@gpp, @cxx_flags, "main.cpp", @output_flag("main"))
```

### Key Concepts

**Function calls** are the primary construct. `DECLARE`, `EXECUTE`, `IF`, `ECHO`, `SET` are all built-in functions.

**`@` dereferences** variables. Without `@`, identifiers are literal names. `@"string"` triggers string interpolation with `$var` syntax.

**`PLATFORM()`** is a compile-time constant function that queries the host platform. No magic variables — you see `()`, you know it's a query.

**Plugins** extend the parser at runtime. The `FOR` loop, `REPEAT`, and array `[...]` syntax are all plugins compiled as shared libraries and loaded dynamically.

**Self-hosting**: The builder can compile itself. `build.mybuild` describes the full build process including compiling plugins, loading them at runtime, and using them within the same script.

## Architecture

```
script.mybuild
     |
     v
  [Lexer]  -->  Token stream
     |
     v
  [Parser]  -->  AST (Abstract Syntax Tree)
     |
     v
  [Interpreter]  -->  Execution
     |
     +-- Built-in functions (DECLARE, EXECUTE, IF, ...)
     +-- Loaded modules (FILESTAT, BUILDCACHE)
     +-- Loaded plugins (FOR, REPEAT, arrays)
```

### Source Layout

```
src/
    main.cpp              Entry point, CLI handling
    lexer.cpp             Tokenizer
    parser.cpp            Pratt parser, AST printer
    interpreter.cpp       Tree-walking interpreter, built-in functions
    plugin_loader.cpp     Dynamic library loading (dlopen/LoadLibrary)

include/
    types.hpp             Token types, AST node definitions
    value.hpp             Runtime value type (variant-based)
    interfaces.hpp        Abstract interfaces (Lexer, Parser, Interpreter, Context)
    lexer.hpp             DefaultLexer
    parser.hpp            DefaultParser
    interpreter.hpp       DefaultInterpreter, DefaultContext
    plugin.hpp            Plugin API header

plugins/                  Parser extensions (compiled to .dll/.so)
    loop.cpp              FOR(var, list, body)
    arrays.cpp            [...] literals and target[index] access
    repeat.cpp            REPEAT(n, body)

modules/                  Runtime modules (compiled to .dll/.so)
    filestat.cpp          STAT(), EXISTS()
    buildcache.cpp        CACHE(), WRITEBUILDCACHE()

vendor/
    json.hpp              nlohmann/json (used by buildcache)
```

### Parser Design

The parser uses a **Pratt parser** (top-down operator precedence) architecture. Parsing functions are registered in two maps:

- **Prefix** — handles tokens at the start of an expression (identifiers, literals, `@`, `(`, `*`)
- **Infix** — handles tokens following a left-hand expression (`(` for calls, `.` for property access, `+` for concatenation)

Plugins extend the parser by registering **token handlers** keyed on identifier values. When the parser encounters an identifier like `FOR`, it delegates to the plugin's handler, which consumes tokens and returns a custom AST node.

### Plugin System

Plugins are shared libraries exporting a C function:

```cpp
extern "C" void register_plugin(dsl::Parser& parser, dsl::Context& context);
```

This function is called at load time and can:
- Register new prefix/infix parse functions
- Register new token handlers (keyword-triggered syntax)
- Register new runtime functions in the context

Plugins are loaded from `bin/plugins/` and `bin/modules/` at startup. Additional plugins can be loaded at runtime via `LOAD_PLUGIN()`.

## Documentation

| Document                                                               | Description                        |
| ---------------------------------------------------------------------- | ---------------------------------- |
| [docs/SYNTAX.md](docs/SYNTAX.md)                                       | Complete language syntax reference |
| [docs/extension/loop.md](docs/extension/loop.md)                       | FOR loop plugin                    |
| [docs/extension/arrays.md](docs/extension/arrays.md)                   | Array literals and indexing        |
| [docs/extension/repeat.md](docs/extension/repeat.md)                   | REPEAT plugin                      |
| [docs/extension/error_handling.md](docs/extension/error_handling.md)   | Error handling (proposed)          |
| [docs/extension/patch.md](docs/extension/patch.md)                     | Patch construct (proposed)         |
| [docs/extension/pipeline.md](docs/extension/pipeline.md)               | Pipeline operator (disabled)       |
| [docs/module/builtin/filestat.md](docs/module/builtin/filestat.md)     | File status module                 |
| [docs/module/builtin/buildcache.md](docs/module/builtin/buildcache.md) | Build cache module                 |

## Self-Hosting

The file `build.mybuild` is the self-hosting build script. It uses the builder to:

1. Compile the builder core from C++ sources
2. Compile the loop plugin, load it at runtime
3. Compile the arrays plugin, load it at runtime
4. Use `FOR` loops and `[...]` arrays (now available) to batch-compile remaining plugins
5. Detect the platform via `PLATFORM("shared_ext")` to produce correct `.dll`/`.so` files

This means the only external dependency is a C++17 compiler. Once bootstrapped, the builder maintains itself.

## AST Visualization

Use `--parse-only` to inspect the parse tree:

```
> bin/builder --parse-only mini_sample.mybuild

Program
|____ FunctionCall
|     |____ Identifier(IMPORT)
|     |____ FunctionCall
|           |____ Identifier(BUILTIN)
|           |____ Identifier(FILESTAT)
|____ FunctionCall
|     |____ Identifier(DECLARE)
|     |____ Identifier(EXECUTABLE)
|     |____ Identifier(gpp)
|     |____ Literal("GNU C++ Compiler")
|     |____ Literal("winlibs.com")
|     |____ Literal(null)
|____ FunctionCall
      |____ Identifier(IF)
      |____ FunctionCall
      |     |____ Identifier(NEQ)
      |     |____ ...
      |____ FunctionCall
      |     |____ Identifier(EXECUTE)
      |     |____ ...
      |____ FunctionCall
            |____ Identifier(ECHO)
            |____ Literal("main.cpp up to date")
```

## License

See repository for license information.
