# BUILDCACHE Module

Provides mechanisms to cache build artifacts and state.

## Import

```
IMPORT(BUILTIN(BUILDCACHE))
USING(BUILDCACHE, *)
```

## Functions

### `CACHE(Path)`
Returns the cached entry for a file.
Properties:
- `LASTMODIFIEDDATE`: Cached timestamp.

### `WRITEBUILDCACHE()`
Writes the current cache state to disk (`.buildcache`).
