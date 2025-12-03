# Patch Extension

The `patch` plugin allows dynamic replacement of symbol values.

## Syntax

```ebnf
patch ::= "PATCH" "(" identifier "," identifier ")"
```

## Usage

```
PATCH(target_symbol, source_symbol)
```

The `PATCH` command updates `target_symbol` with the value of `source_symbol`.

### Example

```
DECLARE(VARIABLE, OLD, "v1")
DECLARE(VARIABLE, NEW, "v2")
PATCH(OLD, NEW)
/* OLD is now "v2" */
```
