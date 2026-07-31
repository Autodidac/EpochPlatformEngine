# EpochPlatformEngine

`EpochPlatformEngine` is the reusable C++23 process, window, event, and multi-context host for EpochEngine applications and standalone Epoch projects.

It deliberately does **not** own rendering. OpenGL, Vulkan, DirectX, SDL, SFML, Raylib, software rendering, and future renderer implementations stay in their own engine drivers. `EpochPlatformEngine` owns the native operating-system boundary those drivers attach to.

## Current capabilities

- C++23 public API in the `epochengine::platform` namespace
- Static library: `EpochPlatformEngineStatic`
- Shared library: `EpochPlatformEngine`
- Internal console entrypoint archives for static and shared linking
- Internal Windows GUI entrypoint archives for static and shared linking
- No user-written `main()`, `WinMain()`, or `wWinMain()`
- Multiple contexts per platform driver
- Separate owner thread per active driver when supported
- Per-context initialization, frame, shutdown, event, and command callbacks
- Per-context native handle publication
- Parent, child, detached, resize, visibility, title, and close operations
- Built-in headless, Win32, X11, and Cocoa drivers
- Automatic native-driver selection with headless fallback
- CMake presets
- Native Visual Studio solution independent of CMake
- Direct GCC, Clang, and MSVC build scripts independent of CMake
- VS Code build and debug tasks

No EpochEngine package-manager registration is included. EpochEngine or the project manager can add this repository as a selected source/project dependency when the platform library is actually required.

## Architecture

```text
Application executable
    └── internal entrypoint archive
            └── EpochPlatformEngine static or shared library
                    ├── Runtime
                    ├── Win32 driver host thread
                    │      ├── OpenGL context route
                    │      ├── Vulkan context route
                    │      └── detached editor route
                    ├── X11 driver host thread
                    ├── Cocoa main-thread driver host
                    └── Headless driver host thread
```

A driver host owns one native event pump and any number of contexts for that operating-system driver. Different drivers can run concurrently. Context callbacks execute on the driver owner thread, which gives renderer code a stable thread-affinity point for native and graphics-context initialization.

`ContextType` mirrors EpochEngine's existing backend set:

- OpenGL
- SDL
- SFML
- Raylib
- Vulkan
- DirectX
- Software
- Custom
- Noop

The platform library records the renderer type but does not link renderer SDKs.

## Automatic internal entrypoint

The application defines an application factory, not `main()`:

```cpp
#include <epochplatformengine/epoch_platform_engine.hpp>

class Game final : public epochengine::platform::IApplication
{
public:
    epochengine::platform::Status on_start(
        epochengine::platform::Runtime& runtime,
        const epochengine::platform::ApplicationLaunchInfo&) override
    {
        auto context = runtime.create_context({
            .driver = epochengine::platform::DriverKind::automatic,
            .type = epochengine::platform::ContextType::vulkan,
            .window = {
                .title = "Game",
                .width = 1280,
                .height = 720
            },
            .route = "game.primary"
        });

        if (!context)
            return std::unexpected(context.error());
        return {};
    }

    bool on_frame(
        epochengine::platform::Runtime& runtime,
        std::chrono::nanoseconds) override
    {
        return runtime.active_context_count() != 0;
    }

    void on_stop(epochengine::platform::Runtime&) noexcept override {}
};

namespace
{
    epochengine::platform::IApplication* EPOCH_PLATFORM_CALL create_app(
        const epochengine::platform::ApplicationLaunchInfo&) noexcept
    {
        return new (std::nothrow) Game();
    }

    void EPOCH_PLATFORM_CALL destroy_app(
        epochengine::platform::IApplication* app) noexcept
    {
        delete app;
    }
}

extern "C" void EPOCH_PLATFORM_CALL epoch_platform_application_factory(
    epochengine::platform::ApplicationFactory* factory) noexcept
{
    if (factory == nullptr)
        return;

    *factory = {
        .create = &create_app,
        .destroy = &destroy_app
    };
}
```

The executable links one entrypoint archive:

- `EpochPlatformEntrypointConsoleStatic`
- `EpochPlatformEntrypointConsoleShared`
- `EpochPlatformEntrypointWindowedStatic` on Windows
- `EpochPlatformEntrypointWindowedShared` on Windows

The windowed entrypoint normalizes the UTF-16 Windows command line into UTF-8 arguments before creating the application.

## Multi-context renderer attachment

Renderer initialization belongs in the context callback. The callback receives the native handles on the correct driver thread:

```cpp
epochengine::platform::ContextCallbacks callbacks{
    .initialize = [](const epochengine::platform::ContextSnapshot& context)
    {
        // Win32: context.native.window and context.native.device_context
        // X11:   context.native.display and context.native.value
        // Cocoa: context.native.window
        // Create the selected renderer surface/context here.
        return epochengine::platform::Status{};
    },
    .frame = [](const epochengine::platform::ContextSnapshot& context,
                std::chrono::nanoseconds delta)
    {
        // Render this route on its owning driver thread.
        return true;
    },
    .shutdown = [](const epochengine::platform::ContextSnapshot& context)
    {
        // Tear down renderer resources before the native window is destroyed.
    }
};
```

Commands can be routed to a specific owner thread:

```cpp
runtime.dispatch(context_id, [](const auto& context)
{
    // Runs on the owning platform-driver thread.
});
```

Dock and detach operations use `Runtime::reparent`. Win32 uses `SetParent`; X11 uses `XReparentWindow`; Cocoa uses native child-window relationships.

## Build methods

### Direct native build, no CMake

Linux/macOS with GCC or Clang:

```bash
./build.sh gcc Debug
./build.sh clang Release
```

Windows with MSVC:

```bat
build.bat Debug
build.bat Release
```

The scripts build and validate:

- static library
- shared library
- static entrypoint archive
- shared entrypoint archive
- static example
- shared example
- tests

### CMake

```bash
cmake --preset ninja-debug
cmake --build --preset ninja-debug
ctest --preset ninja-debug
```

Release:

```bash
cmake --preset ninja-release
cmake --build --preset ninja-release
ctest --preset ninja-release
```

Visual Studio generator:

```bat
cmake --preset vs2022
cmake --build --preset vs2022-release
```

The `vs2022` preset remains usable from newer Visual Studio installations that have the v143 toolset. Visual Studio 2026 can also open the repository as a CMake folder or use the native solution.

### Native Visual Studio solution

Open:

```text
msvc/EpochPlatformEngine.sln
```

This path does not require CMake. It contains separate static, shared, entrypoint, example, and test projects.

### VS Code

Open the repository and run one of these tasks:

- `EpochPlatformEngine: CMake build Debug`
- `EpochPlatformEngine: direct native build`
- `EpochPlatformEngine: direct Clang build`

The checked-in launch configurations run the static example or test executable.

## CMake consumer integration

```cmake
find_package(EpochPlatformEngine CONFIG REQUIRED)

add_executable(MyGame game.cpp)
target_link_libraries(MyGame PRIVATE
    EpochPlatformEngine::EntrypointConsoleStatic
    EpochPlatformEngine::Static)
```

Or use the helper:

```cmake
epoch_platform_add_application(MyGame
    LINKAGE STATIC
    SOURCES game.cpp)
```

For a shared application:

```cmake
epoch_platform_add_application(MyGame
    LINKAGE SHARED
    SOURCES game.cpp)
```

## Platform drivers

| Driver | Native windows | Multiple contexts | Parenting | Default thread model |
|---|---:|---:|---:|---|
| Headless | No | Yes | No | Dedicated driver thread |
| Win32 | Yes | Yes | Yes | Dedicated driver thread |
| X11 | Yes | Yes | Yes | Dedicated driver thread |
| Cocoa | Yes | Yes | Native child relation | Main thread |

X11 is enabled automatically when its development package is available. A Linux runtime falls back to the headless driver when no usable display can be opened.

## EpochEngine integration

The migration boundary is documented in [`docs/epochengine-integration.md`](docs/epochengine-integration.md). The short form:

- `EpochPlatformEngine` replaces native window creation, event pumps, parent/child ownership, detached hosts, and driver-thread routing.
- EpochEngine keeps graphics backend implementations, render contexts, RHI state, resource ownership, and editor composition.
- `ContextSnapshot::route` replaces the platform part of `WindowData::guiRoute`.
- `Runtime::dispatch` replaces owner-thread platform command routing.
- `NativeWindowHandle` replaces platform handles embedded directly in shared engine state.
- No global `WindowData::s_instance` is required.

## License

`LicenseRef-MIT-NoSell`. Commercial use requires prior written permission from the copyright holder. See [`LICENSE`](LICENSE).
