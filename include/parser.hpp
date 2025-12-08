#pragma once

#include "protocols.hpp"
#include <map>
#include <memory>

namespace dsl {

class Parser : public IParser {
private:
    std::shared_ptr<ILexer> lexer;
    Token<std::string> current_token;

    std::map<TokenType, std::function<std::shared_ptr<ASTNode>()>> prefix_parse_fns;
    std::map<TokenType, std::pair<std::function<std::shared_ptr<ASTNode>(std::shared_ptr<ASTNode>)>, int>> infix_parse_fns;
    std::map<std::string, std::function<std::shared_ptr<ASTNode>(IParser&)>> token_handlers;

    int peek_precedence();

    // Core parsers
    std::shared_ptr<ASTNode> parse_identifier();
    std::shared_ptr<ASTNode> parse_literal();
    std::shared_ptr<ASTNode> parse_identifier_star();
    std::shared_ptr<ASTNode> parse_grouped_expression();
    std::shared_ptr<ASTNode> parse_deref();
    std::shared_ptr<ASTNode> parse_call_expression(std::shared_ptr<ASTNode> left);
    std::shared_ptr<ASTNode> parse_property_access(std::shared_ptr<ASTNode> left);

    std::vector<std::shared_ptr<ASTNode>> parse_arg_list();

public:
    explicit Parser(std::shared_ptr<ILexer> l);

    std::shared_ptr<Program> parse_program() override;
    std::shared_ptr<ASTNode> parse_expression(int precedence) override;

    void register_prefix(TokenType type, std::function<std::shared_ptr<ASTNode>()> fn) override;
    void register_infix(TokenType type, std::function<std::shared_ptr<ASTNode>(std::shared_ptr<ASTNode>)> fn, int precedence) override;
    void register_token_handler(const std::string& keyword, std::function<std::shared_ptr<ASTNode>(IParser&)> fn) override;

    Token<std::string> eat(TokenType type) override;

    void register_core_grammar();
};

} // namespace dsl
