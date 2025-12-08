#pragma once

#include "protocols.hpp"
#include <map>
#include <vector>
#include <string>

namespace dsl {

class Context : public IContext {
private:
    std::map<std::string, Value> symbols;
    std::map<std::string, std::function<Value(const std::vector<std::shared_ptr<ASTNode>>&, IInterpreter&)>> functions;
    std::map<std::string, Value> modules; // Storing modules as Values for now if needed

public:
    Value get(const std::string& name) override;
    void set(const std::string& name, Value value) override;
    void register_function(const std::string& name, std::function<Value(const std::vector<std::shared_ptr<ASTNode>>&, IInterpreter&)> func) override;
    Value call_function(const std::string& name, const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& interpreter) override;
};

class Interpreter : public IInterpreter {
private:
    Context context;
    bool dry_run_mode;

    // Core Functions
    Value func_echo(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& interp);
    Value func_execute(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& interp);
    Value func_declare(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& interp);
    Value func_set(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& interp);
    Value func_if(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& interp);
    Value func_array(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& interp);
    Value func_exists(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& interp);
    Value func_not(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& interp);

    // Visitors
    Value visit_program(Program* node);
    Value visit_function_call(FunctionCall* node);
    Value visit_identifier(Identifier* node);
    Value visit_literal(Literal* node);
    Value visit_variable_deref(VariableDeref* node);
    Value visit_property_access(PropertyAccess* node);

public:
    explicit Interpreter(bool dry_run = false);

    Value visit(ASTNode* node) override;
    IContext& get_context() override;
    bool is_dry_run() const override;
    std::string interpolate_string(const std::string& s) override;
    std::vector<Value> evaluate_args(const std::vector<std::shared_ptr<ASTNode>>& args) override;
};

} // namespace dsl
