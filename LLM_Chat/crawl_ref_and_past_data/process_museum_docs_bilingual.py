#!/usr/bin/env python3
"""
Bilingual Document Processor for ITRI Museum Documents

This script processes all files under itri_museum_docs directory and creates
bilingual versions (English and Traditional Chinese) for each file.
"""

import os
import shutil
import csv
from pathlib import Path
import chardet
from googletrans import Translator, LANGUAGES

# Initialize translator
translator = Translator()

def translate(text, dest):
    """Translate text to destination language using Google Translate"""
    try:
        # More comprehensive validation
        if text is None:
            print("Translation skipped: text is None")
            return ""
        
        # Convert to string and check if empty
        text_str = str(text).strip()
        if len(text_str) == 0:
            print("Translation skipped: empty text after strip")
            return ""
        
        # Additional validation for very short text
        if len(text_str) < 2:
            print(f"Translation skipped: text too short ({len(text_str)} chars)")
            return text_str
        
        # Check if text is too long and needs chunking
        max_chunk_size = 4000  # Google Translate limit is around 5000 chars
        if len(text_str) > max_chunk_size:
            print(f"Text too long ({len(text_str)} chars), splitting into chunks...")
            return translate_long_text(text_str, dest)
        
        # Debug: print text length and first few characters
        print(f"Translating {len(text_str)} chars: '{text_str[:50]}...' to {dest}")
        
        # Add small delay to avoid rate limiting
        import time
        time.sleep(0.1)
        
        result = translator.translate(text_str, dest=dest)
        
        if result and hasattr(result, 'text'):
            return result.text
        else:
            print("Translation result is None or has no text attribute")
            return text_str
            
    except Exception as e:
        print(f"Translation error: {e}")
        print(f"Failed text type: {type(text)}, length: {len(str(text)) if text else 0}")
        return str(text) if text else ""

def translate_long_text(text, dest):
    """Translate long text by splitting into chunks"""
    max_chunk_size = 4000
    chunks = []
    
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 <= max_chunk_size:
            if current_chunk:
                current_chunk += '\n\n' + paragraph
            else:
                current_chunk = paragraph
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = paragraph
    
    if current_chunk:
        chunks.append(current_chunk)
    
    # If still too long, split by sentences
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_chunk_size:
            final_chunks.append(chunk)
        else:
            # Split by sentences
            sentences = chunk.replace('。', '.\n').replace('.', '.\n').split('\n')
            current_sentence_chunk = ""
            
            for sentence in sentences:
                if len(current_sentence_chunk) + len(sentence) <= max_chunk_size:
                    current_sentence_chunk += sentence
                else:
                    if current_sentence_chunk:
                        final_chunks.append(current_sentence_chunk.strip())
                    current_sentence_chunk = sentence
            
            if current_sentence_chunk:
                final_chunks.append(current_sentence_chunk.strip())
    
    # Translate each chunk
    translated_chunks = []
    for i, chunk in enumerate(final_chunks):
        print(f"  Translating chunk {i+1}/{len(final_chunks)} ({len(chunk)} chars)...")
        
        try:
            import time
            time.sleep(0.5)  # Longer delay between chunks
            
            result = translator.translate(chunk, dest=dest)
            if result and hasattr(result, 'text'):
                translated_chunks.append(result.text)
            else:
                print(f"  Chunk {i+1} translation failed, keeping original")
                translated_chunks.append(chunk)
                
        except Exception as e:
            print(f"  Chunk {i+1} translation error: {e}")
            translated_chunks.append(chunk)
    
    return '\n\n'.join(translated_chunks)

def detect_language(text):
    """Detect the language of the text"""
    try:
        # More comprehensive validation
        if text is None:
            print("Language detection skipped: text is None")
            return 'unknown'
        
        # Convert to string and check if empty
        text_str = str(text).strip()
        if len(text_str) == 0:
            print("Language detection skipped: empty text after strip")
            return 'unknown'
        
        # Additional validation for very short text
        if len(text_str) < 5:
            print(f"Language detection skipped: text too short ({len(text_str)} chars)")
            return 'unknown'
        
        print(f"Detecting language for {len(text_str)} chars: '{text_str[:50]}...'")
        
        detection = translator.detect(text_str)
        
        if detection and hasattr(detection, 'lang'):
            return detection.lang
        else:
            print("Language detection result is None or has no lang attribute")
            return 'unknown'
            
    except Exception as e:
        print(f"Language detection error: {e}")
        print(f"Failed text type: {type(text)}, length: {len(str(text)) if text else 0}")
        return 'unknown'

def is_text_file(file_path):
    """Check if a file is a text file"""
    text_extensions = {'.txt', '.md', '.json'}
    
    # Check by extension first
    if file_path.suffix.lower() in text_extensions:
        return True
    
    # For files without extension, try to detect if it's text
    try:
        with open(file_path, 'rb') as f:
            sample = f.read(1024)
            if not sample:
                return False
            
            # Try to decode as text
            try:
                sample.decode('utf-8')
                return True
            except UnicodeDecodeError:
                # Try to detect encoding
                result = chardet.detect(sample)
                if result['confidence'] > 0.7:
                    return True
                return False
    except Exception:
        return False

def read_file_content(file_path):
    """Read file content with proper encoding detection"""
    try:
        # Try UTF-8 first
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Detect encoding if UTF-8 fails
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding'] if result['confidence'] > 0.7 else 'utf-8'
            
        try:
            return raw_data.decode(encoding)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

def process_file(source_file, output_dir, relative_path):
    """Process a single file and create bilingual versions"""
    print(f"Processing: {relative_path}")
    
    # Read file content
    content = read_file_content(source_file)
    if content is None:
        print(f"Skipping {relative_path} - could not read content")
        return
    
    # Skip if file is empty or too small
    if not content or len(content.strip()) < 0:
        print(f"Skipping {relative_path} - content too small or empty")
        return
    
    # Detect language
    detected_lang = detect_language(content[:500])  # Use first 500 chars for detection
    print(f"Detected language: {detected_lang}")
    detected_lang = 'no-detect:)'

    # Prepare file names without extension
    file_stem = source_file.stem
    file_extension = source_file.suffix
    
    # Create output file paths
    en_filename = f"{file_stem}_en{file_extension}"
    zh_tw_filename = f"{file_stem}_zh-tw{file_extension}"
    
    # Create the directory structure in output
    output_subdir = output_dir / relative_path.parent
    output_subdir.mkdir(parents=True, exist_ok=True)
    
    en_path = output_subdir / en_filename
    zh_tw_path = output_subdir / zh_tw_filename
    
    # Translate and save files
    try:
        if detected_lang == 'zh' or detected_lang == 'zh-tw':
            # Original is Chinese, translate to English
            print(f"Translating Chinese to English...")
            en_content = translate(content, 'en')
            zh_tw_content = content  # Keep original Chinese
        elif detected_lang == 'en':
            # Original is English, translate to Chinese
            print(f"Translating English to Traditional Chinese...")
            en_content = content  # Keep original English
            zh_tw_content = translate(content, 'zh-tw')
        else:
            # Unknown language, create both translations
            print(f"Unknown language, creating both translations...")
            en_content = translate(content, 'en')
            zh_tw_content = translate(content, 'zh-tw')
        
        # Write English version
        with open(en_path, 'w', encoding='utf-8') as f:
            f.write(en_content)
        print(f"Created: {en_path}")
        
        # Write Traditional Chinese version
        with open(zh_tw_path, 'w', encoding='utf-8') as f:
            f.write(zh_tw_content)
        print(f"Created: {zh_tw_path}")
        
    except Exception as e:
        print(f"Error processing {relative_path}: {e}")

def process_museum_docs():
    """Main function to process all museum documents"""
    # Define paths
    source_dir = Path("/mnt/HDD4/thanglq/he110/GitSpace/LLM_Chat/itri_museum_docs")
    output_dir = Path("/mnt/HDD4/thanglq/he110/GitSpace/LLM_Chat/itri_museum_docs_bilingual")
    
    # Check if source directory exists
    if not source_dir.exists():
        print(f"Error: Source directory {source_dir} does not exist!")
        print("Please ensure the path is correct.")
        return
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Initialize CSV file for skipped files
    skipped_csv_path = output_dir / "skipped_files.csv"
    
    # Open CSV file for writing skipped files
    csvfile = open(skipped_csv_path, 'w', newline='', encoding='utf-8')
    fieldnames = ['file_path', 'file_name', 'file_extension', 'file_size_bytes', 'reason', 'full_path']
    csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    csv_writer.writeheader()
    
    # Process all files recursively
    processed_count = 0
    skipped_count = 0
    
    import time
    try:
        for root, dirs, files in os.walk(source_dir):
            root_path = Path(root)
            
            for file in files:
                file_path = root_path / file
                relative_path = file_path.relative_to(source_dir)
                
                # Check if it's a text file
                if is_text_file(file_path):
                    process_file(file_path, output_dir, relative_path)
                    time.sleep(1)
                    processed_count += 1
                else:
                    print(f"Skipping non-text file: {relative_path}")
                    # Write skipped file information directly to CSV
                    file_size = file_path.stat().st_size if file_path.exists() else 0
                    file_ext = file_path.suffix.lower()
                    reason = "Non-text file extension" if file_ext else "No file extension"
                    
                    csv_writer.writerow({
                        'file_path': str(relative_path),
                        'file_name': file_path.name,
                        'file_extension': file_ext,
                        'file_size_bytes': file_size,
                        'reason': reason,
                        'full_path': str(file_path)
                    })
                    csvfile.flush()  # Ensure data is written immediately
                    skipped_count += 1
    finally:
        # Close the CSV file
        csvfile.close()
        if skipped_count > 0:
            print(f"Skipped files recorded in: {skipped_csv_path}")
    
    print(f"\nProcessing complete!")
    print(f"Processed: {processed_count} files")
    print(f"Skipped: {skipped_count} files")

def main():
    """Main entry point"""
    print("ITRI Museum Documents Bilingual Processor")
    print("=" * 50)
    
    # Check if googletrans is available
    try:
        test_translator = Translator()
        print("Google Translator initialized successfully")
    except Exception as e:
        print(f"Error initializing translator: {e}")
        print("Please install googletrans: pip install googletrans==4.0.0rc1")
        return
    
    # Process documents
    process_museum_docs()

if __name__ == "__main__":
    main()