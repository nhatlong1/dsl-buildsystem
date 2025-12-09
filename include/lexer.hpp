#pragma once

#include "protocols.hpp"
#include <string>

namespace dsl {

class Lexer : public ILexer {
private:
    std::string text;
    size_t pos;
    char current_char;
    int line;
    int column;

    void advance();
    char peek();
    void skip_whitespace();
    Token<std::string> make_identifier();
    Token<std::string> make_string();
    Token<std::string> make_number();

public:
    explicit Lexer(std::string input);
    Token<std::string> get_next_token() override;
};

} // namespace dsl
