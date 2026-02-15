#
# MIT License
# 
# Copyright (c) 2024-2025 Manuel Bottini
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#



# Use > for indentation
.RECIPEPREFIX := >

format:
> find src -name '*.cpp' -o -name '*.h' | xargs clang-format -i

buildir: format
> mkdir -p build

BnWifiHostCommunicator.o: buildir
> g++ -c -o build/BnWifiHostCommunicator.o -g src/BnWifiHostCommunicator.cpp -Iinclude -Ithird_party -I../../body-nodes-common/cpp/src/ -fPIC

build-lib: BnWifiHostCommunicator.o
> g++ -shared -o build/libBnWifiHostCommunicator.so build/BnWifiHostCommunicator.o

build-host: 
> g++ -o build/host_example -g host_example.cpp -Iinclude -Ithird_party -I../../body-nodes-common/cpp/src/ -Lbuild -lBnWifiHostCommunicator -lpthread

run-host: build/host_example
> LD_LIBRARY_PATH=$LD_LIBRARY_PATH:build ./build/host_example

clean: 
> rm -r build
