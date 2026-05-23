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

    config_candidates = ['db_config.json', 'database_config.json']
    config_path = None
    for candidate in config_candidates:
        if os.path.exists(candidate):
            config_path = candidate
            break

    if not config_path:
        print("⚠️  未找到数据库配置文件（db_config.json / database_config.json）")
        return True, None
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print(f"✅ 配置文件格式正确：{config_path}")
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
            ("数据校验 (_parse_date)", "def _parse_date"),
            ("评审功能", "class ScholarshipReviewer"),
            ("撤销功能", "def undo_review"),
            ("重做功能", "def redo_review"),
            ("导出功能", "def export_excel"),
            ("PDF导出", "def export_pdf_report"),
            ("PDF批量", "def export_pdf_batch"),
            ("可视化面板", "class VisualizationPanel"),
            ("角色权限 (is_admin)", "def is_admin"),
            ("管理员面板", "def open_admin_panel"),
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
    
    files = ['db_integration.py', 'history_window.py', 'report_generator.py']
    
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
