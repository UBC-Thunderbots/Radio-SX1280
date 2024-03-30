# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/sx128x_driver-src"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/sx128x_driver-build"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/sx128x_driver-subbuild/sx128x_driver-populate-prefix"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/sx128x_driver-subbuild/sx128x_driver-populate-prefix/tmp"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/sx128x_driver-subbuild/sx128x_driver-populate-prefix/src/sx128x_driver-populate-stamp"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/sx128x_driver-subbuild/sx128x_driver-populate-prefix/src"
  "/home/robot/Documents/sx128x_linux_driver/build/_deps/sx128x_driver-subbuild/sx128x_driver-populate-prefix/src/sx128x_driver-populate-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/robot/Documents/sx128x_linux_driver/build/_deps/sx128x_driver-subbuild/sx128x_driver-populate-prefix/src/sx128x_driver-populate-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/robot/Documents/sx128x_linux_driver/build/_deps/sx128x_driver-subbuild/sx128x_driver-populate-prefix/src/sx128x_driver-populate-stamp${cfgdir}") # cfgdir has leading slash
endif()
