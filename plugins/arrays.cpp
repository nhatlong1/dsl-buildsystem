#include "plugin.hpp"
#include "types.hpp"
#include "protocols.hpp"
#include "value.hpp"
#include <iostream>
#include <memory>
#include <vector>

namespace dsl {

// Array Literal Node
struct ArrayNode : public ASTNode {
    std::vector<std::shared_ptr<ASTNode>> items;

    explicit ArrayNode(std::vector<std::shared_ptr<ASTNode>> i) : items(std::move(i)) {}

    void* execute(void* interpreter_ptr) override {
        IInterpreter* interpreter = static_cast<IInterpreter*>(interpreter_ptr);
        std::vector<Value> evaluated_items;
        for (const auto& item : items) {
            evaluated_items.push_back(interpreter->visit(item.get()));
        }
        return new Value(evaluated_items);
    }
};

// Index Access Node: target[index]
struct IndexNode : public ASTNode {
    std::shared_ptr<ASTNode> target;
    std::shared_ptr<ASTNode> index;

    IndexNode(std::shared_ptr<ASTNode> t, std::shared_ptr<ASTNode> i) : target(std::move(t)), index(std::move(i)) {}

    void* execute(void* interpreter_ptr) override {
        IInterpreter* interpreter = static_cast<IInterpreter*>(interpreter_ptr);
        Value target_val = interpreter->visit(target.get());
        Value index_val = interpreter->visit(index.get());

        if (target_val.is_list()) {
            const auto& list = target_val.get<std::vector<Value>>();
            if (index_val.is_int()) {
                int idx = index_val.get<int>();
                if (idx >= 0 && idx < (int)list.size()) {
                    return new Value(list[idx]);
                } else {
                    std::cerr << "Index out of bounds: " << idx << std::endl;
                }
            } else {
                std::cerr << "Array index must be an integer." << std::endl;
            }
        } else {
            std::cerr << "Indexing requires a list target." << std::endl;
        }
        return new Value();
    }
};

// Parse [1, 2]
std::shared_ptr<ASTNode> parse_array_literal(IParser& parser) {
    parser.eat(TokenType::LBRACKET);

    std::vector<std::shared_ptr<ASTNode>> items;

    if (parser.peek_type() != TokenType::RBRACKET) {
        items.push_back(parser.parse_expression(static_cast<int>(Precedence::LOWEST)));
        while (parser.peek_type() == TokenType::COMMA) {
            parser.eat(TokenType::COMMA);
            items.push_back(parser.parse_expression(static_cast<int>(Precedence::LOWEST)));
        }
    }

    parser.eat(TokenType::RBRACKET);
    return std::make_shared<ArrayNode>(items);
}

// Parse target[index]
std::shared_ptr<ASTNode> parse_index_expression(IParser& parser, std::shared_ptr<ASTNode> left) {
    parser.eat(TokenType::LBRACKET);
    auto index = parser.parse_expression(static_cast<int>(Precedence::LOWEST));
    parser.eat(TokenType::RBRACKET);
    return std::make_shared<IndexNode>(left, index);
}

extern "C" void register_plugin(dsl::IParser& parser, dsl::IContext& /* context */) {
    // Prefix [
    parser.register_prefix(TokenType::LBRACKET, [&parser]() {
        return parse_array_literal(parser);
    });

    // Infix [ (Index)
    // Precedence should be high (CALL=50). Let's use 60 or match CALL.
    // Python usually has Index same as Call/Dot.
    parser.register_infix(TokenType::LBRACKET, [&parser](std::shared_ptr<ASTNode> left) {
        return parse_index_expression(parser, left);
    }, 60);
}

}
