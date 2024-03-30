# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/sppi-src"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/sppi-build"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/sppi-subbuild/sppi-populate-prefix"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/sppi-subbuild/sppi-populate-prefix/tmp"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/sppi-subbuild/sppi-populate-prefix/src/sppi-populate-stamp"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/sppi-subbuild/sppi-populate-prefix/src"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/sppi-subbuild/sppi-populate-prefix/src/sppi-populate-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/robot/Documents/sx128x_linux_driver/build/_deps/sppi-subbuild/sppi-populate-prefix/src/sppi-populate-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/robot/Documents/sx128x_linux_driver/build/_deps/sppi-subbuild/sppi-populate-prefix/src/sppi-populate-stamp${cfgdir}") # cfgdir has leading slash
endif()
