# Error Handling Extension (Proposed)

> **Status**: Proposed. Not yet implemented. See `extensions/ext04.errorhandling.ebnf.txt` for the grammar specification.

The error handling extension would provide a functional `TRY` construct.

## Proposed Syntax

```ebnf
try_catch ::= "TRY" "(" identifier "," statement "," statement ")"
```

## Proposed Usage

```
TRY(contextvar, operation, catch_block)
```

`TRY` would attempt to execute `operation`. If it completes successfully, its result is returned. If an exception occurs (e.g., command failure, missing file), `catch_block` is executed. The error message would be available via a `contextvar` context variable inside the catch block.

### Example

```
TRY(
    EXECUTE(optional_tool, "--check"),
    ECHO(last_error, @"Tool failed: $last_error")
)
```
