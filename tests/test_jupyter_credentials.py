#!/usr/bin/env python3
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class JupyterCredentialsTest(unittest.TestCase):
    def load_config(self, token=None):
        config = SimpleNamespace(IdentityProvider=SimpleNamespace())
        env = {} if token is None else {"JUPYTER_TOKEN": token}
        with patch.dict(os.environ, env, clear=True):
            runpy.run_path(
                str(Path(__file__).resolve().parents[1] / "scripts/jupyter_notebook_config.py"),
                init_globals={"get_config": lambda: config},
            )
            self.assertNotIn("JUPYTER_TOKEN", os.environ)
        return config.IdentityProvider.token

    def test_standalone_startup_uses_fresh_random_token(self):
        first = self.load_config()
        second = self.load_config()
        self.assertRegex(first, r"^[0-9a-f]{64}$")
        self.assertNotEqual(first, second)

    def test_empty_token_keeps_authentication_enabled(self):
        self.assertRegex(self.load_config(""), r"^[0-9a-f]{64}$")

    def test_shared_or_custom_token_is_preserved_and_removed_from_environment(self):
        self.assertEqual(self.load_config("custom-service-credential"), "custom-service-credential")

    def test_reloading_config_preserves_existing_token_after_env_pop(self):
        config = SimpleNamespace(IdentityProvider=SimpleNamespace())
        config_path = str(Path(__file__).resolve().parents[1] / "scripts/jupyter_notebook_config.py")
        with patch.dict(os.environ, {"JUPYTER_TOKEN": "bootstrap-shared-token"}, clear=True):
            runpy.run_path(config_path, init_globals={"get_config": lambda: config})
            self.assertNotIn("JUPYTER_TOKEN", os.environ)
            runpy.run_path(config_path, init_globals={"get_config": lambda: config})
        self.assertEqual(config.IdentityProvider.token, "bootstrap-shared-token")


if __name__ == "__main__":
    unittest.main()
