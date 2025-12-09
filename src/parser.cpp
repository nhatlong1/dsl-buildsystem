#include "parser.hpp"
#include <iostream>

namespace dsl {

DefaultParser::DefaultParser(std::shared_ptr<Lexer> l) : lexer(std::move(l)) {
    current_token = lexer->get_next_token();
    register_builtins();
}

void DefaultParser::register_builtins() {
    register_prefix(TokenType::IDENTIFIER, std::bind(&DefaultParser::parse_identifier, this));
    register_prefix(TokenType::STRING, std::bind(&DefaultParser::parse_literal, this));
    register_prefix(TokenType::NUMBER, std::bind(&DefaultParser::parse_literal, this));
    register_prefix(TokenType::BOOLEAN, std::bind(&DefaultParser::parse_literal, this));
    register_prefix(TokenType::NULL_TYPE, std::bind(&DefaultParser::parse_literal, this));
    register_prefix(TokenType::LPAREN, std::bind(&DefaultParser::parse_grouped_expression, this));
    register_prefix(TokenType::LBRACKET, std::bind(&DefaultParser::parse_list_literal, this));
    register_prefix(TokenType::AT, std::bind(&DefaultParser::parse_variable_deref, this));

    register_infix(TokenType::DOT, std::bind(&DefaultParser::parse_dot, this, std::placeholders::_1), static_cast<int>(Precedence::DOT));
    register_infix(TokenType::PLUS, std::bind(&DefaultParser::parse_binary_expression, this, std::placeholders::_1), static_cast<int>(Precedence::SUM));
    // Support indexing
    register_infix(TokenType::LBRACKET, [this](std::shared_ptr<ASTNode> left) {
        eat(TokenType::LBRACKET);
        auto index = parse_expression(static_cast<int>(Precedence::LOWEST));
        eat(TokenType::RBRACKET);
        return std::make_shared<IndexExpression>(left, index);
    }, static_cast<int>(Precedence::INDEX));

    precedences[TokenType::PLUS] = static_cast<int>(Precedence::SUM);
    precedences[TokenType::DOT] = static_cast<int>(Precedence::DOT);
    precedences[TokenType::LPAREN] = static_cast<int>(Precedence::CALL);
    precedences[TokenType::LBRACKET] = static_cast<int>(Precedence::INDEX);
}

void DefaultParser::register_prefix(TokenType type, std::function<std::shared_ptr<ASTNode>()> fn) {
    prefix_parse_fns[type] = fn;
}

void DefaultParser::register_infix(TokenType type, std::function<std::shared_ptr<ASTNode>(std::shared_ptr<ASTNode>)> fn, int precedence) {
    infix_parse_fns[type] = fn;
    precedences[type] = precedence;
}

void DefaultParser::register_token_handler(const std::string& keyword, std::function<std::shared_ptr<ASTNode>(Parser&)> fn) {
    token_handlers[keyword] = fn;
}

Token<std::string> DefaultParser::eat(TokenType type) {
    if (current_token.type == type) {
        Token<std::string> prev = current_token;
        current_token = lexer->get_next_token();
        return prev;
    }
    std::cerr << "Expected token type " << (int)type << " but got " << (int)current_token.type << " at line " << current_token.line << std::endl;
    // For simplicity, just return current and advance, or throw
    Token<std::string> prev = current_token;
    current_token = lexer->get_next_token();
    return prev;
}

TokenType DefaultParser::peek_type() {
    return current_token.type;
}

std::shared_ptr<Program> DefaultParser::parse_program() {
    auto program = std::make_shared<Program>();
    while (current_token.type != TokenType::EOF_TOKEN) {
        auto stmt = parse_statement();
        if (stmt) {
            program->statements.push_back(stmt);
        } else {
            // Error recovery or skip
            current_token = lexer->get_next_token();
        }
    }
    return program;
}

std::shared_ptr<ASTNode> DefaultParser::parse_statement() {
    return parse_expression(static_cast<int>(Precedence::LOWEST));
}

std::shared_ptr<ASTNode> DefaultParser::parse_expression(int precedence) {
    auto prefix = prefix_parse_fns[current_token.type];

    // Check if it's an Identifier that has a special handler (like FOR)
    if (current_token.type == TokenType::IDENTIFIER && token_handlers.count(current_token.value)) {
        auto handler = token_handlers[current_token.value];
        return handler(*this);
    }

    if (!prefix) {
        // std::cerr << "No prefix parse function for " << (int)current_token.type << std::endl;
        return nullptr;
    }
    auto left = prefix();

    while (current_token.type != TokenType::EOF_TOKEN && precedence < (precedences.count(current_token.type) ? precedences[current_token.type] : 0)) {
        auto infix = infix_parse_fns[current_token.type];
        if (!infix) {
            return left;
        }
        left = infix(left);
    }
    return left;
}

std::shared_ptr<ASTNode> DefaultParser::parse_identifier() {
    // Check if we have a special token handler (plugin)
    if (token_handlers.count(current_token.value)) {
         auto handler = token_handlers[current_token.value];
         // eat the keyword inside the handler? Or before?
         // Usually Pratt parsers consume the token in the prefix function.
         // But here we are dispatching based on identifier value.
         return handler(*this);
    }

    auto token = eat(TokenType::IDENTIFIER);
    auto node = std::make_shared<Identifier>(token.value);

    // Function Call?
    if (current_token.type == TokenType::LPAREN) {
        eat(TokenType::LPAREN);
        std::vector<std::shared_ptr<ASTNode>> args;
        if (current_token.type != TokenType::RPAREN) {
            args.push_back(parse_expression(static_cast<int>(Precedence::LOWEST)));
            while (current_token.type == TokenType::COMMA) {
                eat(TokenType::COMMA);
                args.push_back(parse_expression(static_cast<int>(Precedence::LOWEST)));
            }
        }
        eat(TokenType::RPAREN);
        return std::make_shared<FunctionCall>(node, args);
    }

    return node;
}

std::shared_ptr<ASTNode> DefaultParser::parse_literal() {
    if (current_token.type == TokenType::STRING) {
        return std::make_shared<Literal>(eat(TokenType::STRING).value);
    }
    if (current_token.type == TokenType::NUMBER) {
        return std::make_shared<Literal>(std::stoi(eat(TokenType::NUMBER).value));
    }
    if (current_token.type == TokenType::BOOLEAN) {
        bool val = (eat(TokenType::BOOLEAN).value == "TRUE");
        return std::make_shared<Literal>(val);
    }
    if (current_token.type == TokenType::NULL_TYPE) {
        eat(TokenType::NULL_TYPE);
        return std::make_shared<Literal>();
    }
    return nullptr;
}

std::shared_ptr<ASTNode> DefaultParser::parse_grouped_expression() {
    eat(TokenType::LPAREN);
    auto exp = parse_expression(static_cast<int>(Precedence::LOWEST));
    eat(TokenType::RPAREN);
    return exp;
}

std::shared_ptr<ASTNode> DefaultParser::parse_list_literal() {
    eat(TokenType::LBRACKET);
    std::vector<std::shared_ptr<ASTNode>> elements;
    if (current_token.type != TokenType::RBRACKET) {
        elements.push_back(parse_expression(static_cast<int>(Precedence::LOWEST)));
        while (current_token.type == TokenType::COMMA) {
            eat(TokenType::COMMA);
            elements.push_back(parse_expression(static_cast<int>(Precedence::LOWEST)));
        }
    }
    eat(TokenType::RBRACKET);

    // We can represent list as a function call ARRAY(...)
    auto name = std::make_shared<Identifier>("ARRAY");
    return std::make_shared<FunctionCall>(name, elements);
}

std::shared_ptr<ASTNode> DefaultParser::parse_variable_deref() {
    eat(TokenType::AT);
    auto target = parse_expression(static_cast<int>(Precedence::PREFIX));
    return std::make_shared<VariableDeref>(target);
}

std::shared_ptr<ASTNode> DefaultParser::parse_dot(std::shared_ptr<ASTNode> left) {
    eat(TokenType::DOT);
    Token<std::string> id_token = eat(TokenType::IDENTIFIER); // Property name must be identifier
    auto prop = std::make_shared<Identifier>(id_token.value);
    return std::make_shared<PropertyAccess>(left, prop);
}

std::shared_ptr<ASTNode> DefaultParser::parse_binary_expression(std::shared_ptr<ASTNode> left) {
    TokenType op = current_token.type;
    int prec = precedences[op];
    eat(op);
    auto right = parse_expression(prec);
    return std::make_shared<BinaryExpression>(left, op, right);
}

} // namespace dsl
