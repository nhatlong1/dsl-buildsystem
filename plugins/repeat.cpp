#include "plugin.hpp"
#include "types.hpp"
#include "interfaces.hpp"
#include "value.hpp"
#include <iostream>
#include <memory>

namespace dsl {

struct RepeatNode : public ASTNode {
    int count;
    std::shared_ptr<ASTNode> body;

    RepeatNode(int c, std::shared_ptr<ASTNode> b) : count(c), body(std::move(b)) {}

    std::string node_name() const override { return "RepeatNode(" + std::to_string(count) + ")"; }
    std::vector<std::shared_ptr<ASTNode>> get_children() const override { return {body}; }

    void* execute(void* interpreter_ptr) override {
        Interpreter* interpreter = static_cast<Interpreter*>(interpreter_ptr);
        for (int i = 0; i < count; ++i) {
            interpreter->visit(body.get());
        }
        return new Value();
    }
};

std::shared_ptr<ASTNode> parse_repeat(Parser& parser) {
    parser.eat(TokenType::IDENTIFIER); // REPEAT
    parser.eat(TokenType::LPAREN);

    auto count_token = parser.eat(TokenType::NUMBER);
    int count = std::stoi(count_token.value);

    parser.eat(TokenType::COMMA);
    auto body = parser.parse_expression(static_cast<int>(Precedence::LOWEST));

    parser.eat(TokenType::RPAREN);

    return std::make_shared<RepeatNode>(count, body);
}

extern "C" void register_plugin(dsl::Parser& parser, dsl::Context& /* context */) {
    parser.register_token_handler("REPEAT", parse_repeat);
}

}
