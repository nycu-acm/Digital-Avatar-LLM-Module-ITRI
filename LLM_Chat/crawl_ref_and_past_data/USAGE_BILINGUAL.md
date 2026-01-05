# Bilingual Document Processor Usage Guide

## Overview
This project contains scripts to process ITRI museum documents and create bilingual versions (English and Traditional Chinese) for each file.

## Files Created
- `process_museum_docs_bilingual.py` - Main script using googletrans
- `process_museum_docs_bilingual_alt.py` - Alternative script using deep_translator
- `requirements_bilingual.txt` - Required dependencies

## Installation
```bash
pip install -r requirements_bilingual.txt
```

## Usage

### Method 1: Using googletrans (Recommended)
```bash
python process_museum_docs_bilingual.py
```

### Method 2: Using deep_translator (Alternative)
```bash
python process_museum_docs_bilingual_alt.py
```

## What the scripts do:

1. **Scan Source Directory**: Recursively processes all files in `/mnt/HDD4/thanglq/he110/GitSpace/LLM_Chat/itri_museum_docs/`

2. **Language Detection**: Automatically detects if files are in English or Chinese

3. **File Processing**: 
   - For text files: Creates bilingual versions with translation
   - For non-text files: Copies as-is to both language versions

4. **Output Structure**: Creates files in `/mnt/HDD4/thanglq/he110/GitSpace/LLM_Chat/itri_museum_docs_bilingual/`
   - Original filename + `_en` for English version
   - Original filename + `_zh-tw` for Traditional Chinese version

## Supported File Types
- Text files: `.txt`, `.md`, `.py`, `.js`, `.html`, `.css`, `.json`, `.xml`, `.yml`, `.yaml`, `.csv`, `.log`, `.rst`, `.tex`
- Document files: `.doc`, `.docx` (alternative script only)
- Files without extensions are checked for text content

## Features
- **Encoding Detection**: Handles various text encodings automatically
- **Chunk Processing**: Splits long texts into manageable chunks for translation
- **Error Handling**: Graceful handling of translation failures
- **Directory Structure**: Preserves original directory structure in output
- **Progress Tracking**: Shows processing progress and statistics

## Notes
- Translation may take time for large files
- API rate limits may apply for large datasets
- Both scripts create the same output structure but use different translation libraries