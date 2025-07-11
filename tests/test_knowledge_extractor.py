"""
知识提取器单元测试
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.backend.services.knowledge_extractor import (
    KnowledgeExtractor, 
    ExtractedKnowledgePoint, 
    ExtractedDomain,
    PDFParser,
    DocxParser,
    MarkdownParser,
    TextParser
)

class TestKnowledgeExtractor(unittest.TestCase):
    """知识提取器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.extractor = KnowledgeExtractor()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_extract_domain_name(self):
        """测试知识域名称提取"""
        # 测试从文件名提取
        file_path = "/path/to/第1章_系统架构.pdf"
        content = "一些内容"
        
        domain_name = self.extractor._extract_domain_name(file_path, content)
        self.assertIn("系统架构", domain_name)
        
        # 测试从内容提取
        content_with_title = "第1章 数据库设计原理\n\n这是一些内容..."
        domain_name = self.extractor._extract_domain_name(file_path, content_with_title)
        self.assertEqual(domain_name, "数据库设计原理")
    
    def test_extract_domain_description(self):
        """测试知识域描述提取"""
        content = """第1章 系统架构设计
        
        系统架构设计是软件开发过程中的重要环节。
        
        它包括系统的整体结构设计、组件划分等。
        
        本章将详细介绍系统架构设计的方法和原则。"""
        
        description = self.extractor._extract_domain_description(content)
        self.assertIn("系统架构设计", description)
        self.assertIn("软件开发", description)
    
    def test_extract_keywords(self):
        """测试关键词提取"""
        text = "理解HTTP协议、掌握RESTful API设计、了解微服务架构"
        
        keywords = self.extractor._extract_keywords(text)
        self.assertIsInstance(keywords, list)
        self.assertTrue(len(keywords) >= 0)
    
    def test_determine_difficulty(self):
        """测试难度级别确定"""
        # 测试不同难度关键词
        easy_text = "了解基本概念"
        medium_text = "理解核心原理"
        hard_text = "掌握高级技术"
        expert_text = "精通复杂系统"
        
        self.assertEqual(self.extractor._determine_difficulty(easy_text), 1)
        self.assertEqual(self.extractor._determine_difficulty(medium_text), 2)
        self.assertEqual(self.extractor._determine_difficulty(hard_text), 3)
        self.assertEqual(self.extractor._determine_difficulty(expert_text), 5)
    
    def test_extract_learning_objectives(self):
        """测试学习目标提取"""
        description = """学习目标：
        1. 能够设计系统架构
        2. 掌握设计模式
        3. 理解性能优化
        """
        
        objectives = self.extractor._extract_learning_objectives(description, "")
        self.assertIsInstance(objectives, list)
        self.assertTrue(any("设计系统架构" in obj for obj in objectives))
    
    def test_extract_examples(self):
        """测试示例提取"""
        content = "例如：MVC模式是一种常见的设计模式。比如：在Web开发中广泛应用。"
        
        examples = self.extractor._extract_examples(content, "")
        self.assertIsInstance(examples, str)
        if examples:
            self.assertIn("MVC", examples)
    
    def test_extract_dependencies(self):
        """测试依赖关系提取"""
        text = "需要先学习Java基础，必须掌握面向对象编程"
        
        dependencies = self.extractor._extract_dependencies(text, "")
        self.assertIsInstance(dependencies, list)
        self.assertTrue(any("Java" in dep for dep in dependencies))
    
    def test_create_knowledge_point(self):
        """测试知识点创建"""
        kp = self.extractor._create_knowledge_point(
            name="HTTP协议",
            description="理解HTTP协议的工作原理",
            chapter="网络编程",
            section="协议基础",
            content="HTTP是超文本传输协议..."
        )
        
        self.assertIsInstance(kp, ExtractedKnowledgePoint)
        self.assertEqual(kp.name, "HTTP协议")
        self.assertEqual(kp.chapter, "网络编程")
        self.assertIsInstance(kp.keywords, list)
        self.assertIsInstance(kp.difficulty_level, int)
        self.assertTrue(1 <= kp.difficulty_level <= 5)
    
    def test_deduplicate_knowledge_points(self):
        """测试知识点去重"""
        kp1 = ExtractedKnowledgePoint(
            name="HTTP协议", description="", content="", difficulty_level=2,
            keywords=[], learning_objectives=[], examples="", chapter="",
            section="", references=[], dependencies=[]
        )
        kp2 = ExtractedKnowledgePoint(
            name="HTTP 协议", description="", content="", difficulty_level=2,
            keywords=[], learning_objectives=[], examples="", chapter="",
            section="", references=[], dependencies=[]
        )
        kp3 = ExtractedKnowledgePoint(
            name="HTTPS协议", description="", content="", difficulty_level=3,
            keywords=[], learning_objectives=[], examples="", chapter="",
            section="", references=[], dependencies=[]
        )
        
        knowledge_points = [kp1, kp2, kp3]
        unique_points = self.extractor._deduplicate_knowledge_points(knowledge_points)
        
        # 应该去除重复的HTTP协议
        self.assertEqual(len(unique_points), 2)
        names = [kp.name for kp in unique_points]
        self.assertIn("HTTP协议", names)
        self.assertIn("HTTPS协议", names)
    
    def test_calculate_exam_weight(self):
        """测试考试权重计算"""
        # 短内容
        short_content = "简单的内容"
        weight1 = self.extractor._calculate_exam_weight(short_content)
        
        # 长内容
        long_content = "这是一个很长的内容" * 1000
        weight2 = self.extractor._calculate_exam_weight(long_content)
        
        # 包含重要关键词的内容
        important_content = "这是重点内容，核心知识点"
        weight3 = self.extractor._calculate_exam_weight(important_content)
        
        self.assertTrue(0.0 <= weight1 <= 1.0)
        self.assertTrue(0.0 <= weight2 <= 1.0)
        self.assertTrue(0.0 <= weight3 <= 1.0)
        self.assertTrue(weight2 > weight1)  # 长内容权重更高
        self.assertTrue(weight3 > weight1)  # 重要内容权重更高
    
    def test_build_dependencies(self):
        """测试依赖关系构建"""
        # 创建测试知识点
        kp1 = ExtractedKnowledgePoint(
            name="Java基础", description="", content="", difficulty_level=1,
            keywords=[], learning_objectives=[], examples="", chapter="",
            section="", references=[], dependencies=[]
        )
        kp2 = ExtractedKnowledgePoint(
            name="面向对象编程", description="", content="", difficulty_level=2,
            keywords=[], learning_objectives=[], examples="", chapter="",
            section="", references=[], dependencies=["Java基础"]
        )
        
        domain = ExtractedDomain(
            name="编程基础",
            description="编程基础知识",
            knowledge_points=[kp1, kp2],
            exam_weight=0.3,
            sort_order=1
        )
        
        self.extractor._build_dependencies([domain])
        
        # 检查依赖关系是否正确解析
        self.assertIn("Java基础", kp2.dependencies)
    
    def test_generate_knowledge_graph_data(self):
        """测试知识图谱数据生成"""
        # 创建测试数据
        kp1 = ExtractedKnowledgePoint(
            name="Java基础", description="Java编程基础", content="", difficulty_level=1,
            keywords=["Java"], learning_objectives=[], examples="", chapter="第1章",
            section="基础", references=[], dependencies=[]
        )
        kp2 = ExtractedKnowledgePoint(
            name="面向对象", description="面向对象编程", content="", difficulty_level=2,
            keywords=["OOP"], learning_objectives=[], examples="", chapter="第2章",
            section="进阶", references=[], dependencies=["Java基础"]
        )
        
        domain = ExtractedDomain(
            name="Java编程",
            description="Java编程知识",
            knowledge_points=[kp1, kp2],
            exam_weight=0.4,
            sort_order=1
        )
        
        graph_data = self.extractor.generate_knowledge_graph_data([domain])
        
        self.assertIn('nodes', graph_data)
        self.assertIn('edges', graph_data)
        self.assertIn('statistics', graph_data)
        
        # 检查节点数量
        nodes = graph_data['nodes']
        self.assertEqual(len(nodes), 3)  # 1个域 + 2个知识点
        
        # 检查边数量
        edges = graph_data['edges']
        self.assertTrue(len(edges) >= 2)  # 至少有域到知识点的边
        
        # 检查统计信息
        stats = graph_data['statistics']
        self.assertEqual(stats['domain_count'], 1)
        self.assertEqual(stats['knowledge_point_count'], 2)


class TestDocumentParsers(unittest.TestCase):
    """文档解析器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_text_parser(self):
        """测试文本解析器"""
        parser = TextParser()
        
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, "test.txt")
        test_content = "这是一个测试文件\n包含多行内容\n用于测试文本解析"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        result = parser.parse(test_file)
        
        self.assertEqual(result['type'], 'text')
        self.assertEqual(result['content'], test_content)
        self.assertEqual(result['lines'], 3)
    
    def test_markdown_parser(self):
        """测试Markdown解析器"""
        parser = MarkdownParser()
        
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, "test.md")
        test_content = """# 标题1
        
## 标题2

这是一些内容

### 标题3

更多内容"""
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        result = parser.parse(test_file)
        
        self.assertEqual(result['type'], 'markdown')
        self.assertIn('structure', result)
        self.assertIn('html', result)
        
        # 检查结构解析
        structure = result['structure']
        self.assertTrue(len(structure) >= 3)  # 至少3个标题
        self.assertEqual(structure[0]['level'], 1)
        self.assertEqual(structure[1]['level'], 2)
    
    @patch('PyPDF2.PdfReader')
    def test_pdf_parser(self, mock_pdf_reader):
        """测试PDF解析器"""
        parser = PDFParser()
        
        # Mock PDF读取
        mock_page = Mock()
        mock_page.extract_text.return_value = "PDF内容"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page, mock_page]
        mock_reader.metadata = {"title": "测试PDF"}
        
        mock_pdf_reader.return_value = mock_reader
        
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, "test.pdf")
        with open(test_file, 'wb') as f:
            f.write(b"fake pdf content")
        
        result = parser.parse(test_file)
        
        self.assertEqual(result['type'], 'pdf')
        self.assertIn('PDF内容', result['content'])
        self.assertEqual(result['pages'], 2)
    
    @patch('docx.Document')
    def test_docx_parser(self, mock_document):
        """测试Word文档解析器"""
        parser = DocxParser()
        
        # Mock段落
        mock_para1 = Mock()
        mock_para1.text = "标题段落"
        mock_para1.style.name = "Heading 1"
        
        mock_para2 = Mock()
        mock_para2.text = "普通段落内容"
        mock_para2.style.name = "Normal"
        
        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_document.return_value = mock_doc
        
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, "test.docx")
        with open(test_file, 'wb') as f:
            f.write(b"fake docx content")
        
        result = parser.parse(test_file)
        
        self.assertEqual(result['type'], 'docx')
        self.assertIn('标题段落', result['content'])
        self.assertIn('普通段落', result['content'])
        self.assertIn('structure', result)
        
        # 检查结构解析
        structure = result['structure']
        self.assertEqual(len(structure), 2)
        self.assertEqual(structure[0]['type'], 'heading')
        self.assertEqual(structure[1]['type'], 'paragraph')


class TestKnowledgeExtractionIntegration(unittest.TestCase):
    """知识提取集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.extractor = KnowledgeExtractor()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_extract_from_directory_empty(self):
        """测试从空目录提取"""
        results = self.extractor.extract_from_directory(self.temp_dir)
        self.assertEqual(len(results), 0)
    
    def test_extract_from_directory_with_files(self):
        """测试从包含文件的目录提取"""
        # 创建测试文件
        test_content = """第1章 系统设计基础

系统设计是软件工程的重要组成部分。

## 1.1 设计原则

理解SOLID原则：
- 单一职责原则
- 开闭原则  
- 里氏替换原则

掌握设计模式的应用。

例如：工厂模式、观察者模式等。

学习目标：
1. 能够应用设计原则
2. 掌握常用设计模式
"""
        
        test_file = os.path.join(self.temp_dir, "chapter1.md")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # 模拟进度回调
        progress_calls = []
        def progress_callback(progress, message):
            progress_calls.append((progress, message))
        
        results = self.extractor.extract_from_directory(
            self.temp_dir, 
            progress_callback=progress_callback
        )
        
        self.assertTrue(len(results) > 0)
        self.assertTrue(len(progress_calls) > 0)
        
        # 检查提取的域
        domain = results[0]
        self.assertIsInstance(domain, ExtractedDomain)
        self.assertIn("系统设计", domain.name)
        self.assertTrue(len(domain.knowledge_points) > 0)
        
        # 检查知识点
        for kp in domain.knowledge_points:
            self.assertIsInstance(kp, ExtractedKnowledgePoint)
            self.assertTrue(len(kp.name) > 0)
            self.assertTrue(1 <= kp.difficulty_level <= 5)

if __name__ == '__main__':
    unittest.main() 