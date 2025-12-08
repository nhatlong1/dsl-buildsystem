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

struct ASTNode {
    virtual ~ASTNode() = default;
};

struct Identifier : public ASTNode {
    std::string name;
    explicit Identifier(std::string n) : name(std::move(n)) {}
};

struct Literal : public ASTNode {
    // Value is handled by the wrapper/visitor, but here we store the raw string repr or rely on the Token
    // For simplicity, let's store the raw parsed value in a variant-like structure or just strings/ints
    // But since this is AST, we might want to store specific types.
    // For now, let's keep it generic or string-based for the parser's perspective.
    std::string string_value;
    int int_value = 0;
    bool bool_value = false;
    bool is_null = false;

    // Type tracking
    enum Type { STR, INT, BOOL, NONE } type;

    Literal(std::string s) : string_value(std::move(s)), type(STR) {}
    Literal(int i) : int_value(i), type(INT) {}
    Literal(bool b) : bool_value(b), type(BOOL) {}
    Literal() : is_null(true), type(NONE) {}
};

struct Program : public ASTNode {
    std::vector<std::shared_ptr<ASTNode>> statements;
};

struct FunctionCall : public ASTNode {
    std::shared_ptr<Identifier> name;
    std::vector<std::shared_ptr<ASTNode>> args;
    FunctionCall(std::shared_ptr<Identifier> n, std::vector<std::shared_ptr<ASTNode>> a)
        : name(std::move(n)), args(std::move(a)) {}
};

struct VariableDeref : public ASTNode {
    std::shared_ptr<ASTNode> target;
    explicit VariableDeref(std::shared_ptr<ASTNode> t) : target(std::move(t)) {}
};

struct PropertyAccess : public ASTNode {
    std::shared_ptr<ASTNode> target;
    std::shared_ptr<Identifier> property_name;
    PropertyAccess(std::shared_ptr<ASTNode> t, std::shared_ptr<Identifier> p)
        : target(std::move(t)), property_name(std::move(p)) {}
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
    std::string path; // Optional in Python, strictly string here (empty if none)

    Executable(std::string n, std::string d, std::string s, std::string p)
        : name(std::move(n)), description(std::move(d)), source(std::move(s)), path(std::move(p)) {}
};

} // namespace dsl
