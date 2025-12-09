#pragma once

#include "interfaces.hpp"
#include <vector>
#include <map>
#include <functional>

namespace dsl {

class DefaultParser : public Parser {
public:
    explicit DefaultParser(std::shared_ptr<Lexer> l);
    std::shared_ptr<Program> parse_program() override;
    std::shared_ptr<ASTNode> parse_expression(int precedence) override;
    void register_prefix(TokenType type, std::function<std::shared_ptr<ASTNode>()> fn) override;
    void register_infix(TokenType type, std::function<std::shared_ptr<ASTNode>(std::shared_ptr<ASTNode>)> fn, int precedence) override;
    void register_token_handler(const std::string& keyword, std::function<std::shared_ptr<ASTNode>(Parser&)> fn) override;
    Token<std::string> eat(TokenType type) override;
    TokenType peek_type() override;

private:
    std::shared_ptr<Lexer> lexer;
    Token<std::string> current_token;

    std::map<TokenType, std::function<std::shared_ptr<ASTNode>()>> prefix_parse_fns;
    std::map<TokenType, std::function<std::shared_ptr<ASTNode>(std::shared_ptr<ASTNode>)>> infix_parse_fns;
    std::map<TokenType, int> precedences;
    std::map<std::string, std::function<std::shared_ptr<ASTNode>(Parser&)>> token_handlers;

    void register_builtins();
    std::shared_ptr<ASTNode> parse_statement();
    std::shared_ptr<ASTNode> parse_function_call(std::shared_ptr<ASTNode> left);
    std::shared_ptr<ASTNode> parse_identifier();
    std::shared_ptr<ASTNode> parse_literal();
    std::shared_ptr<ASTNode> parse_grouped_expression();
    std::shared_ptr<ASTNode> parse_list_literal();
    std::shared_ptr<ASTNode> parse_variable_deref();
    std::shared_ptr<ASTNode> parse_binary_expression(std::shared_ptr<ASTNode> left);
    std::shared_ptr<ASTNode> parse_dot(std::shared_ptr<ASTNode> left);
};

} // namespace dsl
