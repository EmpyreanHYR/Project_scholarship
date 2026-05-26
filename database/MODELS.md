# 数据库模型使用示例

## 模型概览

本项目定义了5个数据模型，用于存储奖学金评审的历史记录。

### 数据模型列表

| 模型名 | 表名 | 说明 |
|--------|------|------|
| ReviewBatch | review_batches | 评审批次表 |
| Student | students | 学生信息表 |
| Application | applications | 申请信息表 |
| Review | reviews | 评审记录表 |
| AuditLog | audit_logs | 审计日志表 |

## 建表步骤

### 方式1：自动建表（推荐）

```python
from database import init_database_schema

# 自动检查并创建缺失的表
result = init_database_schema()
print(result)
```

### 方式2：使用测试脚本

```bash
python test_database_schema.py
```

## 数据结构说明

### ReviewBatch（评审批次）

每次奖学金评审活动创建一个批次记录。

**主要字段：**
- `batch_code`: 批次唯一编号
- `academic_year`: 学年（如2023-2024）
- `semester`: 学期
- `status`: 状态（draft/active/completed/archived）
- `total_students`: 总学生数
- `reviewed_count`: 已评审数量

### Student（学生）

存储参与评审的学生基本信息。

**主要字段：**
- `student_id`: 学号
- `name`: 姓名
- `class_name`: 班级
- `major`: 专业
- `batch_id`: 所属批次（外键）

**约束：**
- 同一批次中学号唯一

### Application（申请）

存储学生的加分项目申请。

**主要字段：**
- `project_name`: 项目名称
- `project_type`: 项目类型
- `award_level`: 获奖等级
- `points`: 加分分值
- `certificate_path`: 证书文件路径
- `status`: 审核状态（pending/approved/rejected）

### Review（评审记录）

存储每次评审的详细记录。

**主要字段：**
- `total_points`: 总分
- `final_result`: 最终结果
- `rank`: 排名
- `review_details`: 详细信息（JSON）
- `review_status`: 评审状态（draft/submitted/finalized）

### AuditLog（审计日志）

记录所有重要操作。

**主要字段：**
- `operation_type`: 操作类型（create/update/delete/export/import）
- `operator_account`: 操作人账号
- `old_value`: 修改前数据
- `new_value`: 修改后数据
- `operation_time`: 操作时间

## 表关系图

```
┌─────────────────┐
│  ReviewBatch    │
│  (评审批次)      │
└────────┬────────┘
         │
         ├──────────────┬──────────────┐
         │              │              │
         ▼              ▼              ▼
  ┌───────────┐  ┌─────────────┐  ┌─────────┐
  │  Student  │  │ Application │  │  Review │
  │  (学生)   │  │  (申请)     │  │ (评审)  │
  └─────┬─────┘  └──────┬──────┘  └────┬────┘
        │               │                │
        └───────────────┴────────────────┘
                        │
                        ▼
                (关联同一学生)

        ┌──────────────┐
        │  AuditLog    │
        │  (审计日志)   │
        └──────────────┘
              (独立表)
```

## 索引说明

所有表都包含以下索引以提高查询性能：

1. **ReviewBatch**
   - `batch_code`（唯一索引）
   - `academic_year`, `status`, `created_at`

2. **Student**
   - `student_id`
   - `(batch_id, student_id)`（联合唯一索引）
   - `name`

3. **Application**
   - `batch_id`, `student_id`
   - `project_type`, `status`

4. **Review**
   - `batch_id`, `student_id`
   - `reviewer_account`, `review_status`

5. **AuditLog**
   - `operation_type`, `operator_account`
   - `operation_time`

## 注意事项

1. **模型与业务代码集成**
   - 所有模型定义在 `database/models.py`
   - 主程序通过 `db_integration.py` 旁路调用数据库功能
   - 完全独立，不影响现有功能

2. **建表是可选的**
   - 只有启用数据库后才会建表
   - 不建表不影响主程序运行

3. **数据库类型**
   - 默认使用 SQLite（Python 内置）
   - 只需安装 sqlalchemy：`pip install sqlalchemy`

4. **配置文件**
   - 创建 `db_config.json`（参考 `db_config.example.json`）
   - 设置 `enabled: true` 启用数据库

## 测试验证

运行完整测试：

```bash
# 测试数据库连接
python test_database.py

# 测试模型和建表
python test_database_schema.py

# 验证主程序不受影响
python -c "import jxj_main3; print('主程序正常')"
```

## 下一步

建表完成后，可以：
1. 创建数据访问层（DAO）
2. 实现历史记录保存功能
3. 添加数据查询和统计功能
4. 与主程序集成（旁路方式）

所有功能都是**附加式**的，不会修改现有代码。
