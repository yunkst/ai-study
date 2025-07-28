# AI学习系统数据库模型结构说明

## 概述

AI学习系统采用关系型数据库设计，主要包含用户管理、学科管理、题库管理、题目管理等核心功能模块。以下是详细的数据库模型结构说明。

## 核心数据模型

### 1. 用户模型 (User)

**文件位置**: `backend/app/models.py`

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**字段说明**:
- `id`: 主键，自增整数
- `username`: 用户名，唯一，最大50字符
- `email`: 邮箱地址，唯一，最大100字符
- `hashed_password`: 加密后的密码，最大255字符
- `is_active`: 用户状态，布尔值，默认为True
- `created_at`: 创建时间
- `updated_at`: 更新时间

### 2. 学科模型 (Subject)

**文件位置**: `backend/app/models.py`

```python
class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    questions = relationship("Question", back_populates="subject")
    question_banks = relationship("QuestionBank", back_populates="subject")
```

**字段说明**:
- `id`: 主键，自增整数
- `name`: 学科名称，最大100字符，不能为空
- `description`: 学科描述，文本类型，可为空
- `created_at`: 创建时间
- `updated_at`: 更新时间

**关系**:
- 一对多关系：一个学科可以有多个题目
- 一对多关系：一个学科可以有多个题库

### 3. 题库模型 (QuestionBank)

**文件位置**: `backend/app/models.py`

```python
class QuestionBank(Base):
    __tablename__ = "question_banks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    total_questions = Column(Integer, default=0)
    imported_questions = Column(Integer, default=0)
    status = Column(Enum(QuestionBankStatus), default=QuestionBankStatus.PENDING)
    error_message = Column(Text, nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    subject = relationship("Subject", back_populates="question_banks")
    questions = relationship("Question", back_populates="question_bank")
```

**字段说明**:
- `id`: 主键，自增整数
- `name`: 题库名称，最大200字符，不能为空
- `description`: 题库描述，文本类型，可为空
- `file_name`: 原始文件名，最大255字符
- `file_path`: 文件存储路径，最大500字符
- `total_questions`: 题库中总题目数量
- `imported_questions`: 已成功导入的题目数量
- `status`: 题库状态枚举值（pending/processing/completed/failed）
- `error_message`: 错误信息，文本类型
- `subject_id`: 外键，关联学科表
- `created_at`: 创建时间
- `updated_at`: 更新时间

**关系**:
- 多对一关系：多个题库属于一个学科
- 一对多关系：一个题库可以有多个题目

### 4. 题目模型 (Question)

**文件位置**: `backend/app/models.py`

```python
class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    options = Column(JSON, nullable=True)  # 存储选择题选项
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.MEDIUM)
    tags = Column(String(500), nullable=True)  # 逗号分隔的标签
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    question_bank_id = Column(Integer, ForeignKey("question_banks.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    subject = relationship("Subject", back_populates="questions")
    question_bank = relationship("QuestionBank", back_populates="questions")
    user_answers = relationship("UserAnswer", back_populates="question")
```

**字段说明**:
- `id`: 主键，自增整数
- `content`: 题目内容，文本类型，不能为空
- `question_type`: 题目类型枚举值（single_choice/multiple_choice/true_false/fill_blank/essay）
- `options`: 选择题选项，JSON格式存储
- `correct_answer`: 正确答案，文本类型
- `explanation`: 题目解析，文本类型
- `difficulty`: 难度等级枚举值（easy/medium/hard）
- `tags`: 题目标签，字符串，逗号分隔
- `subject_id`: 外键，关联学科表
- `question_bank_id`: 外键，关联题库表，可为空
- `created_at`: 创建时间
- `updated_at`: 更新时间

**关系**:
- 多对一关系：多个题目属于一个学科
- 多对一关系：多个题目属于一个题库
- 一对多关系：一个题目可以有多个用户答案记录

### 5. 用户答案模型 (UserAnswer)

**文件位置**: `backend/app/models.py`

```python
class UserAnswer(Base):
    __tablename__ = "user_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    answered_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User")
    question = relationship("Question", back_populates="user_answers")
```

**字段说明**:
- `id`: 主键，自增整数
- `user_id`: 外键，关联用户表
- `question_id`: 外键，关联题目表
- `user_answer`: 用户答案，文本类型
- `is_correct`: 答案是否正确，布尔值
- `answered_at`: 答题时间

**关系**:
- 多对一关系：多个答案记录属于一个用户
- 多对一关系：多个答案记录属于一个题目

## 枚举类型定义

### 题目类型 (QuestionType)

```python
class QuestionType(str, Enum):
    SINGLE_CHOICE = "single_choice"      # 单选题
    MULTIPLE_CHOICE = "multiple_choice"  # 多选题
    TRUE_FALSE = "true_false"            # 判断题
    FILL_BLANK = "fill_blank"            # 填空题
    ESSAY = "essay"                      # 问答题
```

### 难度等级 (DifficultyLevel)

```python
class DifficultyLevel(str, Enum):
    EASY = "easy"      # 简单
    MEDIUM = "medium"  # 中等
    HARD = "hard"      # 困难
```

### 题库状态 (QuestionBankStatus)

```python
class QuestionBankStatus(str, Enum):
    PENDING = "pending"        # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败
```

## 数据库关系图

```
User (用户)
  |
  └── UserAnswer (用户答案)
        |
        └── Question (题目)
              |
              ├── Subject (学科)
              └── QuestionBank (题库)
                    |
                    └── Subject (学科)
```

## 主要特性

### 1. 数据完整性
- 使用外键约束确保数据关系的完整性
- 设置必要字段的非空约束
- 使用唯一约束防止重复数据

### 2. 索引优化
- 在经常查询的字段上建立索引
- 外键字段自动建立索引
- 用户名、邮箱等唯一字段建立唯一索引

### 3. 时间戳管理
- 所有主要表都包含创建时间和更新时间
- 更新时间自动维护

### 4. 状态管理
- 题库导入过程使用状态机管理
- 用户激活状态管理
- 答题正确性记录

### 5. 灵活性设计
- 题目选项使用JSON格式存储，支持不同类型题目
- 标签系统支持灵活的题目分类
- 题目可以独立存在或属于题库

## API数据传输对象 (DTO)

系统还定义了相应的Pydantic模型用于API数据传输，这些模型位于各个服务模块中，提供了数据验证和序列化功能。主要包括：

- 用户相关：`User`, `LoginForm`, `RegisterForm`
- 学科相关：`Subject`, `CreateSubjectForm`
- 题库相关：`QuestionBank`, `QuestionBankImportRequest`, `QuestionBankImportResponse`
- 题目相关：`Question`, `CreateQuestionForm`

这种设计确保了数据的类型安全和API文档的自动生成。