# MIT License
# 
# Copyright (c) 2026 Manuel Bottini
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

EXCLUDE_DIRS := -path "*/Adeept.py" -o -path "./venv" -o -path "./.git" -o -path "./__pycache__"
PYTHONPATH_VAR := ../../modules/pythonlib:../../body-nodes-common/python

format-all:
> find . \( $(EXCLUDE_DIRS) \) -prune -o -name "*.py" -type f -print0 | xargs -0 black

# pip install pyautogui
# PYTHONPATH=../../modules/pythonlib:../../body-nodes-common/python pylint --disable=C0301,C0302 <file>
check-all:
> find . \( $(EXCLUDE_DIRS) \) -prune -o -name "*.py" -type f -print0 | xargs -0 black --check
> find . \( $(EXCLUDE_DIRS) \) -prune -o -name "*.py" -type f -print0 | xargs -0 -I {} sh -c 'PYTHONPATH=$(PYTHONPATH_VAR) pylint --extension-pkg-whitelist=pygame --disable=C0301,C0302 "{}"'
