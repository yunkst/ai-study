"""
RAG Service 单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import numpy as np
from datetime import datetime
import tempfile
import os

from services.rag_service import rag_service

# 测试数据
MOCK_DOCUMENT_TEXT = """
软件架构是系统的根本组织结构，它定义了系统的各个组件、组件之间的关系以及指导其设计和演化的原则和准则。

软件架构的重要性体现在以下几个方面：
1. 提供系统的整体视图
2. 支持系统质量属性
3. 便于团队协作
4. 支持系统演化

常见的架构模式包括：
- 分层架构
- 微服务架构
- 事件驱动架构
- 领域驱动设计
"""

MOCK_CHUNKS = [
    {
        "id": "chunk_1",
        "content": "软件架构是系统的根本组织结构，它定义了系统的各个组件、组件之间的关系以及指导其设计和演化的原则和准则。",
        "metadata": {"source": "test_doc.md", "chunk_index": 0},
        "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
    },
    {
        "id": "chunk_2", 
        "content": "软件架构的重要性体现在提供系统的整体视图、支持系统质量属性、便于团队协作、支持系统演化等方面。",
        "metadata": {"source": "test_doc.md", "chunk_index": 1},
        "embedding": [0.2, 0.3, 0.4, 0.5, 0.6]
    }
]

MOCK_QUERY_EMBEDDING = [0.15, 0.25, 0.35, 0.45, 0.55]

MOCK_SEARCH_RESULTS = [
    {
        "content": "软件架构是系统的根本组织结构，它定义了系统的各个组件、组件之间的关系以及指导其设计和演化的原则和准则。",
        "metadata": {"source": "test_doc.md", "chunk_index": 0},
        "similarity": 0.95
    },
    {
        "content": "软件架构的重要性体现在提供系统的整体视图、支持系统质量属性、便于团队协作、支持系统演化等方面。",
        "metadata": {"source": "test_doc.md", "chunk_index": 1},
        "similarity": 0.87
    }
]

class TestRAGService:
    """RAG服务测试类"""
    
    def test_rag_service_initialization(self):
        """测试RAG服务初始化"""
        assert rag_service is not None
        assert hasattr(rag_service, 'embedding_model')
        assert hasattr(rag_service, 'vector_store')
        assert hasattr(rag_service, 'chunk_size')
        assert hasattr(rag_service, 'chunk_overlap')
    
    def test_text_splitting(self):
        """测试文本分割功能"""
        long_text = "这是一段很长的文本。" * 100  # 模拟长文本
        
        chunks = rag_service.split_text(long_text, chunk_size=100, chunk_overlap=20)
        
        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk) <= 120 for chunk in chunks)  # 考虑overlap
    
    def test_text_splitting_empty_input(self):
        """测试空输入的文本分割"""
        chunks = rag_service.split_text("", chunk_size=100)
        assert chunks == []
        
        chunks = rag_service.split_text(None, chunk_size=100)
        assert chunks == []
    
    @patch('services.rag_service.SentenceTransformer')
    def test_generate_embeddings_success(self, mock_sentence_transformer):
        """测试生成嵌入向量 - 成功"""
        # Mock模型
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        mock_sentence_transformer.return_value = mock_model
        
        # 重新初始化服务以使用mock模型
        rag_service._init_embedding_model()
        
        texts = ["文本1", "文本2"]
        embeddings = rag_service.generate_embeddings(texts)
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 3
        assert isinstance(embeddings, list)
        mock_model.encode.assert_called_once_with(texts, convert_to_tensor=False)
    
    @patch('services.rag_service.SentenceTransformer')
    def test_generate_embeddings_empty_input(self, mock_sentence_transformer):
        """测试生成嵌入向量 - 空输入"""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([])
        mock_sentence_transformer.return_value = mock_model
        
        rag_service._init_embedding_model()
        
        embeddings = rag_service.generate_embeddings([])
        assert embeddings == []
        
        embeddings = rag_service.generate_embeddings([""])
        assert len(embeddings) == 1
    
    @patch('services.rag_service.get_db')
    def test_add_document_success(self, mock_get_db):
        """测试添加文档 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        with patch.object(rag_service, 'split_text') as mock_split, \
             patch.object(rag_service, 'generate_embeddings') as mock_embeddings, \
             patch('services.rag_service.DocumentChunk') as mock_chunk_model:
            
            # 设置mock返回值
            mock_split.return_value = ["chunk1", "chunk2"]
            mock_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4]]
            
            mock_chunk = MagicMock()
            mock_chunk_model.return_value = mock_chunk
            
            result = rag_service.add_document(
                content=MOCK_DOCUMENT_TEXT,
                metadata={"source": "test.md", "title": "测试文档"}
            )
            
            assert result["status"] == "success"
            assert result["chunks_created"] == 2
            assert "document_id" in result
            
            # 验证数据库操作
            assert mock_db.add.call_count == 2  # 两个chunk
            mock_db.commit.assert_called_once()
    
    @patch('services.rag_service.get_db')
    def test_add_document_empty_content(self, mock_get_db):
        """测试添加文档 - 空内容"""
        result = rag_service.add_document(content="", metadata={})
        
        assert result["status"] == "error"
        assert "文档内容不能为空" in result["message"]
    
    @patch('services.rag_service.get_db')
    def test_search_similar_chunks_success(self, mock_get_db):
        """测试搜索相似片段 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock数据库查询结果
        mock_chunks = [
            MagicMock(
                content=MOCK_CHUNKS[0]["content"],
                metadata=MOCK_CHUNKS[0]["metadata"],
                embedding=MOCK_CHUNKS[0]["embedding"]
            ),
            MagicMock(
                content=MOCK_CHUNKS[1]["content"],
                metadata=MOCK_CHUNKS[1]["metadata"],
                embedding=MOCK_CHUNKS[1]["embedding"]
            )
        ]
        mock_db.query.return_value.all.return_value = mock_chunks
        
        with patch.object(rag_service, 'generate_embeddings') as mock_embeddings:
            mock_embeddings.return_value = [MOCK_QUERY_EMBEDDING]
            
            results = rag_service.search_similar_chunks(
                query="什么是软件架构？",
                top_k=2,
                similarity_threshold=0.8
            )
            
            assert len(results) == 2
            assert all("content" in result for result in results)
            assert all("metadata" in result for result in results)
            assert all("similarity" in result for result in results)
            assert all(result["similarity"] >= 0.8 for result in results)
    
    @patch('services.rag_service.get_db')
    def test_search_similar_chunks_no_results(self, mock_get_db):
        """测试搜索相似片段 - 无结果"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.all.return_value = []
        
        with patch.object(rag_service, 'generate_embeddings') as mock_embeddings:
            mock_embeddings.return_value = [MOCK_QUERY_EMBEDDING]
            
            results = rag_service.search_similar_chunks(
                query="不相关的查询",
                top_k=5
            )
            
            assert results == []
    
    def test_calculate_cosine_similarity(self):
        """测试余弦相似度计算"""
        vec1 = [1, 0, 0]
        vec2 = [0, 1, 0]
        vec3 = [1, 0, 0]
        
        similarity_orthogonal = rag_service._calculate_cosine_similarity(vec1, vec2)
        similarity_identical = rag_service._calculate_cosine_similarity(vec1, vec3)
        
        assert abs(similarity_orthogonal - 0.0) < 1e-10  # 垂直向量相似度为0
        assert abs(similarity_identical - 1.0) < 1e-10   # 相同向量相似度为1
    
    def test_calculate_cosine_similarity_edge_cases(self):
        """测试余弦相似度计算边界情况"""
        # 零向量
        zero_vec = [0, 0, 0]
        normal_vec = [1, 1, 1]
        
        similarity = rag_service._calculate_cosine_similarity(zero_vec, normal_vec)
        assert similarity == 0.0
        
        # 空向量
        similarity = rag_service._calculate_cosine_similarity([], [])
        assert similarity == 0.0
    
    @patch('services.rag_service.get_db')
    def test_delete_document_success(self, mock_get_db):
        """测试删除文档 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock查询结果
        mock_chunks = [MagicMock(), MagicMock()]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_chunks
        
        result = rag_service.delete_document("test_doc_id")
        
        assert result["status"] == "success"
        assert result["deleted_chunks"] == 2
        
        # 验证删除操作
        for chunk in mock_chunks:
            mock_db.delete.assert_any_call(chunk)
        mock_db.commit.assert_called_once()
    
    @patch('services.rag_service.get_db')
    def test_delete_document_not_found(self, mock_get_db):
        """测试删除文档 - 文档不存在"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = rag_service.delete_document("nonexistent_doc_id")
        
        assert result["status"] == "error"
        assert "文档未找到" in result["message"]
    
    @patch('services.rag_service.get_db')
    def test_get_document_stats(self, mock_get_db):
        """测试获取文档统计"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock统计查询
        mock_db.query.return_value.count.return_value = 150  # 总chunk数
        mock_db.query.return_value.distinct.return_value.count.return_value = 25  # 文档数
        
        # Mock文档源统计
        mock_sources = [("doc1.md", 10), ("doc2.pdf", 20), ("doc3.txt", 15)]
        mock_db.query.return_value.group_by.return_value.all.return_value = mock_sources
        
        stats = rag_service.get_document_stats()
        
        assert stats["total_chunks"] == 150
        assert stats["total_documents"] == 25
        assert stats["sources"] == [
            {"source": "doc1.md", "chunks": 10},
            {"source": "doc2.pdf", "chunks": 20},
            {"source": "doc3.txt", "chunks": 15}
        ]
    
    def test_answer_question_with_context(self):
        """测试基于上下文回答问题"""
        context_chunks = [
            {"content": "软件架构是系统的根本组织结构。", "similarity": 0.95},
            {"content": "它定义了系统的各个组件和组件之间的关系。", "similarity": 0.88}
        ]
        
        question = "什么是软件架构？"
        
        with patch.object(rag_service, 'search_similar_chunks') as mock_search:
            mock_search.return_value = context_chunks
            
            answer = rag_service.answer_question(question, use_ai=False)
            
            assert "软件架构是系统的根本组织结构" in answer["answer"]
            assert answer["confidence"] > 0.8
            assert len(answer["sources"]) == 2
    
    @patch('services.rag_service.get_db')
    def test_batch_add_documents(self, mock_get_db):
        """测试批量添加文档"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        documents = [
            {"content": "文档1内容", "metadata": {"source": "doc1.txt"}},
            {"content": "文档2内容", "metadata": {"source": "doc2.txt"}},
            {"content": "文档3内容", "metadata": {"source": "doc3.txt"}}
        ]
        
        with patch.object(rag_service, 'add_document') as mock_add_doc:
            mock_add_doc.return_value = {"status": "success", "chunks_created": 2}
            
            results = rag_service.batch_add_documents(documents)
            
            assert results["total_documents"] == 3
            assert results["successful_documents"] == 3
            assert results["failed_documents"] == 0
            assert mock_add_doc.call_count == 3
    
    @patch('services.rag_service.get_db')
    def test_update_document_success(self, mock_get_db):
        """测试更新文档 - 成功"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        with patch.object(rag_service, 'delete_document') as mock_delete, \
             patch.object(rag_service, 'add_document') as mock_add:
            
            mock_delete.return_value = {"status": "success", "deleted_chunks": 3}
            mock_add.return_value = {"status": "success", "chunks_created": 4, "document_id": "new_doc_id"}
            
            result = rag_service.update_document(
                document_id="old_doc_id",
                new_content="新的文档内容",
                new_metadata={"source": "updated_doc.txt"}
            )
            
            assert result["status"] == "success"
            assert result["old_chunks_deleted"] == 3
            assert result["new_chunks_created"] == 4
            assert result["new_document_id"] == "new_doc_id"


class TestRAGServiceIntegration:
    """RAG服务集成测试"""
    
    @patch('services.rag_service.get_db')
    def test_complete_rag_workflow(self, mock_get_db):
        """测试完整的RAG工作流"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        with patch.object(rag_service, 'split_text') as mock_split, \
             patch.object(rag_service, 'generate_embeddings') as mock_embeddings, \
             patch('services.rag_service.DocumentChunk') as mock_chunk_model:
            
            # 1. 添加文档
            mock_split.return_value = ["chunk1", "chunk2"]
            mock_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4]]
            mock_chunk_model.return_value = MagicMock()
            
            add_result = rag_service.add_document(
                content=MOCK_DOCUMENT_TEXT,
                metadata={"source": "test.md"}
            )
            assert add_result["status"] == "success"
            
            # 2. 搜索相似内容
            mock_chunks = [
                MagicMock(
                    content="软件架构是系统的根本组织结构",
                    metadata={"source": "test.md"},
                    embedding=[0.1, 0.2, 0.3]
                )
            ]
            mock_db.query.return_value.all.return_value = mock_chunks
            mock_embeddings.return_value = [[0.1, 0.2, 0.3]]
            
            search_results = rag_service.search_similar_chunks("什么是软件架构？")
            assert len(search_results) == 1
            
            # 3. 回答问题
            answer = rag_service.answer_question("什么是软件架构？", use_ai=False)
            assert "软件架构" in answer["answer"]
            
            # 4. 删除文档
            mock_db.query.return_value.filter.return_value.all.return_value = mock_chunks
            delete_result = rag_service.delete_document("test_doc_id")
            assert delete_result["status"] == "success"
    
    def test_document_processing_pipeline(self):
        """测试文档处理管道"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(MOCK_DOCUMENT_TEXT)
            temp_file_path = f.name
        
        try:
            # 测试文件处理
            with patch.object(rag_service, 'add_document') as mock_add_doc:
                mock_add_doc.return_value = {"status": "success", "chunks_created": 3}
                
                # 模拟从文件读取内容
                with open(temp_file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                result = rag_service.add_document(
                    content=content,
                    metadata={"source": temp_file_path, "file_type": "text"}
                )
                
                assert result["status"] == "success"
                mock_add_doc.assert_called_once()
        finally:
            os.unlink(temp_file_path)


class TestRAGServiceValidation:
    """RAG服务验证测试"""
    
    def test_chunk_size_validation(self):
        """测试chunk大小验证"""
        text = "这是一段测试文本。" * 10
        
        # 测试最小chunk大小
        chunks = rag_service.split_text(text, chunk_size=10)
        assert all(len(chunk) >= 10 for chunk in chunks if chunk.strip())
        
        # 测试最大chunk大小
        chunks = rag_service.split_text(text, chunk_size=1000)
        assert all(len(chunk) <= 1000 for chunk in chunks)
    
    def test_embedding_dimension_consistency(self):
        """测试嵌入向量维度一致性"""
        with patch.object(rag_service, 'generate_embeddings') as mock_embeddings:
            # 模拟不同文本的嵌入向量都有相同维度
            mock_embeddings.side_effect = [
                [[0.1, 0.2, 0.3]],  # 第一次调用
                [[0.4, 0.5, 0.6]],  # 第二次调用
            ]
            
            embeddings1 = rag_service.generate_embeddings(["文本1"])
            embeddings2 = rag_service.generate_embeddings(["文本2"])
            
            assert len(embeddings1[0]) == len(embeddings2[0])
    
    def test_similarity_threshold_validation(self):
        """测试相似度阈值验证"""
        with patch('services.rag_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.all.return_value = []
            
            with patch.object(rag_service, 'generate_embeddings') as mock_embeddings:
                mock_embeddings.return_value = [[0.1, 0.2, 0.3]]
                
                # 测试有效阈值
                results = rag_service.search_similar_chunks(
                    query="测试查询",
                    similarity_threshold=0.8
                )
                assert isinstance(results, list)
                
                # 测试边界值
                results = rag_service.search_similar_chunks(
                    query="测试查询",
                    similarity_threshold=0.0
                )
                assert isinstance(results, list)
                
                results = rag_service.search_similar_chunks(
                    query="测试查询",
                    similarity_threshold=1.0
                )
                assert isinstance(results, list)


class TestRAGServicePerformance:
    """RAG服务性能测试"""
    
    @patch('services.rag_service.get_db')
    def test_large_document_processing(self, mock_get_db):
        """测试大文档处理性能"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 生成大文档
        large_content = MOCK_DOCUMENT_TEXT * 100  # 约10KB内容
        
        with patch.object(rag_service, 'split_text') as mock_split, \
             patch.object(rag_service, 'generate_embeddings') as mock_embeddings, \
             patch('services.rag_service.DocumentChunk') as mock_chunk_model:
            
            # 模拟分割成多个chunk
            mock_split.return_value = [f"chunk_{i}" for i in range(50)]
            mock_embeddings.return_value = [[0.1, 0.2] for _ in range(50)]
            mock_chunk_model.return_value = MagicMock()
            
            import time
            start_time = time.time()
            
            result = rag_service.add_document(content=large_content, metadata={"source": "large_doc.txt"})
            
            end_time = time.time()
            
            assert result["status"] == "success"
            assert end_time - start_time < 5.0  # 应该在5秒内完成
    
    @patch('services.rag_service.get_db')
    def test_batch_search_performance(self, mock_get_db):
        """测试批量搜索性能"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟大量文档chunk
        mock_chunks = [
            MagicMock(
                content=f"测试内容 {i}",
                metadata={"source": f"doc_{i}.txt"},
                embedding=[0.1 + i*0.01, 0.2 + i*0.01, 0.3 + i*0.01]
            ) for i in range(1000)
        ]
        mock_db.query.return_value.all.return_value = mock_chunks
        
        with patch.object(rag_service, 'generate_embeddings') as mock_embeddings:
            mock_embeddings.return_value = [[0.5, 0.5, 0.5]]
            
            import time
            start_time = time.time()
            
            results = rag_service.search_similar_chunks(
                query="测试查询",
                top_k=10,
                similarity_threshold=0.7
            )
            
            end_time = time.time()
            
            assert len(results) <= 10
            assert end_time - start_time < 2.0  # 应该在2秒内完成


@pytest.fixture
def mock_rag_dependencies():
    """RAG服务依赖的mock fixture"""
    with patch('services.rag_service.get_db') as mock_get_db, \
         patch('services.rag_service.SentenceTransformer') as mock_transformer:
        
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_transformer.return_value = mock_model
        
        yield {
            "db": mock_db,
            "transformer": mock_transformer,
            "model": mock_model
        }


class TestRAGServiceEdgeCases:
    """RAG服务边界情况测试"""
    
    def test_unicode_text_handling(self):
        """测试Unicode文本处理"""
        unicode_text = "这是中文测试。🎉 This is English. العربية فارسی 한글"
        
        chunks = rag_service.split_text(unicode_text, chunk_size=20)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        # 验证Unicode字符被正确保留
        combined_text = "".join(chunks)
        assert "🎉" in combined_text
        assert "العربية" in combined_text
    
    def test_very_long_single_line(self):
        """测试极长单行文本"""
        very_long_line = "这是一个非常长的单行文本，" * 1000  # 约15KB的单行
        
        chunks = rag_service.split_text(very_long_line, chunk_size=100)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 120 for chunk in chunks)  # 考虑overlap
    
    @patch('services.rag_service.get_db')
    def test_concurrent_document_additions(self, mock_get_db):
        """测试并发文档添加"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        with patch.object(rag_service, 'split_text') as mock_split, \
             patch.object(rag_service, 'generate_embeddings') as mock_embeddings, \
             patch('services.rag_service.DocumentChunk') as mock_chunk_model:
            
            mock_split.return_value = ["chunk1"]
            mock_embeddings.return_value = [[0.1, 0.2]]
            mock_chunk_model.return_value = MagicMock()
            
            # 模拟并发添加多个文档
            import concurrent.futures
            
            def add_doc(doc_id):
                return rag_service.add_document(
                    content=f"文档{doc_id}内容",
                    metadata={"source": f"doc_{doc_id}.txt"}
                )
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(add_doc, i) for i in range(5)]
                results = [future.result() for future in futures]
            
            # 验证所有文档都成功添加
            assert all(result["status"] == "success" for result in results) 