# Error Handling Extension

The `error` plugin provides functional error handling via `TRY`.

## Syntax

```ebnf
try_catch ::= "TRY" "(" expression "," expression ")"
```

## Usage

```
TRY(operation, catch_block)
```

The `TRY` function attempts to execute `operation`. If it completes successfully, its result is returned. If an exception occurs during execution (e.g., system error, missing file, script error), `catch_block` is executed.

The error message is available in the `LAST_ERROR` context variable within the catch block.

### Example

```
TRY(
    EXECUTE(optional_tool),
    ECHO(@"Tool failed: $LAST_ERROR")
)
```
