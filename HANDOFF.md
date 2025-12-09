# Handoff Document

## Status Summary
The codebase has undergone a significant refactoring to align with Google C++ Style Guide naming conventions and to implement a proper build caching mechanism.

### Completed Work
1.  **Interface Renaming:**
    - `include/protocols.hpp` was renamed to `include/interfaces.hpp`.
    - Interfaces have been renamed to remove the `I` prefix: `Lexer`, `Parser`, `Interpreter`, `Context`, `Object`.

2.  **Concrete Class Renaming:**
    - Default implementations in `src/` have been renamed to include `Default` prefix: `DefaultLexer`, `DefaultParser`, `DefaultInterpreter`, `DefaultContext`.
    - `src/main.cpp` and `src/interpreter.cpp` were updated to instantiate these new classes.

3.  **BuildCache Implementation:**
    - `modules/buildcache.cpp` now uses `nlohmann/json` (expected in `vendor/json.hpp`) to load and save cache data in `.buildcache`.
    - `CACHE`, `UPDATE`, and `WRITEBUILDCACHE` functions are implemented.

4.  **Interpreter Enhancements:**
    - Added `LT` (Less Than) for integer comparison.
    - Added `NATIVEPATH` for OS-specific path separators.
    - Added `SELECT` for canonical property access.
    - `property.access` syntax is now syntactic sugar for `SELECT`.

5.  **Build Script Update:**
    - `build.mybuild` has been updated to use the new caching logic (`IF(LT(CACHE(...), STAT(...)))`).
    - Uses `NATIVEPATH` for directory creation.

### Current Issues
The project compiles successfully using `./bootstrap.sh`. However, running the self-hosted build script `bin/builder build.mybuild` fails with runtime errors:

1.  **Parser Errors:** "Expected token type 5 but got 0" around the `FOR` loop in `build.mybuild`. This suggests an issue with how the `FOR` plugin is parsing arguments or interaction with the main parser.
2.  **Segmentation Fault / Linker Errors:** There are observed segfaults and "cannot open output file" errors when the builder tries to compile or load plugins during the script execution. This might be related to:
    - ABI mismatches between the host `bin/builder` and the dynamically loaded plugins, especially since the base classes (`ASTNode`, `Interpreter`) have changed names/vtables.
    - The `extern "C"` interface in plugins uses `dsl::Parser&` and `dsl::Context&`. Ensure the shared objects are linking against the same definitions.

## Next Steps
1.  **Debug Plugin Loading:** Verify that plugins compiled with the new headers are binary-compatible with the host executable.
2.  **Fix `FOR` Loop Parsing:** Investigate `plugins/loop.cpp`. The `parse_for_loop` function might be mishandling the token stream, causing the "Expected token" error.
3.  **Resolve Segfaults:** Run `bin/builder build.mybuild` under `gdb` (if available) to pinpoint the crash. It is likely inside `ASTNode::execute` when crossing the plugin boundary.
4.  **Vendor JSON:** Ensure `vendor/json.hpp` is properly managed or documented as a dependency.

## Files Changed
- `include/interfaces.hpp` (was `protocols.hpp`)
- `include/types.hpp`, `include/value.hpp`, `include/lexer.hpp`, `include/parser.hpp`, `include/interpreter.hpp`
- `src/*.cpp`
- `plugins/*.cpp`
- `modules/*.cpp`
- `build.mybuild`
- `bootstrap.sh`
