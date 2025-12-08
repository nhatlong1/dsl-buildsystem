#pragma once

#include "types.hpp"
#include <variant>
#include <vector>
#include <string>
#include <memory>
#include <iostream>

namespace dsl {

// Forward declaration
class Value;

// Using std::variant for dynamic typing
// Monostate represents null/None
using ValueVariant = std::variant<
    std::monostate,
    std::string,
    int,
    bool,
    std::shared_ptr<Flag>,
    std::shared_ptr<Executable>,
    std::vector<Value> // Recursive definition requires wrapper or pointer. std::vector<Value> works if Value is defined.
>;

// Recursive variant definition is tricky in standard C++17 without incomplete type support in vector.
// Typically std::vector<T> allows incomplete T in C++17, so this wrapper class helps.

class Value {
public:
    ValueVariant raw;

    Value() : raw(std::monostate{}) {}
    Value(std::string s) : raw(s) {}
    Value(const char* s) : raw(std::string(s)) {}
    Value(int i) : raw(i) {}
    Value(bool b) : raw(b) {}
    Value(std::shared_ptr<Flag> f) : raw(f) {}
    Value(std::shared_ptr<Executable> e) : raw(e) {}
    Value(std::vector<Value> v) : raw(v) {}

    bool is_null() const { return std::holds_alternative<std::monostate>(raw); }
    bool is_string() const { return std::holds_alternative<std::string>(raw); }
    bool is_int() const { return std::holds_alternative<int>(raw); }
    bool is_bool() const { return std::holds_alternative<bool>(raw); }
    bool is_flag() const { return std::holds_alternative<std::shared_ptr<Flag>>(raw); }
    bool is_executable() const { return std::holds_alternative<std::shared_ptr<Executable>>(raw); }
    bool is_list() const { return std::holds_alternative<std::vector<Value>>(raw); }

    std::string as_string() const {
        if (is_string()) return std::get<std::string>(raw);
        if (is_int()) return std::to_string(std::get<int>(raw));
        if (is_bool()) return std::get<bool>(raw) ? "true" : "false";
        if (is_flag()) return std::get<std::shared_ptr<Flag>>(raw)->name;
        if (is_executable()) return std::get<std::shared_ptr<Executable>>(raw)->name;
        if (is_null()) return "null";
        return "[List]";
    }

    // Explicit getter helper
    template <typename T>
    const T& get() const {
        return std::get<T>(raw);
    }
};

} // namespace dsl
