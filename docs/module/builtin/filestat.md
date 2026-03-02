# FILESTAT Module

**Source**: `modules/filestat.cpp` (compiled to `filestat.dll` / `filestat.so`)

Provides file status and existence checks. Used for incremental builds to detect when source files have changed.

## Import

```
IMPORT(BUILTIN(FILESTAT))
USING(FILESTAT, *)
```

## Functions

### `STAT(Path)`

Returns a file status object for the given path. The object exposes properties accessible via `.` notation.

**Properties**:

| Property           | Type   | Description                                          |
| ------------------ | ------ | ---------------------------------------------------- |
| `LASTMODIFIEDDATE` | Number | Timestamp of last modification (seconds since epoch) |

```
DECLARE(VARIABLE, info, STAT("main.cpp"))
ECHO(@info.LASTMODIFIEDDATE)
```

Or inline:

```
STAT("main.cpp").LASTMODIFIEDDATE
```

## Typical Usage

Compare file timestamps against cached values for incremental builds:

```
IF(NEQ(
    STAT("main.cpp").LASTMODIFIEDDATE,
    CACHE("main.cpp").LASTMODIFIEDDATE
  ),
  EXECUTE(@gpp, "main.cpp", "-o", "main"),
  ECHO("main.cpp up to date")
)
```
