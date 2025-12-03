# Pipeline Extension (Disabled)

The `pipeline` extension adds the `|>` operator for chaining function calls.
This extension is currently **disabled** (located in `disabled_plugins/`).

## Syntax

```ebnf
program  ::= { statement | pipeline }
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
// Equivalent to: ECHO("Hello World")
```
