#include "interpreter.hpp"
#include "parser.hpp"
#include "plugin.hpp"
#include <iostream>
#include <string>

#ifdef _WIN32
    #include <windows.h>
    typedef HMODULE LibHandle;
#else
    #include <dlfcn.h>
    typedef void* LibHandle;
#endif

namespace dsl {

LibHandle load_library(const std::string& path) {
#ifdef _WIN32
    return LoadLibrary(path.c_str());
#else
    return dlopen(path.c_str(), RTLD_NOW | RTLD_GLOBAL);
#endif
}

void* get_function(LibHandle handle, const std::string& name) {
#ifdef _WIN32
    return (void*)GetProcAddress(handle, name.c_str());
#else
    return dlsym(handle, name.c_str());
#endif
}

std::string get_error() {
#ifdef _WIN32
    return "Windows Error " + std::to_string(GetLastError());
#else
    const char* err = dlerror();
    return err ? std::string(err) : "Unknown Error";
#endif
}

void load_plugin(const std::string& path, IParser& parser, IContext& context) {
    LibHandle handle = load_library(path);
    if (!handle) {
        std::cerr << "Failed to load plugin " << path << ": " << get_error() << std::endl;
        return;
    }

    auto reg_fn = (RegisterPluginFn)get_function(handle, PLUGIN_ENTRY_POINT);
    if (!reg_fn) {
        std::cerr << "Failed to find entry point " << PLUGIN_ENTRY_POINT << " in " << path << ": " << get_error() << std::endl;
        return;
    }

    reg_fn(parser, context);
}

} // namespace dsl
