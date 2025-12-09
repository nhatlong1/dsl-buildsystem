#!/bin/bash
set -e

echo "Bootstrapping builder..."

mkdir -p bin

OS="linux"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    OS="windows"
    EXT="dll"
    LIB_FLAGS="-shared"
    DL_FLAG=""
    FPIC=""
else
    EXT="so"
    LIB_FLAGS="-shared"
    DL_FLAG="-ldl"
    FPIC="-fPIC"
fi

echo "Building Core..."
g++ -std=c++17 -Iinclude $FPIC \
    src/lexer.cpp \
    src/parser.cpp \
    src/interpreter.cpp \
    src/plugin_loader.cpp \
    src/main.cpp \
    -o bin/builder $DL_FLAG

echo "Building Plugins..."
mkdir -p bin/plugins bin/modules

build_plugin() {
    SRC=$1
    OUT=$2
    g++ -std=c++17 -Iinclude $FPIC $LIB_FLAGS \
        $SRC \
        -o $OUT
}

if [[ "$OS" != "windows" ]]; then
    g++ -std=c++17 -Iinclude $FPIC -rdynamic \
        src/lexer.cpp \
        src/parser.cpp \
        src/interpreter.cpp \
        src/plugin_loader.cpp \
        src/main.cpp \
        -o bin/builder $DL_FLAG
fi

build_plugin plugins/loop.cpp bin/plugins/loop.$EXT
build_plugin plugins/arrays.cpp bin/plugins/arrays.$EXT
build_plugin plugins/repeat.cpp bin/plugins/repeat.$EXT
build_plugin modules/filestat.cpp bin/modules/filestat.$EXT
build_plugin modules/buildcache.cpp bin/modules/buildcache.$EXT

echo "Build complete. Executable is at bin/builder"
