#include "parser.hpp"
#include <iostream>

namespace dsl {

DefaultParser::DefaultParser(std::shared_ptr<Lexer> l) : lexer(std::move(l)) {
    current_token = lexer->get_next_token();
    register_core_grammar();
}

void DefaultParser::register_core_grammar() {
    // Prefix
    register_prefix(TokenType::IDENTIFIER, [this] { return parse_identifier(); });
    register_prefix(TokenType::STRING, [this] { return parse_literal(); });
    register_prefix(TokenType::NUMBER, [this] { return parse_literal(); });
    register_prefix(TokenType::BOOLEAN, [this] { return parse_literal(); });
    register_prefix(TokenType::NULL_TYPE, [this] { return parse_literal(); });
    register_prefix(TokenType::STAR, [this] { return parse_identifier_star(); });
    register_prefix(TokenType::LPAREN, [this] { return parse_grouped_expression(); });
    register_prefix(TokenType::AT, [this] { return parse_deref(); });

    // Infix
    register_infix(TokenType::LPAREN, [this](auto left) { return parse_call_expression(left); }, static_cast<int>(Precedence::CALL));
    register_infix(TokenType::DOT, [this](auto left) { return parse_property_access(left); }, static_cast<int>(Precedence::DOT));
    register_infix(TokenType::PLUS, [this](auto left) { return parse_infix_expression(left); }, static_cast<int>(Precedence::SUM));
}

void DefaultParser::register_prefix(TokenType type, std::function<std::shared_ptr<ASTNode>()> fn) {
    prefix_parse_fns[type] = fn;
}

void DefaultParser::register_infix(TokenType type, std::function<std::shared_ptr<ASTNode>(std::shared_ptr<ASTNode>)> fn, int precedence) {
    infix_parse_fns[type] = {fn, precedence};
}

void DefaultParser::register_token_handler(const std::string& keyword, std::function<std::shared_ptr<ASTNode>(Parser&)> fn) {
    token_handlers[keyword] = fn;
}

Token<std::string> DefaultParser::eat(TokenType type) {
    Token<std::string> token = current_token;
    if (token.type == type) {
        current_token = lexer->get_next_token();
        return token;
    } else {
        std::cerr << "Expected token type " << static_cast<int>(type) << " but got " << static_cast<int>(token.type)
                  << " (" << token.value << ")" << " at line " << token.line << std::endl;
        throw std::runtime_error("Parser Error");
    }
}

TokenType DefaultParser::peek_type() {
    return current_token.type;
}

int DefaultParser::peek_precedence() {
    auto it = infix_parse_fns.find(current_token.type);
    if (it != infix_parse_fns.end()) {
        return it->second.second;
    }
    return static_cast<int>(Precedence::LOWEST);
}

std::shared_ptr<Program> DefaultParser::parse_program() {
    auto program = std::make_shared<Program>();
    while (current_token.type != TokenType::EOF_TOKEN) {
        program->statements.push_back(parse_expression(static_cast<int>(Precedence::LOWEST)));
    }
    return program;
}

std::shared_ptr<ASTNode> DefaultParser::parse_expression(int precedence) {
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

std::shared_ptr<ASTNode> DefaultParser::parse_identifier() {
    auto it = token_handlers.find(current_token.value);
    if (it != token_handlers.end()) {
        return it->second(*this);
    }

    Token<std::string> token = eat(TokenType::IDENTIFIER);
    return std::make_shared<Identifier>(token.value);
}

std::shared_ptr<ASTNode> DefaultParser::parse_literal() {
    Token<std::string> token = current_token;
    eat(token.type);

    if (token.type == TokenType::STRING) return std::make_shared<Literal>(token.value);
    if (token.type == TokenType::NUMBER) return std::make_shared<Literal>(std::stoi(token.value));
    if (token.type == TokenType::BOOLEAN) return std::make_shared<Literal>(token.value == "TRUE");
    if (token.type == TokenType::NULL_TYPE) return std::make_shared<Literal>();

    return nullptr;
}

std::shared_ptr<ASTNode> DefaultParser::parse_identifier_star() {
    eat(TokenType::STAR);
    return std::make_shared<Identifier>("*");
}

std::shared_ptr<ASTNode> DefaultParser::parse_grouped_expression() {
    eat(TokenType::LPAREN);
    auto exp = parse_expression(static_cast<int>(Precedence::LOWEST));
    eat(TokenType::RPAREN);
    return exp;
}

std::shared_ptr<ASTNode> DefaultParser::parse_deref() {
    eat(TokenType::AT);
    auto target = parse_expression(static_cast<int>(Precedence::PREFIX));
    return std::make_shared<VariableDeref>(target);
}

std::shared_ptr<ASTNode> DefaultParser::parse_call_expression(std::shared_ptr<ASTNode> left) {
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

std::shared_ptr<ASTNode> DefaultParser::parse_property_access(std::shared_ptr<ASTNode> left) {
    eat(TokenType::DOT);
    Token<std::string> token = eat(TokenType::IDENTIFIER);
    auto prop = std::make_shared<Identifier>(token.value);
    return std::make_shared<PropertyAccess>(left, prop);
}

std::shared_ptr<ASTNode> DefaultParser::parse_infix_expression(std::shared_ptr<ASTNode> left) {
    Token<std::string> token = current_token;
    int precedence = peek_precedence();
    eat(token.type);
    auto right = parse_expression(precedence);
    return std::make_shared<BinaryExpression>(left, token.type, right);
}

std::vector<std::shared_ptr<ASTNode>> DefaultParser::parse_arg_list() {
    std::vector<std::shared_ptr<ASTNode>> args;
    args.push_back(parse_expression(static_cast<int>(Precedence::LOWEST)));
    while (current_token.type == TokenType::COMMA) {
        eat(TokenType::COMMA);
        args.push_back(parse_expression(static_cast<int>(Precedence::LOWEST)));
    }
    return args;
}

} // namespace dsl
