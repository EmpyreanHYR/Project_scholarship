-- 数据库Schema参考
-- 本文件仅供参考，实际建表由SQLAlchemy自动完成

-- ============================================
-- 1. 评审批次表
-- ============================================
CREATE TABLE review_batches (
    id SERIAL PRIMARY KEY,
    batch_name VARCHAR(200) NOT NULL,
    batch_code VARCHAR(50) UNIQUE NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    semester VARCHAR(20) NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'draft',
    description TEXT,
    reviewer_name VARCHAR(100),
    total_students INTEGER DEFAULT 0,
    reviewed_count INTEGER DEFAULT 0
);

CREATE INDEX idx_batch_code ON review_batches(batch_code);
CREATE INDEX idx_academic_year ON review_batches(academic_year);
CREATE INDEX idx_status ON review_batches(status);
CREATE INDEX idx_created_at ON review_batches(created_at);

COMMENT ON TABLE review_batches IS '评审批次表';

-- ============================================
-- 2. 学生信息表
-- ============================================
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES review_batches(id) ON DELETE CASCADE,
    student_id VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    class_name VARCHAR(100),
    major VARCHAR(100),
    grade VARCHAR(20),
    phone VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_batch_student UNIQUE (batch_id, student_id)
);

CREATE INDEX idx_student_id ON students(student_id);
CREATE INDEX idx_batch_student ON students(batch_id, student_id);
CREATE INDEX idx_name ON students(name);

COMMENT ON TABLE students IS '学生信息表';

-- ============================================
-- 3. 申请信息表
-- ============================================
CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES review_batches(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    project_name VARCHAR(200),
    project_type VARCHAR(100),
    project_category VARCHAR(100),
    project_level VARCHAR(50),
    award_name VARCHAR(200),
    award_level VARCHAR(50),
    award_rank VARCHAR(50),
    award_date TIMESTAMP,
    points FLOAT DEFAULT 0.0,
    base_points FLOAT DEFAULT 0.0,
    bonus_points FLOAT DEFAULT 0.0,
    certificate_path VARCHAR(500),
    certificate_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending',
    is_valid BOOLEAN DEFAULT TRUE,
    remarks TEXT,
    reviewer_notes TEXT,
    submitted_at TIMESTAMP,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_batch_id ON applications(batch_id);
CREATE INDEX idx_student_id ON applications(student_id);
CREATE INDEX idx_project_type ON applications(project_type);
CREATE INDEX idx_status ON applications(status);
CREATE INDEX idx_submitted_at ON applications(submitted_at);

COMMENT ON TABLE applications IS '申请信息表';

-- ============================================
-- 4. 评审记录表
-- ============================================
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES review_batches(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    reviewer_name VARCHAR(100),
    reviewer_account VARCHAR(100),
    total_points FLOAT DEFAULT 0.0,
    final_result VARCHAR(50),
    rank INTEGER,
    review_details TEXT,
    review_status VARCHAR(20) DEFAULT 'draft',
    is_passed BOOLEAN,
    review_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submit_time TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comments TEXT
);

CREATE INDEX idx_batch_id ON reviews(batch_id);
CREATE INDEX idx_student_id ON reviews(student_id);
CREATE INDEX idx_reviewer_account ON reviews(reviewer_account);
CREATE INDEX idx_review_status ON reviews(review_status);
CREATE INDEX idx_review_time ON reviews(review_time);

COMMENT ON TABLE reviews IS '评审记录表';

-- ============================================
-- 5. 审计日志表
-- ============================================
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL,
    operation_module VARCHAR(50),
    operation_action VARCHAR(100),
    operator_name VARCHAR(100),
    operator_account VARCHAR(100),
    operator_ip VARCHAR(50),
    batch_id INTEGER,
    student_id INTEGER,
    target_id INTEGER,
    target_type VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    change_summary TEXT,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    operation_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_agent VARCHAR(500),
    request_params TEXT
);

CREATE INDEX idx_operation_type ON audit_logs(operation_type);
CREATE INDEX idx_operator_account ON audit_logs(operator_account);
CREATE INDEX idx_operation_time ON audit_logs(operation_time);
CREATE INDEX idx_batch_id ON audit_logs(batch_id);
CREATE INDEX idx_target ON audit_logs(target_type, target_id);

COMMENT ON TABLE audit_logs IS '审计日志表';

-- ============================================
-- 示例查询
-- ============================================

-- 查询某批次的所有学生及其总分
SELECT 
    s.student_id,
    s.name,
    r.total_points,
    r.rank
FROM students s
LEFT JOIN reviews r ON s.id = r.student_id
WHERE s.batch_id = 1
ORDER BY r.rank;

-- 查询某学生的所有加分项目
SELECT 
    a.project_name,
    a.award_level,
    a.points,
    a.status
FROM applications a
JOIN students s ON a.student_id = s.id
WHERE s.student_id = '20230001'
AND a.is_valid = TRUE
ORDER BY a.created_at DESC;

-- 统计某批次的评审进度
SELECT 
    rb.batch_name,
    rb.total_students,
    rb.reviewed_count,
    ROUND(rb.reviewed_count * 100.0 / rb.total_students, 2) as progress_percent
FROM review_batches rb
WHERE rb.status = 'active';

-- 查询操作日志
SELECT 
    operation_type,
    operator_account,
    operation_action,
    operation_time
FROM audit_logs
WHERE operation_time >= CURRENT_DATE
ORDER BY operation_time DESC
LIMIT 100;
