# Repeat Extension (`REPEAT`)

**Plugin**: `plugins/repeat.cpp` (compiled to `repeat.dll` / `repeat.so`)

Adds a `REPEAT` construct for executing an expression a fixed number of times.

## Syntax

```ebnf
repeat_stmt ::= "REPEAT" "(" number "," expression ")"
```

## Usage

```
REPEAT(count, body)
```

- `count` — A numeric literal specifying how many times to repeat.
- `body` — Expression executed on each iteration.

## Examples

```
REPEAT(3, ECHO("Hello"))
/* Output:
   Hello
   Hello
   Hello
*/
```

```
REPEAT(5, EXECUTE(@gpp, "--version"))
```

## Loading

The repeat plugin must be compiled and placed in `bin/plugins/`. It is loaded automatically at startup.
