# EpochPlatformEngine

Current source version: **0.2.0**. Release artifacts and native acceptance are separate gates.

MPL-2.0 permits commercial use, including proprietary larger works subject to its covered-file obligations. See [Commercial use and giving back](#commercial-use-and-giving-back) for licensing, origin links and voluntary credit requests.

`EpochPlatformEngine` is the reusable C++23 process, window, event, and multi-context host for EpochEngine applications and standalone tools.

It deliberately does **not** own rendering. OpenGL, Vulkan, DirectX, SDL, SFML, Raylib, software rendering, and future renderer implementations remain in their own EpochEngine drivers. `EpochPlatformEngine` owns the native operating-system boundary those drivers attach to.

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
- Runnable static and shared release examples
- Versioned Windows x64 and Linux x64 release packages
- CMake presets
- Native Visual Studio solution independent of CMake
- Direct GCC, Clang, and MSVC build scripts independent of CMake
- VS Code build, test, and launch configurations

No EpochEngine package-manager registration is included. EpochEngine or the project manager can add this repository as a selected source/project dependency only when the platform library is required.

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

A driver host owns one native event pump and any number of contexts for that operating-system driver. Different drivers can run concurrently. Context callbacks execute on the driver owner thread, giving renderer code a stable thread-affinity point for native and graphics-context initialization.

`ContextType` mirrors the existing EpochEngine backend set:

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

## Release example

The release example is a runnable demonstration, not only a source snippet. It opens:

- one primary native window
- one independent detached tools window
- one headless worker context on a separate driver host

It demonstrates the automatic internal entrypoint, multi-context ownership, detached-window routing, per-context frame callbacks, live title updates, clean close handling, and static/shared linkage. It remains renderer-neutral so EpochEngine graphics drivers can attach to the published native handles.

Close both visible windows to stop the worker and exit. Pass `--auto-exit` to close all contexts after eight seconds. A display-less system automatically uses the headless driver and exits after the same validation period.

Source:

```text
examples/release_app.cpp
```

Targets:

```text
EpochPlatformReleaseExampleStatic
EpochPlatformReleaseExampleShared
```

Release packages include both executables, the shared runtime, the installed SDK, source for the example, documentation, license, and SHA-256 checksums. See [`docs/release-example.md`](docs/release-example.md).

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

The scripts build:

- static library
- shared library
- static and shared entrypoint archives
- static and shared validation examples
- static and shared release examples
- tests

The noninteractive validation examples and tests run automatically. The release examples are built but left for interactive execution.

### CMake

The compiler and standard library must provide C++23 `std::expected` and
`std::jthread`; configure checks both before building. Linux CI uses Clang 19
with libstdc++ 13 or newer and its matching `clang-scan-deps`. Clang 18 with
Ubuntu's default libstdc++ does not expose the required `std::expected` API.


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

This path does not require CMake. It contains separate static, shared, entrypoint, validation-example, release-example, and test projects.

### VS Code

Open the repository and use:

- `EpochPlatformEngine: CMake build Debug`
- `EpochPlatformEngine: CMake build Release`
- `EpochPlatformEngine: direct native build`
- `EpochPlatformEngine: direct native Release`
- `EpochPlatformEngine: direct Clang build`

The checked-in launch configurations run the release example, validation example, or tests.

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

## Canonical native API and module adapters

The native header API and `platform.native` share the same global declarations;
`RuntimePlatform` retains its uint8 representation and Unknown/Windows/Linux/MacOS
values 0/1/2/3. Android, IOS and Web identifiers append values without claiming
native driver implementations. Existing Static/Shared libraries and native
application entrypoints remain available.

`EpochPlatformEngine::ModuleStatic` and `::ModuleShared` also own the accepted
portable core, capability, tier and software-application modules. `platform.engine`
reexports the native API and keeps distribution/archive/topology policy under
`epochengine::platform::policy`. The previous software window session and native
attachment/input helpers live under `epochengine::platform::window_adapter`, so
they cannot redefine the published native WindowDesc, WindowEvent or policy types.
The two ContextType domains remain distinct and retain their numeric values.

Consumers choose a native application runtime or their existing Engine host.
Importing/linking these modules starts no second Runtime, registry, event pump or
scheduler. Direct adoption of canonical drivers by the existing Engine manager
remains a separate integration gate; this graph does not claim that migration is
complete. The explicit `Epoch::PlatformEntry` is the existing software-session
entry choice, while the native EntrypointConsole/Windowed targets keep their API.

## Commercial use and giving back

Quick guide to [MPL-2.0](LICENSE); the full license governs. "Covered files"
means this library's MPL source, your changes to it, and new files containing
its code. Separate files in a larger application can use another license.

### Allowed

- [x] Use the library commercially, including in proprietary applications.
- [x] Sell applications or redistribute the library itself, changed or unchanged.
- [x] Make private/internal changes without publishing them or sending a PR.
- [x] License your separate application files under your own terms while meeting
  MPL obligations for the covered files.

### Required when distributing outside your organization

- [ ] Keep covered source, including your modifications, available under MPL-2.0.
- [ ] When shipping binaries, tell recipients how to obtain that covered source
  reasonably and promptly, charging no more than its distribution cost.
- [ ] Tell recipients the source is MPL-2.0 and include the license or explain
  how to obtain it.
- [ ] Preserve required copyright, patent, license and warranty/liability notices.
- [ ] Keep recipients' MPL source rights intact under any additional terms.

### Not allowed

- [ ] Do not make distributed covered source proprietary-only or withhold the
  covered source required for your binaries.
- [ ] Do not remove substantive required notices or present someone else's work
  as your own.
- [ ] Do not assume MPL grants rights to project names/logos or imply official
  endorsement. Use distinct product branding; see [TRADEMARKS.md](TRADEMARKS.md).

### Recommended, entirely optional

- [ ] Give visible credit and link to [this repository](https://github.com/Autodidac/EpochPlatformEngine) and
  [EpochEngine](https://github.com/Autodidac/EpochEngine) in your About screen or README.
- [ ] Share useful fixes, features, tests and documentation through a
  [pull request](https://github.com/Autodidac/EpochPlatformEngine/pulls); accepted contributions receive author credit.
- [ ] Follow [CONTRIBUTING.md](CONTRIBUTING.md) when choosing to contribute.

**MPL does not require an upstream pull request. But it would be a lot cooler if
you shared!** Contributions help these libraries support themselves and continued
work on EpochEngine. These recommendations add no copyright-license conditions.

See [Mozilla's MPL FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/) for examples.

## License

First-party source uses **MPL-2.0**; LICENSE contains the unmodified full text.
Private modification is allowed; distribution obligations apply to covered
files under that license. Commercial use is allowed. Required notices and
third-party licenses remain in force. Historical grants are not revoked.
See NOTICE for origin, TRADEMARKS.md for separate branding rules, and
CONTRIBUTING.md / CONTRIBUTOR_LICENSE.md for explicit contribution acceptance.
