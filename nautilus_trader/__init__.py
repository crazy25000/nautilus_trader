# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2021 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# -------------------------------------------------------------------------------------------------

"""
The top-level package contains all sub-packages needed for NautilusTrader.
"""

import os

import toml


PACKAGE_ROOT = os.path.dirname(os.path.abspath(__file__))
PYPROJECT_PATH = PACKAGE_ROOT.strip("nautilus_trader") + "/pyproject.toml"  # noqa

try:
    __version__ = toml.load(PYPROJECT_PATH)["tool"]["poetry"]["version"]
except FileNotFoundError:
    __version__ = "latest"
