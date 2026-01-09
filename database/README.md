# 数据库模块使用说明

## 概述

本模块提供数据库连接和会话管理功能，采用**完全旁路式设计**，不影响任何现有功能。

## 特性

✅ **非侵入式设计** - 不修改任何现有代码
✅ **故障隔离** - 数据库异常不会阻断主程序
✅ **灵活配置** - 支持环境变量和配置文件
✅ **多数据库支持** - 支持 PostgreSQL 和 MySQL
✅ **线程安全** - 使用 scoped_session 确保线程安全

## 目录结构

```
database/
├── __init__.py         # 模块导入
├── config.py           # 配置管理
├── connection.py       # 连接管理
├── init.py            # 初始化和健康检查
├── models.py          # 数据模型定义（ORM）
├── migrate.py         # 数据库迁移和建表
└── README.md          # 本文档
```

## 快速开始

### 1. 安装依赖

根据使用的数据库类型安装相应驱动：

```bash
# PostgreSQL
pip install sqlalchemy psycopg2-binary

# MySQL
pip install sqlalchemy pymysql
```

### 2. 配置数据库

#### 方式一：配置文件（推荐）

在项目根目录创建 `database_config.json`：

```json
{
    "enabled": true,
    "db_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "username": "your_username",
    "password": "your_password",
    "database": "scholarship_db",
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "echo": false
}
```

MySQL 配置示例：

```json
{
    "enabled": true,
    "db_type": "mysql",
    "host": "localhost",
    "port": 3306,
    "username": "your_username",
    "password": "your_password",
    "database": "scholarship_db"
}
```

#### 方式二：环境变量

```bash
export DB_ENABLED=true
export DB_TYPE=postgresql
export DB_HOST=localhost
export DB_PORT=5432
export DB_USERNAME=your_username
export DB_PASSWORD=your_password
export DB_DATABASE=scholarship_db
```

### 3. 使用示例

#### 基础使用

```python
from database import session_scope, check_database_available

# 检查数据库是否可用
if check_database_available():
    print("数据库可用")
else:
    print("数据库不可用，使用本地存储")

# 使用会话上下文管理器（推荐）
with session_scope() as session:
    if session:
        # 执行数据库操作
        from sqlalchemy import text
        result = session.execute(text("SELECT * FROM users"))
        for row in result:
            print(row)
```

#### 手动管理会话

```python
from database import get_session

session = get_session()
if session:
    try:
        # 执行数据库操作
        result = session.execute(text("SELECT 1"))
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"操作失败: {e}")
    finally:
        session.close()
```

#### 数据库健康检查

```python
from database.init import health_check, get_database_info

# 健康检查
status = health_check()
print(f"数据库状态: {status['status']}")
print(f"详细信息: {status['message']}")

# 获取数据库信息
info = get_database_info()
print(f"数据库类型: {info['type']}")
print(f"数据库版本: {info['version']}")
print(f"是否可用: {info['available']}")
```

## 配置说明

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| enabled | bool | false | 是否启用数据库功能 |
| db_type | string | postgresql | 数据库类型（postgresql/mysql） |
| host | string | localhost | 数据库主机地址 |
| port | int | 5432 | 数据库端口 |
| username | string | - | 数据库用户名 |
| password | string | - | 数据库密码 |
| database | string | scholarship_db | 数据库名称 |
| pool_size | int | 5 | 连接池大小 |
| max_overflow | int | 10 | 最大溢出连接数 |
| pool_timeout | int | 30 | 连接超时时间（秒） |
| pool_recycle | int | 3600 | 连接回收时间（秒） |
| echo | bool | false | 是否打印SQL语句 |

## API 文档

### session_scope()

上下文管理器，自动管理会话的生命周期。

**特性:**
- 自动提交成功的事务
- 自动回滚失败的事务
- 自动关闭会话
- 异常不会向上传播

**使用:**
```python
with session_scope() as session:
    if session:
        # 执行数据库操作
        pass
```

### get_session()

获取数据库会话对象。

**返回:** Session对象或None

**注意:** 需要手动关闭会话

### check_database_available()

检查数据库是否可用。

**返回:** bool

### init_database()

初始化数据库模块（可选调用）。

**返回:** bool

## 故障处理

### 数据库未安装驱动

```
WARNING:database.connection:数据库驱动未安装: No module named 'psycopg2'
提示：PostgreSQL需要安装 psycopg2，MySQL需要安装 pymysql
```

**解决方案:**
```bash
pip install psycopg2-binary  # PostgreSQL
pip install pymysql          # MySQL
```

### 数据库连接失败

```
WARNING:database.connection:数据库连接失败: ...
```

**检查项:**
1. 数据库服务是否运行
2. 连接配置是否正确（主机、端口、用户名、密码）
3. 数据库是否存在
4. 防火墙是否允许连接

### 数据库未启用

```
INFO:database.connection:数据库功能未启用
```

**解决方案:** 在配置文件中设置 `"enabled": true`

## 安全建议

1. **不要将配置文件提交到版本控制**
   ```bash
   echo "database_config.json" >> .gitignore
   ```

2. **使用环境变量存储敏感信息**（生产环境推荐）
   
3. **限制数据库用户权限**

4. **使用 SSL/TLS 连接**（生产环境）

## 日志级别

模块使用 Python logging 模块，可以通过配置日志级别控制输出：

```python
import logging

# 查看详细日志
logging.basicConfig(level=logging.DEBUG)

# 只查看错误
logging.basicConfig(level=logging.ERROR)
```

## 兼容性

- Python 3.6+
- SQLAlchemy 1.4+
- PostgreSQL 9.6+
- MySQL 5.7+

## 注意事项

1. **默认禁用** - 数据库功能默认关闭，不影响现有程序
2. **故障隔离** - 所有数据库异常都会被捕获，只记录日志
3. **线程安全** - 使用 scoped_session 确保多线程环境安全
4. **资源清理** - 程序退出时会自动清理数据库连接

## 下一步

本模块只提供数据库基础能力，不包含具体业务逻辑。后续可以：

1. ~~创建数据模型（ORM）~~ ✅ 已完成
2. ~~实现数据迁移~~ ✅ 已完成
3. 添加业务逻辑
4. 集成到主程序

所有扩展功能都应遵循**非侵入式原则**，不影响现有功能。

## 数据库模型

已定义以下数据模型（位于 `models.py`）：

### 1. ReviewBatch（评审批次表）
存储评审活动的基本信息
- 批次名称、编号、学年、学期
- 评审时间、状态
- 统计信息（总学生数、已评审数）

### 2. Student（学生信息表）
存储学生基本信息
- 学号、姓名、班级、专业、年级
- 联系方式（手机、邮箱）
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
- 评审状态和时间

### 5. AuditLog（审计日志表）
记录所有重要操作的审计日志
- 操作类型、模块、动作
- 操作人信息、IP地址
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
    print(f"表列表: {result['tables_created']}")
```

### 检查表状态

```python
from database import check_tables_exist, get_table_info

# 检查表是否存在
check_result = check_tables_exist()
print(f"已存在的表: {check_result['existing_tables']}")
print(f"缺失的表: {check_result['missing_tables']}")

# 获取表详细信息
info_result = get_table_info()
for table_name, details in info_result['table_details'].items():
    print(f"\n表: {table_name}")
    print(f"  列数: {len(details['columns'])}")
    print(f"  主键: {details['primary_key']}")
    print(f"  外键数: {len(details['foreign_keys'])}")
```

### 测试建表功能

```bash
# 运行建表测试脚本
python test_database_schema.py
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
