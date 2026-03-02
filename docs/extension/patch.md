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

```
DECLARE(VARIABLE, OLD, "v1")
DECLARE(VARIABLE, NEW, "v2")
PATCH(OLD, NEW)
/* OLD is now "v2" */
```
