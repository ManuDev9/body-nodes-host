#!/bin/bash
# MIT License
# 
# Copyright (c) 2025 Manuel Bottini
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

# Use > for indentation
.RECIPEPREFIX := >

format-wifi:
> black bnwifibodynodeshost.py

check-wifi:
> PYTHONPATH=../../body-nodes-common/python/ pylint --disable=C0301 bnwifibodynodeshost.py
> black --check bnwifibodynodeshost.py

run-wifi: check-wifi
> PYTHONPATH=../../body-nodes-common/python/ python3 bnwifibodynodeshost.py

format-ble:
> black bnblebodynodeshost.py

check-ble:
> PYTHONPATH=../../body-nodes-common/python/ pylint --disable=C0301 bnblebodynodeshost.py
> black --check bnblebodynodeshost.py

run-ble: check-ble
> PYTHONPATH=../../body-nodes-common/python/ python3 bnblebodynodeshost.py


format-bluetooth:
> black bnbluetoothbodynodeshost.py

check-bluetooth:
> PYTHONPATH=../../body-nodes-common/python/ pylint --disable=C0301 bnbluetoothbodynodeshost.py
> black --check bnbluetoothbodynodeshost.py

run-bluetooth: check-bluetooth
> PYTHONPATH=../../body-nodes-common/python/ python3 bnbluetoothbodynodeshost.py
