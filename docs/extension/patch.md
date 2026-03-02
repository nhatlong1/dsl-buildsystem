# Patch Extension (Proposed)

> **Status**: Proposed. Not yet implemented. See `extensions/ext05.patchconstruct.ebnf.txt` for the grammar specification.

The patch extension would allow dynamic replacement of symbol values.

## Proposed Syntax

```ebnf
patch ::= "PATCH" "(" identifier "," identifier ")"
```

## Proposed Usage

```
PATCH(target_symbol, source_symbol)
```

`PATCH` would update `target_symbol` with the value of `source_symbol`.

### Example

A simple example would be simply:

```
DECLARE(VARIABLE, OLD, "v1")
DECLARE(VARIABLE, NEW, "v2")
PATCH(OLD, NEW)
/* OLD is now "v2" */
```

However it can also be done with `SET`.

The intended purpose for this function is to at runtime replaces an existing function with another one, and subsequent commands will run that function instead, without extensively modifying the existing code.