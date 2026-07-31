cmake_minimum_required(VERSION 3.28)

project(EpochPlatformEngine
    VERSION 0.1.0
    DESCRIPTION "Cross-platform C++23 multi-context platform runtime"
    LANGUAGES CXX)

include(GNUInstallDirs)
include(CMakePackageConfigHelpers)
include(CTest)

# Header-first public API: do not require compiler module scanners.
set(CMAKE_CXX_SCAN_FOR_MODULES OFF)

option(EPOCH_PLATFORM_BUILD_STATIC "Build EpochPlatformEngine as a static library" ON)
option(EPOCH_PLATFORM_BUILD_SHARED "Build EpochPlatformEngine as a shared library" ON)
option(EPOCH_PLATFORM_BUILD_EXAMPLES "Build internal-entrypoint examples" ON)
option(EPOCH_PLATFORM_BUILD_TESTS "Build tests" ON)
option(EPOCH_PLATFORM_ENABLE_X11 "Enable the native X11 driver when available" ON)
option(EPOCH_PLATFORM_WARNINGS_AS_ERRORS "Treat warnings as errors" OFF)

find_package(Threads REQUIRED)

set(EPOCH_PLATFORM_COMMON_SOURCES
    src/application.cpp
    src/runtime.cpp
    src/runtime_host.cpp
    src/types.cpp
    src/drivers/headless_driver.cpp)

set(EPOCH_PLATFORM_PLATFORM_SOURCES)
set(EPOCH_PLATFORM_PLATFORM_LIBRARIES)
set(EPOCH_PLATFORM_PLATFORM_DEFINITIONS)

if(WIN32)
    list(APPEND EPOCH_PLATFORM_PLATFORM_SOURCES src/drivers/win32_driver.cpp)
    list(APPEND EPOCH_PLATFORM_PLATFORM_LIBRARIES user32 shell32)
    list(APPEND EPOCH_PLATFORM_PLATFORM_DEFINITIONS
        _WIN32_WINNT=0x0A00 WINVER=0x0A00 WIN32_LEAN_AND_MEAN NOMINMAX)
elseif(APPLE)
    enable_language(OBJCXX)
    list(APPEND EPOCH_PLATFORM_PLATFORM_SOURCES src/drivers/cocoa_driver.mm)
    find_library(COCOA_FRAMEWORK Cocoa REQUIRED)
    list(APPEND EPOCH_PLATFORM_PLATFORM_LIBRARIES ${COCOA_FRAMEWORK})
elseif(UNIX AND EPOCH_PLATFORM_ENABLE_X11)
    find_package(X11 QUIET)
    if(X11_FOUND)
        list(APPEND EPOCH_PLATFORM_PLATFORM_SOURCES src/drivers/x11_driver.cpp)
        list(APPEND EPOCH_PLATFORM_PLATFORM_LIBRARIES X11::X11)
        list(APPEND EPOCH_PLATFORM_PLATFORM_DEFINITIONS EPOCH_PLATFORM_HAS_X11=1)
    endif()
endif()

function(epoch_platform_configure_library target linkage)
    add_library(${target} ${linkage}
        ${EPOCH_PLATFORM_COMMON_SOURCES}
        ${EPOCH_PLATFORM_PLATFORM_SOURCES})

    target_compile_features(${target} PUBLIC cxx_std_23)
    target_include_directories(${target}
        PUBLIC
            $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
            $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>)
    target_link_libraries(${target} PUBLIC Threads::Threads ${EPOCH_PLATFORM_PLATFORM_LIBRARIES})
    target_compile_definitions(${target} PUBLIC ${EPOCH_PLATFORM_PLATFORM_DEFINITIONS})

    if(linkage STREQUAL "STATIC")
        target_compile_definitions(${target} PUBLIC EPOCH_PLATFORM_ENGINE_STATIC=1)
    else()
        target_compile_definitions(${target} PRIVATE EPOCH_PLATFORM_ENGINE_EXPORTS=1)
        set_target_properties(${target} PROPERTIES
            CXX_VISIBILITY_PRESET hidden
            VISIBILITY_INLINES_HIDDEN YES)
    endif()

    if(MSVC)
        target_compile_options(${target} PRIVATE /W4 /permissive- /Zc:__cplusplus /EHsc)
        if(EPOCH_PLATFORM_WARNINGS_AS_ERRORS)
            target_compile_options(${target} PRIVATE /WX)
        endif()
    else()
        target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
        if(EPOCH_PLATFORM_WARNINGS_AS_ERRORS)
            target_compile_options(${target} PRIVATE -Werror)
        endif()
    endif()

    if(APPLE)
        set_source_files_properties(src/drivers/cocoa_driver.mm PROPERTIES COMPILE_FLAGS "-fno-objc-arc")
    endif()

    set_target_properties(${target} PROPERTIES
        POSITION_INDEPENDENT_CODE ON
        VERSION ${PROJECT_VERSION}
        SOVERSION ${PROJECT_VERSION_MAJOR})
endfunction()

if(EPOCH_PLATFORM_BUILD_STATIC)
    epoch_platform_configure_library(EpochPlatformEngineStatic STATIC)
    set_target_properties(EpochPlatformEngineStatic PROPERTIES OUTPUT_NAME EpochPlatformEngineStatic EXPORT_NAME Static)
    add_library(EpochPlatformEngine::Static ALIAS EpochPlatformEngineStatic)
endif()

if(EPOCH_PLATFORM_BUILD_SHARED)
    epoch_platform_configure_library(EpochPlatformEngineShared SHARED)
    set_target_properties(EpochPlatformEngineShared PROPERTIES OUTPUT_NAME EpochPlatformEngine EXPORT_NAME Shared)
    add_library(EpochPlatformEngine::Shared ALIAS EpochPlatformEngineShared)
endif()

function(epoch_platform_add_entrypoint target engine_target)
    add_library(${target} STATIC src/entrypoint/entrypoint.cpp)
    target_compile_features(${target} PUBLIC cxx_std_23)
    target_include_directories(${target} PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>)
    target_link_libraries(${target} PUBLIC ${engine_target})
endfunction()

if(TARGET EpochPlatformEngineStatic)
    epoch_platform_add_entrypoint(EpochPlatformEntrypointConsoleStatic EpochPlatformEngineStatic)
    set_target_properties(EpochPlatformEntrypointConsoleStatic PROPERTIES OUTPUT_NAME EpochPlatformEntrypointConsoleStatic EXPORT_NAME EntrypointConsoleStatic)
    add_library(EpochPlatformEngine::EntrypointConsoleStatic ALIAS EpochPlatformEntrypointConsoleStatic)
endif()

if(TARGET EpochPlatformEngineShared)
    epoch_platform_add_entrypoint(EpochPlatformEntrypointConsoleShared EpochPlatformEngineShared)
    set_target_properties(EpochPlatformEntrypointConsoleShared PROPERTIES OUTPUT_NAME EpochPlatformEntrypointConsoleShared EXPORT_NAME EntrypointConsoleShared)
    add_library(EpochPlatformEngine::EntrypointConsoleShared ALIAS EpochPlatformEntrypointConsoleShared)
endif()

if(WIN32)
    if(TARGET EpochPlatformEngineStatic)
        epoch_platform_add_entrypoint(EpochPlatformEntrypointWindowedStatic EpochPlatformEngineStatic)
        target_compile_definitions(EpochPlatformEntrypointWindowedStatic PRIVATE EPOCH_PLATFORM_WINDOWED_ENTRYPOINT=1)
        set_target_properties(EpochPlatformEntrypointWindowedStatic PROPERTIES OUTPUT_NAME EpochPlatformEntrypointWindowedStatic EXPORT_NAME EntrypointWindowedStatic)
        add_library(EpochPlatformEngine::EntrypointWindowedStatic ALIAS EpochPlatformEntrypointWindowedStatic)
    endif()
    if(TARGET EpochPlatformEngineShared)
        epoch_platform_add_entrypoint(EpochPlatformEntrypointWindowedShared EpochPlatformEngineShared)
        target_compile_definitions(EpochPlatformEntrypointWindowedShared PRIVATE EPOCH_PLATFORM_WINDOWED_ENTRYPOINT=1)
        set_target_properties(EpochPlatformEntrypointWindowedShared PROPERTIES OUTPUT_NAME EpochPlatformEntrypointWindowedShared EXPORT_NAME EntrypointWindowedShared)
        add_library(EpochPlatformEngine::EntrypointWindowedShared ALIAS EpochPlatformEntrypointWindowedShared)
    endif()
endif()

include(cmake/EpochPlatformApplication.cmake)

if(EPOCH_PLATFORM_BUILD_EXAMPLES)
    if(TARGET EpochPlatformEntrypointConsoleStatic)
        epoch_platform_add_application(EpochPlatformExampleStatic
            LINKAGE STATIC
            SOURCES examples/basic_app.cpp)
        epoch_platform_add_application(EpochPlatformReleaseExampleStatic
            WINDOWED
            LINKAGE STATIC
            SOURCES examples/release_app.cpp)
    endif()
    if(TARGET EpochPlatformEntrypointConsoleShared)
        epoch_platform_add_application(EpochPlatformExampleShared
            LINKAGE SHARED
            SOURCES examples/basic_app.cpp)
        epoch_platform_add_application(EpochPlatformReleaseExampleShared
            WINDOWED
            LINKAGE SHARED
            SOURCES examples/release_app.cpp)

        if(APPLE)
            set_target_properties(EpochPlatformReleaseExampleShared PROPERTIES
                BUILD_RPATH "@loader_path"
                INSTALL_RPATH "@loader_path")
        elseif(UNIX)
            set_target_properties(EpochPlatformReleaseExampleShared PROPERTIES
                BUILD_RPATH "$ORIGIN"
                INSTALL_RPATH "$ORIGIN")
        endif()
    endif()
endif()

if(BUILD_TESTING AND EPOCH_PLATFORM_BUILD_TESTS AND TARGET EpochPlatformEngineStatic)
    add_executable(EpochPlatformEngineTests tests/platform_tests.cpp)
    target_compile_features(EpochPlatformEngineTests PRIVATE cxx_std_23)
    target_link_libraries(EpochPlatformEngineTests PRIVATE EpochPlatformEngineStatic)
    add_test(NAME EpochPlatformEngineTests COMMAND EpochPlatformEngineTests)
endif()

set(EPOCH_PLATFORM_INSTALL_TARGETS)
foreach(target IN ITEMS
    EpochPlatformEngineStatic EpochPlatformEngineShared
    EpochPlatformEntrypointConsoleStatic EpochPlatformEntrypointConsoleShared
    EpochPlatformEntrypointWindowedStatic EpochPlatformEntrypointWindowedShared)
    if(TARGET ${target})
        list(APPEND EPOCH_PLATFORM_INSTALL_TARGETS ${target})
    endif()
endforeach()

install(TARGETS ${EPOCH_PLATFORM_INSTALL_TARGETS}
    EXPORT EpochPlatformEngineTargets
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
install(DIRECTORY include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
install(FILES cmake/EpochPlatformApplication.cmake DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/EpochPlatformEngine)
install(EXPORT EpochPlatformEngineTargets
    FILE EpochPlatformEngineTargets.cmake
    NAMESPACE EpochPlatformEngine::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/EpochPlatformEngine)

set(EPOCH_PLATFORM_CONFIG_NEEDS_X11 OFF)
if(X11_FOUND)
    set(EPOCH_PLATFORM_CONFIG_NEEDS_X11 ON)
endif()

configure_package_config_file(
    cmake/EpochPlatformEngineConfig.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/EpochPlatformEngineConfig.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/EpochPlatformEngine)
write_basic_package_version_file(
    ${CMAKE_CURRENT_BINARY_DIR}/EpochPlatformEngineConfigVersion.cmake
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion)
install(FILES
    ${CMAKE_CURRENT_BINARY_DIR}/EpochPlatformEngineConfig.cmake
    ${CMAKE_CURRENT_BINARY_DIR}/EpochPlatformEngineConfigVersion.cmake
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/EpochPlatformEngine)
