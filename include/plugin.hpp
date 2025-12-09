#pragma once

#include "interfaces.hpp"
#include <string>

// Standard entry point name for plugins
#define PLUGIN_ENTRY_POINT "register_plugin"

typedef void (*RegisterPluginFn)(dsl::Parser&, dsl::Context&);
