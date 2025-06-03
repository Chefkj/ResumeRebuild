#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sequential Text Ordering for OCR Text

This module provides functionality to order OCR-extracted text in a logical
sequential order based on posi                # 3. Special case for any header that might be part of a word split across blocks
                # (e.g., "OBJECTIVE" in "objectives", "SKILLS" in "skillset", etc.)
                # Check if this block contains a header and the next block starts with lowercase letters/numbers
                try:
                    block_index = blocks.index(block)
                    if block_index + 1 < len(blocks):
                        next_block = blocks[block_index + 1]
                        next_text = next_block.text.strip()
                        # If the next block starts with lowercase letter/number, this is likely a word split across blocks
                        if next_text and next_text[0].isalnum() and next_text[0].lower() == next_text[0]:
                            continue
                except ValueError:
                    # block not in blocks (shouldn't happen)
                    passt analysis.
"""

import re
import logging
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

class TextBlock:
    """A block of text with position and ordering information."""
    
    def __init__(self, text: str, x0: float = 0, y0: float = 0, 
                 width: float = 0, height: float = 0, page: int = 0):
        """
        Initialize a text block.
        
        Args:
            text: The text content
            x0: Left coordinate
            y0: Top coordinate
            width: Block width
            height: Block height
            page: Page number
        """
        self.text = text
        self.x0 = x0
        self.y0 = y0
        self.width = width
        self.height = height
        self.page = page
        
        # Derived attributes
        self.x1 = x0 + width
        self.y1 = y0 + height
        self.is_header = False
        self.content_type = None
        self.section = None
    
    def __str__(self):
        """Return string representation."""
        return f"TextBlock[p{self.page}]({self.x0:.1f},{self.y0:.1f}): {self.text[:20]}..."
        
    def overlaps_horizontally(self, other: 'TextBlock', threshold: float = 0.3) -> bool:
        """Check if this block overlaps horizontally with another block."""
        # Calculate overlap
        overlap_width = min(self.x1, other.x1) - max(self.x0, other.x0)
        if overlap_width <= 0:
            return False
        
        # Calculate percentage of overlap relative to the narrower block
        min_width = min(self.width, other.width)
        return overlap_width / min_width >= threshold
    
    def is_same_line(self, other: 'TextBlock', threshold: float = 0.5) -> bool:
        """Check if this block is on the same line as another block."""
        # Check if blocks are on the same page
        if self.page != other.page:
            return False
            
        # Check vertical overlap
        overlap_height = min(self.y1, other.y1) - max(self.y0, other.y0)
        if overlap_height <= 0:
            return False
            
        # Calculate percentage of overlap relative to the shorter block
        min_height = min(self.height, other.height)
        return overlap_height / min_height >= threshold


class SequentialTextOrderer:
    """Orders OCR text blocks in a logical sequential order."""
    
    def __init__(self):
        """Initialize the text orderer."""
        # Common resume section headers for pattern recognition
        self.section_headers = [
            'SUMMARY', 'PROFILE', 'OBJECTIVE', 'ABOUT ME', 'PROFESSIONAL SUMMARY',
            'EXPERIENCE', 'EMPLOYMENT', 'WORK HISTORY', 'CAREER', 'PROFESSIONAL EXPERIENCE',
            'EDUCATION', 'ACADEMIC', 'QUALIFICATIONS', 'EDUCATIONAL BACKGROUND', 
            'SKILLS', 'COMPETENCIES', 'EXPERTISE', 'TECHNICAL SKILLS', 'CORE SKILLS',
            'PROJECTS', 'ACCOMPLISHMENTS', 'ACHIEVEMENTS', 'KEY PROJECTS',
            'CERTIFICATIONS', 'LANGUAGES', 'INTERESTS', 'CERTIFICATES',
            'PROFESSIONAL', 'VOLUNTEER', 'REFERENCES', 'ACTIVITIES',
            'PUBLICATIONS', 'AWARDS', 'HONORS', 'LEADERSHIP'
        ]
    
    def order_text_blocks(self, blocks: List[TextBlock]) -> List[TextBlock]:
        """
        Order text blocks in a logical sequential order.
        
        Args:
            blocks: List of text blocks to order
            
        Returns:
            List of ordered text blocks
        """
        if not blocks:
            return []
            
        # Group blocks by page
        pages = {}
        for block in blocks:
            if block.page not in pages:
                pages[block.page] = []
            pages[block.page].append(block)
        
        # Process each page separately
        ordered_blocks = []
        for page_num in sorted(pages.keys()):
            page_blocks = pages[page_num]
            
            # Identify and mark headers
            self._identify_headers(page_blocks)
            
            # Form lines from blocks that are horizontally adjacent
            lines = self._form_lines(page_blocks)
            
            # Sort lines by vertical position
            lines.sort(key=lambda line: line[0].y0 if line else float('inf'))
            
            # Add blocks from lines to the ordered list
            for line in lines:
                # Sort blocks within a line by horizontal position
                line.sort(key=lambda block: block.x0)
                ordered_blocks.extend(line)
        
        return ordered_blocks
    
    def _identify_headers(self, blocks: List[TextBlock]) -> None:
        """
        Identify section headers in text blocks.
        
        Args:
            blocks: List of text blocks to analyze
        """
        for block in blocks:
            # Skip blocks that are likely not headers
            # Headers should be on their own line and not part of a sentence
            block_text = block.text.strip()
            
            # Skip very short text that's unlikely to be a header
            if len(block_text) < 3:
                continue
            
            # If the block has text before or after that's not a newline, it's likely not a header
            # Headers should be wrapped in newlines: \nHEADER\n
            
            # Check if the block text contains a header
            for header in self.section_headers:
                # Only consider exact matches or very clear header patterns
                
                # Check if the text is equal to the header (case insensitive)
                # This is the most reliable indicator of a header
                if block_text.upper() == header.upper():
                    block.is_header = True
                    block.content_type = "header"
                    block.section = header
                    break
                
                # Check for the pattern: header alone on a line surrounded by newlines
                # This enforces the \nHEADER\n pattern
                # Use stricter pattern that requires actual newlines, not just whitespace
                header_pattern = fr'(^|\n)\s*{header}(\s*$|\s*\n)'  # \nHEADER\n pattern
                if re.search(header_pattern, block.text, re.IGNORECASE):
                    # Extra check to make sure the next line doesn't start with lowercase letter/number
                    # which would indicate it's part of a word (like 'objectives', 'experiences', etc.)
                    if '\n' in block.text:
                        after_header = block.text.split(re.search(fr'{header}', block.text, re.IGNORECASE).group(), 1)[1]
                        if after_header.strip() and after_header.strip()[0].isalnum() and after_header.strip()[0].lower() == after_header.strip()[0]:
                            continue  # Skip if followed by lowercase letter/number (likely part of a word)
                    
                    block.is_header = True
                    block.content_type = "header"
                    block.section = header
                    break
                
                # Rules to reject non-header patterns
                
                # 1. Not a header if it appears inside a sentence
                # Example: "...achieve objectives with lower..."
                sentence_context_pattern = fr'[a-z0-9]\s+{header}|\b{header}\s+[a-z0-9]'
                if re.search(sentence_context_pattern, block.text, re.IGNORECASE):
                    continue
                
                # 2. Not a header if it's part of a word (like "objectives" containing "OBJECTIVE")
                word_fragment_pattern = fr'\b{header}([a-z0-9])|([a-z0-9]){header}\b'
                if re.search(word_fragment_pattern, block.text, re.IGNORECASE):
                    continue
                
                # 3. Special case for any header that might be part of a word split across blocks
                # (e.g., "OBJECTIVE" in "objectives", "SKILLS" in "skillset", etc.)
                # Check if this block contains a header and the next block starts with lowercase letters/numbers
                try:
                    block_index = blocks.index(block)
                    if block_index + 1 < len(blocks):
                        next_block = blocks[block_index + 1]
                        next_text = next_block.text.strip()
                        # If the next block starts with lowercase letter/number, this is likely a word split across blocks
                        if next_text and next_text[0].isalnum() and next_text[0].lower() == next_text[0]:
                            continue
                except ValueError:
                    # block not in blocks (shouldn't happen)
                    pass
                
                # 4. Check if the potential header is surrounded by text that makes it part of a sentence
                # This handles cases where the word is preceded or followed by text without newlines
                surrounding_text_pattern = fr'[^\n]\s*{header}|\b{header}\s*[^\n]'
                if re.search(surrounding_text_pattern, block.text, re.IGNORECASE) and not re.search(fr'(^|\n)\s*{header}\s*($|\n)', block.text, re.IGNORECASE):
                    continue
                
                # If we've passed all the rejection rules, and we found a header pattern, 
                # still be careful about potential false positives
                if re.search(fr'\b{header}\b', block.text, re.IGNORECASE):
                    # Check if this might be part of a word rather than a standalone header
                    # For example, "objective" in "objectives", "experience" in "experienced", etc.
                    # Check if the lowercase version of the header is part of a longer word in the text
                    header_lower = header.lower()
                    if any(word.lower().startswith(header_lower) and len(word) > len(header_lower) for word in block.text.split()):
                        continue
                        
                    # If we can't tell from this block, look at the next block
                    try:
                        block_index = blocks.index(block)
                        if block_index + 1 < len(blocks):
                            next_block = blocks[block_index + 1]
                            next_text = next_block.text.strip()
                            # If the next block starts with lowercase letter/number, skip this header
                            if next_text and next_text[0].isalnum() and next_text[0].lower() == next_text[0]:
                                continue
                    except ValueError:
                        pass
                    
                    block.is_header = True
                    block.content_type = "header"
                    block.section = header
                    break
    
    def _form_lines(self, blocks: List[TextBlock]) -> List[List[TextBlock]]:
        """
        Group blocks into lines based on vertical position.
        
        Args:
            blocks: List of text blocks to group
            
        Returns:
            List of lines, where each line is a list of blocks
        """
        # First, sort blocks by vertical position
        sorted_blocks = sorted(blocks, key=lambda b: (b.y0, b.x0))
        
        # Initialize lines
        lines = []
        current_line = []
        
        # Process each block
        for block in sorted_blocks:
            # If this is the first block or it's on the same line as the previous blocks
            if not current_line or any(block.is_same_line(b) for b in current_line):
                current_line.append(block)
            else:
                # This block is on a new line
                lines.append(current_line)
                current_line = [block]
        
        # Add the last line if it's not empty
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def process_text(self, text: str, block_info: Optional[List[Dict]] = None) -> str:
        """
        Process text to ensure sequential order.
        
        Args:
            text: Text to process
            block_info: Optional positional information about text blocks
            
        Returns:
            Re-ordered text
        """
        # If we don't have positional info, apply heuristics
        if not block_info:
            return self._apply_ordering_heuristics(text)
        
        # Create text blocks from position info
        blocks = []
        lines = text.split('\n')
        
        for i, block_data in enumerate(block_info):
            if i < len(lines):
                block = TextBlock(
                    text=lines[i],
                    x0=block_data.get('x0', 0),
                    y0=block_data.get('y0', 0),
                    width=block_data.get('width', 0),
                    height=block_data.get('height', 0),
                    page=block_data.get('page', 0)
                )
                blocks.append(block)
                
        # Enhanced special handling for section headers split across blocks 
        # (e.g., "objectives" as "OBJECTIVE" + "s", "skillset" as "SKILLS" + "et", etc.)
        # Do this before header identification to ensure correct handling
        i = 0
        while i < len(blocks) - 1:
            current_block = blocks[i]
            next_block = blocks[i+1]
            current_text = current_block.text.strip()
            next_text = next_block.text.strip()
            
            # Enhanced header detection with more robust checks
            for header in self.section_headers:
                # Check if current block matches a header exactly AND the next block starts with lowercase letter/number
                # This handles cases like "SKILLS" followed by "et" (from "skillset"), or any header followed by text
                # that appears to be part of a word
                if current_text.upper() == header.upper() and next_text and len(next_text) > 0:
                    # Check if next block starts with a lowercase letter or number - indicating it's part of a word
                    if next_text[0].isalnum() and next_text[0].lower() == next_text[0]:
                        # Found a potential header followed by lowercase text (likely part of a word)
                        
                        # Special check for the cases where the next text might actually be part of the section
                        # content rather than part of the header word
                        # For example, "SKILLS" + "\n\n• Java" would be a valid header + content
                        if next_text.startswith('\n') or next_text.startswith('•') or next_text.startswith('-'):
                            # This looks like proper section content, not part of a header word - do not combine
                            i += 1
                            break
                        
                        # Combine the blocks to form a complete word/phrase
                        current_block.text = f"{current_text}{next_text}"
                        blocks.pop(i+1)  # Remove the next block safely
                        # Don't increment i, as we need to check the next pair
                        break
                    
                    # If the next text starts with uppercase or punctuation, 
                    # it's likely a proper break between header and content
                    else:
                        i += 1
                        break
            else:  # No header match found or no need to combine
                i += 1
        
        # Order the blocks
        ordered_blocks = self.order_text_blocks(blocks)
        
        # Reassemble text
        ordered_text = '\n'.join(block.text for block in ordered_blocks)
        
        return ordered_text
    
    def _apply_ordering_heuristics(self, text: str) -> str:
        """
        Apply heuristics to improve text ordering when positional info is missing.
        
        Args:
            text: Text to reorder
            
        Returns:
            Reordered text
        """
        # Enhanced pre-processing to fix cases where section headers are split across lines
        # This handles cases like "OBJECTIVE\ns" -> "objectives", "SKILLS\net" -> "skillset", etc.
        for header in self.section_headers:
            # Match header at start or after newline, followed by a newline and lowercase letter/digit
            pattern = fr'(^|\n)({header})\s*\n\s*([a-z0-9][a-z0-9\s]*)'
            # Replace with the context + lowercase header + the following text
            # This handles not just single letters like 's' but entire word fragments
            replacement = lambda m: f"{m.group(1)}{m.group(2).lower()}{m.group(3)}"
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            
            # Also handle cases where there's an intervening character like a hyphen or dot
            # For example: "SKILL\n. Advanced user" -> "skill. Advanced user"
            pattern2 = fr'(^|\n)({header})\s*\n\s*([.•\-–—:,])'
            replacement2 = lambda m: f"{m.group(1)}{m.group(2)}\n{m.group(3)}"
            text = re.sub(pattern2, replacement2, text, flags=re.IGNORECASE)
        
        # Split text into lines
        lines = text.split('\n')
        
        # Identify section headers with more careful matching - ensuring they are wrapped in newlines
        header_indices = []
        for i, line in enumerate(lines):
            line_text = line.strip()
            
            # Skip very short lines or lines that are likely parts of sentences
            if len(line_text) < 3:
                continue
                
            # Avoid lines that start with lowercase (likely continuation of previous text)
            if line_text and line_text[0].islower():
                continue
                
            # Check if next line (if exists) starts with lowercase (indicating current line isn't a header)
            if i+1 < len(lines) and lines[i+1].strip() and lines[i+1].strip()[0].islower():
                # This looks like a continuation, not a header
                continue
                
            # Check previous and next line to enforce \nHEADER\n pattern
            # Previous line should be empty or not exist
            prev_line_empty = (i == 0) or not lines[i-1].strip()
            # Next line should be empty or not exist
            next_line_empty = (i == len(lines)-1) or not lines[i+1].strip()
                
            for header in self.section_headers:
                # Skip if the header is not properly wrapped in newlines
                if not prev_line_empty and not next_line_empty:
                    continue
                    
                # Check if next line starts with lowercase letter or digit
                # This would indicate the header is part of a word split across lines (e.g., "objectives")
                if i+1 < len(lines):
                    next_line = lines[i+1].strip()
                    if next_line and next_line[0].isalnum() and next_line[0].lower() == next_line[0]:
                        # This is likely a word split across lines, not a header
                        continue
                
                # Check if the text is equal to the header (case insensitive)
                if line_text.upper() == header.upper():
                    header_indices.append((i, header))
                    break
                
                # Check if the header is at the beginning of a line and not part of a sentence
                header_pattern = fr'^\s*{header}\s*$'  # Header alone on a line
                if re.search(header_pattern, line_text, re.IGNORECASE):
                    # Double-check this isn't a word split across lines
                    if i+1 < len(lines):
                        next_line = lines[i+1].strip()
                        if next_line and next_line[0].isalnum() and next_line[0].lower() == next_line[0]:
                            continue  # Skip, likely part of a word split across lines
                    
                    header_indices.append((i, header))
                    break
        
        # If no headers found, return original text
        if not header_indices:
            return text
        
        # Create sections based on header positions
        sections = []
        for i in range(len(header_indices)):
            start_idx = header_indices[i][0]
            end_idx = header_indices[i+1][0] if i < len(header_indices) - 1 else len(lines)
            
            section_text = '\n'.join(lines[start_idx:end_idx])
            sections.append((header_indices[i][1], section_text))
        
        # Order sections in a logical sequence
        # More common header order in resumes
        section_priority = {
            'SUMMARY': 1, 
            'PROFILE': 2,
            'OBJECTIVE': 3,
            'ABOUT ME': 4, 
            'PROFESSIONAL SUMMARY': 5,
            'EXPERIENCE': 10, 
            'EMPLOYMENT': 11, 
            'WORK HISTORY': 12, 
            'CAREER': 13, 
            'PROFESSIONAL EXPERIENCE': 14,
            'EDUCATION': 20, 
            'ACADEMIC': 21, 
            'QUALIFICATIONS': 22, 
            'EDUCATIONAL BACKGROUND': 23,
            'SKILLS': 30, 
            'COMPETENCIES': 31, 
            'EXPERTISE': 32, 
            'TECHNICAL SKILLS': 33, 
            'CORE SKILLS': 34,
            'PROJECTS': 40, 
            'ACCOMPLISHMENTS': 41, 
            'ACHIEVEMENTS': 42, 
            'KEY PROJECTS': 43,
            'CERTIFICATIONS': 50, 
            'LANGUAGES': 51, 
            'INTERESTS': 52, 
            'CERTIFICATES': 53,
            'PROFESSIONAL': 60, 
            'VOLUNTEER': 61, 
            'REFERENCES': 62, 
            'ACTIVITIES': 63,
            'PUBLICATIONS': 64, 
            'AWARDS': 65, 
            'HONORS': 66, 
            'LEADERSHIP': 67
        }
        
        # Sort sections by priority
        sections.sort(key=lambda s: section_priority.get(s[0].upper(), 100))
        
        # Combine into final text
        result = '\n\n'.join(section[1] for section in sections)
        
        return result


def apply_sequential_ordering(text: str, block_info: Optional[List[Dict]] = None) -> str:
    """
    Apply sequential ordering to OCR text.
    
    Args:
        text: Text to reorder
        block_info: Optional positional information for text blocks
        
    Returns:
        Reordered text
    """
    orderer = SequentialTextOrderer()
    return orderer.process_text(text, block_info)
