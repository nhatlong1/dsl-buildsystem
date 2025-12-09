#include "plugin.hpp"
#include "types.hpp"
#include "interfaces.hpp"
#include "value.hpp"
#include <iostream>
#include <memory>

namespace dsl {

struct ForLoopNode : public ASTNode {
    std::string var_name;
    std::shared_ptr<ASTNode> items;
    std::shared_ptr<ASTNode> body;

    ForLoopNode(std::string v, std::shared_ptr<ASTNode> i, std::shared_ptr<ASTNode> b)
        : var_name(std::move(v)), items(std::move(i)), body(std::move(b)) {}

    void* execute(void* interpreter_ptr) override {
        Interpreter* interpreter = static_cast<Interpreter*>(interpreter_ptr);

        Value items_val = interpreter->visit(items.get());
        if (!items_val.is_list()) {
             std::cerr << "FOR loop expects a list, got " << items_val.as_string() << std::endl;
             return new Value();
        }

        auto list = items_val.get<std::vector<Value>>();
        for (const auto& val : list) {
            interpreter->get_context().set(var_name, val);
            interpreter->visit(body.get());
        }
        return new Value();
    }
};

std::shared_ptr<ASTNode> parse_for(Parser& parser) {
    parser.eat(TokenType::IDENTIFIER); // FOR
    parser.eat(TokenType::LPAREN);

    auto var_token = parser.eat(TokenType::IDENTIFIER);
    std::string var_name = var_token.value;

    parser.eat(TokenType::COMMA);
    auto items = parser.parse_expression(static_cast<int>(Precedence::LOWEST));

    parser.eat(TokenType::COMMA);
    auto body = parser.parse_expression(static_cast<int>(Precedence::LOWEST));

    parser.eat(TokenType::RPAREN);

    return std::make_shared<ForLoopNode>(var_name, items, body);
}

extern "C" void register_plugin(Parser& parser, Context& /* context */) {
    parser.register_token_handler("FOR", parse_for);
}

}
