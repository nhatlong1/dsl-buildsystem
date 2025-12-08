#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <memory>
#include "lexer.hpp"
#include "parser.hpp"
#include "interpreter.hpp"

void print_help() {
    std::cout << "Usage: builder [options] <file.mybuild>" << std::endl;
    std::cout << "Options:" << std::endl;
    std::cout << "  --dry-run      Print execution commands without running them" << std::endl;
    std::cout << "  --parse-only   Print AST and exit" << std::endl;
    std::cout << "  --help         Show this help message" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        print_help();
        return 1;
    }

    std::string filename;
    bool dry_run = false;
    bool parse_only = false;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--dry-run") {
            dry_run = true;
        } else if (arg == "--parse-only") {
            parse_only = true;
        } else if (arg == "--help") {
            print_help();
            return 0;
        } else if (arg[0] == '-') {
            std::cerr << "Unknown option: " << arg << std::endl;
            return 1;
        } else {
            filename = arg;
        }
    }

    if (filename.empty()) {
        std::cerr << "No input file specified." << std::endl;
        return 1;
    }

    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Could not open file: " << filename << std::endl;
        return 1;
    }

    std::string source_code((std::istreambuf_iterator<char>(file)),
                             std::istreambuf_iterator<char>());
    file.close();

    // Pipeline
    try {
        auto lexer = std::make_shared<dsl::Lexer>(source_code);
        dsl::Parser parser(lexer);
        auto program = parser.parse_program();

        if (parse_only) {
            std::cout << "Program parsed successfully." << std::endl;
            // (Pretty print implementation skipped for MVP)
            return 0;
        }

        dsl::Interpreter interpreter(dry_run);
        interpreter.visit(program.get());

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
