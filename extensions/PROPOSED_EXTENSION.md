| Extension Name | Description | Severity | Status | EBNF |
| :--- | :--- | :--- | :--- | :--- |
| **Nested Function Call** | Nested calls (e.g. `func(other())`) and property access (`.`) are native. | **Must-have** | **Integrated** | [[ext01.nestedfunctioncall.ebnf.txt]] |
| **Extended Template** | String interpolation with `@"..."` and `$var`. | **Must-have** | **Integrated** | [[ext02.extendedtemplate.ebnf.txt]] |
| **Shell Integration** | Execution of commands via `EXECUTE()`. Dedicated `SHELL()` syntax not strictly needed. | **Must-have** | **Integrated** (via `EXECUTE`) | [[ext03.shellintegration.ebnf.txt]] |
| **Error Handling** | Functional `TRY(op, catch)` handling. | **Should-have** | **Implemented** | [[ext04.errorhandling.ebnf.txt]] |
| **Patch Construct** | Dynamic identifier replacement. | **Nice-to-have** | **Implemented** | [[ext05.patchconstruct.ebnf.txt]] |
| **Array and Loop** | Iteration and lists. Functional `FOR` implemented. | **Must-have** | **Implemented** | [[ext06.arrayandloop.ebnf.txt]] |
| **Extended Access Notation** | `@` dereferencing and property access. | **Nice-to-have** | **Integrated** | [[ext07.extendedaccessnotation.ebnf.txt]] |
| **Conditionals** | `IF(cond, true, false)` and `IFANY` logic. | **Must-have** | **Integrated** | N/A (Core) |
| **Assignment** | `DECLARE()` and `SET()` functions. | **Must-have** | **Integrated** | N/A (Core) |
| **Imports** | `IMPORT()` function. | **Must-have** | **Integrated** | N/A (Core) |
| **Pipeline Operator** | `|>` syntax for chaining. Enhances readability of nested functional calls. | **Nice-to-have** | **Implemented** (Disabled) | [[ext11.pipeline.ebnf.txt]] |
| **Repeat Loop** | `REPEAT n { ... }` block syntax. | **Nice-to-have** | **Implemented** | N/A (Plugin) |
