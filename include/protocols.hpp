#pragma once

#include "types.hpp"
#include "value.hpp"
#include <string>
#include <vector>
#include <map>
#include <functional>

namespace dsl {

class ILexer {
public:
    virtual ~ILexer() = default;
    virtual Token<std::string> get_next_token() = 0;
};

class IInterpreter;

class IContext {
public:
    virtual ~IContext() = default;
    virtual Value get(const std::string& name) = 0;
    virtual void set(const std::string& name, Value value) = 0;
    virtual void register_function(const std::string& name, std::function<Value(const std::vector<std::shared_ptr<ASTNode>>&, IInterpreter&)> func) = 0;
    virtual Value call_function(const std::string& name, const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& interpreter) = 0;
};

class IInterpreter {
public:
    virtual ~IInterpreter() = default;
    virtual Value visit(ASTNode* node) = 0;
    virtual IContext& get_context() = 0;
    virtual bool is_dry_run() const = 0;
    virtual std::string interpolate_string(const std::string& s) = 0;
    virtual std::vector<Value> evaluate_args(const std::vector<std::shared_ptr<ASTNode>>& args) = 0;
    virtual void attach_parser(class IParser* parser) = 0;
};

class IParser {
public:
    virtual ~IParser() = default;
    virtual std::shared_ptr<Program> parse_program() = 0;
    virtual std::shared_ptr<ASTNode> parse_expression(int precedence) = 0;
    virtual void register_prefix(TokenType type, std::function<std::shared_ptr<ASTNode>()> fn) = 0;
    virtual void register_infix(TokenType type, std::function<std::shared_ptr<ASTNode>(std::shared_ptr<ASTNode>)> fn, int precedence) = 0;
    virtual void register_token_handler(const std::string& keyword, std::function<std::shared_ptr<ASTNode>(IParser&)> fn) = 0;
    virtual Token<std::string> eat(TokenType type) = 0;
    virtual TokenType peek_type() = 0;
};

} // namespace dsl
