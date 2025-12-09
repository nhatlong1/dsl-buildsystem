#include "lexer.hpp"
#include <cctype>
#include <iostream>

namespace dsl {

DefaultLexer::DefaultLexer(std::string input) : text(std::move(input)), pos(0), current_char(0), line(1), column(1) {
    if (!text.empty()) {
        current_char = text[0];
    } else {
        current_char = '\0';
    }
}

void DefaultLexer::advance() {
    pos++;
    if (current_char == '\n') {
        line++;
        column = 0;
    } else {
        column++;
    }

    if (pos < text.length()) {
        current_char = text[pos];
    } else {
        current_char = '\0';
    }
}

char DefaultLexer::peek() {
    if (pos + 1 < text.length()) {
        return text[pos + 1];
    }
    return '\0';
}

void DefaultLexer::skip_whitespace() {
    while (current_char != '\0' && isspace(static_cast<unsigned char>(current_char))) {
        advance();
    }
}

Token<std::string> DefaultLexer::make_identifier() {
    std::string result;
    int start_col = column;
    while (current_char != '\0' && (isalnum(static_cast<unsigned char>(current_char)) || current_char == '_' || current_char == '-')) {
        result += current_char;
        advance();
    }

    TokenType type = TokenType::IDENTIFIER;
    if (result == "TRUE") type = TokenType::BOOLEAN;
    else if (result == "FALSE") type = TokenType::BOOLEAN;
    else if (result == "NULL") type = TokenType::NULL_TYPE;

    return {type, result, line, start_col};
}

Token<std::string> DefaultLexer::make_string() {
    int start_col = column;
    char quote_type = current_char;
    advance(); // Skip opening quote
    std::string result;

    while (current_char != '\0' && current_char != quote_type) {
        if (current_char == '\\' && peek() == quote_type) {
            advance(); // Skip backslash
            result += current_char;
            advance();
        } else {
            result += current_char;
            advance();
        }
    }

    if (current_char == quote_type) {
        advance(); // Skip closing quote
    } else {
        std::cerr << "Unterminated string at line " << line << std::endl;
    }

    return {TokenType::STRING, result, line, start_col};
}

Token<std::string> DefaultLexer::make_number() {
    std::string result;
    int start_col = column;
    while (current_char != '\0' && isdigit(static_cast<unsigned char>(current_char))) {
        result += current_char;
        advance();
    }
    return {TokenType::NUMBER, result, line, start_col};
}

Token<std::string> DefaultLexer::get_next_token() {
    while (current_char != '\0') {
        if (isspace(static_cast<unsigned char>(current_char))) {
            skip_whitespace();
            continue;
        }

        if (current_char == '#') {
            while (current_char != '\0' && current_char != '\n') {
                advance();
            }
            continue;
        }

        if (isalpha(static_cast<unsigned char>(current_char)) || current_char == '_') {
            return make_identifier();
        }

        if (current_char == '"' || current_char == '\'') {
            return make_string();
        }

        if (isdigit(static_cast<unsigned char>(current_char))) {
            return make_number();
        }

        int start_col = column;

        if (current_char == '|' && peek() == '>') {
             advance(); advance();
             return {TokenType::PIPE_GT, "|>", line, start_col};
        }

        TokenType type;
        std::string val(1, current_char);
        bool found = true;

        switch (current_char) {
            case '(': type = TokenType::LPAREN; break;
            case ')': type = TokenType::RPAREN; break;
            case '{': type = TokenType::LBRACE; break;
            case '}': type = TokenType::RBRACE; break;
            case '[': type = TokenType::LBRACKET; break;
            case ']': type = TokenType::RBRACKET; break;
            case ',': type = TokenType::COMMA; break;
            case '.': type = TokenType::DOT; break;
            case '@': type = TokenType::AT; break;
            case '*': type = TokenType::STAR; break;
            case '+': type = TokenType::PLUS; break; // Added PLUS
            default: found = false; break;
        }

        if (found) {
            advance();
            return {type, val, line, start_col};
        }

        std::cerr << "Unknown character: " << current_char << " at line " << line << std::endl;
        advance();
    }

    return {TokenType::EOF_TOKEN, "", line, column};
}

} // namespace dsl
