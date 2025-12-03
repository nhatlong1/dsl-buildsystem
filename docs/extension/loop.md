# Loop Extension

The `loop` plugin adds a `FOR` loop construct to the language.

## Syntax

```ebnf
loop ::= "FOR" "(" identifier "," arg_list "," statement ")"
```

## Usage

```
FOR(variable, item1, item2, ..., statement)
```

The loop iterates over the provided items. For each item, it assigns the value to `variable` and executes `statement`.

### Example

```
FOR(i, "a.c", "b.c",
    ECHO(@"Compiling $i")
)
```
