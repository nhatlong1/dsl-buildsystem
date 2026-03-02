# Arrays Extension

**Plugin**: `plugins/arrays.cpp` (compiled to `arrays.dll` / `arrays.so`)

Adds array literal syntax (`[...]`) and index access (`target[index]`) to the language.

## Syntax

```ebnf
array_literal ::= "[" [ expression { "," expression } ] "]"
index_access  ::= expression "[" expression "]"
```

## Usage

### Array Literals

Create arrays using bracket notation:

```
DECLARE(VARIABLE, files, ["main.cpp", "util.cpp", "io.cpp"])
```

Arrays can be nested:

```
DECLARE(VARIABLE, pairs, [["a.cpp", "a.o"], ["b.cpp", "b.o"]])
```

### Index Access

Access array elements by zero-based integer index:

```
DECLARE(VARIABLE, items, ["first", "second", "third"])
ECHO(@items[0])   /* prints: first */
ECHO(@items[2])   /* prints: third */
```

Combined with nested arrays:

```
DECLARE(VARIABLE, pair, ["source.cpp", "output.o"])
ECHO(@pair[0])    /* prints: source.cpp */
ECHO(@pair[1])    /* prints: output.o */
```

## Loading

The arrays plugin must be compiled and placed in `bin/plugins/` for it to be loaded automatically at startup. It can also be loaded at runtime:

```
LOAD_PLUGIN("path/to/arrays.dll")
```

## Notes

- Index out of bounds prints an error and returns `NULL`.
- Indexing a non-list value prints an error and returns `NULL`.
- Index must evaluate to an integer.
