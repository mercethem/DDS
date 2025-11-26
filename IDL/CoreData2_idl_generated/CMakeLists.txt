cmake_minimum_required(VERSION 3.16)
project(CoreData2)

# Find required packages
find_package(fastcdr REQUIRED)
find_package(fastdds REQUIRED)
find_package(OpenSSL REQUIRED)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Portable binary settings - RPATH for shared libraries
# Use relative RPATH so binaries work when moved to different locations
set(CMAKE_BUILD_RPATH_USE_ORIGIN TRUE)  # Use $ORIGIN for relative paths
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH FALSE)
# Add common library paths to RPATH (relative to executable)
set(CMAKE_BUILD_RPATH "$ORIGIN/../lib:$ORIGIN/../../lib:/usr/local/lib")

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../include)

# Create library
file(GLOB_RECURSE LIB_SOURCES "*.cxx" "*.cpp")
list(FILTER LIB_SOURCES EXCLUDE REGEX ".*main\.cxx$")

if(LIB_SOURCES)
    add_library(CoreData2_lib STATIC ${LIB_SOURCES})
    target_link_libraries(CoreData2_lib fastdds fastcdr OpenSSL::SSL OpenSSL::Crypto)
    target_include_directories(CoreData2_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
    target_include_directories(CoreData2_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/../../include)
endif()

# Create executable
file(GLOB_RECURSE MAIN_SOURCES "*main.cxx")
if(MAIN_SOURCES)
    foreach(MAIN_SOURCE ${MAIN_SOURCES})
        get_filename_component(EXEC_NAME ${MAIN_SOURCE} NAME_WE)
        add_executable(${EXEC_NAME} ${MAIN_SOURCE})
        
        # Set RPATH for portable binaries (relative to executable location)
        set_target_properties(${EXEC_NAME} PROPERTIES
            BUILD_RPATH "$ORIGIN/../lib:$ORIGIN/../../lib"
            INSTALL_RPATH "$ORIGIN/../lib:$ORIGIN/../../lib"
            BUILD_WITH_INSTALL_RPATH FALSE
            INSTALL_WITH_INSTALL_RPATH FALSE
        )
        
        if(TARGET CoreData2_lib)
            target_link_libraries(${EXEC_NAME} CoreData2_lib fastdds fastcdr OpenSSL::SSL OpenSSL::Crypto)
        else()
            target_link_libraries(${EXEC_NAME} fastdds fastcdr OpenSSL::SSL OpenSSL::Crypto)
        endif()
    endforeach()
endif()
