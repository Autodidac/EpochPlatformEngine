# EpochPlatformEngine v0.1.0

Initial runnable release of EpochPlatformEngine.

## Included

- C++23 static and shared platform libraries
- automatic console and Windows GUI entrypoint libraries
- Win32, X11, Cocoa, and headless platform drivers
- multiple contexts per driver host
- dedicated platform-driver thread routing
- primary, detached, child, hidden, and headless context support
- native handle publication for renderer attachment
- CMake, native Visual Studio, VS Code, GCC, Clang, and direct MSVC build paths
- static and shared release-example executables
- Windows x64 and Linux x64 SDK/example packages
- SHA-256 checksums

The release example opens a primary window and a detached tools window while a headless worker context runs on a separate driver host. The windows are intentionally renderer-neutral; EpochPlatformEngine provides the native hosting layer that EpochEngine render drivers attach to.
