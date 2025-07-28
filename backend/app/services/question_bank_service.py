"""题库服务模块，提供题库管理和题目导入功能。"""
import json
import logging
import re
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.db import models
from app.schemas.question_bank import QuestionImportItem

logger = logging.getLogger(__name__)


class QuestionBankService:
    """题库服务类"""

    def __init__(self, db: Session):
        self.db = db

    def create_question_bank(
        self, name: str, description: str, file_name: str, subject_id: int | None = None
    ) -> models.QuestionBank:
        """创建题库记录"""
        question_bank = models.QuestionBank(
            name=name,
            description=description,
            file_name=file_name,
            subject_id=subject_id,
            status="pending"
        )
        self.db.add(question_bank)
        self.db.commit()
        self.db.refresh(question_bank)
        return question_bank

    def parse_question_bank_file(self, file_content: str) -> list[QuestionImportItem]:
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
                
                # 处理raw_data字段，确保传入字符串
                raw_data = item.get("raw_data", "")
                if isinstance(raw_data, dict):
                    # 如果是字典，尝试获取文本内容
                    content_text = raw_data.get("content", "") or raw_data.get("text", "") or str(raw_data)
                else:
                    content_text = str(raw_data) if raw_data else ""
                
                # 清理title
                raw_title = item.get("question_title", "")
                title = self._clean_html_content(raw_title)
                
                # 获取题目类型，优先使用show_type_name
                show_type_name = ""
                if "raw_data" in item and isinstance(item["raw_data"], dict):
                    show_type_name = item["raw_data"].get("show_type_name", "")
                
                question_item = QuestionImportItem(
                    section_id=item.get("section_id"),
                    section_name=item.get("section_name", ""),
                    question_id=item.get("question_id"),
                    question_title=item.get("question_title", ""),
                    question_type=item.get("question_type", 1),
                    answer_type=1,
                    option=item.get("option", []),
                    answer=item.get("answer", []),
                    analysis=item.get("analysis", ""),
                    raw_data=item.get("raw_data"),
                    crawl_time=item.get("crawl_time"),
                    title=title,
                    content=self._clean_html_content(content_text),
                    options=options,
                    correct_answer=answer_str,
                    explanation=item.get("analysis", ""),
                    difficulty="medium",
                    tags="",
                    show_type_name=show_type_name
                )
                questions.append(question_item)
            
            return questions
        except json.JSONDecodeError as e:
            logger.error("JSON解析错误: %s", e)
            raise ValueError(f"JSON文件格式错误: {e}") from e
        except (ValueError, TypeError) as e:
            logger.error("文件解析错误: %s", e)
            raise ValueError(f"文件解析失败: {e}") from e

    def import_questions(self, question_bank_id: int, questions: list[QuestionImportItem]) -> Dict[str, Any]:
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
                    # 使用题库所属的学科ID，而不是根据section_name自动创建学科
                    if not question_bank.subject_id:
                        raise ValueError("题库未关联学科，无法导入题目")
                    
                    # 检查题目是否已存在（根据原始question_id）
                    existing_question = self.db.query(models.Question).filter(
                        models.Question.title == question_item.title
                    ).first()
                    
                    if existing_question:
                        logger.info("题目已存在，跳过: %s...", question_item.title[:50])
                        continue
                    
                    # 创建新题目
                    question = models.Question(
                        subject_id=question_bank.subject_id,
                        question_bank_id=question_bank.id,
                        title=question_item.title,
                        content=question_item.content,
                        question_type=self._map_question_type_from_item(question_item.question_type, question_item.show_type_name),
                        options=question_item.options,
                        correct_answer=question_item.correct_answer,
                        explanation=question_item.explanation,
                        difficulty=1,
                        tags=[question_item.section_name] if question_item.section_name else []
                    )
                    
                    self.db.add(question)
                    imported_count += 1
                    
                except (ValueError, TypeError, AttributeError, KeyError) as e:
                    failed_count += 1
                    error_msg = f"导入题目失败: {question_item.title[:50]}... - {str(e)}"
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
        
        # 智能提取学科名称
        subject_name = self._extract_subject_name(section_name)
        
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
    
    def _extract_subject_name(self, section_name: str) -> str:
        """智能提取学科名称"""
        # 去掉版本信息
        name = re.sub(r'（第.*?版）', '', section_name)
        
        # 定义学科映射规则
        subject_mapping = {
            '计算机系统基础知识': '计算机系统',
            '信息系统基础知识': '信息系统',
            '信息安全技术基础知识': '信息安全',
            '软件工程基础知识': '软件工程',
            '数据库设计基础知识': '数据库',
            '系统架构设计基础知识': '系统架构',
            '系统质量属性与架构评估': '架构评估',
            '软件可靠性基础知识': '软件可靠性',
            '软件架构的演化和维护': '架构演化',
            '未来信息综合技术': '综合技术',
            '信息系统架构设计理论与实践': '信息系统架构',
            '层次式架构设计理论与实践': '层次式架构',
            '云原生架构设计理论与实践': '云原生架构',
            '面向服务架构设计理论与实践': 'SOA架构',
            '嵌入式系统架构设计理论与实践': '嵌入式架构',
            '通信系统架构设计理论与实践': '通信架构',
            '安全架构设计理论与实践': '安全架构',
            '大数据架构设计理论与实践': '大数据架构',
            '绪论': '软件架构基础'
        }
        
        # 尝试匹配映射规则
        for key, value in subject_mapping.items():
            if key in name:
                return value
        
        # 如果没有匹配到，使用第一个部分作为学科名称
        if ' - ' in name:
            return name.split(' - ')[0].strip()
        
        return name.strip() if name.strip() else '未分类'



    def _map_question_type(self, question_type: int) -> str:
        """映射题目类型"""
        type_mapping = {
            1: "single_choice",  # 单选题
            2: "multiple_choice",  # 多选题
            3: "essay",  # 问答题
            9: "single_choice",  # 填空题当作单选处理
        }
        return type_mapping.get(question_type, "single_choice")
    
    def _map_question_type_from_item(self, question_type, show_type_name: str = "") -> str:
        """从导入项映射题目类型"""
        # 优先使用show_type_name字段
        if show_type_name:
            type_name_mapping = {
                "单选题": "single_choice",
                "多选题": "multiple_choice",
                "判断题": "true_false",
                "填空题": "fill_blank",
                "简答题": "short_answer",
                "问答题": "short_answer",
                "essay": "short_answer"
            }
            mapped_type = type_name_mapping.get(show_type_name, "")
            if mapped_type:
                return mapped_type
        
        # 如果show_type_name没有匹配到，使用原有逻辑
        if isinstance(question_type, str):
            # 如果是字符串，直接返回或映射
            string_mapping = {
                "single_choice": "single_choice",
                "multiple_choice": "multiple_choice",
                "essay": "short_answer",
                "填空题": "fill_blank",
                "单选题": "single_choice",
                "多选题": "multiple_choice",
                "问答题": "short_answer"
            }
            return string_mapping.get(question_type, "single_choice")
        if isinstance(question_type, int):
            return self._map_question_type(question_type)
        return "single_choice"

    def _format_options(self, options: list[str] | None) -> Dict[str, str] | None:
        """格式化选项"""
        if not options:
            return None
        
        formatted_options = {}
        for i, option in enumerate(options):
            formatted_options[chr(65 + i)] = option.strip()
        
        return formatted_options

    def _clean_html_content(self, content: str | dict | None) -> str:
        """清理HTML内容"""
        # 确保content是字符串类型
        if content is None:
            return ""
        if isinstance(content, dict):
            # 如果是字典，尝试获取文本内容
            content = content.get("content", "") or content.get("text", "") or str(content)
        elif not isinstance(content, str):
            content = str(content)
        
        # 简单的HTML标签清理
        content = re.sub(r'<[^>]+>', '', content)
        content = content.replace('&nbsp;', ' ')
        content = content.replace('&lt;', '<')
        content = content.replace('&gt;', '>')
        content = content.replace('&amp;', '&')
        return content.strip()

    def get_question_banks(
        self, skip: int = 0, limit: int = 100, subject_id: int | None = None
    ) -> list[models.QuestionBank]:
        """获取题库列表"""
        query = self.db.query(models.QuestionBank)
        if subject_id is not None:
            query = query.filter(models.QuestionBank.subject_id == subject_id)
        question_banks = query.offset(skip).limit(limit).all()
        
        # 为每个题库计算实际题目数量
        for question_bank in question_banks:
            # 计算特定题库的题目数量
            actual_count = self.db.query(models.Question).filter(
                models.Question.question_bank_id == question_bank.id
            ).count()
            question_bank.question_count = actual_count
        
        return question_banks

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