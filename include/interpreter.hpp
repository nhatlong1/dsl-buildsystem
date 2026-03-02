#pragma once

#include "interfaces.hpp"
#include <map>
#include <vector>
#include <string>

namespace dsl
{

    class DefaultContext : public Context
    {
    private:
        std::map<std::string, Value> symbols;
        std::map<std::string, std::function<Value(const std::vector<std::shared_ptr<ASTNode>> &, Interpreter &)>> functions;
        std::map<std::string, Value> modules;

    public:
        Value get(const std::string &name) override;
        void set(const std::string &name, Value value) override;
        void register_function(const std::string &name, std::function<Value(const std::vector<std::shared_ptr<ASTNode>> &, Interpreter &)> func) override;
        Value call_function(const std::string &name, const std::vector<std::shared_ptr<ASTNode>> &args, Interpreter &interpreter) override;
    };

    class DefaultInterpreter : public Interpreter
    {
    private:
        DefaultContext context;
        bool dry_run_mode;
        Parser *attached_parser = nullptr;

        // Core Functions
        Value func_echo(const std::vector<std::shared_ptr<ASTNode>> &args, Interpreter &interp);
        Value func_execute(const std::vector<std::shared_ptr<ASTNode>> &args, Interpreter &interp);
        Value func_declare(const std::vector<std::shared_ptr<ASTNode>> &args, Interpreter &interp);
        Value func_set(const std::vector<std::shared_ptr<ASTNode>> &args, Interpreter &interp);
        Value func_if(const std::vector<std::shared_ptr<ASTNode>> &args, Interpreter &interp);
        Value func_array(const std::vector<std::shared_ptr<ASTNode>> &args, Interpreter &interp);
        Value func_exists(const std::vector<std::shared_ptr<ASTNode>> &args, Interpreter &interp);
        Value func_not(const std::vector<std::shared_ptr<ASTNode>> &args, Interpreter &interp);
        Value func_eq(const std::vector<std::shared_ptr<ASTNode>> &args, Interpreter &interp);
        Value func_load_plugin(const std::vector<std::shared_ptr<ASTNode>> &args, Interpreter &interp);
        Value func_platform(const std::vector<std::shared_ptr<ASTNode>> &args, Interpreter &interp);
        Value func_neq(const std::vector<std::shared_ptr<ASTNode>> &args, Interpreter &interp);

        // Visitors
        Value visit_program(Program *node);
        Value visit_function_call(FunctionCall *node);
        Value visit_identifier(Identifier *node);
        Value visit_literal(Literal *node);
        Value visit_variable_deref(VariableDeref *node);
        Value visit_property_access(PropertyAccess *node);
        Value visit_binary_expression(BinaryExpression *node);

    public:
        explicit DefaultInterpreter(bool dry_run = false);

        void attach_parser(Parser *parser) override { attached_parser = parser; }

        Value visit(ASTNode *node) override;
        Context &get_context() override;
        bool is_dry_run() const override;
        std::string interpolate_string(const std::string &s) override;
        std::vector<Value> evaluate_args(const std::vector<std::shared_ptr<ASTNode>> &args) override;
    };

} // namespace dsl
