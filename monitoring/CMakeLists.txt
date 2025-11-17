cmake_minimum_required(VERSION 3.10)
project(monitoring_dds)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Portable binary settings - RPATH for shared libraries
set(CMAKE_BUILD_RPATH_USE_ORIGIN TRUE)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH FALSE)
set(CMAKE_BUILD_RPATH "$ORIGIN/../lib:$ORIGIN/../../lib:/usr/local/lib")

find_package(fastcdr REQUIRED)
find_package(fastdds REQUIRED)
find_package(OpenSSL REQUIRED)

# Repo-relative paths to generated IDL headers and libs
# IDL directories are in parent directory (DDS root)
get_filename_component(DDS_ROOT "${CMAKE_SOURCE_DIR}" DIRECTORY)
set(IDL_CORE_DATA_DIR "${DDS_ROOT}/IDL/CoreData_idl_generated")
set(IDL_INTEL_DIR "${DDS_ROOT}/IDL/Intelligence_idl_generated")
set(IDL_MSG_DIR "${DDS_ROOT}/IDL/Messaging_idl_generated")

# Static libraries are produced in each generated module's build/ directory
set(IDL_CORE_DATA_LIB "${IDL_CORE_DATA_DIR}/build/libCoreData_lib.a")
set(IDL_INTEL_LIB "${IDL_INTEL_DIR}/build/libIntelligence_lib.a")
set(IDL_MSG_LIB "${IDL_MSG_DIR}/build/libMessaging_lib.a")

include_directories(
    ${IDL_CORE_DATA_DIR}
    ${IDL_INTEL_DIR}
    ${IDL_MSG_DIR}
)

add_executable(monitor
    monitor.cpp
)

# Set RPATH for portable binary
set_target_properties(monitor PROPERTIES
    BUILD_RPATH "$ORIGIN/../lib:$ORIGIN/../../lib"
    INSTALL_RPATH "$ORIGIN/../lib:$ORIGIN/../../lib"
    BUILD_WITH_INSTALL_RPATH FALSE
    INSTALL_WITH_INSTALL_RPATH FALSE
)

# Link Fast DDS and generated IDL libs
target_link_libraries(monitor
    fastdds
    fastcdr
    OpenSSL::SSL
    OpenSSL::Crypto
    ${IDL_CORE_DATA_LIB}
    ${IDL_INTEL_LIB}
    ${IDL_MSG_LIB}
)

message(STATUS "Using IDL dirs: ${IDL_CORE_DATA_DIR}; ${IDL_INTEL_DIR}; ${IDL_MSG_DIR}")
message(STATUS "Linking IDL libs: ${IDL_CORE_DATA_LIB}; ${IDL_INTEL_LIB}; ${IDL_MSG_LIB}")
