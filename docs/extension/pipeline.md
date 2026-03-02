# Pipeline Extension (Disabled)

> **Status**: Disabled. Located in `disabled_plugins/pipeline.py`. See `extensions/ext11.pipeline.ebnf.txt` for the grammar specification.

The pipeline extension adds the `|>` operator for chaining function calls.

## Syntax

```ebnf
pipeline ::= expression "|>" function_call
```

## Usage

```
expression |> function()
```

The pipeline operator inserts the result of the left-hand expression as the **first argument** of the right-hand function call.

### Example

```
"Hello World" |> ECHO()
/* Equivalent to: ECHO("Hello World") */
```

## Notes

- The `|>` token (`PIPE_GT`) is defined in the lexer.
- Pipeline precedence is 10 (between LOWEST and SUM).
- This extension is currently disabled and not compiled as a plugin.
