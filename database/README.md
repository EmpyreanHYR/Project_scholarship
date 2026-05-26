# 数据库模块使用说明

## 概述

本模块提供 SQLite 数据库连接和会话管理功能，用于存储奖学金评审的历史记录。

## 特性

✅ **开箱即用** - SQLite 是 Python 内置的，无需安装额外数据库服务
✅ **数据持久化** - 数据自动存储在 `data/scholarship.db`
✅ **故障隔离** - 数据库异常不会阻断主程序
✅ **线程安全** - 使用 scoped_session 确保线程安全
✅ **审计日志** - 完整记录所有操作历史

## 目录结构

```
database/
├── __init__.py         # 模块导入
├── config.py           # 配置管理
├── connection.py       # 连接管理
├── init.py            # 初始化和健康检查
├── models.py          # 数据模型定义（ORM）
├── migrate.py         # 数据库迁移和建表
├── dao.py             # 数据访问层
├── services.py        # 业务服务层
├── query_service.py   # 查询服务
├── export_service.py   # 导出服务
└── README.md          # 本文档
```

## 快速开始

### 1. 安装依赖

```bash
# 只需安装 SQLAlchemy（SQLite 是 Python 内置的）
pip install sqlalchemy
```

### 2. 配置数据库

默认配置已预设好，SQLite 数据库文件将存储在 `data/scholarship.db`。

如需修改，编辑 `db_config.json`：

```json
{
    "enabled": true,
    "db_type": "sqlite",
    "database": "data/scholarship.db",
    "echo": false
}
```

### 3. 初始化数据库

```bash
# 初始化建表
python -c "from database import init_database_schema; init_database_schema()"
```

### 4. 运行主程序

```bash
python jxj_main3.py
```

## 配置说明

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| enabled | bool | false | 是否启用数据库功能 |
| db_type | string | sqlite | 数据库类型 |
| database | string | data/scholarship.db | 数据库文件路径 |
| echo | bool | false | 是否打印SQL语句 |

## 使用示例

### 基础使用

```python
from database import session_scope, check_database_available

# 检查数据库是否可用
if check_database_available():
    print("数据库可用")
else:
    print("数据库不可用，使用本地存储")

# 使用会话上下文管理器
with session_scope() as session:
    if session:
        # 执行数据库操作
        from sqlalchemy import text
        result = session.execute(text("SELECT * FROM students"))
```

### 数据库健康检查

```python
from database.init import health_check, get_database_info

# 健康检查
status = health_check()
print(f"数据库状态: {status['status']}")

# 获取数据库信息
info = get_database_info()
print(f"数据库类型: {info['type']}")
print(f"是否可用: {info['available']}")
```

## 数据库模型

### 1. ReviewBatch（评审批次表）
存储评审活动的基本信息
- 批次名称、编号、学年、学期
- 评审时间、状态
- 统计信息（总学生数、已评审数）

### 2. Student（学生信息表）
存储学生基本信息
- 学号、姓名、班级、专业、年级
- 关联到评审批次

### 3. Application（申请信息表）
存储学生的奖学金申请和加分项目
- 项目信息（名称、类型、类别、级别）
- 获奖信息（名称、等级、排名、时间）
- 分数信息（加分分值、基础分、奖励分）
- 证明材料路径
- 审核状态

### 4. Review（评审记录表）
存储每次评审操作的详细记录
- 评审人信息
- 评审结果（总分、排名、是否通过）
- 评审详情（JSON格式）

### 5. AuditLog（审计日志表）
记录所有重要操作的审计日志
- 操作类型、模块、动作
- 操作人信息
- 变更前后数据对比
- 操作状态和时间

## 数据库建表

### 自动建表

```python
from database import init_database_schema

# 自动检查并创建缺失的表
result = init_database_schema()
if result['success']:
    print("数据表初始化成功")
```

### 手动建表

```python
from database import create_all_tables

# 创建所有表
result = create_all_tables()
if result['success']:
    print(f"成功创建 {len(result['tables_created'])} 个表")
```

### 检查表状态

```python
from database import check_tables_exist, get_table_info

# 检查表是否存在
check_result = check_tables_exist()
print(f"已存在的表: {check_result['existing_tables']}")
print(f"缺失的表: {check_result['missing_tables']}")
```

## 模型关系

```
ReviewBatch (评审批次)
    ├── students (1:N) → Student (学生)
    ├── applications (1:N) → Application (申请)
    └── reviews (1:N) → Review (评审)

Student (学生)
    ├── applications (1:N) → Application (申请)
    └── reviews (1:N) → Review (评审)

Application (申请)
    ├── batch (N:1) → ReviewBatch
    └── student (N:1) → Student

Review (评审)
    ├── batch (N:1) → ReviewBatch
    └── student (N:1) → Student

AuditLog (审计日志) - 独立表，无外键关联
```

## API 文档

### session_scope()

上下文管理器，自动管理会话的生命周期。

**特性:**
- 自动提交成功的事务
- 自动回滚失败的事务
- 自动关闭会话
- 异常不会向上传播

### get_session()

获取数据库会话对象。

**返回:** Session对象或None

**注意:** 需要手动关闭会话，建议使用 session_scope()

### check_database_available()

检查数据库是否可用。

**返回:** bool

## 故障处理

### 数据库文件不存在

首次运行时，数据库文件会自动创建在 `data/scholarship.db`。

如果需要手动创建目录：

```bash
mkdir -p data
python -c "from database import init_database_schema; init_database_schema()"
```

### 权限问题

确保程序有权限在项目目录下创建 `data` 文件夹和 `scholarship.db` 文件。

## 日志级别

模块使用 Python logging 模块，可以通过配置日志级别控制输出：

```python
import logging

# 查看详细日志
logging.basicConfig(level=logging.DEBUG)

# 只查看错误
logging.basicConfig(level=logging.ERROR)
```

## 注意事项

1. **故障隔离** - 所有数据库异常都会被捕获，只记录日志
2. **线程安全** - 使用 scoped_session 确保多线程环境安全
3. **资源清理** - 程序退出时会自动清理数据库连接

## 兼容性

- Python 3.6+
- SQLAlchemy 1.4+
- SQLite 3（Python 内置）