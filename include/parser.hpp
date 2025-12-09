#pragma once

#include "interfaces.hpp"
#include <map>
#include <memory>

namespace dsl {

class DefaultParser : public Parser {
private:
    std::shared_ptr<Lexer> lexer;
    Token<std::string> current_token;

    std::map<TokenType, std::function<std::shared_ptr<ASTNode>()>> prefix_parse_fns;
    std::map<TokenType, std::pair<std::function<std::shared_ptr<ASTNode>(std::shared_ptr<ASTNode>)>, int>> infix_parse_fns;
    std::map<std::string, std::function<std::shared_ptr<ASTNode>(Parser&)>> token_handlers;

    // Core parsers
    std::shared_ptr<ASTNode> parse_identifier();
    std::shared_ptr<ASTNode> parse_literal();
    std::shared_ptr<ASTNode> parse_identifier_star();
    std::shared_ptr<ASTNode> parse_grouped_expression();
    std::shared_ptr<ASTNode> parse_deref();
    std::shared_ptr<ASTNode> parse_call_expression(std::shared_ptr<ASTNode> left);
    std::shared_ptr<ASTNode> parse_property_access(std::shared_ptr<ASTNode> left);
    std::shared_ptr<ASTNode> parse_infix_expression(std::shared_ptr<ASTNode> left); // Generic Infix

    std::vector<std::shared_ptr<ASTNode>> parse_arg_list();

public:
    explicit DefaultParser(std::shared_ptr<Lexer> l);

    std::shared_ptr<Program> parse_program() override;
    std::shared_ptr<ASTNode> parse_expression(int precedence) override;

    void register_prefix(TokenType type, std::function<std::shared_ptr<ASTNode>()> fn) override;
    void register_infix(TokenType type, std::function<std::shared_ptr<ASTNode>(std::shared_ptr<ASTNode>)> fn, int precedence) override;
    void register_token_handler(const std::string& keyword, std::function<std::shared_ptr<ASTNode>(Parser&)> fn) override;

    Token<std::string> eat(TokenType type) override;
    TokenType peek_type() override;
    int peek_precedence();

    void register_core_grammar();
};

} // namespace dsl
