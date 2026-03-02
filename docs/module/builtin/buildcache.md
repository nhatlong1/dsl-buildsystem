# BUILDCACHE Module

**Source**: `modules/buildcache.cpp` (compiled to `buildcache.dll` / `buildcache.so`)

Provides a simple JSON-based caching mechanism for tracking build artifact state. Cache data is persisted to a `.buildcache` file in the working directory.

Requires `vendor/json.hpp` ([nlohmann/json](https://github.com/nlohmann/json)) at compile time.

## Import

```
IMPORT(BUILTIN(BUILDCACHE))
USING(BUILDCACHE, *)
```

## Functions

### `CACHE(Path)`

Returns the cached entry for a file path. The entry exposes properties accessible via `.` notation.

**Properties**:

| Property           | Type   | Description                         |
| ------------------ | ------ | ----------------------------------- |
| `LASTMODIFIEDDATE` | Number | The recorded timestamp in the cache |

```
CACHE("main.cpp").LASTMODIFIEDDATE
```

If no entry exists for the path, properties return `NULL` or `0`.

### `WRITEBUILDCACHE()`

Writes the current in-memory cache state to the `.buildcache` file on disk. Call this after builds to persist updated timestamps.

```
WRITEBUILDCACHE()
```

## Typical Usage

Use with FILESTAT for incremental builds — only rebuild when the source has changed since the last cached build:

```
IMPORT(BUILTIN(FILESTAT))
IMPORT(BUILTIN(BUILDCACHE))
USING(FILESTAT, *)
USING(BUILDCACHE, *)

IF(NEQ(
    STAT("main.cpp").LASTMODIFIEDDATE,
    CACHE("main.cpp").LASTMODIFIEDDATE
  ),
  EXECUTE(@gpp, "main.cpp", "-o", "main"),
  ECHO("main.cpp up to date")
)

WRITEBUILDCACHE()
```
