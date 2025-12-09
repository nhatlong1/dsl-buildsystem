#pragma once

#include "protocols.hpp"
#include <string>

// Standard entry point name for plugins
#define PLUGIN_ENTRY_POINT "register_plugin"

typedef void (*RegisterPluginFn)(dsl::IParser&, dsl::IContext&);
