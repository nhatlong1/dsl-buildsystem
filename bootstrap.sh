#!/bin/bash
set -e

# Bootstrap script to build the DSL build system using raw g++ commands

echo "Bootstrapping builder..."

# Ensure output directory exists
mkdir -p bin

# Compile commands
# Utilizing C++17
g++ -std=c++17 -Iinclude \
    src/lexer.cpp \
    src/parser.cpp \
    src/interpreter.cpp \
    src/main.cpp \
    -o bin/builder

echo "Build complete. Executable is at bin/builder"
