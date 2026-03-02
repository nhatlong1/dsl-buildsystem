# Error Handling Extension (Proposed)

> **Status**: Proposed. Not yet implemented. See `extensions/ext04.errorhandling.ebnf.txt` for the grammar specification.

The error handling extension would provide a functional `TRY` construct.

## Proposed Syntax

```ebnf
try_catch ::= "TRY" "(" expression "," expression ")"
```

## Proposed Usage

```
TRY(operation, catch_block)
```

`TRY` would attempt to execute `operation`. If it completes successfully, its result is returned. If an exception occurs (e.g., command failure, missing file), `catch_block` is executed. The error message would be available via a `LAST_ERROR` context variable inside the catch block.

### Example

```
TRY(
    EXECUTE(optional_tool, "--check"),
    ECHO(@"Tool failed: $LAST_ERROR")
)
```
