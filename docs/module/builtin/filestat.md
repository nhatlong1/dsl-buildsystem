# FILESTAT Module

Provides file status and existence checks.

## Import

```
IMPORT(BUILTIN(FILESTAT))
USING(FILESTAT, *)
```

## Functions

### `STAT(Path)`
Returns a file status object.
Properties:
- `LASTMODIFIEDDATE`: Timestamp of last modification.

### `EXISTS(Path)`
Returns `TRUE` if the file/directory exists, `FALSE` otherwise.
