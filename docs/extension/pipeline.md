# Pipeline Extension (Disabled)

> **Status**: Disabled. Python sample located in `disabled_plugins/pipeline.py`. See `extensions/ext11.pipeline.ebnf.txt` for the grammar specification.

The pipeline extension adds the `|>` operator for chaining function calls.

## Syntax

```ebnf
pipeline ::= statement "|>" statement
```

## Usage

```
function_a() |> function_b()
```

The pipeline operator inserts the result of the left-hand statement as the **first argument** of the right-hand statement.

### Example

```
@"Hello World" |> ECHO()
/* Equivalent to: ECHO("Hello World") */

@EXISTS("main.cpp") |> IF(EXECUTE(gpp, "main.cpp -o main"), ECHO("main.cpp doesn't exist"))
```

## Notes

- The `|>` token (`PIPE_GT`) is defined in the lexer.
- Pipeline precedence is 10 (between LOWEST and SUM).
- This extension is currently disabled and not compiled as a plugin.
- A non-returning (no result) statement can be piped into any statement
- Caller provide argument to multi-parameter functions as if the first field was filled
