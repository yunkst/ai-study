"""题库服务模块，提供题库管理和题目导入功能。"""
import json
import logging
import re
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.db import models
from app.schemas.question_bank import QuestionImportItem

logger = logging.getLogger(__name__)


class QuestionBankService:
    """题库服务类"""

    def __init__(self, db: Session):
        self.db = db

    def create_question_bank(self, name: str, description: str, file_name: str) -> models.QuestionBank:
        """创建题库记录"""
        question_bank = models.QuestionBank(
            name=name,
            description=description,
            file_name=file_name,
            status="pending"
        )
        self.db.add(question_bank)
        self.db.commit()
        self.db.refresh(question_bank)
        return question_bank

    def parse_question_bank_file(self, file_content: str) -> List[QuestionImportItem]:
        """解析题库JSON文件"""
        try:
            data = json.loads(file_content)
            questions = []
            
            for item in data:
                # 解析选项
                options = self._format_options(item.get("option", []))
                
                # 解析答案
                answers = item.get("answer", [])
                answer_str = ",".join(answers) if answers else ""
                
                question_item = QuestionImportItem(
                    section_id=item.get("section_id"),
                    section_name=item.get("section_name", ""),
                    question_id=item.get("question_id"),
                    title=item.get("question_title", ""),
                    content=self._clean_html_content(item.get("raw_data", "")),
                    question_type=self._map_question_type(item.get("question_type", 1)),
                    options=options,
                    correct_answer=answer_str,
                    explanation=item.get("analysis", ""),
                    difficulty="medium",
                    tags=""
                )
                questions.append(question_item)
            
            return questions
        except json.JSONDecodeError as e:
            logger.error("JSON解析错误: %s", e)
            raise ValueError(f"JSON文件格式错误: {e}") from e
        except (ValueError, TypeError) as e:
            logger.error("文件解析错误: %s", e)
            raise ValueError(f"文件解析失败: {e}") from e

    def import_questions(self, question_bank_id: int, questions: List[QuestionImportItem]) -> Dict[str, Any]:
        """导入题目到数据库"""
        question_bank = self.db.query(models.QuestionBank).filter(
            models.QuestionBank.id == question_bank_id
        ).first()
        
        if not question_bank:
            raise ValueError("题库不存在")
        
        # 更新状态为处理中
        question_bank.status = "processing"
        question_bank.total_questions = len(questions)
        self.db.commit()
        
        imported_count = 0
        failed_count = 0
        errors = []
        
        try:
            for question_item in questions:
                try:
                    # 查找或创建学科
                    subject = self._get_or_create_subject(question_item.section_name)
                    
                    # 检查题目是否已存在（根据原始question_id）
                    existing_question = self.db.query(models.Question).filter(
                        models.Question.title == question_item.question_title
                    ).first()
                    
                    if existing_question:
                        logger.info("题目已存在，跳过: %s...", question_item.question_title[:50])
                        continue
                    
                    # 创建新题目
                    question = models.Question(
                        subject_id=subject.id,
                        title=question_item.question_title,
                        content=self._clean_html_content(question_item.question_title),
                        question_type=self._map_question_type(question_item.question_type),
                        options=self._format_options(question_item.option),
                        correct_answer=",".join(question_item.answer),
                        explanation=question_item.analysis or "",
                        difficulty=1,
                        tags=[question_item.section_name] if question_item.section_name else []
                    )
                    
                    self.db.add(question)
                    imported_count += 1
                    
                except (ValueError, TypeError, AttributeError, KeyError) as e:
                    failed_count += 1
                    error_msg = f"导入题目失败: {question_item.question_title[:50]}... - {str(e)}"
                    errors.append(error_msg)
                    logger.error("导入题目失败: %s", str(e))
            
            # 批量提交
            self.db.commit()
            
            # 更新题库状态
            question_bank.imported_questions = imported_count
            question_bank.status = "completed" if failed_count == 0 else "completed_with_errors"
            if errors:
                question_bank.error_message = "\n".join(errors[:10])  # 只保存前10个错误
            
            self.db.commit()
            
            return {
                "imported_count": imported_count,
                "failed_count": failed_count,
                "errors": errors
            }
            
        except (ValueError, TypeError, AttributeError) as e:
            self.db.rollback()
            question_bank.status = "failed"
            question_bank.error_message = str(e)
            self.db.commit()
            raise e

    def _get_or_create_subject(self, section_name: str) -> models.Subject:
        """获取或创建学科"""
        if not section_name:
            section_name = "未分类"
        
        # 提取学科名称（去掉版本信息等）
        subject_name = section_name.split(" - ")[0] if " - " in section_name else section_name
        
        subject = self.db.query(models.Subject).filter(
            models.Subject.name == subject_name
        ).first()
        
        if not subject:
            subject = models.Subject(
                name=subject_name,
                description=f"从题库导入: {section_name}"
            )
            self.db.add(subject)
            self.db.flush()  # 获取ID但不提交事务
        
        return subject



    def _map_question_type(self, question_type: int) -> str:
        """映射题目类型"""
        type_mapping = {
            1: "single_choice",  # 单选题
            2: "multiple_choice",  # 多选题
            3: "essay",  # 问答题
            9: "single_choice",  # 填空题当作单选处理
        }
        return type_mapping.get(question_type, "single_choice")

    def _format_options(self, options: List[str] | None) -> Dict[str, str] | None:
        """格式化选项"""
        if not options:
            return None
        
        formatted_options = {}
        for i, option in enumerate(options):
            formatted_options[chr(65 + i)] = option.strip()
        
        return formatted_options

    def _clean_html_content(self, content: str) -> str:
        """清理HTML内容"""
        # 简单的HTML标签清理
        content = re.sub(r'<[^>]+>', '', content)
        content = content.replace('&nbsp;', ' ')
        content = content.replace('&lt;', '<')
        content = content.replace('&gt;', '>')
        content = content.replace('&amp;', '&')
        return content.strip()

    def get_question_banks(self, skip: int = 0, limit: int = 100) -> List[models.QuestionBank]:
        """获取题库列表"""
        return self.db.query(models.QuestionBank).offset(skip).limit(limit).all()

    def get_question_bank(self, question_bank_id: int) -> models.QuestionBank | None:
        """获取单个题库"""
        return self.db.query(models.QuestionBank).filter(
            models.QuestionBank.id == question_bank_id
        ).first()

    def delete_question_bank(self, question_bank_id: int) -> bool:
        """删除题库"""
        question_bank = self.get_question_bank(question_bank_id)
        if question_bank:
            self.db.delete(question_bank)
            self.db.commit()
            return True
        return False