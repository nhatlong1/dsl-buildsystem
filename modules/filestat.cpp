#include "plugin.hpp"
#include "types.hpp"
#include "interfaces.hpp"
#include "value.hpp"
#include <iostream>
#include <sys/stat.h>
#include <filesystem>
#include <memory>
#include <map>

namespace dsl {

class FileStatObject : public IObject {
    std::string path;
    struct stat stat_buf;
    bool stat_ok;

public:
    explicit FileStatObject(std::string p) : path(std::move(p)) {
        stat_ok = (stat(path.c_str(), &stat_buf) == 0);
    }

    Value get_property(const std::string& name) override {
        if (name == "LASTMODIFIEDDATE") {
            if (stat_ok) {
#ifdef __APPLE__
                return Value((int)stat_buf.st_mtimespec.tv_sec);
#else
                return Value((int)stat_buf.st_mtime);
#endif
            }
            return Value(0);
        }
        return Value();
    }
};

Value func_stat(const std::vector<std::shared_ptr<ASTNode>>& args, IInterpreter& interp) {
    if (args.empty()) return Value();
    auto path = interp.visit(args[0].get()).as_string();
    return Value(std::make_shared<FileStatObject>(path));
}

extern "C" void register_plugin(dsl::IParser& /* parser */, dsl::IContext& context) {
    context.register_function("STAT", func_stat);
}

}
