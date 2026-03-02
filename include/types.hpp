#pragma once

#include <string>
#include <vector>
#include <variant>
#include <memory>
#include <iostream>
#include <algorithm>
#include <regex>

namespace dsl {

enum class TokenType {
    IDENTIFIER,
    STRING,
    NUMBER,
    BOOLEAN,
    NULL_TYPE,
    LPAREN,
    RPAREN,
    COMMA,
    DOT,
    AT,
    STAR,
    LBRACE,
    RBRACE,
    LBRACKET,
    RBRACKET,
    PIPE_GT,
    PLUS, // Added PLUS
    EOF_TOKEN
};

enum class SymbolType {
    VARIABLE,
    FLAGS,
    EXECUTABLE,
    MACRO
};

enum class Precedence {
    LOWEST = 0,
    SUM = 20, // Added SUM
    PIPELINE = 10,
    DOT = 30,
    PREFIX = 40,
    CALL = 50
};

template <typename T>
struct Token {
    TokenType type;
    T value;
    int line;
    int column;
};

// --- AST Nodes ---

class Interpreter; // Forward declaration
class Value; // Forward declaration

struct ASTNode {
    virtual ~ASTNode() = default;
    virtual void* execute(void* interpreter) { return nullptr; }
    virtual std::string node_name() const { return "ASTNode"; }
    virtual std::vector<std::shared_ptr<ASTNode>> get_children() const { return {}; }
};

void print_ast(const std::shared_ptr<ASTNode>& node, const std::string& prefix = "", bool is_last = true);

struct Identifier : public ASTNode {
    std::string name;
    explicit Identifier(std::string n) : name(std::move(n)) {}
    std::string node_name() const override { return "Identifier(" + name + ")"; }
};

struct Literal : public ASTNode {
    std::string string_value;
    int int_value = 0;
    bool bool_value = false;
    bool is_null = false;

    enum Type { STR, INT, BOOL, NONE } type;

    Literal(std::string s) : string_value(std::move(s)), type(STR) {}
    Literal(int i) : int_value(i), type(INT) {}
    Literal(bool b) : bool_value(b), type(BOOL) {}
    Literal() : is_null(true), type(NONE) {}

    std::string node_name() const override {
        switch (type) {
            case STR: return "Literal(\"" + string_value + "\")";
            case INT: return "Literal(" + std::to_string(int_value) + ")";
            case BOOL: return "Literal(" + std::string(bool_value ? "true" : "false") + ")";
            case NONE: return "Literal(null)";
        }
        return "Literal";
    }
};

struct Program : public ASTNode {
    std::vector<std::shared_ptr<ASTNode>> statements;
    std::string node_name() const override { return "Program"; }
    std::vector<std::shared_ptr<ASTNode>> get_children() const override { return statements; }
};

struct FunctionCall : public ASTNode {
    std::shared_ptr<Identifier> name;
    std::vector<std::shared_ptr<ASTNode>> args;
    FunctionCall(std::shared_ptr<Identifier> n, std::vector<std::shared_ptr<ASTNode>> a)
        : name(std::move(n)), args(std::move(a)) {}
    std::string node_name() const override { return "FunctionCall"; }
    std::vector<std::shared_ptr<ASTNode>> get_children() const override {
        std::vector<std::shared_ptr<ASTNode>> children;
        children.push_back(name);
        children.insert(children.end(), args.begin(), args.end());
        return children;
    }
};

struct VariableDeref : public ASTNode {
    std::shared_ptr<ASTNode> target;
    explicit VariableDeref(std::shared_ptr<ASTNode> t) : target(std::move(t)) {}
    std::string node_name() const override { return "VariableDeref"; }
    std::vector<std::shared_ptr<ASTNode>> get_children() const override { return {target}; }
};

struct PropertyAccess : public ASTNode {
    std::shared_ptr<ASTNode> target;
    std::shared_ptr<Identifier> property_name;
    PropertyAccess(std::shared_ptr<ASTNode> t, std::shared_ptr<Identifier> p)
        : target(std::move(t)), property_name(std::move(p)) {}
    std::string node_name() const override { return "PropertyAccess"; }
    std::vector<std::shared_ptr<ASTNode>> get_children() const override { return {target, property_name}; }
};

struct BinaryExpression : public ASTNode {
    std::shared_ptr<ASTNode> left;
    TokenType op;
    std::shared_ptr<ASTNode> right;
    BinaryExpression(std::shared_ptr<ASTNode> l, TokenType o, std::shared_ptr<ASTNode> r)
        : left(std::move(l)), op(o), right(std::move(r)) {}
    std::string node_name() const override {
        std::string op_str;
        switch (op) {
            case TokenType::PLUS: op_str = "+"; break;
            case TokenType::PIPE_GT: op_str = "|>"; break;
            case TokenType::DOT: op_str = "."; break;
            default: op_str = "op(" + std::to_string(static_cast<int>(op)) + ")"; break;
        }
        return "BinaryExpression(" + op_str + ")";
    }
    std::vector<std::shared_ptr<ASTNode>> get_children() const override { return {left, right}; }
};

// --- Runtime Types ---

struct Flag {
    std::string name;
    std::string template_str;
    int arity;

    Flag(std::string n, std::string t) : name(std::move(n)), template_str(std::move(t)) {
        calculate_arity();
    }

    void calculate_arity() {
        arity = 0;
        std::regex re(R"(\$(\d+))");
        auto words_begin = std::sregex_iterator(template_str.begin(), template_str.end(), re);
        auto words_end = std::sregex_iterator();

        for (std::sregex_iterator i = words_begin; i != words_end; ++i) {
            std::smatch match = *i;
            int idx = std::stoi(match[1].str());
            if (idx > arity) arity = idx;
        }
    }

    std::string apply(const std::vector<std::string>& args) const {
        std::string result = template_str;
        for (size_t i = 0; i < args.size(); ++i) {
             std::string placeholder = "$" + std::to_string(i + 1);
             size_t pos = 0;
             while ((pos = result.find(placeholder, pos)) != std::string::npos) {
                 result.replace(pos, placeholder.length(), args[i]);
                 pos += args[i].length();
             }
        }
        return result;
    }
};

struct Executable {
    std::string name;
    std::string description;
    std::string source;
    std::string path;

    Executable(std::string n, std::string d, std::string s, std::string p)
        : name(std::move(n)), description(std::move(d)), source(std::move(s)), path(std::move(p)) {}
};

struct Object {
    virtual ~Object() = default;
    virtual Value get_property(const std::string& name) = 0;
};

} // namespace dsl
