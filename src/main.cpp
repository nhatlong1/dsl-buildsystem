#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <memory>
#include <filesystem>
#include "lexer.hpp"
#include "parser.hpp"
#include "interpreter.hpp"

// Forward declaration
namespace dsl {
    void load_plugin(const std::string& path, Parser& parser, Context& context);
}

void load_plugins_from_dir(const std::string& dir, dsl::Parser& parser, dsl::Context& context) {
    namespace fs = std::filesystem;
    if (!fs::exists(dir)) return;

    for (const auto& entry : fs::directory_iterator(dir)) {
        if (entry.is_regular_file()) {
            std::string ext = entry.path().extension().string();
            if (ext == ".so" || ext == ".dll") {
                dsl::load_plugin(entry.path().string(), parser, context);
            }
        }
    }
}

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
        auto lexer = std::make_shared<dsl::DefaultLexer>(source_code);
        dsl::DefaultParser parser(lexer);
        dsl::DefaultInterpreter interpreter(dry_run);
        interpreter.attach_parser(&parser);

        load_plugins_from_dir("bin/plugins", parser, interpreter.get_context());
        load_plugins_from_dir("bin/modules", parser, interpreter.get_context());

        auto program = parser.parse_program(parse_only);

        if (parse_only) {
            return 0;
        }

        interpreter.visit(program.get());

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
