#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ITRI Data Processor for Dataset 2025
基礎資料處理和語義分塊
"""

import json
import re
import jieba
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Represents a document chunk with metadata"""
    content: str
    chunk_id: str
    source_file: str
    chunk_index: int
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class ITRIDataProcessor:
    def __init__(self, dataset_dir: str = "dataset_202512"):
        """Initialize the ITRI data processor"""
        self.dataset_dir = Path(dataset_dir)
        self.chunk_size = 300
        self.chunk_overlap = 50
        self.chunk_counter = 0
        
        # Initialize jieba for Chinese text processing
        self._initialize_jieba()
        
        logger.info(f"📊 ITRI Data Processor initialized. Dataset dir: {dataset_dir}")
    
    def _initialize_jieba(self):
        """Initialize jieba with domain-specific vocabulary"""
        try:
            custom_terms = [
                "工研院", "工業技術研究院", "ITRI",
                "人才培育", "產業升級", "創新技術",
                "半導體", "人工智慧", "綠能科技", "生醫技術"
            ]
            for term in custom_terms:
                jieba.add_word(term)
            
            # Preload jieba
            _ = list(jieba.cut("工研院是台灣重要的產業技術研發機構"))
            logger.info("✅ Jieba initialized with ITRI vocabulary")
        except Exception as e:
            logger.warning(f"⚠️ Jieba initialization failed: {e}")
    
    def semantic_chunking(self, text: str, source_file: str) -> List[DocumentChunk]:
        """Advanced semantic chunking that respects sentence boundaries"""
        chunks = []
        
        # Split by sentences first (handle both Chinese and English)
        sentences = re.split(r'[。！？.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    # Create chunk with overlap
                    chunk_id = f"{source_file}_{self.chunk_counter}"
                    chunks.append(DocumentChunk(
                        content=current_chunk.strip(),
                        chunk_id=chunk_id,
                        source_file=source_file,
                        chunk_index=self.chunk_counter,
                        metadata={
                            'length': len(current_chunk),
                            'sentence_count': current_chunk.count('。') + current_chunk.count('!') + current_chunk.count('?'),
                            'language': 'chinese' if re.search(r'[\u4e00-\u9fff]', current_chunk) else 'english'
                        }
                    ))
                    self.chunk_counter += 1
                    
                    # Start new chunk with overlap
                    overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                    current_chunk = current_chunk[overlap_start:] + " " + sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk += " " + sentence
        
        # Add the last chunk
        if current_chunk.strip():
            chunk_id = f"{source_file}_{self.chunk_counter}"
            chunks.append(DocumentChunk(
                content=current_chunk.strip(),
                chunk_id=chunk_id,
                source_file=source_file,
                chunk_index=self.chunk_counter,
                metadata={
                    'length': len(current_chunk),
                    'sentence_count': current_chunk.count('。') + current_chunk.count('!') + current_chunk.count('?'),
                    'language': 'chinese' if re.search(r'[\u4e00-\u9fff]', current_chunk) else 'english'
                }
            ))
            self.chunk_counter += 1
        
        return chunks
    
    def process_crawled_data(self, input_file: str) -> List[DocumentChunk]:
        """Process crawled data and create document chunks"""
        input_path = self.dataset_dir / input_file
        
        if not input_path.exists():
            logger.error(f"❌ Input file not found: {input_path}")
            return []
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"📊 Processing {len(data)} items from {input_file}")
            
            all_chunks = []
            for item in data:
                if 'content' in item and item['content']:
                    content = item['content']
                    source_id = item.get('id', f"item_{len(all_chunks)}")
                    
                    # Create chunks from content
                    chunks = self.semantic_chunking(content, source_id)
                    
                    # Enhance metadata
                    for chunk in chunks:
                        chunk.metadata.update({
                            'original_source': item.get('source', 'unknown'),
                            'original_url': item.get('url', ''),
                            'content_type': item.get('content_type', 'text'),
                            'language': item.get('language', 'unknown'),
                            'crawled_at': item.get('crawled_at', '')
                        })
                    
                    all_chunks.extend(chunks)
            
            logger.info(f"✅ Created {len(all_chunks)} chunks from {len(data)} items")
            return all_chunks
            
        except Exception as e:
            logger.error(f"❌ Error processing crawled data: {e}")
            return []
    
    def save_processed_chunks(self, chunks: List[DocumentChunk], output_file: str):
        """Save processed chunks to JSON file"""
        output_path = self.dataset_dir / output_file
        
        try:
            # Convert chunks to serializable format
            chunk_data = []
            for chunk in chunks:
                chunk_dict = {
                    'content': chunk.content,
                    'chunk_id': chunk.chunk_id,
                    'source_file': chunk.source_file,
                    'chunk_index': chunk.chunk_index,
                    'metadata': chunk.metadata
                }
                chunk_data.append(chunk_dict)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Saved {len(chunks)} chunks to {output_path}")
            
        except Exception as e:
            logger.error(f"❌ Error saving chunks: {e}")
    
    def generate_rag_ready_format(self, chunks: List[DocumentChunk]) -> List[Dict[str, Any]]:
        """Generate RAG-ready format from processed chunks"""
        rag_data = []
        
        for chunk in chunks:
            rag_item = {
                'content': chunk.content,
                'chunk_id': chunk.chunk_id,
                'source_file': chunk.source_file,
                'chunk_index': chunk.chunk_index,
                'metadata': {
                    **chunk.metadata,
                    'quality_score': self._calculate_quality_score(chunk.content),
                    'content_hash': hashlib.md5(chunk.content.encode()).hexdigest()
                }
            }
            rag_data.append(rag_item)
        
        return rag_data
    
    def _calculate_quality_score(self, content: str) -> float:
        """Calculate basic quality score for content"""
        try:
            score = 0.5  # Base score
            
            # Length factor
            if len(content) > 50:
                score += 0.2
            if len(content) > 100:
                score += 0.1
            
            # Content richness
            if re.search(r'[\u4e00-\u9fff]', content):  # Chinese characters
                score += 0.1
            if re.search(r'[a-zA-Z]', content):  # English letters
                score += 0.1
            
            # Technical terms
            technical_terms = ['技術', '研發', '創新', '產業', 'technology', 'research', 'innovation']
            for term in technical_terms:
                if term in content:
                    score += 0.05
                    break
            
            return min(1.0, max(0.0, score))
            
        except Exception:
            return 0.5  # Default score on error