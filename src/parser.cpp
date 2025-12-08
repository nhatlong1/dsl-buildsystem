#include "parser.hpp"
#include <iostream>

namespace dsl {

Parser::Parser(std::shared_ptr<ILexer> l) : lexer(std::move(l)) {
    current_token = lexer->get_next_token();
    register_core_grammar();
}

void Parser::register_core_grammar() {
    using namespace std::placeholders;

    // Prefix
    register_prefix(TokenType::IDENTIFIER, std::bind(&Parser::parse_identifier, this));
    register_prefix(TokenType::STRING, std::bind(&Parser::parse_literal, this));
    register_prefix(TokenType::NUMBER, std::bind(&Parser::parse_literal, this));
    register_prefix(TokenType::BOOLEAN, std::bind(&Parser::parse_literal, this));
    register_prefix(TokenType::NULL_TYPE, std::bind(&Parser::parse_literal, this));
    register_prefix(TokenType::STAR, std::bind(&Parser::parse_identifier_star, this));
    register_prefix(TokenType::LPAREN, std::bind(&Parser::parse_grouped_expression, this));
    register_prefix(TokenType::AT, std::bind(&Parser::parse_deref, this));

    // Infix
    register_infix(TokenType::LPAREN, std::bind(&Parser::parse_call_expression, this, _1), static_cast<int>(Precedence::CALL));
    register_infix(TokenType::DOT, std::bind(&Parser::parse_property_access, this, _1), static_cast<int>(Precedence::DOT));
}

void Parser::register_prefix(TokenType type, std::function<std::shared_ptr<ASTNode>()> fn) {
    prefix_parse_fns[type] = fn;
}

void Parser::register_infix(TokenType type, std::function<std::shared_ptr<ASTNode>(std::shared_ptr<ASTNode>)> fn, int precedence) {
    infix_parse_fns[type] = {fn, precedence};
}

void Parser::register_token_handler(const std::string& keyword, std::function<std::shared_ptr<ASTNode>(IParser&)> fn) {
    token_handlers[keyword] = fn;
}

Token<std::string> Parser::eat(TokenType type) {
    Token<std::string> token = current_token;
    if (token.type == type) {
        current_token = lexer->get_next_token();
        return token;
    } else {
        std::cerr << "Expected token type " << static_cast<int>(type) << " but got " << static_cast<int>(token.type)
                  << " at line " << token.line << std::endl;
        throw std::runtime_error("Parser Error");
    }
}

int Parser::peek_precedence() {
    auto it = infix_parse_fns.find(current_token.type);
    if (it != infix_parse_fns.end()) {
        return it->second.second;
    }
    return static_cast<int>(Precedence::LOWEST);
}

std::shared_ptr<Program> Parser::parse_program() {
    auto program = std::make_shared<Program>();
    while (current_token.type != TokenType::EOF_TOKEN) {
        program->statements.push_back(parse_expression(static_cast<int>(Precedence::LOWEST)));
    }
    return program;
}

std::shared_ptr<ASTNode> Parser::parse_expression(int precedence) {
    auto prefix_it = prefix_parse_fns.find(current_token.type);
    if (prefix_it == prefix_parse_fns.end()) {
        std::cerr << "No prefix parse function for " << static_cast<int>(current_token.type)
                  << " (" << current_token.value << ")" << " at line " << current_token.line << std::endl;
        throw std::runtime_error("Parser Error");
    }

    auto left = prefix_it->second();

    while (precedence < peek_precedence()) {
        auto infix_it = infix_parse_fns.find(current_token.type);
        if (infix_it == infix_parse_fns.end()) {
            return left;
        }

        auto fn = infix_it->second.first;
        left = fn(left);
    }

    return left;
}

// Parsers

std::shared_ptr<ASTNode> Parser::parse_identifier() {
    // Check keyword handlers
    auto it = token_handlers.find(current_token.value);
    if (it != token_handlers.end()) {
        return it->second(*this);
    }

    Token<std::string> token = eat(TokenType::IDENTIFIER);
    return std::make_shared<Identifier>(token.value);
}

std::shared_ptr<ASTNode> Parser::parse_literal() {
    Token<std::string> token = current_token;
    eat(token.type);

    if (token.type == TokenType::STRING) return std::make_shared<Literal>(token.value);
    if (token.type == TokenType::NUMBER) return std::make_shared<Literal>(std::stoi(token.value));
    if (token.type == TokenType::BOOLEAN) return std::make_shared<Literal>(token.value == "TRUE");
    if (token.type == TokenType::NULL_TYPE) return std::make_shared<Literal>();

    return nullptr;
}

std::shared_ptr<ASTNode> Parser::parse_identifier_star() {
    eat(TokenType::STAR);
    return std::make_shared<Identifier>("*");
}

std::shared_ptr<ASTNode> Parser::parse_grouped_expression() {
    eat(TokenType::LPAREN);
    auto exp = parse_expression(static_cast<int>(Precedence::LOWEST));
    eat(TokenType::RPAREN);
    return exp;
}

std::shared_ptr<ASTNode> Parser::parse_deref() {
    eat(TokenType::AT);
    auto target = parse_expression(static_cast<int>(Precedence::PREFIX));
    return std::make_shared<VariableDeref>(target);
}

std::shared_ptr<ASTNode> Parser::parse_call_expression(std::shared_ptr<ASTNode> left) {
    auto id = std::dynamic_pointer_cast<Identifier>(left);
    if (!id) {
         throw std::runtime_error("Function call must be on an Identifier");
    }

    eat(TokenType::LPAREN);
    std::vector<std::shared_ptr<ASTNode>> args;
    if (current_token.type != TokenType::RPAREN) {
        args = parse_arg_list();
    }
    eat(TokenType::RPAREN);

    return std::make_shared<FunctionCall>(id, args);
}

std::shared_ptr<ASTNode> Parser::parse_property_access(std::shared_ptr<ASTNode> left) {
    eat(TokenType::DOT);
    Token<std::string> token = eat(TokenType::IDENTIFIER);
    auto prop = std::make_shared<Identifier>(token.value);
    return std::make_shared<PropertyAccess>(left, prop);
}

std::vector<std::shared_ptr<ASTNode>> Parser::parse_arg_list() {
    std::vector<std::shared_ptr<ASTNode>> args;
    args.push_back(parse_expression(static_cast<int>(Precedence::LOWEST)));
    while (current_token.type == TokenType::COMMA) {
        eat(TokenType::COMMA);
        args.push_back(parse_expression(static_cast<int>(Precedence::LOWEST)));
    }
    return args;
}

} // namespace dsl
