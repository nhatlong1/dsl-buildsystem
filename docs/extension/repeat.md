# REPEAT Extension

The `repeat` plugin adds a loop construct to the language.

## Syntax

```ebnf
statement ::= ... | repeat_stmt
repeat_stmt ::= "REPEAT" number block
block ::= "{" { statement } "}"
```

## Example

```
REPEAT 3 {
    ECHO("This prints 3 times")
}
```

## Usage

Ensure the `repeat.py` file is in the `plugins/` directory. The parser automatically loads it.
