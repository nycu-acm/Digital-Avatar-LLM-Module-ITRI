#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama-Enhanced Data Processor for ITRI Dataset 2025
Uses Ollama LLM to intelligently clean, enhance, and structure web-crawled data.
"""

import json
import re
import requests
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedChunk:
    """Structure for LLM-enhanced data chunks"""
    chunk_id: str
    original_content: str
    cleaned_content: str
    structured_data: Dict[str, Any]
    summary: str
    key_points: List[str]
    entities: List[str]
    metadata: Dict[str, Any]
    language: str
    quality_score: float
    enhancement_log: List[str]

class OllamaDataEnhancer:
    def __init__(self, 
                 ollama_base_url: str = "http://localhost:11435",
                 model_name: str = "linly-llama3.1:70b-instruct-q4_0",
                 dataset_dir: str = "dataset_202512"):
        """Initialize the Ollama-enhanced data processor"""
        self.ollama_base_url = ollama_base_url
        self.model_name = model_name
        self.dataset_dir = Path(dataset_dir)
        
        # Test Ollama connection immediately 
        self._test_ollama_connection()
        
        # Enhancement configuration
        self.enhancement_config = {
            'max_retries': 3,
            'request_timeout': 120,  # 2 minutes timeout
            'batch_size': 5,  # Process multiple items together for efficiency
            'quality_threshold': 0.6,
            'min_content_length': 50,
            'max_content_length': 2000
        }
        
        logger.info(f"🤖 Ollama Data Enhancer initialized with model: {model_name}")

    def _test_ollama_connection(self):
        """Test connection to Ollama server and show detailed error if fails"""
        try:
            logger.info(f"🔗 Testing connection to Ollama server at {self.ollama_base_url}")
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=120)
            response.raise_for_status()
            
            # Also test if the model exists
            tags_data = response.json()
            models = [model.get('name', '') for model in tags_data.get('models', [])]
            
            if self.model_name in models:
                logger.info(f"✅ Connected to Ollama server successfully")
                logger.info(f"✅ Model {self.model_name} is available")
            else:
                logger.error(f"❌ Model {self.model_name} not found")
                logger.error(f"Available models: {models}")
                raise ConnectionError(f"Model {self.model_name} not available. Run: ollama pull {self.model_name}")
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Cannot connect to Ollama server at {self.ollama_base_url}")
            logger.error(f"Connection error: {e}")
            logger.error("Please ensure Ollama server is running:")
            logger.error("  ollama serve")
            raise ConnectionError("Ollama server not reachable")
            
        except requests.exceptions.Timeout as e:
            logger.error(f"❌ Connection to Ollama server timed out")
            logger.error(f"Timeout error: {e}")
            raise ConnectionError("Ollama server timeout")
            
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to Ollama: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise ConnectionError(f"Ollama connection failed: {e}")

    def enhance_crawled_data(self, input_file: str) -> List[EnhancedChunk]:
        """Process crawled data with Ollama LLM enhancement"""
        logger.info(f"🚀 Starting Ollama-enhanced processing of {input_file}")
        
        # Load crawled data
        input_path = self.dataset_dir / input_file
        with open(input_path, 'r', encoding='utf-8') as f:
            crawled_data = json.load(f)
        
        # Extract content items
        if isinstance(crawled_data, list):
            content_items = crawled_data
        elif isinstance(crawled_data, dict) and 'rag_ready_data' in crawled_data:
            content_items = crawled_data['rag_ready_data']
        else:
            content_items = [crawled_data]
        
        enhanced_chunks = []
        
        # Process items in batches for efficiency
        for i in range(0, len(content_items), self.enhancement_config['batch_size']):
            batch = content_items[i:i + self.enhancement_config['batch_size']]
            batch_results = self._process_batch(batch, i)
            enhanced_chunks.extend(batch_results)
            
            # Small delay to avoid overwhelming Ollama
            time.sleep(0.5)
        
        logger.info(f"✅ Enhanced {len(content_items)} items into {len(enhanced_chunks)} high-quality chunks")
        return enhanced_chunks

    def _process_batch(self, batch: List[Dict[str, Any]], batch_index: int) -> List[EnhancedChunk]:
        """Process a batch of content items with Ollama"""
        logger.info(f"⚙️ Processing batch {batch_index // self.enhancement_config['batch_size'] + 1}")
        
        enhanced_chunks = []
        
        for item in batch:
            try:
                enhanced_chunk = self._enhance_single_item(item)
                if enhanced_chunk:
                    enhanced_chunks.append(enhanced_chunk)
            except Exception as e:
                logger.error(f"❌ Error processing item: {e}")
                continue
        
        return enhanced_chunks

    def _enhance_single_item(self, item: Dict[str, Any]) -> Optional[EnhancedChunk]:
        """Enhance a single content item using Ollama"""
        original_content = item.get('content', '').strip()
        
        if len(original_content) < self.enhancement_config['min_content_length']:
            return None
        
        # Truncate very long content
        if len(original_content) > self.enhancement_config['max_content_length']:
            original_content = original_content[:self.enhancement_config['max_content_length']] + "..."
        
        enhancement_log = []
        
        try:
            # Step 1: Clean and extract main content
            cleaned_content = self._clean_content_with_llm(original_content)
            enhancement_log.append("Content cleaned with LLM")
            
            # Step 2: Extract structured data
            structured_data = self._extract_structured_data(cleaned_content)
            enhancement_log.append("Structured data extracted")
            
            # Step 3: Generate summary
            summary = self._generate_summary(cleaned_content)
            enhancement_log.append("Summary generated")
            
            # Step 4: Extract key points
            key_points = self._extract_key_points(cleaned_content)
            enhancement_log.append("Key points extracted")
            
            # Step 5: Extract entities
            entities = self._extract_entities(cleaned_content)
            enhancement_log.append("Entities extracted")
            
            # Step 6: Calculate enhanced quality score
            quality_score = self._calculate_enhanced_quality_score(
                original_content, cleaned_content, structured_data, key_points
            )
            
            # Create enhanced chunk
            chunk_id = f"enhanced_{hashlib.md5(original_content.encode()).hexdigest()[:8]}"
            
            enhanced_chunk = EnhancedChunk(
                chunk_id=chunk_id,
                original_content=original_content,
                cleaned_content=cleaned_content,
                structured_data=structured_data,
                summary=summary,
                key_points=key_points,
                entities=entities,
                metadata={
                    **item.get('metadata', {}),
                    'original_source': item.get('source', 'unknown'),
                    'enhanced_at': datetime.now().isoformat(),
                    'enhancement_model': self.model_name,
                    'original_length': len(original_content),
                    'cleaned_length': len(cleaned_content),
                    'compression_ratio': len(cleaned_content) / len(original_content) if original_content else 0
                },
                language=self._detect_language(cleaned_content),
                quality_score=quality_score,
                enhancement_log=enhancement_log
            )
            
            return enhanced_chunk
            
        except Exception as e:
            logger.error(f"❌ Error enhancing content: {e}")
            return None

    def _clean_content_with_llm(self, content: str) -> str:
        """Use Ollama to clean and extract main content from noisy web data"""
        system_prompt = """你是一個專業的內容清理專家。你的任務是從網頁抓取的原始內容中提取最重要和最相關的信息。

請執行以下任務：
1. 移除導航元素、廣告、重複內容和無關信息
2. 保留所有與工研院(ITRI)相關的重要內容
3. 確保內容結構清晰、語句完整
4. 保持原有的語言（中文或英文）
5. 如果內容太短或無關，請回應"INSUFFICIENT_CONTENT"

只返回清理後的主要內容，不要添加任何解釋或標記。"""

        user_prompt = f"請清理以下網頁內容，提取與工研院相關的核心信息：\n\n{content}"
        
        try:
            response = self._call_ollama(system_prompt, user_prompt)
            
            if response and response.strip() != "INSUFFICIENT_CONTENT":
                return response.strip()
            else:
                # Fallback to basic cleaning if LLM considers content insufficient
                return self._basic_content_cleaning(content)
                
        except Exception as e:
            logger.warning(f"⚠️ LLM cleaning failed, using basic cleaning: {e}")
            return self._basic_content_cleaning(content)

    def _extract_structured_data(self, content: str) -> Dict[str, Any]:
        """Extract structured data using Ollama"""
        system_prompt = """你是一個數據結構化專家。請從給定的內容中提取結構化信息。

請以JSON格式返回以下信息（如果存在）：
- organization_info: 組織基本信息
- key_people: 重要人物
- achievements: 成就或獎項
- technologies: 技術領域
- dates: 重要日期
- locations: 地點信息
- numbers: 重要數字（員工數、營收等）

如果某個類別沒有信息，請省略該字段。只返回JSON格式，不要其他解釋。"""

        user_prompt = f"請從以下內容中提取結構化信息：\n\n{content}"
        
        try:
            response = self._call_ollama(system_prompt, user_prompt)
            
            # Try to parse JSON response, but fall back to text extraction if JSON fails
            if response:
                # Clean up response - remove markdown formatting if present
                json_str = response.strip()
                if json_str.startswith('```json'):
                    json_str = json_str.replace('```json', '').replace('```', '').strip()
                
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # JSON parsing failed, return the raw LLM response directly
                    logger.info("📊 JSON parsing failed, keeping raw LLM response")
                    return {"raw_llm_response": response}
            
        except Exception as e:
            logger.warning(f"⚠️ Structured data extraction failed: {e}")
            
        return {}
    

    def _generate_summary(self, content: str) -> str:
        """Generate a concise summary using Ollama"""
        system_prompt = """你是一個專業的摘要專家。請為工研院相關內容生成簡潔而全面的摘要。

摘要要求：
1. 長度控制在100-200字之間
2. 突出最重要的信息
3. 保持原有語言
4. 使用清晰簡潔的表達

只返回摘要內容，不要添加任何前綴或後綴。"""

        user_prompt = f"請為以下內容生成摘要：\n\n{content}"
        
        try:
            response = self._call_ollama(system_prompt, user_prompt)
            return response.strip() if response else ""
        except Exception as e:
            logger.warning(f"⚠️ Summary generation failed: {e}")
            # Fallback to first few sentences
            sentences = re.split(r'[。！？.!?]', content)
            return '。'.join(sentences[:2]) + '。' if sentences else ""

    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points using Ollama"""
        system_prompt = """你是一個信息提取專家。請從內容中提取3-7個最重要的關鍵點。

要求：
1. 每個關鍵點應該簡潔明瞭（不超過50字）
2. 重點關注工研院的核心信息
3. 保持原有語言
4. 以列表格式返回，每行一個要點
5. 不要添加編號或符號，直接列出要點

只返回關鍵點列表，每行一個。"""

        user_prompt = f"請從以下內容中提取關鍵點：\n\n{content}"
        
        try:
            response = self._call_ollama(system_prompt, user_prompt)
            
            if response:
                # Split response into lines and clean up
                key_points = [
                    line.strip().strip('-•*').strip()
                    for line in response.split('\n')
                    if line.strip() and not line.strip().startswith('關鍵點')
                ]
                return [point for point in key_points if len(point) > 5][:7]  # Max 7 points
            
        except Exception as e:
            logger.warning(f"⚠️ Key points extraction failed: {e}")
            
        return []

    def _extract_entities(self, content: str) -> List[str]:
        """Extract named entities using Ollama"""
        system_prompt = """你是一個實體識別專家。請從內容中識別所有相關的實體。

請識別以下類型的實體：
1. 人物姓名
2. 組織機構
3. 技術名詞
4. 地點
5. 產品或服務名稱
6. 重要日期或年份

只返回實體名稱，每行一個，不要分類標籤。"""

        user_prompt = f"請從以下內容中識別實體：\n\n{content}"
        
        try:
            response = self._call_ollama(system_prompt, user_prompt)
            
            if response:
                entities = [
                    line.strip()
                    for line in response.split('\n')
                    if line.strip() and len(line.strip()) > 1
                ]
                entities = list(set(entities))[:20]  # Remove duplicates, max 20 entities
                
                # If we got entities, return them
                if entities:
                    return entities
                    
        except Exception as e:
            logger.warning(f"⚠️ Entity extraction failed: {e}")
        
        # Fallback: extract entities using simple regex patterns
        logger.info("🔄 Using fallback entity extraction...")
        return self._extract_entities_fallback(content)
    
    def _extract_entities_fallback(self, content: str) -> List[str]:
        """Fallback entity extraction using regex patterns"""
        try:
            entities = []
            
            # Extract years (1900-2099)
            years = re.findall(r'\b(?:19|20)\d{2}年?\b', content)
            entities.extend(years)
            
            # Extract names (Chinese names - 2-4 characters, proper format)
            chinese_names = re.findall(r'[趙錢孫李周吳鄭王馮陳褚衛蔣沈韓楊朱秦尤許何呂施張孔曹嚴華金魏陶姜戚謝鄒喻柏水竇章雲蘇潘葛奚范彭郎魯韋昌馬苗鳳花方俞任袁柳豐鮑史唐費廉岑薛雷賀倪湯滕殷羅畢郝鄔安常樂於時傅皮卞齊康伍余元卜顧孟平黃和穆蕭尹姚邵堪汪祁毛禹狄米貝明臧計伏成戴談宋茅龐熊紀舒屈項祝董][一-龯]{1,3}', content)
            entities.extend(chinese_names)
            
            # Extract organizations (containing 公司, 研究所, 大學, etc.)
            orgs = re.findall(r'[一-龯\w]+(?:公司|研究所|大學|學院|中心|協會|基金會|集團)', content)
            entities.extend(orgs)
            
            # Extract technology terms
            tech_terms = re.findall(r'(?:人工智慧|AI|半導體|生醫|綠能|5G|IoT|區塊鏈|雲端|大數據|機器學習)', content)
            entities.extend(tech_terms)
            
            # Extract locations (Taiwan cities and areas)
            locations = re.findall(r'(?:台北|新北|桃園|新竹|苗栗|台中|彰化|南投|雲林|嘉義|台南|高雄|屏東|宜蘭|花蓮|台東|澎湖|金門|連江|竹北|竹東|六甲)', content)
            entities.extend(locations)
            
            # Clean and deduplicate
            clean_entities = []
            for entity in entities:
                entity = entity.strip()
                if len(entity) > 1 and entity not in clean_entities:
                    clean_entities.append(entity)
            
            return clean_entities[:15]  # Return max 15 entities
            
        except Exception as e:
            logger.warning(f"⚠️ Fallback entity extraction failed: {e}")
            return []

    def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """Make a call to Ollama API with retry logic"""
        for attempt in range(self.enhancement_config['max_retries']):
            try:
                response = requests.post(
                    f"{self.ollama_base_url}/api/chat",
                    json={
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "stream": False,
                        "options": {
                            "temperature": 0.3,  # Lower temperature for more consistent results
                            "top_p": 0.9
                        }
                    },
                    timeout=self.enhancement_config['request_timeout']
                )
                response.raise_for_status()
                return response.json()['message']['content']
                
            except Exception as e:
                if attempt < self.enhancement_config['max_retries'] - 1:
                    logger.warning(f"⚠️ Ollama call failed (attempt {attempt + 1}), retrying: {e}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"❌ Ollama call failed after {self.enhancement_config['max_retries']} attempts: {e}")
                    raise

    def _basic_content_cleaning(self, content: str) -> str:
        """Fallback basic content cleaning"""
        # Remove common noise patterns
        noise_patterns = [
            r'Cookie.*?Policy',
            r'Privacy.*?Policy',
            r'Terms.*?of.*?Service',
            r'Skip to.*?content',
            r'Navigation.*?menu',
            r'Footer.*?links',
            r'Copyright.*?\d{4}',
            r'All rights reserved',
            r'Click here',
            r'Read more',
            r'Learn more'
        ]
        
        cleaned = content
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Clean up whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned

    def _detect_language(self, text: str) -> str:
        """Detect language of the text"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text.replace(' ', ''))
        
        if total_chars == 0:
            return 'unknown'
        
        chinese_ratio = chinese_chars / total_chars
        return 'zh-tw' if chinese_ratio > 0.1 else 'en'

    def _calculate_enhanced_quality_score(self, original: str, cleaned: str, 
                                        structured_data: Dict, key_points: List[str]) -> float:
        """Calculate quality score for enhanced content"""
        scores = {}
        
        # Content improvement score (based on cleaning effectiveness)
        if len(original) > 0:
            compression_ratio = len(cleaned) / len(original)
            # Good compression (removing noise) should be between 0.3-0.8
            scores['content_improvement'] = min(1.0, max(0.0, 1.0 - abs(compression_ratio - 0.6) * 2))
        else:
            scores['content_improvement'] = 0.0
        
        # Structured data richness
        structured_count = sum(len(v) if isinstance(v, (list, dict, str)) else 1 for v in structured_data.values())
        scores['structured_richness'] = min(1.0, structured_count / 10.0)
        
        # Key points quality
        scores['key_points_quality'] = min(1.0, len(key_points) / 5.0)
        
        # Content length appropriateness
        length = len(cleaned)
        if 100 <= length <= 800:
            scores['length_quality'] = 1.0
        elif length < 100:
            scores['length_quality'] = length / 100.0
        else:
            scores['length_quality'] = max(0.3, 800.0 / length)
        
        # ITRI relevance (keyword-based)
        itri_keywords = ['工研院', 'ITRI', '研發', '技術', '創新', 'research', 'technology', 'innovation']
        keyword_matches = sum(1 for keyword in itri_keywords if keyword.lower() in cleaned.lower())
        scores['itri_relevance'] = min(1.0, keyword_matches / 3.0)
        
        # Weighted average
        weights = {
            'content_improvement': 0.25,
            'structured_richness': 0.2,
            'key_points_quality': 0.2,
            'length_quality': 0.15,
            'itri_relevance': 0.2
        }
        
        total_score = sum(scores[metric] * weight for metric, weight in weights.items())
        return round(total_score, 3)

    def save_enhanced_data(self, enhanced_chunks: List[EnhancedChunk], output_file: str):
        """Save enhanced data to file"""
        output_path = self.dataset_dir / output_file
        
        # Prepare data for saving
        enhanced_data = {
            'metadata': {
                'total_chunks': len(enhanced_chunks),
                'enhanced_at': datetime.now().isoformat(),
                'enhancement_model': self.model_name,
                'quality_distribution': self._analyze_quality_distribution(enhanced_chunks),
                'language_distribution': self._analyze_language_distribution(enhanced_chunks),
                'average_enhancement_ratio': self._calculate_average_enhancement_ratio(enhanced_chunks)
            },
            'chunks': [asdict(chunk) for chunk in enhanced_chunks]
        }
        
        # Save as JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Saved {len(enhanced_chunks)} enhanced chunks to {output_path}")

    def _analyze_quality_distribution(self, chunks: List[EnhancedChunk]) -> Dict[str, Any]:
        """Analyze quality score distribution"""
        if not chunks:
            return {}
        
        quality_scores = [chunk.quality_score for chunk in chunks]
        
        return {
            'min_score': min(quality_scores),
            'max_score': max(quality_scores),
            'avg_score': sum(quality_scores) / len(quality_scores),
            'high_quality_count': len([s for s in quality_scores if s >= 0.7]),
            'medium_quality_count': len([s for s in quality_scores if 0.4 <= s < 0.7]),
            'low_quality_count': len([s for s in quality_scores if s < 0.4])
        }

    def _analyze_language_distribution(self, chunks: List[EnhancedChunk]) -> Dict[str, int]:
        """Analyze language distribution"""
        languages = {}
        for chunk in chunks:
            lang = chunk.language
            languages[lang] = languages.get(lang, 0) + 1
        return languages

    def _calculate_average_enhancement_ratio(self, chunks: List[EnhancedChunk]) -> float:
        """Calculate average content enhancement ratio"""
        if not chunks:
            return 0.0
        
        ratios = []
        for chunk in chunks:
            if chunk.original_content and chunk.cleaned_content:
                ratio = len(chunk.cleaned_content) / len(chunk.original_content)
                ratios.append(ratio)
        
        return sum(ratios) / len(ratios) if ratios else 0.0

    def generate_rag_ready_format(self, enhanced_chunks: List[EnhancedChunk], 
                                 quality_threshold: float = 0.6) -> List[Dict[str, Any]]:
        """Generate RAG-ready format from enhanced chunks"""
        
        # Filter by quality threshold
        high_quality_chunks = [chunk for chunk in enhanced_chunks if chunk.quality_score >= quality_threshold]
        
        logger.info(f"📊 Filtered {len(enhanced_chunks)} chunks to {len(high_quality_chunks)} high-quality chunks (threshold={quality_threshold})")
        
        rag_ready_data = []
        
        for chunk in high_quality_chunks:
            # Use cleaned content as primary content, with summary as backup
            primary_content = chunk.cleaned_content if len(chunk.cleaned_content) > 50 else chunk.summary
            
            # Create enhanced metadata
            enhanced_metadata = {
                **chunk.metadata,
                'summary': chunk.summary,
                'key_points': chunk.key_points,
                'entities': chunk.entities,
                'structured_data': chunk.structured_data,
                'enhancement_log': chunk.enhancement_log,
                'quality_score': chunk.quality_score,
                'content_length': len(primary_content),
                'language': chunk.language
            }
            
            rag_item = {
                'content': primary_content,
                'chunk_id': chunk.chunk_id,
                'source_file': chunk.metadata.get('original_source', 'unknown'),
                'chunk_index': len(rag_ready_data),
                'metadata': enhanced_metadata
            }
            
            rag_ready_data.append(rag_item)
        
        return rag_ready_data

def main():
    """Main function for testing the Ollama data enhancer"""
    print("🤖 Ollama-Enhanced ITRI Data Processor")
    print("=" * 50)
    
    try:
        # Initialize enhancer
        enhancer = OllamaDataEnhancer()
        
        # Look for crawled data files
        dataset_dir = Path("dataset_202512")
        data_files = list(dataset_dir.glob("*rag_ready*.json"))
        
        if not data_files:
            print("❌ No RAG-ready data files found. Please run the crawler first.")
            return
        
        # Process the most recent data file
        input_file = data_files[0].name
        print(f"📊 Processing: {input_file}")
        
        # Enhance data with Ollama
        enhanced_chunks = enhancer.enhance_crawled_data(input_file)
        
        # Save enhanced data
        enhancer.save_enhanced_data(enhanced_chunks, "ollama_enhanced_data.json")
        
        # Generate RAG-ready format
        rag_ready_data = enhancer.generate_rag_ready_format(enhanced_chunks, quality_threshold=0.6)
        
        # Save final RAG-ready data
        final_output_path = dataset_dir / "ollama_enhanced_rag_ready.json"
        with open(final_output_path, 'w', encoding='utf-8') as f:
            json.dump(rag_ready_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Ollama enhancement completed!")
        print(f"📊 Total enhanced chunks: {len(enhanced_chunks)}")
        print(f"📊 High-quality RAG-ready chunks: {len(rag_ready_data)}")
        print(f"📁 Final output: {final_output_path}")
        
    except Exception as e:
        print(f"❌ Enhancement failed: {e}")

if __name__ == "__main__":
    main()
