"""
RAG (Retrieval-Augmented Generation) 服务
提供文档向量化、智能检索和问答功能
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
from datetime import datetime
import hashlib
import json

from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, String, Text, DateTime, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 文档处理相关
import PyPDF2
import docx
from markdown import markdown
from bs4 import BeautifulSoup
import jieba
import re

# 向量化相关 (这里用伪代码，实际需要安装相应包)
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# 向量数据库相关 (简化版，实际可用 Chroma, Pinecone 等)
try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

logger = logging.getLogger(__name__)

# 数据库模型
Base = declarative_base()

class DocumentChunk(Base):
    """文档分块存储"""
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True)
    source_file = Column(String, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    meta = Column(Text)  # JSON格式 (避免 metadata 保留名)
    embedding_model = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RAGService:
    """RAG服务类"""
    
    def __init__(self, db_session: Session = None):
        self.db_session = db_session
        self.embedding_model = None
        self.vector_index = None
        self.chunk_size = 1024
        self.chunk_overlap = 200
        
        # 初始化向量数据库
        self._init_vector_store()
        
    def _init_vector_store(self):
        """初始化向量存储"""
        try:
            if FAISS_AVAILABLE:
                # 简化的FAISS索引
                self.vector_index = None
                logger.info("FAISS向量存储初始化成功")
            else:
                logger.warning("FAISS不可用，将使用内存存储")
                self.vector_store = {}
        except Exception as e:
            logger.error(f"向量存储初始化失败: {e}")
    
    def _load_embedding_model(self, model_name: str = "bge-m3"):
        """加载向量化模型"""
        try:
            if model_name == "bge-m3" and SENTENCE_TRANSFORMERS_AVAILABLE:
                # 使用本地BGE-M3模型
                self.embedding_model = SentenceTransformer('BAAI/bge-m3')
                logger.info("BGE-M3模型加载成功")
            elif model_name == "ada-002" and OPENAI_AVAILABLE:
                # 使用OpenAI的embedding模型
                self.embedding_model = "text-embedding-ada-002"
                logger.info("OpenAI Embedding模型配置成功")
            else:
                # 简化的假模型（实际项目中需要真实模型）
                logger.warning("使用简化向量化模型")
                self.embedding_model = "simple"
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            self.embedding_model = "simple"
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """从文件中提取文本"""
        file_path = Path(file_path)
        
        try:
            if file_path.suffix.lower() == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_path.suffix.lower() in ['.doc', '.docx']:
                return self._extract_from_docx(file_path)
            elif file_path.suffix.lower() == '.md':
                return self._extract_from_markdown(file_path)
            elif file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(f"不支持的文件类型: {file_path.suffix}")
                return ""
        except Exception as e:
            logger.error(f"文件文本提取失败 {file_path}: {e}")
            return ""
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """从PDF提取文本"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"PDF文本提取失败: {e}")
        return text
    
    def _extract_from_docx(self, file_path: Path) -> str:
        """从Word文档提取文本"""
        text = ""
        try:
            doc = docx.Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            logger.error(f"Word文档文本提取失败: {e}")
        return text
    
    def _extract_from_markdown(self, file_path: Path) -> str:
        """从Markdown提取文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 转换为HTML再提取纯文本
            html = markdown(md_content)
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text()
        except Exception as e:
            logger.error(f"Markdown文本提取失败: {e}")
            return ""
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = 1024) -> List[str]:
        """将文本分割成块"""
        # 简化的分块策略
        chunks = []
        
        # 按段落分割
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            # 如果当前段落太长，进一步分割
            if len(paragraph) > chunk_size:
                # 保存当前块
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # 分割长段落
                sentences = re.split(r'[。！？\n]', paragraph)
                for sentence in sentences:
                    if len(current_chunk + sentence) > chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += sentence + "。"
            else:
                # 检查是否会超过块大小
                if len(current_chunk + paragraph) > chunk_size:
                    # 保存当前块，开始新块
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    current_chunk += "\n\n" + paragraph
        
        # 添加最后一块
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _generate_embedding(self, text: str) -> List[float]:
        """生成文本向量"""
        try:
            if hasattr(self.embedding_model, 'encode'):
                # SentenceTransformers模型
                embedding = self.embedding_model.encode([text])[0]
                return embedding.tolist()
            elif self.embedding_model == "text-embedding-ada-002":
                # OpenAI模型
                response = openai.Embedding.create(
                    input=text,
                    model="text-embedding-ada-002"
                )
                return response['data'][0]['embedding']
            else:
                # 简化的假向量（实际使用中需要真实的embedding）
                import hashlib
                hash_obj = hashlib.md5(text.encode())
                # 生成固定长度的伪向量
                vector = [float(int(hash_obj.hexdigest()[i:i+2], 16)) for i in range(0, 32, 2)]
                return vector
        except Exception as e:
            logger.error(f"向量生成失败: {e}")
            return [0.0] * 16  # 返回零向量
    
    def _store_chunk_embedding(self, chunk_id: str, embedding: List[float]):
        """存储块向量"""
        try:
            if FAISS_AVAILABLE and self.vector_index is not None:
                # 使用FAISS存储
                vector = np.array([embedding], dtype=np.float32)
                self.vector_index.add(vector)
            else:
                # 使用内存存储
                if not hasattr(self, 'vector_store'):
                    self.vector_store = {}
                self.vector_store[chunk_id] = embedding
        except Exception as e:
            logger.error(f"向量存储失败: {e}")
    
    async def process_documents(
        self, 
        mode: str = "full", 
        embedding_model: str = "bge-m3",
        chunk_size: int = 1024
    ):
        """处理文档并向量化"""
        try:
            logger.info(f"开始RAG文档处理: {mode} 模式")
            
            # 加载模型
            self._load_embedding_model(embedding_model)
            self.chunk_size = chunk_size
            
            # 扫描文档目录
            document_paths = self._scan_documents()
            
            if not document_paths:
                logger.warning("未找到需要处理的文档")
                return
            
            # 处理每个文档
            total_docs = len(document_paths)
            for idx, doc_path in enumerate(document_paths):
                logger.info(f"处理文档 {idx+1}/{total_docs}: {doc_path}")
                
                # 提取文本
                text_content = self._extract_text_from_file(doc_path)
                if not text_content.strip():
                    continue
                
                # 分块
                chunks = self._split_text_into_chunks(text_content, chunk_size)
                
                # 向量化并存储
                for chunk_idx, chunk_text in enumerate(chunks):
                    chunk_id = f"{Path(doc_path).stem}_{chunk_idx}"
                    
                    # 生成向量
                    embedding = self._generate_embedding(chunk_text)
                    
                    # 存储块信息
                    await self._store_document_chunk(
                        chunk_id=chunk_id,
                        source_file=str(doc_path),
                        chunk_index=chunk_idx,
                        content=chunk_text,
                        embedding=embedding,
                        embedding_model=embedding_model
                    )
            
            logger.info("RAG文档处理完成")
            
        except Exception as e:
            logger.error(f"RAG文档处理失败: {e}")
            raise
    
    def _scan_documents(self) -> List[str]:
        """扫描文档目录"""
        document_paths = []
        
        # Docker环境中的可能路径
        search_paths = [
            "/app/resources/System_Architect",
            "/app/data/System_Architect", 
            "/data/System_Architect",
            "/app/resources"
        ]
        
        supported_extensions = {'.pdf', '.doc', '.docx', '.md', '.txt'}
        
        for base_path in search_paths:
            if os.path.exists(base_path):
                for root, dirs, files in os.walk(base_path):
                    for file in files:
                        file_path = Path(root) / file
                        if file_path.suffix.lower() in supported_extensions:
                            document_paths.append(str(file_path))
                break
        
        logger.info(f"找到 {len(document_paths)} 个文档文件")
        return document_paths
    
    async def _store_document_chunk(
        self,
        chunk_id: str,
        source_file: str,
        chunk_index: int,
        content: str,
        embedding: List[float],
        embedding_model: str
    ):
        """存储文档块到数据库"""
        try:
            if self.db_session:
                # 检查是否已存在
                existing = self.db_session.query(DocumentChunk).filter(
                    DocumentChunk.id == chunk_id
                ).first()
                
                metadata_info = {
                    "embedding_dimension": len(embedding),
                    "chunk_length": len(content),
                    "created_at": datetime.now().isoformat()
                }
                
                if existing:
                    # 更新
                    existing.content = content
                    existing.meta = json.dumps(metadata_info)
                    existing.updated_at = datetime.utcnow()
                else:
                    # 新建
                    chunk = DocumentChunk(
                        id=chunk_id,
                        source_file=source_file,
                        chunk_index=chunk_index,
                        content=content,
                        meta=json.dumps(metadata_info),
                        embedding_model=embedding_model
                    )
                    self.db_session.add(chunk)
                
                self.db_session.commit()
            
            # 存储向量
            self._store_chunk_embedding(chunk_id, embedding)
            
        except Exception as e:
            logger.error(f"存储文档块失败: {e}")
            if self.db_session:
                self.db_session.rollback()
    
    def search_similar_documents(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        try:
            # 生成查询向量
            query_embedding = self._generate_embedding(query)
            
            # 搜索相似向量
            similar_chunks = self._search_similar_vectors(query_embedding, top_k)
            
            return similar_chunks
            
        except Exception as e:
            logger.error(f"文档搜索失败: {e}")
            return []
    
    def _search_similar_vectors(
        self, 
        query_vector: List[float], 
        top_k: int
    ) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        try:
            if FAISS_AVAILABLE and self.vector_index is not None:
                # 使用FAISS搜索
                query_array = np.array([query_vector], dtype=np.float32)
                scores, indices = self.vector_index.search(query_array, top_k)
                
                # 获取对应的文档块
                results = []
                for idx, score in zip(indices[0], scores[0]):
                    # 这里需要维护向量索引和文档块的映射
                    results.append({
                        "score": float(score),
                        "chunk_id": f"chunk_{idx}",  # 简化处理
                        "content": "相关内容..."  # 需要从数据库获取
                    })
                
                return results
            else:
                # 简化的相似度计算
                if not hasattr(self, 'vector_store'):
                    return []
                
                similarities = []
                for chunk_id, stored_vector in self.vector_store.items():
                    # 计算余弦相似度
                    similarity = self._cosine_similarity(query_vector, stored_vector)
                    similarities.append((chunk_id, similarity))
                
                # 排序并返回top_k
                similarities.sort(key=lambda x: x[1], reverse=True)
                
                results = []
                for chunk_id, score in similarities[:top_k]:
                    if self.db_session:
                        chunk = self.db_session.query(DocumentChunk).filter(
                            DocumentChunk.id == chunk_id
                        ).first()
                        if chunk:
                            results.append({
                                "score": score,
                                "chunk_id": chunk_id,
                                "content": chunk.content[:200] + "...",
                                "source_file": chunk.source_file
                            })
                
                return results
                
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        try:
            if len(vec1) != len(vec2):
                return 0.0
            
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except:
            return 0.0
    
    def answer_question(self, question: str, context_limit: int = 3) -> Dict[str, Any]:
        """基于文档回答问题"""
        try:
            # 搜索相关文档
            relevant_docs = self.search_similar_documents(question, context_limit)
            
            if not relevant_docs:
                return {
                    "answer": "抱歉，我没有找到相关的信息来回答您的问题。",
                    "confidence": 0.0,
                    "sources": []
                }
            
            # 构建上下文
            context = "\n\n".join([doc["content"] for doc in relevant_docs])
            
            # 简化的回答生成（实际项目中可以用GPT等模型）
            answer = self._generate_answer(question, context)
            
            return {
                "answer": answer,
                "confidence": 0.8,  # 简化的置信度
                "sources": [
                    {
                        "file": doc.get("source_file", ""),
                        "content": doc["content"][:100] + "...",
                        "score": doc["score"]
                    }
                    for doc in relevant_docs
                ]
            }
            
        except Exception as e:
            logger.error(f"问答失败: {e}")
            return {
                "answer": "处理您的问题时发生了错误，请稍后重试。",
                "confidence": 0.0,
                "sources": []
            }
    
    def _generate_answer(self, question: str, context: str) -> str:
        """生成答案（简化版）"""
        # 这里是简化版本，实际项目中应该使用LLM
        
        # 基于关键词匹配的简单回答
        question_lower = question.lower()
        context_lower = context.lower()
        
        if "什么是" in question or "定义" in question:
            # 寻找定义相关的内容
            sentences = context.split('。')
            for sentence in sentences:
                if any(word in sentence for word in ["是", "定义", "指"]):
                    return sentence.strip() + "。"
        
        # 默认返回上下文的前几句
        sentences = context.split('。')[:3]
        return "。".join(sentences) + "。"
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取RAG系统统计信息"""
        try:
            if self.db_session:
                total_chunks = self.db_session.query(DocumentChunk).count()
                unique_files = self.db_session.query(
                    DocumentChunk.source_file
                ).distinct().count()
                
                return {
                    "total_document_chunks": total_chunks,
                    "unique_source_files": unique_files,
                    "embedding_model": getattr(self.embedding_model, 'model_name', 'simple'),
                    "vector_store_type": "FAISS" if FAISS_AVAILABLE else "Memory"
                }
            else:
                return {
                    "total_document_chunks": 0,
                    "unique_source_files": 0,
                    "embedding_model": "simple",
                    "vector_store_type": "Memory"
                }
                
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {} 