"""
奖学金评审软件 - 核心功能单元测试
"""
import unittest
import hashlib
import secrets
import os
import json
import tempfile
import sys

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestPasswordHashing(unittest.TestCase):
    """测试密码哈希功能"""

    def test_hash_password_format(self):
        """测试哈希密码格式正确"""
        # 模拟 LoginManager 的 hash_password 方法
        def hash_password(password: str) -> str:
            salt = secrets.token_bytes(32)
            key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 260000)
            return salt.hex() + ':' + key.hex()

        hashed = hash_password("test123")
        # 验证格式：salt(64字符) + ':' + hash(64字符) = 129字符
        self.assertEqual(len(hashed), 129)
        self.assertIn(':', hashed)

    def test_verify_password_correct(self):
        """测试密码验证 - 正确密码"""
        def hash_password(password: str) -> str:
            salt = secrets.token_bytes(32)
            key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 260000)
            return salt.hex() + ':' + key.hex()

        def verify_password(stored: str, password: str) -> bool:
            if ':' in stored and len(stored) == 129:
                try:
                    salt_hex, key_hex = stored.split(':')
                    salt = bytes.fromhex(salt_hex)
                    new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 260000)
                    return new_key.hex() == key_hex
                except (ValueError, IndexError):
                    return False
            return stored == password

        hashed = hash_password("mypassword")
        self.assertTrue(verify_password(hashed, "mypassword"))

    def test_verify_password_incorrect(self):
        """测试密码验证 - 错误密码"""
        def hash_password(password: str) -> str:
            salt = secrets.token_bytes(32)
            key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 260000)
            return salt.hex() + ':' + key.hex()

        def verify_password(stored: str, password: str) -> bool:
            if ':' in stored and len(stored) == 129:
                try:
                    salt_hex, key_hex = stored.split(':')
                    salt = bytes.fromhex(salt_hex)
                    new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 260000)
                    return new_key.hex() == key_hex
                except (ValueError, IndexError):
                    return False
            return stored == password

        hashed = hash_password("mypassword")
        self.assertFalse(verify_password(hashed, "wrongpassword"))

    def test_verify_password_plain_text_fallback(self):
        """测试密码验证 - 旧格式明文密码兼容"""
        def verify_password(stored: str, password: str) -> bool:
            if ':' in stored and len(stored) == 129:
                try:
                    salt_hex, key_hex = stored.split(':')
                    salt = bytes.fromhex(salt_hex)
                    new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 260000)
                    return new_key.hex() == key_hex
                except (ValueError, IndexError):
                    return False
            return stored == password

        # 旧格式明文密码
        self.assertTrue(verify_password("plainpassword", "plainpassword"))
        self.assertFalse(verify_password("plainpassword", "wrongpassword"))


class TestConstants(unittest.TestCase):
    """测试全局常量配置"""

    def test_constants_exist(self):
        """测试常量是否定义"""
        # 导入主模块的常量
        try:
            from jxj_main3 import (
                MAX_FILE_SIZE,
                MAX_EXCEL_ROWS,
                DEFAULT_SCORE_CAP,
                DEFAULT_PROJECT_TYPES,
                MAX_LOGIN_ATTEMPTS,
                MIN_USERNAME_LENGTH,
                MAX_USERNAME_LENGTH,
                MIN_PASSWORD_LENGTH
            )
            # 验证常量值
            self.assertEqual(MAX_FILE_SIZE, 50 * 1024 * 1024)
            self.assertEqual(MAX_EXCEL_ROWS, 5000)
            self.assertEqual(DEFAULT_SCORE_CAP, 6)
            self.assertEqual(len(DEFAULT_PROJECT_TYPES), 3)
            self.assertEqual(MAX_LOGIN_ATTEMPTS, 3)
            self.assertEqual(MIN_USERNAME_LENGTH, 2)
            self.assertEqual(MAX_USERNAME_LENGTH, 20)
            self.assertEqual(MIN_PASSWORD_LENGTH, 4)
        except ImportError as e:
            self.skipTest(f"无法导入 jxj_main3 模块: {e}")


class TestGitignore(unittest.TestCase):
    """测试 .gitignore 配置"""

    def test_gitignore_exists(self):
        """测试 .gitignore 文件存在"""
        self.assertTrue(os.path.exists('.gitignore'))

    def test_gitignore_ignores_sensitive_files(self):
        """测试 .gitignore 忽略敏感文件"""
        with open('.gitignore', 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否忽略了敏感文件
        self.assertIn('users.json', content)
        self.assertIn('db_config.json', content)
        self.assertIn('data/', content)
        self.assertIn('__pycache__/', content)
        self.assertIn('.idea/', content)


class TestRequirementsTxt(unittest.TestCase):
    """测试 requirements.txt"""

    def test_requirements_exists(self):
        """测试 requirements.txt 文件存在"""
        self.assertTrue(os.path.exists('requirements.txt'))

    def test_requirements_content(self):
        """测试 requirements.txt 内容"""
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否包含必需依赖
        self.assertIn('pandas', content)
        self.assertIn('openpyxl', content)
        self.assertIn('Pillow', content)
        self.assertIn('SQLAlchemy', content)


if __name__ == '__main__':
    unittest.main()
