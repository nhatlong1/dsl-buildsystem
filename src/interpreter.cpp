#include "interpreter.hpp"
#include <iostream>
#include <regex>
#include <cstdlib>
#include <sstream>
#include <filesystem>

namespace dsl {

// --- Context ---

Value Context::get(const std::string& name) {
    auto it = symbols.find(name);
    if (it != symbols.end()) {
        return it->second;
    }
    return Value(); // Null
}

void Context::set(const std::string& name, Value value) {
    symbols[name] = value;
}

void Context::register_function(const std::string& name, std::function<Value(const std::vector<std::shared_ptr<ASTNode>>&, IInterpreter&)> func) {
    functions[name] = func;
}

Value Context::call_function(const std::string& name, const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& interpreter) {
    auto it = functions.find(name);
    if (it != functions.end()) {
        return it->second(args, interpreter);
    }

    // Check if name is a Variable that calls a Flag
    Value val = get(name);
    if (!val.is_null()) {
         auto eval_args = interpreter.evaluate_args(args);

         // Case: Variable(Flag) -> Flag(Variable)
         if (eval_args.size() == 1 && eval_args[0].is_flag()) {
             auto flag = eval_args[0].get<std::shared_ptr<Flag>>();
             return Value(flag->apply({val.as_string()}));
         }

         // Case: Flag(Args...)
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

Interpreter::Interpreter(bool dry_run) : dry_run_mode(dry_run) {
    using namespace std::placeholders;
    context.register_function("ECHO", std::bind(&Interpreter::func_echo, this, _1, _2));
    context.register_function("EXECUTE", std::bind(&Interpreter::func_execute, this, _1, _2));
    context.register_function("DECLARE", std::bind(&Interpreter::func_declare, this, _1, _2));
    context.register_function("SET", std::bind(&Interpreter::func_set, this, _1, _2));
    context.register_function("IF", std::bind(&Interpreter::func_if, this, _1, _2));
    context.register_function("ARRAY", std::bind(&Interpreter::func_array, this, _1, _2));
    context.register_function("EXISTS", std::bind(&Interpreter::func_exists, this, _1, _2));
    context.register_function("NOT", std::bind(&Interpreter::func_not, this, _1, _2));
}

Value Interpreter::visit(ASTNode* node) {
    if (auto p = dynamic_cast<Program*>(node)) return visit_program(p);
    if (auto f = dynamic_cast<FunctionCall*>(node)) return visit_function_call(f);
    if (auto l = dynamic_cast<Literal*>(node)) return visit_literal(l);
    if (auto i = dynamic_cast<Identifier*>(node)) return visit_identifier(i);
    if (auto v = dynamic_cast<VariableDeref*>(node)) return visit_variable_deref(v);
    if (auto p = dynamic_cast<PropertyAccess*>(node)) return visit_property_access(p);

    return Value();
}

IContext& Interpreter::get_context() {
    return context;
}

bool Interpreter::is_dry_run() const {
    return dry_run_mode;
}

std::string Interpreter::interpolate_string(const std::string& s) {
    std::regex re(R"(\$([a-zA-Z_]\w*))");
    std::string result = s;
    std::smatch match;

    // Naive replacement
    std::string::const_iterator searchStart(s.cbegin());
    std::string out;

    while (std::regex_search(searchStart, s.cend(), match, re)) {
        out.append(searchStart, match.prefix().second);
        std::string var_name = match[1];
        Value val = context.get(var_name);
        if (!val.is_null()) {
            out.append(val.as_string());
        } else {
            out.append(match[0]); // Keep original if not found
        }
        searchStart = match.suffix().first;
    }
    out.append(searchStart, s.cend());
    return out;
}

std::vector<Value> Interpreter::evaluate_args(const std::vector<std::shared_ptr<ASTNode>>& args) {
    std::vector<Value> values;
    for (const auto& arg : args) {
        values.push_back(visit(arg.get()));
    }
    return values;
}

// Visitors

Value Interpreter::visit_program(Program* node) {
    Value result;
    for (auto& stmt : node->statements) {
        result = visit(stmt.get());
    }
    return result;
}

Value Interpreter::visit_function_call(FunctionCall* node) {
    return context.call_function(node->name->name, node->args, *this);
}

Value Interpreter::visit_identifier(Identifier* node) {
    Value val = context.get(node->name);
    if (!val.is_null()) return val;
    return Value(node->name); // Return name as string if not found (mostly for args)
}

Value Interpreter::visit_literal(Literal* node) {
    if (node->type == Literal::STR) return Value(node->string_value);
    if (node->type == Literal::INT) return Value(node->int_value);
    if (node->type == Literal::BOOL) return Value(node->bool_value);
    return Value();
}

Value Interpreter::visit_variable_deref(VariableDeref* node) {
    auto target = node->target;
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

Value Interpreter::visit_property_access(PropertyAccess* node) {
    Value obj = visit(node->target.get());
    std::string prop = node->property_name->name;

    if (obj.is_executable()) {
        auto exe = obj.get<std::shared_ptr<Executable>>();
        if (prop == "path") return Value(exe->path);
        if (prop == "name") return Value(exe->name);
    }
    // More property access logic here
    return Value();
}

// Core Functions

Value Interpreter::func_echo(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& /* interp */) {
    auto vals = evaluate_args(args);
    for (size_t i = 0; i < vals.size(); ++i) {
        std::cout << vals[i].as_string() << (i == vals.size() - 1 ? "" : " ");
    }
    std::cout << std::endl;
    return Value(true);
}

Value Interpreter::func_array(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& /* interp */) {
    return Value(evaluate_args(args));
}

Value Interpreter::func_not(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& /* interp */) {
     auto vals = evaluate_args(args);
     if (vals.empty()) return Value(true);
     if (vals[0].is_bool()) return Value(!vals[0].get<bool>());
     return Value(false); // Default logic
}

Value Interpreter::func_exists(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& /* interp */) {
    auto vals = evaluate_args(args);
    if (vals.empty()) return Value(false);
    return Value(std::filesystem::exists(vals[0].as_string()));
}

Value Interpreter::func_declare(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& /* interp */) {
    // DECLARE(type, name, val...)
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
        // description, source, path
        std::string desc = (vals.size() > 0) ? vals[0].as_string() : "";
        std::string src = (vals.size() > 1) ? vals[1].as_string() : "";
        std::string path = (vals.size() > 2) ? vals[2].as_string() : "";
        context.set(name, Value(std::make_shared<Executable>(name, desc, src, path)));
    }
    return Value();
}

Value Interpreter::func_set(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& /* interp */) {
    auto name_node = args[0];
    std::string name;
    if (auto id = dynamic_cast<Identifier*>(name_node.get())) name = id->name;
    else name = visit(name_node.get()).as_string();

    Value val = visit(args[1].get());
    context.set(name, val);
    return Value();
}

Value Interpreter::func_if(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& /* interp */) {
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

Value Interpreter::func_execute(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& /* interp */) {
    auto evaluated_args = evaluate_args(args);
    if (evaluated_args.empty()) return Value();

    Value exe = evaluated_args[0];
    std::vector<Value> cmd_args(evaluated_args.begin() + 1, evaluated_args.end());

    std::vector<std::string> final_args;

    // Argument processing logic (Flag handling)
    // Simplified for porting:

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
             // Split result by space and add to processed_args
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

} // namespace dsl
