#include "plugin.hpp"
#include "types.hpp"
#include "interfaces.hpp"
#include "value.hpp"
#include <iostream>
#include <fstream>
#include <filesystem>
#include <memory>
#include <map>
#include <sstream>
#include <chrono>

namespace dsl {

std::string escape_json(const std::string& s) {
    std::string res;
    for (char c : s) {
        if (c == '\\') res += "\\\\";
        else if (c == '"') res += "\\\"";
        else res += c;
    }
    return res;
}

class CacheEntry : public IObject {
    std::map<std::string, Value> data;
public:
    explicit CacheEntry(std::map<std::string, Value> d) : data(std::move(d)) {}

    Value get_property(const std::string& name) override {
        auto it = data.find(name);
        if (it != data.end()) return it->second;
        return Value();
    }
};

class BuildCache {
    std::string cache_file = ".buildcache";
    std::map<std::string, std::map<std::string, Value>> cache;

public:
    BuildCache() {
        load();
    }

    void load() {
        if (!std::filesystem::exists(cache_file)) return;
    }

    void save() {
        std::ofstream f(cache_file);
        f << "{";
        bool first = true;
        for (const auto& [path, entry] : cache) {
            if (!first) f << ",";
            first = false;
            f << "\"" << escape_json(path) << "\": {";
            bool first_prop = true;
            for (const auto& [prop, val] : entry) {
                if (!first_prop) f << ",";
                first_prop = false;
                if (val.is_string()) {
                    f << "\"" << prop << "\": \"" << escape_json(val.as_string()) << "\"";
                } else {
                    f << "\"" << prop << "\": " << val.as_string();
                }
            }
            f << "}";
        }
        f << "}";
    }

    std::map<std::string, Value> get_entry(const std::string& path) {
        return cache[path];
    }

    void update_entry(const std::string& path, int timestamp) {
        cache[path]["LASTMODIFIEDDATE"] = Value(timestamp);
    }
};

static BuildCache global_cache;

Value func_cache(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& interp) {
    if (args.empty()) return Value();
    auto path = interp.visit(args[0].get()).as_string();
    return Value(std::make_shared<CacheEntry>(global_cache.get_entry(path)));
}

Value func_write(const std::vector<std::shared_ptr<ASTNode>>& /* args */, IInterpreter& /* interp */) {
    global_cache.save();
    return Value();
}

Value func_update(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& interp) {
    if (args.empty()) return Value();
    auto path = interp.visit(args[0].get()).as_string();
    if (std::filesystem::exists(path)) {
        auto ftime = std::filesystem::last_write_time(path);
        auto sctp = std::chrono::time_point_cast<std::chrono::system_clock::duration>(ftime - std::filesystem::file_time_type::clock::now() + std::chrono::system_clock::now());
        std::time_t cftime = std::chrono::system_clock::to_time_t(sctp);
        global_cache.update_entry(path, (int)cftime);
    }
    return Value();
}

extern "C" void register_plugin(dsl::IParser& /* parser */, dsl::IContext& context) {
    context.register_function("CACHE", func_cache);
    context.register_function("WRITEBUILDCACHE", func_write);
    context.register_function("UPDATE", func_update);
}

}
