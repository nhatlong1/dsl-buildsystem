# Loop Extension (`FOR`)

**Plugin**: `plugins/loop.cpp` (compiled to `loop.dll` / `loop.so`)

Adds a `FOR` loop construct for iterating over lists.

## Syntax

```ebnf
for_loop ::= "FOR" "(" identifier "," expression "," expression ")"
```

## Usage

```
FOR(variable, list_expression, body)
```

- `variable` — Loop variable name (bound on each iteration).
- `list_expression` — An expression that evaluates to a list.
- `body` — Expression executed on each iteration.

The loop evaluates `list_expression` once, then iterates. On each iteration, the current element is assigned to `variable` in the context, and `body` is executed.

## Examples

Iterate over an inline array (requires the arrays plugin):

```
FOR(file, ["a.cpp", "b.cpp", "c.cpp"],
    EXECUTE(@gpp, @file, @output_flag(@file))
)
```

Iterate over a variable holding a list:

```
DECLARE(VARIABLE, sources, ARRAY("main.cpp", "util.cpp"))

FOR(src, @sources,
    ECHO(@"Compiling $src")
)
```

Nested arrays for batch plugin builds:

```
DECLARE(VARIABLE, plugins,
    [
        ["plugins/loop.cpp", "bin/plugins/loop.dll"],
        ["plugins/arrays.cpp", "bin/plugins/arrays.dll"]
    ]
)

FOR(item, @plugins,
    EXECUTE(@gpp, @cxx_flags, @shared_flag(@item[1]), @item[0])
)
```

## Loading

The loop plugin must be compiled and placed in `bin/plugins/`. It is loaded automatically at startup, or can be loaded at runtime:

```
LOAD_PLUGIN("bin/plugins/loop.dll")
```
