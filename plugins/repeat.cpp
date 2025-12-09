#include "plugin.hpp"
#include "types.hpp"
#include "protocols.hpp"
#include "value.hpp"
#include <iostream>
#include <memory>

namespace dsl {

struct RepeatNode : public ASTNode {
    int count;
    std::shared_ptr<ASTNode> body;

    RepeatNode(int c, std::shared_ptr<ASTNode> b) : count(c), body(std::move(b)) {}

    void* execute(void* interpreter_ptr) override {
        IInterpreter* interpreter = static_cast<IInterpreter*>(interpreter_ptr);
        for (int i = 0; i < count; ++i) {
            interpreter->visit(body.get());
        }
        return new Value();
    }
};

std::shared_ptr<ASTNode> parse_repeat(IParser& parser) {
    parser.eat(TokenType::IDENTIFIER); // REPEAT
    parser.eat(TokenType::LPAREN);

    auto count_token = parser.eat(TokenType::NUMBER);
    int count = std::stoi(count_token.value);

    parser.eat(TokenType::COMMA);
    auto body = parser.parse_expression(static_cast<int>(Precedence::LOWEST));

    parser.eat(TokenType::RPAREN);

    return std::make_shared<RepeatNode>(count, body);
}

extern "C" void register_plugin(dsl::IParser& parser, dsl::IContext& /* context */) {
    parser.register_token_handler("REPEAT", parse_repeat);
}

}
