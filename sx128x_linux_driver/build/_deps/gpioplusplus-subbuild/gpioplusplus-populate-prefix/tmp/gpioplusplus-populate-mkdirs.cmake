# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/gpioplusplus-src"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/gpioplusplus-build"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/gpioplusplus-subbuild/gpioplusplus-populate-prefix"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/gpioplusplus-subbuild/gpioplusplus-populate-prefix/tmp"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/gpioplusplus-subbuild/gpioplusplus-populate-prefix/src/gpioplusplus-populate-stamp"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/gpioplusplus-subbuild/gpioplusplus-populate-prefix/src"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/gpioplusplus-subbuild/gpioplusplus-populate-prefix/src/gpioplusplus-populate-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/robot/Documents/sx128x_linux_driver/build/_deps/gpioplusplus-subbuild/gpioplusplus-populate-prefix/src/gpioplusplus-populate-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/robot/Documents/sx128x_linux_driver/build/_deps/gpioplusplus-subbuild/gpioplusplus-populate-prefix/src/gpioplusplus-populate-stamp${cfgdir}") # cfgdir has leading slash
endif()
