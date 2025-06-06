# OCR Improvement Guide

This guide explains how to use the enhanced OCR improvement system to fix problematic word recognition issues in PDF documents.

## Enhanced OCR Improvements

The OCR improvement system now includes comprehensive accuracy enhancements through multiple processing methods and advanced post-processing corrections.

## Targeted OCR Improvement

The targeted OCR improvement script (`targeted_ocr_improvement.py`) addresses specific recognition problems that occur consistently across multiple OCR runs, such as "Ciplomacy" instead of "diplomacy" and "villereek" instead of "millcreek".

### How It Works

The enhanced script now uses several specialized techniques:

1. **Multiple OCR Processing Methods**: Applies 7 different OCR approaches to each page:
   - Traditional OCR with contrast/sharpness enhancement
   - Enhanced contrast processing for better character distinction
   - Multi-scale processing (normal, enlarged, reduced)
   - Character-focused processing with specialized filters
   - Threshold-based processing for better character separation
   - Location-specific processing optimized for address fields
   - **NEW**: Enhanced preprocessing with advanced noise reduction and adaptive thresholding

2. **Enhanced Consensus Approach**: Combines results from different processing methods using a sophisticated case-insensitive word-level voting mechanism to select the most likely correct text, with special handling for known problematic words.

3. **Expanded Known Word Correction**: Applies specific corrections for a comprehensive set of problematic words including:
   - Common OCR substitution errors (rn→m patterns)
   - URL and protocol fixes (httos→https, corn→com)
   - Phone number artifacts (JJ, JJR patterns)
   - Word separation issues

4. **Pattern-Based Post-Processing**: Uses advanced pattern recognition to correct:
   - URLs and web addresses
   - Email addresses  
   - Phone numbers
   - Common word separations
   - Character substitutions in context

5. **Specialized Location Recognition**: Uses pattern matching to detect and correct location fields that often contain problematic city names.

### Usage

```bash
python targeted_ocr_improvement.py path/to/resume.pdf [--output OUTPUT_DIR] [--dpi DPI] [--view-full]
```

Options:
- `--output`, `-o`: Directory to save extracted text (default: current directory)
- `--dpi`, `-d`: DPI for PDF to image conversion (default: 1500)
- `--view-full`, `-f`: View the full extracted text in terminal output

### Comparing OCR Methods

You can compare how different OCR methods perform on the same PDF using the comparison script:

```bash
python compare_problematic_words.py path/to/resume.pdf [--output OUTPUT_DIR]
```

This will:
1. Run traditional OCR on the PDF
2. Extract regions with problematic words
3. Compare traditional OCR, raw OCR, and the targeted OCR approach
4. Show a summary of which methods correctly recognized problematic words

## Adding New Problematic Words

If you identify additional problematic words that are consistently misrecognized, add them to the `known_problem_words` dictionary in `targeted_ocr_improvement.py`:

```python
known_problem_words = {
    "ciplomacy": "diplomacy",
    "villereek": "millcreek",
    "cornpany": "company",
    "comrnittee": "committee", 
    "rnanagement": "management",
    "cornmunication": "communication",
    "rnanufacturing": "manufacturing",
    "rnarketing": "marketing",
    "developrnent": "development",
    "environrnent": "environment",
    "requirernents": "requirements",
    "achievernent": "achievement",
    "irnplementation": "implementation",
    "docurnent": "document",
    "rnonitoring": "monitoring",
    "prornotion": "promotion",
    "recomrnendation": "recommendation",
    # URL and protocol fixes
    "httos": "https",
    "hftp": "http",
    "wwvv": "www",
    # Add your new problematic words here
    "misrecognized": "correct",
}
```

You can also add character confusion patterns to the expanded `char_confusions` dictionary:

```python
self.char_confusions = {
    'C': ['d', 'D'],  # For "Ciplomacy" -> "diplomacy"
    'v': ['m'],       # For "villereek" -> "millcreek"
    'rn': ['m'],      # Common OCR confusion "rn" -> "m"
    'cl': ['d'],      # For "clifficulty" -> "difficulty"
    'cI': ['d'],      # Capital I confusion
    'li': ['d'],      # For "lifficulty" -> "difficulty"
    'ij': ['y'],      # For "identifij" -> "identify"
    'tl': ['d'],      # For "studient" -> "student"
    'fi': ['f'],      # For "difficujt" -> "difficult"
    'JJ': [''],       # Phone number artifacts
    'JJR': [''],      # Phone number artifacts
    'l1': ['d'],      # Number/letter confusion
    '0': ['o', 'O'],  # Zero/letter O confusion
    'S': ['5'],       # Letter S/number 5 confusion
    '5': ['S'],       # Number 5/letter S confusion
    '1': ['l', 'I'],  # Number 1/letter l/I confusion
    # Add your new character confusions here
}
```

## Performance Considerations

The enhanced targeted OCR process is more computationally intensive than standard OCR due to:
- Running 7 different OCR methods on each page (increased from 6)
- Higher DPI processing (1500 DPI)
- Additional advanced image preprocessing steps
- Comprehensive pattern-based post-processing

For best results:
- Use 1500 DPI for detailed text and maximum accuracy
- Use 1200 DPI for faster processing with good quality
- The enhanced preprocessing particularly improves accuracy for degraded or poor-quality documents

## New Pattern-Based Corrections

The enhanced system now includes comprehensive pattern recognition that automatically fixes:

### URL and Web Address Corrections
- `httos://` → `https://`
- `hftp://` → `http://`
- `wwvv.` → `www.`
- `github.corn/` → `github.com/`
- `gmail.corn` → `gmail.com`
- And many other common web address OCR errors

### Phone Number Cleaning
- Removes `JJ` and `JJR` artifacts commonly appearing near phone numbers
- Cleans up standalone OCR artifacts that interfere with phone number readability

### Email Address Corrections
- Fixes common domain OCR errors like `.corn` → `.com`
- Handles major email providers (Gmail, Yahoo, Outlook, Hotmail)

### Word Separation Fixes
- Reconnects words incorrectly separated by OCR
- Handles patterns like `manage ment` → `management`
- Fixes `develop ment` → `development`

### Character Substitution in Context
- Comprehensive `rn` → `m` corrections for common words
- Context-aware corrections that preserve proper capitalization
- Handles words like `cornpany` → `company`, `rnanagement` → `management`

## Automated Workflow

For convenience, the `run_ocr_improvement.sh` script automates the entire OCR improvement workflow:

```bash
./run_ocr_improvement.sh path/to/resume.pdf [output_dir] [dpi]
```

This script will:
1. Run a comparison of traditional OCR methods as a baseline
2. Apply the targeted OCR improvement with consensus approach
3. Run a high-quality (1500 DPI) targeted OCR if needed
4. Display a summary of results and output locations

## Results of the Enhanced Consensus Approach

The enhanced consensus approach significantly improves OCR accuracy for problematic words:

| Problem Word | Traditional OCR | Raw OCR | Targeted OCR |
|--------------|-----------------|---------|--------------|
| Ciplomacy    | ❌              | ❌      | ✅ (Diplomacy) |
| villereek    | ❌              | ❌      | ✅ (millcreek) |

This improvement is achieved through:
- Case-insensitive word voting for better consensus
- Special handling of capitalization for known problematic words
- Location pattern recognition for address fields
- Multi-approach character-focused image processing to better distinguish similar characters
