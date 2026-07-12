"""
resource_base / default_data_dir 路径兼容性测试
===============================================
验证桌面打包（PyInstaller 冻结）与开发环境两种情形下资源路径定位正确。
"""

import importlib.util
import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_utils():
    """动态加载 api/infrastructure/utils.py（模块内使用绝对导入，不含 __init__）。"""
    path = os.path.join(PROJECT_ROOT, "api", "infrastructure", "utils.py")
    spec = importlib.util.spec_from_file_location("infrastructure.utils", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["infrastructure.utils"] = module
    spec.loader.exec_module(module)
    return module


utils = _load_utils()


class ResourceBaseTest(unittest.TestCase):
    def tearDown(self):
        # 确保测试之间不残留 _MEIPASS
        if hasattr(sys, "_MEIPASS"):
            delattr(sys, "_MEIPASS")

    def test_dev_env_returns_project_root(self):
        """开发环境（无 _MEIPASS）：返回项目根目录，且关键资源存在。"""
        if hasattr(sys, "_MEIPASS"):
            delattr(sys, "_MEIPASS")
        base = utils.resource_base()
        self.assertEqual(base, PROJECT_ROOT)
        self.assertTrue(os.path.isdir(os.path.join(base, "data", "processed_data")))
        self.assertTrue(os.path.isfile(os.path.join(base, "config", "business.yaml")))

    def test_frozen_env_uses_meipass(self):
        """冻结环境：返回 sys._MEIPASS。"""
        fake = os.path.join("/tmp", "meipass_fake")
        sys._MEIPASS = fake
        try:
            self.assertEqual(utils.resource_base(), fake)
        finally:
            delattr(sys, "_MEIPASS")

    def test_default_data_dir_follows_base(self):
        """default_data_dir 基于 resource_base 拼接。"""
        fake = os.path.join("/tmp", "meipass_fake")
        sys._MEIPASS = fake
        try:
            self.assertEqual(
                utils.default_data_dir(),
                os.path.join(fake, "data", "processed_data"),
            )
        finally:
            delattr(sys, "_MEIPASS")


if __name__ == "__main__":
    unittest.main()
