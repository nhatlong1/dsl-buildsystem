#include "plugin.hpp"
#include "types.hpp"
#include "interfaces.hpp"
#include "value.hpp"

namespace dsl {

std::shared_ptr<ASTNode> parse_for_loop(Parser& parser) {
    // FOR(var, array, stmt1 stmt2 ...)
    parser.eat(TokenType::LPAREN);

    // 1. Variable Name
    Token<std::string> var_token = parser.eat(TokenType::IDENTIFIER);
    std::string var_name = var_token.value;

    parser.eat(TokenType::COMMA);

    // 2. Array Expression
    std::shared_ptr<ASTNode> array_expr = parser.parse_expression(static_cast<int>(Precedence::LOWEST));

    // 3. Body Statements
    // The syntax in build.mybuild is: FOR(item, list, STMT STMT STMT)
    // There are NO commas between statements.
    // And it ends with RPAREN.
    // So we parse expressions/statements until RPAREN.

    std::vector<std::shared_ptr<ASTNode>> body;

    // If there is a comma after array expr, consume it.
    // But check if next token is NOT RPAREN.
    if (parser.peek_type() == TokenType::COMMA) {
        parser.eat(TokenType::COMMA);
    }

    while (parser.peek_type() != TokenType::RPAREN && parser.peek_type() != TokenType::EOF_TOKEN) {
        // Parse expression/statement
        // Note: Standard parser expects statements to be just expressions.
        auto stmt = parser.parse_expression(static_cast<int>(Precedence::LOWEST));
        if (stmt) {
            body.push_back(stmt);
        } else {
            // Should not happen if parser works correctly?
            break;
        }
    }

    parser.eat(TokenType::RPAREN);

    return std::make_shared<ForLoopNode>(var_name, array_expr, body);
}

extern "C" void register_plugin(dsl::Parser& parser, dsl::Context& /* context */) {
    // Register token handler for "FOR" identifier
    parser.register_token_handler("FOR", parse_for_loop);
}

}
