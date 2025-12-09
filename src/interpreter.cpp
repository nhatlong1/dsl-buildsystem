#include "interpreter.hpp"
#include <iostream>
#include <regex>
#include <cstdlib>
#include <sstream>
#include <filesystem>

namespace dsl {

// Forward declaration
void load_plugin(const std::string& path, Parser& parser, Context& context);

// --- Context ---

Value DefaultContext::get(const std::string& name) {
    auto it = symbols.find(name);
    if (it != symbols.end()) {
        return it->second;
    }
    return Value(); // Null
}

void DefaultContext::set(const std::string& name, Value value) {
    symbols[name] = value;
}

void DefaultContext::register_function(const std::string& name, std::function<Value(const std::vector<std::shared_ptr<ASTNode>>&, Interpreter&)> func) {
    functions[name] = func;
}

Value DefaultContext::call_function(const std::string& name, const std::vector<std::shared_ptr<ASTNode>>& args, Interpreter& interpreter) {
    auto it = functions.find(name);
    if (it != functions.end()) {
        return it->second(args, interpreter);
    }

    Value val = get(name);
    if (!val.is_null()) {
         auto eval_args = interpreter.evaluate_args(args);

         if (eval_args.size() == 1 && eval_args[0].is_flag()) {
             auto flag = eval_args[0].get<std::shared_ptr<Flag>>();
             return Value(flag->apply({val.as_string()}));
         }

         if (val.is_flag()) {
             auto flag = val.get<std::shared_ptr<Flag>>();
             std::vector<std::string> str_args;
             for (const auto& arg : eval_args) str_args.push_back(arg.as_string());
             return Value(flag->apply(str_args));
         }
    }

    std::cerr << "Unknown function or callable: " << name << std::endl;
    throw std::runtime_error("Runtime Error");
}

// --- Interpreter ---

DefaultInterpreter::DefaultInterpreter(bool dry_run) : dry_run_mode(dry_run) {
    using namespace std::placeholders;
    context.register_function("ECHO", std::bind(&DefaultInterpreter::func_echo, this, _1, _2));
    context.register_function("EXECUTE", std::bind(&DefaultInterpreter::func_execute, this, _1, _2));
    context.register_function("DECLARE", std::bind(&DefaultInterpreter::func_declare, this, _1, _2));
    context.register_function("SET", std::bind(&DefaultInterpreter::func_set, this, _1, _2));
    context.register_function("IF", std::bind(&DefaultInterpreter::func_if, this, _1, _2));
    context.register_function("ARRAY", std::bind(&DefaultInterpreter::func_array, this, _1, _2));
    context.register_function("EXISTS", std::bind(&DefaultInterpreter::func_exists, this, _1, _2));
    context.register_function("NOT", std::bind(&DefaultInterpreter::func_not, this, _1, _2));
    context.register_function("EQ", std::bind(&DefaultInterpreter::func_eq, this, _1, _2));
    context.register_function("LOAD_PLUGIN", std::bind(&DefaultInterpreter::func_load_plugin, this, _1, _2));
    context.register_function("LT", std::bind(&DefaultInterpreter::func_lt, this, _1, _2));
    context.register_function("NATIVEPATH", std::bind(&DefaultInterpreter::func_native_path, this, _1, _2));
    context.register_function("SELECT", std::bind(&DefaultInterpreter::func_select, this, _1, _2));

    // Register OS variable
#if defined(_WIN32) || defined(_WIN64)
    context.set("OS", Value("windows"));
#else
    context.set("OS", Value("linux"));
#endif
}

Value DefaultInterpreter::visit(ASTNode* node) {
    if (auto p = dynamic_cast<Program*>(node)) return visit_program(p);
    if (auto f = dynamic_cast<FunctionCall*>(node)) return visit_function_call(f);
    if (auto l = dynamic_cast<Literal*>(node)) return visit_literal(l);
    if (auto i = dynamic_cast<Identifier*>(node)) return visit_identifier(i);
    if (auto v = dynamic_cast<VariableDeref*>(node)) return visit_variable_deref(v);
    if (auto p = dynamic_cast<PropertyAccess*>(node)) return visit_property_access(p);
    if (auto b = dynamic_cast<BinaryExpression*>(node)) return visit_binary_expression(b);
    if (auto idx = dynamic_cast<IndexExpression*>(node)) return visit_index_expression(idx);
    if (auto fl = dynamic_cast<ForLoopNode*>(node)) return visit_for_loop(fl);

    // Try plugin execution
    void* result = node->execute(this);
    if (result) {
        Value* v = static_cast<Value*>(result);
        Value ret = *v;
        delete v;
        return ret;
    }

    return Value();
}

Context& DefaultInterpreter::get_context() {
    return context;
}

bool DefaultInterpreter::is_dry_run() const {
    return dry_run_mode;
}

std::string DefaultInterpreter::interpolate_string(const std::string& s) {
    std::regex re(R"(\$([a-zA-Z_]\w*))");
    std::string result = s;
    std::smatch match;

    std::string::const_iterator searchStart(s.cbegin());
    std::string out;

    while (std::regex_search(searchStart, s.cend(), match, re)) {
        out.append(searchStart, match.prefix().second);
        std::string var_name = match[1];
        Value val = context.get(var_name);
        if (val.is_null()) {
             // Handle array indexing in interpolation? $item[0]
             // Basic implementation: if variable is list, and string contains [...], might need parser support.
             // Here we assume basic variable interpolation.
             out.append(match[0]);
        } else {
            out.append(val.as_string());
        }
        searchStart = match.suffix().first;
    }
    out.append(searchStart, s.cend());
    return out;
}

std::vector<Value> DefaultInterpreter::evaluate_args(const std::vector<std::shared_ptr<ASTNode>>& args) {
    std::vector<Value> values;
    for (const auto& arg : args) {
        values.push_back(visit(arg.get()));
    }
    return values;
}

// Visitors

Value DefaultInterpreter::visit_program(Program* node) {
    Value result;
    for (auto& stmt : node->statements) {
        result = visit(stmt.get());
    }
    return result;
}

Value DefaultInterpreter::visit_function_call(FunctionCall* node) {
    return context.call_function(node->name->name, node->args, *this);
}

Value DefaultInterpreter::visit_identifier(Identifier* node) {
    Value val = context.get(node->name);
    if (!val.is_null()) return val;
    return Value(node->name);
}

Value DefaultInterpreter::visit_literal(Literal* node) {
    if (node->type == Literal::STR) return Value(node->string_value);
    if (node->type == Literal::INT) return Value(node->int_value);
    if (node->type == Literal::BOOL) return Value(node->bool_value);
    return Value();
}

Value DefaultInterpreter::visit_variable_deref(VariableDeref* node) {
    auto target = node->target;
    // If target is identifier, get value
    // If target is expression, evaluate it?
    // VariableDeref usually means @var -> context.get("var")

    // But what if target is IndexExpression? @item[0]
    // The parser returns VariableDeref(IndexExpression(...))?
    // No, Precedence of LBRACKET (50) > PREFIX (40).
    // So @item[0] -> (@item)[0] because [ binds tighter than @?
    // Wait. Precedence:
    // CALL = 50.
    // PREFIX = 40.
    // parse_expression(40) calls parse_prefix.
    // parse_prefix consumes @. Then parse_expression(40).
    // It calls parse_identifier (item).
    // It sees [. If [ precedence is > 40?
    // INDEX = 50.
    // So parse_identifier returns Identifier(item).
    // Loop continues. [ is infix.
    // It parses index expression. Identifier(item) becomes left of IndexExpression.
    // Returns IndexExpression(item, 0).
    // So @ calls parse_expression(40) which returns IndexExpression.
    // So VariableDeref contains IndexExpression.

    // So we need to evaluate target.
    // If target is Identifier -> context.get(name)
    // If target is IndexExpression -> evaluate index expression?
    // BUT IndexExpression(item, 0) evaluates to... item[0]?
    // If `item` is Identifier, visit_identifier returns context.get("item")?
    // If `item` is a variable name (string), then `visit_identifier` returns the value of the variable?
    // No. `visit_identifier` usually returns the value if found, or the name if not.
    // If `item` is a variable holding a list. context.get("item") returns List Value.
    // Then `visit_index_expression` takes that List Value and gets element 0.
    // So `visit(target)` returns the element value.
    // Then `VariableDeref` wraps it?
    // `VariableDeref` logic:
    // If target evaluates to a String, treat it as a variable name and get from context.
    // If target evaluates to something else (like the value itself), return it?

    Value val = visit(target.get());
    if (val.is_string()) {
         // Check if it's a variable name
         // But wait, if `item` is a list variable, `visit(item)` returns the List Value.
         // `visit_index_expression` returns the element Value.
         // If element is string "plugins/loop.cpp".
         // `VariableDeref` sees "plugins/loop.cpp".
         // Does it try to look up variable named "plugins/loop.cpp"?
         // Usually `@var` means "value of var".
         // If `var` is "x", `@var` -> value of x.
         // If `visit(target)` already returns the value, then `VariableDeref` is redundant or wrong if applied on value.

         // In `build.mybuild`: `EXECUTE(..., @item[0])`
         // `item` is a variable holding `["src", "out"]`.
         // `item[0]` should evaluate to "src".
         // If we write `item[0]`, `visit_identifier(item)` returns List. `visit_index` returns "src".
         // Then why `@`?
         // In this DSL, `@` seems to be the "Get Variable" operator.
         // Without `@`, `item` is just the string "item" (Identifier).
         // `visit_identifier` returns `Value("item")` if not found?
         // `Interpreter::visit_identifier`:
         // Value val = context.get(node->name);
         // if (!val.is_null()) return val;
         // return Value(node->name);

         // So if `item` is in context, `item` evaluates to its value.
         // So `@` is NOT needed for variables?
         // But the DSL uses `@var` everywhere.
         // Maybe `visit_identifier` should ONLY return the name?
         // And `@` does the lookup?

         // Let's check `visit_identifier` in `interpreter.cpp` again.
         /*
         Value Interpreter::visit_identifier(Identifier* node) {
            Value val = context.get(node->name);
            if (!val.is_null()) return val;
            return Value(node->name);
        }
        */
        // This implies identifiers auto-resolve.
        // If so, `@` is redundant?
        // Or maybe `@` forces interpolation?
        // `visit_variable_deref`:
        /*
        if (auto lit = dynamic_cast<Literal*>(target.get())) {
             if (lit->type == Literal::STR) {
                 return Value(interpolate_string(lit->string_value));
             }
        }
        */

        // If I change `visit_identifier` to NOT resolve, then `@` is required.
        // But `DECLARE(..., loop_src, ...)` uses `loop_src` as name.
        // If `loop_src` resolves to value, then `DECLARE` gets value.
        // `func_declare` handles Identifier args by taking name.

        // If `visit_identifier` resolves, then `item[0]` resolves.
        // So `@item[0]` -> `VariableDeref` of "src".
        // `VariableDeref` of string "src" -> looks up variable "src".
        // But "src" is a file path, not a variable.
        // So `@` might be harmful here if it forces lookup!

        // Unless `@` is what triggers the lookup, and `visit_identifier` should NOT lookup.
        // But existing code `src/interpreter.cpp` had lookup in `visit_identifier`.
        // And `VariableDeref` logic was:
        /*
        if (auto id = dynamic_cast<Identifier*>(target.get())) {
            return context.get(id->name);
        }
        */
        // It specifically handled Identifier target.

        // If target is `IndexExpression`, it is NOT `Identifier`.
        // So it fell through to `visit(target.get())`.

        // So if `visit_identifier` resolves, `@item[0]` works (returns "src") IF "src" is not a variable.
        // Wait, if `visit_identifier` resolves `item` to List.
        // `visit_index` returns Element (Value "src").
        // `visit_variable_deref` gets Value "src".
        // It returns "src".

        // So it seems okay?

    }

    if (auto id = dynamic_cast<Identifier*>(target.get())) {
        return context.get(id->name);
    }
    if (auto lit = dynamic_cast<Literal*>(target.get())) {
         if (lit->type == Literal::STR) {
             return Value(interpolate_string(lit->string_value));
         }
         return visit(lit);
    }
    return visit(target.get());
}

Value DefaultInterpreter::visit_property_access(PropertyAccess* node) {
    // Treat dot access as syntactic sugar for SELECT(target, property_name)
    Value obj = visit(node->target.get());
    std::string prop = node->property_name->name;

    // We can just call logic same as SELECT here
    if (obj.is_executable()) {
        auto exe = obj.get<std::shared_ptr<Executable>>();
        if (prop == "path") return Value(exe->path);
        if (prop == "name") return Value(exe->name);
    }

    if (obj.is_object()) {
        auto object = obj.get<std::shared_ptr<Object>>();
        return object->get_property(prop);
    }

    return Value();
}

Value DefaultInterpreter::visit_binary_expression(BinaryExpression* node) {
    Value left = visit(node->left.get());
    Value right = visit(node->right.get());

    if (node->op == TokenType::PLUS) {
        // Concatenation
        return Value(left.as_string() + right.as_string());
    }
    return Value();
}

Value DefaultInterpreter::visit_index_expression(IndexExpression* node) {
    Value left = visit(node->left.get());
    Value index = visit(node->index.get());

    if (left.is_list() && index.is_int()) {
        auto list = left.get<std::vector<Value>>();
        int idx = index.get<int>();
        if (idx >= 0 && idx < (int)list.size()) {
            return list[idx];
        }
        // Out of bounds? Return null or error.
        std::cerr << "Index out of bounds: " << idx << std::endl;
        return Value();
    }
    return Value();
}

Value DefaultInterpreter::visit_for_loop(ForLoopNode* node) {
    // node->var_name
    // node->array_expr (evaluate to list)
    // node->body_statements (list of ASTNodes)

    Value array_val = visit(node->array_expr.get());
    if (!array_val.is_list()) {
        std::cerr << "FOR loop expects an array." << std::endl;
        return Value();
    }

    auto list = array_val.get<std::vector<Value>>();
    for (const auto& item : list) {
        context.set(node->var_name, item);
        for (const auto& stmt : node->body_statements) {
            visit(stmt.get());
        }
    }
    return Value();
}

// Core Functions

Value DefaultInterpreter::func_echo(const std::vector<std::shared_ptr<ASTNode>>& args, Interpreter& /* interp */) {
    auto vals = evaluate_args(args);
    for (size_t i = 0; i < vals.size(); ++i) {
        std::cout << vals[i].as_string() << (i == vals.size() - 1 ? "" : " ");
    }
    std::cout << std::endl;
    return Value(true);
}

Value DefaultInterpreter::func_array(const std::vector<std::shared_ptr<ASTNode>>& args, Interpreter& /* interp */) {
    return Value(evaluate_args(args));
}

Value DefaultInterpreter::func_not(const std::vector<std::shared_ptr<ASTNode>>& args, Interpreter& /* interp */) {
     auto vals = evaluate_args(args);
     if (vals.empty()) return Value(true);
     if (vals[0].is_bool()) return Value(!vals[0].get<bool>());
     return Value(false);
}

Value DefaultInterpreter::func_eq(const std::vector<std::shared_ptr<ASTNode>>& args, Interpreter& /* interp */) {
     auto vals = evaluate_args(args);
     if (vals.size() < 2) return Value(false);

     if (vals[0].is_string() && vals[1].is_string()) return Value(vals[0].as_string() == vals[1].as_string());
     if (vals[0].is_int() && vals[1].is_int()) return Value(vals[0].get<int>() == vals[1].get<int>());
     if (vals[0].is_bool() && vals[1].is_bool()) return Value(vals[0].get<bool>() == vals[1].get<bool>());

     return Value(false);
}

Value DefaultInterpreter::func_exists(const std::vector<std::shared_ptr<ASTNode>>& args, Interpreter& /* interp */) {
    auto vals = evaluate_args(args);
    if (vals.empty()) return Value(false);
    return Value(std::filesystem::exists(vals[0].as_string()));
}

Value DefaultInterpreter::func_declare(const std::vector<std::shared_ptr<ASTNode>>& args, Interpreter& /* interp */) {
    auto type_node = args[0];
    auto name_node = args[1];

    Value decl_type_val = visit(type_node.get());
    std::string decl_type = decl_type_val.as_string();

    std::string name;
    if (auto id = dynamic_cast<Identifier*>(name_node.get())) name = id->name;
    else name = visit(name_node.get()).as_string();

    auto vals = evaluate_args({args.begin() + 2, args.end()});

    if (decl_type == "VARIABLE") {
        context.set(name, vals[0]);
    } else if (decl_type == "FLAGS") {
        context.set(name, Value(std::make_shared<Flag>(name, vals[0].as_string())));
    } else if (decl_type == "EXECUTABLE") {
        std::string desc = (vals.size() > 0) ? vals[0].as_string() : "";
        std::string src = (vals.size() > 1) ? vals[1].as_string() : "";
        std::string path = (vals.size() > 2) ? vals[2].as_string() : "";
        context.set(name, Value(std::make_shared<Executable>(name, desc, src, path)));
    }
    return Value();
}

Value DefaultInterpreter::func_set(const std::vector<std::shared_ptr<ASTNode>>& args, Interpreter& /* interp */) {
    auto name_node = args[0];
    std::string name;
    if (auto id = dynamic_cast<Identifier*>(name_node.get())) name = id->name;
    else name = visit(name_node.get()).as_string();

    Value val = visit(args[1].get());
    context.set(name, val);
    return Value();
}

Value DefaultInterpreter::func_if(const std::vector<std::shared_ptr<ASTNode>>& args, Interpreter& /* interp */) {
    Value cond = visit(args[0].get());
    bool is_true = false;
    if (cond.is_bool()) is_true = cond.get<bool>();
    else if (cond.is_int()) is_true = cond.get<int>() != 0;
    else if (!cond.is_null()) is_true = true;

    if (is_true) {
        visit(args[1].get());
    } else if (args.size() > 2) {
        visit(args[2].get());
    }
    return Value();
}

Value DefaultInterpreter::func_execute(const std::vector<std::shared_ptr<ASTNode>>& args, Interpreter& /* interp */) {
    auto evaluated_args = evaluate_args(args);
    if (evaluated_args.empty()) return Value();

    Value exe = evaluated_args[0];
    std::vector<Value> cmd_args(evaluated_args.begin() + 1, evaluated_args.end());

    std::vector<std::string> final_args;

    std::vector<Value> processed_args;
    size_t i = 0;
    while (i < cmd_args.size()) {
        Value arg = cmd_args[i];
        if (arg.is_flag()) {
             auto flag = arg.get<std::shared_ptr<Flag>>();
             int arity = flag->arity;
             std::vector<std::string> flag_inputs;
             for (int k = 0; k < arity; ++k) {
                 if (!processed_args.empty()) {
                     flag_inputs.insert(flag_inputs.begin(), processed_args.back().as_string());
                     processed_args.pop_back();
                 }
             }
             std::string res = flag->apply(flag_inputs);
             std::stringstream ss(res);
             std::string segment;
             while(std::getline(ss, segment, ' ')) {
                 if(!segment.empty()) processed_args.push_back(Value(segment));
             }
        } else if (arg.is_list()) {
            auto list = arg.get<std::vector<Value>>();
            for (const auto& item : list) processed_args.push_back(item);
        } else {
            processed_args.push_back(arg);
        }
        i++;
    }

    std::string exe_name = exe.as_string();
    if (exe.is_executable()) {
        auto e = exe.get<std::shared_ptr<Executable>>();
        exe_name = e->path.empty() ? e->name : e->path;
    }

    std::string full_command = exe_name;
    for (const auto& arg : processed_args) {
        full_command += " " + arg.as_string();
    }

    if (dry_run_mode) {
        std::cout << "EXECUTE (DRY): " << full_command << std::endl;
        return Value();
    }

    std::cout << "EXECUTE: " << full_command << std::endl;
    int ret = std::system(full_command.c_str());
    if (ret != 0) {
        std::cerr << "Command failed with code " << ret << std::endl;
    }
    return Value();
}

Value DefaultInterpreter::func_load_plugin(const std::vector<std::shared_ptr<ASTNode>>& args, Interpreter& /* interp */) {
    if (!attached_parser) {
        std::cerr << "Cannot load plugins: No parser attached to interpreter." << std::endl;
        return Value();
    }
    auto vals = evaluate_args(args);
    if (vals.empty()) return Value();

    std::string path = vals[0].as_string();
    load_plugin(path, *attached_parser, context);
    return Value();
}

Value DefaultInterpreter::func_lt(const std::vector<std::shared_ptr<ASTNode>>& args, Interpreter& /* interp */) {
    auto vals = evaluate_args(args);
    if (vals.size() < 2) return Value(false);

    if (vals[0].is_int() && vals[1].is_int()) {
        return Value(vals[0].get<int>() < vals[1].get<int>());
    }
    return Value(false);
}

Value DefaultInterpreter::func_native_path(const std::vector<std::shared_ptr<ASTNode>>& args, Interpreter& /* interp */) {
    auto vals = evaluate_args(args);
    if (vals.empty()) return Value();

    std::filesystem::path p(vals[0].as_string());
    return Value(p.make_preferred().string());
}

Value DefaultInterpreter::func_select(const std::vector<std::shared_ptr<ASTNode>>& args, Interpreter& /* interp */) {
    if (args.size() < 2) return Value();

    // Evaluate arguments to get the object and the property name
    auto vals = evaluate_args(args);
    Value obj = vals[0];
    std::string prop = vals[1].as_string();

    if (obj.is_executable()) {
        auto exe = obj.get<std::shared_ptr<Executable>>();
        if (prop == "path") return Value(exe->path);
        if (prop == "name") return Value(exe->name);
    }

    if (obj.is_object()) {
        auto object = obj.get<std::shared_ptr<Object>>();
        return object->get_property(prop);
    }

    return Value();
}

} // namespace dsl
