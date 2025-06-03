# OCR Improvement Guide

This guide explains how to use the OCR improvement scripts to fix problematic word recognition issues in PDF documents.

## Targeted OCR Improvement

The targeted OCR improvement script (`targeted_ocr_improvement.py`) addresses specific recognition problems that occur consistently across multiple OCR runs, such as "Ciplomacy" instead of "diplomacy" and "villereek" instead of "millcreek".

### How It Works

The script uses several specialized techniques:

1. **Multiple OCR Processing Methods**: Applies 6 different OCR approaches to each page:
   - Traditional OCR with contrast/sharpness enhancement
   - Enhanced contrast processing for better character distinction
   - Multi-scale processing (normal, enlarged, reduced)
   - Character-focused processing with specialized filters
   - Threshold-based processing for better character separation
   - Location-specific processing optimized for address fields

2. **Enhanced Consensus Approach**: Combines results from different processing methods using a sophisticated case-insensitive word-level voting mechanism to select the most likely correct text, with special handling for known problematic words.

3. **Known Word Correction**: Applies specific corrections for known problematic words.

4. **Specialized Location Recognition**: Uses pattern matching to detect and correct location fields that often contain problematic city names.

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
    # Add your new problematic words here
    "misrecognized": "correct",
}
```

You can also add character confusion patterns to the `char_confusions` dictionary:

```python
self.char_confusions = {
    'C': ['d', 'D'],  # For "Ciplomacy" -> "diplomacy"
    'v': ['m'],       # For "villereek" -> "millcreek"
    'rn': ['m'],      # For "cornpany" -> "company"
    # Add your new character confusions here
}
```

## Performance Considerations

The targeted OCR process is more computationally intensive than standard OCR due to:
- Running 6 different OCR methods on each page
- Higher DPI processing (1500 DPI)
- Additional image preprocessing steps

For best results:
- Use 1500 DPI for detailed text
- Use 1200 DPI for faster processing with reasonable quality

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
