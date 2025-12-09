#pragma once

#include "interfaces.hpp"
#include <string>

namespace dsl {

class DefaultLexer : public Lexer {
public:
    explicit DefaultLexer(std::string input);
    Token<std::string> get_next_token() override;

private:
    std::string text;
    size_t pos;
    char current_char;
    int line;
    int column;

    void advance();
    void skip_whitespace();
    char peek();
    Token<std::string> make_identifier();
    Token<std::string> make_number();
    Token<std::string> make_string();
};

} // namespace dsl
