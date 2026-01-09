"""
系统验证工具
整合了数据库配置验证和系统完整性检查
"""

import json
import logging
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def check_config_file():
    """检查配置文件"""
    print_header("1. 配置文件检查")
    
    if not os.path.exists('db_config.json'):
        print("⚠️  db_config.json 不存在（数据库功能未配置）")
        return True, None
    
    try:
        with open('db_config.json', 'r') as f:
            config = json.load(f)
        print("✅ 配置文件格式正确")
        return True, config
    except Exception as e:
        print(f"❌ 配置文件错误: {e}")
        return False, None


def check_database_connection(config):
    """检查数据库连接"""
    print_header("2. 数据库连接检查")
    
    if not config or not config.get('enabled'):
        print("⏭️  跳过（数据库未启用）")
        return True
    
    try:
        from database.connection import check_database_available
        if check_database_available():
            print("✅ 数据库连接成功")
            return True
        else:
            print("❌ 数据库连接失败")
            return False
    except Exception as e:
        print(f"⚠️  数据库模块错误: {e}")
        return False


def check_main_program():
    """检查主程序完整性"""
    print_header("3. 主程序完整性")
    
    try:
        with open('jxj_main3.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("Excel导入", "def load_excel_data"),
            ("评审功能", "class ScholarshipReviewer"),
            ("导出功能", "def export_excel"),
        ]
        
        all_ok = True
        for name, keyword in checks:
            if keyword in content:
                print(f"✅ {name}")
            else:
                print(f"❌ {name} 缺失")
                all_ok = False
        
        return all_ok
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False


def check_database_modules():
    """检查数据库模块"""
    print_header("4. 数据库模块检查")
    
    modules = [
        'database/__init__.py',
        'database/connection.py',
        'database/models.py',
        'database/dao.py',
        'database/services.py',
    ]
    
    all_ok = True
    for module in modules:
        if os.path.exists(module):
            print(f"✅ {module}")
        else:
            print(f"⚠️  {module} 不存在")
            all_ok = False
    
    return all_ok


def check_integration():
    """检查集成文件"""
    print_header("5. 集成检查")
    
    files = ['db_integration.py', 'history_window.py']
    
    for f in files:
        if os.path.exists(f):
            print(f"✅ {f}")
        else:
            print(f"⚠️  {f} 不存在")
    
    return True


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("奖学金评审系统 - 完整性验证工具")
    print("=" * 60)
    
    results = []
    
    # 执行检查
    success, config = check_config_file()
    results.append(("配置文件", success))
    
    results.append(("数据库连接", check_database_connection(config)))
    results.append(("主程序", check_main_program()))
    results.append(("数据库模块", check_database_modules()))
    results.append(("集成", check_integration()))
    
    # 总结
    print_header("验证总结")
    
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    all_passed = all(s for _, s in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 系统验证通过，可以正常使用")
    else:
        print("⚠️  部分检查未通过，但不影响基本功能")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
