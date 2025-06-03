#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pattern Library for OCR Text Processing

This module provides a centralized pattern library for managing and applying
regex patterns used in OCR text extraction and processing. It allows for better
organization, documentation, and optimization of pattern matching operations.
"""

import re
import logging
from typing import Dict, List, Tuple, Union, Optional, Any, Callable

logger = logging.getLogger(__name__)

class PatternLibrary:
    """
    A centralized library for managing regex patterns used in OCR text processing.
    
    This class provides methods to register, categorize, and apply regex patterns,
    making pattern management more maintainable and allowing for optimization
    and measurement of pattern application performance.
    """
    
    def __init__(self):
        """Initialize an empty pattern library."""
        self.patterns = {}
        self.categories = {}
        self.performance_stats = {}
    
    def add_pattern(self, name: str, pattern: str, replacement: str, 
                    description: str, category: str = "general") -> None:
        """
        Add a regex pattern to the library.
        
        Args:
            name: Unique identifier for the pattern
            pattern: Regex pattern string
            replacement: Replacement string or template
            description: Description of what the pattern does
            category: Category for grouping related patterns
        """
        self.patterns[name] = {
            'pattern': pattern,
            'replacement': replacement,
            'description': description,
            'category': category,
            'compiled': re.compile(pattern),
            'count_applied': 0,
            'time_spent': 0.0
        }
        
        # Add to category index
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(name)
        
        logger.debug(f"Added pattern '{name}' to category '{category}'")
    
    def get_pattern(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a pattern by name.
        
        Args:
            name: Pattern identifier
            
        Returns:
            Pattern information dictionary or None if not found
        """
        return self.patterns.get(name)
    
    def get_patterns_by_category(self, category: str) -> List[str]:
        """
        Get all pattern names in a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of pattern names in the category
        """
        return self.categories.get(category, [])
    
    def apply_pattern(self, text: str, pattern_name: str) -> str:
        """
        Apply a single pattern to text.
        
        Args:
            text: Text to process
            pattern_name: Name of the pattern to apply
            
        Returns:
            Processed text with pattern applied
        """
        import time
        pattern_info = self.get_pattern(pattern_name)
        
        if not pattern_info:
            logger.warning(f"Pattern '{pattern_name}' not found")
            return text
            
        start_time = time.time()
        result = pattern_info['compiled'].sub(pattern_info['replacement'], text)
        end_time = time.time()
        
        # Update performance stats
        duration = end_time - start_time
        pattern_info['count_applied'] += 1
        pattern_info['time_spent'] += duration
        
        # Count matches (by comparing input and output)
        if result != text:
            logger.debug(f"Pattern '{pattern_name}' applied {pattern_info['count_applied']} times")
            
        return result
    
    def apply_category(self, text: str, category: str) -> str:
        """
        Apply all patterns in a category to text.
        
        Args:
            text: Text to process
            category: Category of patterns to apply
            
        Returns:
            Processed text with all patterns in category applied
        """
        pattern_names = self.get_patterns_by_category(category)
        result = text
        
        for name in pattern_names:
            result = self.apply_pattern(result, name)
            
        return result
    
    def apply_all(self, text: str, categories: Optional[List[str]] = None) -> str:
        """
        Apply all patterns to text, optionally filtering by categories.
        
        Args:
            text: Text to process
            categories: Optional list of categories to include
            
        Returns:
            Processed text with all applicable patterns applied
        """
        result = text
        
        # If categories specified, only use those
        if categories:
            for category in categories:
                result = self.apply_category(result, category)
        else:
            # Otherwise apply all patterns
            for name in self.patterns:
                result = self.apply_pattern(result, name)
                
        return result
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate a performance report for pattern application.
        
        Returns:
            Dictionary with performance metrics for each pattern
        """
        report = {
            'patterns': {},
            'categories': {},
            'total_time': 0.0,
            'total_applications': 0
        }
        
        # Pattern-level stats
        for name, info in self.patterns.items():
            report['patterns'][name] = {
                'count': info['count_applied'],
                'time': info['time_spent'],
                'avg_time': info['time_spent'] / info['count_applied'] if info['count_applied'] > 0 else 0,
                'category': info['category']
            }
            report['total_time'] += info['time_spent']
            report['total_applications'] += info['count_applied']
            
        # Category-level stats
        for category in self.categories:
            cat_time = 0
            cat_count = 0
            
            for name in self.categories[category]:
                info = self.patterns[name]
                cat_time += info['time_spent']
                cat_count += info['count_applied']
                
            report['categories'][category] = {
                'count': cat_count,
                'time': cat_time,
                'avg_time': cat_time / cat_count if cat_count > 0 else 0
            }
            
        return report
    
    def print_performance_report(self) -> None:
        """Print a formatted performance report to the console."""
        report = self.get_performance_report()
        
        print("\n===== Pattern Library Performance Report =====")
        print(f"Total patterns: {len(self.patterns)}")
        print(f"Total categories: {len(self.categories)}")
        print(f"Total pattern applications: {report['total_applications']}")
        print(f"Total processing time: {report['total_time']:.6f} seconds")
        
        print("\n----- By Category -----")
        for category, stats in sorted(report['categories'].items(), 
                                    key=lambda x: x[1]['time'], reverse=True):
            print(f"{category}: {stats['count']} applications, {stats['time']:.6f}s " +
                  f"({stats['time']/report['total_time']*100:.1f}% of total)")
        
        print("\n----- Top 10 Patterns by Processing Time -----")
        patterns_by_time = sorted(report['patterns'].items(), 
                               key=lambda x: x[1]['time'], reverse=True)
        
        for name, stats in patterns_by_time[:10]:
            pattern_info = self.patterns[name]
            print(f"{name} ({pattern_info['category']}): {stats['count']} applications, " +
                  f"{stats['time']:.6f}s ({stats['time']/report['total_time']*100:.1f}% of total)")
            print(f"  Description: {pattern_info['description']}")
            print(f"  Pattern: {pattern_info['pattern']}")
            print()

# Create date pattern functions
def create_date_patterns() -> List[Tuple[str, str, str, str]]:
    """
    Create standardized date patterns for resumes.
    
    Returns:
        List of tuples: (name, pattern, replacement, description)
    """
    month_names = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)'
    
    patterns = [
        # Date with newline between month and year
        (
            'date_month_year_newline',
            fr'({month_names})\s+(\d{{4}})\s*\n\s*-\s*({month_names})\s*\n?\s*(\d{{4}})',
            r'\1 \2 - \3 \4',
            'Fix date ranges with newlines between month and year'
        ),
        
        # Date with no spaces
        (
            'date_no_spaces',
            fr'({month_names})(\d{{4}})-({month_names})(\d{{4}})',
            r'\1 \2 - \3 \4',
            'Fix date ranges without spaces'
        ),
        
        # Date with dash prefix
        (
            'date_dash_prefix',
            fr'^-\s*({month_names})\s+(\d{{4}})',
            r' - \1 \2',
            'Fix dates with dash prefix at start of line'
        ),
        
        # Date with dash prefix after newline
        (
            'date_dash_prefix_inline',
            fr'\n-\s*({month_names})\s+(\d{{4}})',
            r'\n - \1 \2',
            'Fix dates with dash prefix after newline'
        ),
        
        # Date with newline in the middle of a range
        (
            'date_newline_in_range',
            fr'({month_names})\s+(\d{{4}})\s*-\s*({month_names})\s*\n\s*(\d{{4}})',
            r'\1 \2 - \3 \4',
            'Fix date ranges with newline in the middle'
        ),
        
        # Normalize month abbreviations
        (
            'date_month_abbreviation',
            fr'\b(Sept)\b',
            r'Sep',
            'Normalize September abbreviation'
        ),
        
        # Date with no spaces between month and year
        (
            'date_month_year_nospace',
            fr'\b({month_names})(\d{{4}})\b',
            r'\1 \2',
            'Add space between month and year'
        ),
        
        # Date with inappropriate spacing around dash
        (
            'date_fix_dash_spacing',
            fr'({month_names})\s+(\d{{4}})\s*[-–—]\s*({month_names})\s+(\d{{4}})',
            r'\1 \2 - \3 \4',
            'Standardize spacing around dash in date ranges'
        ),
        
        # Spans multiple years with inappropriate spacing
        (
            'date_year_range_spacing',
            r'(\d{4})\s*[-–—]\s*(\d{4})',
            r'\1 - \2',
            'Fix spacing in year ranges'
        ),
        
        # Present or current dates
        (
            'date_present',
            fr'({month_names})\s+(\d{{4}})\s*[-–—]\s*(Present|Current)',
            r'\1 \2 - \3',
            'Standardize present/current date formats'
        )
    ]
    
    return patterns

def initialize_standard_library() -> PatternLibrary:
    """
    Initialize a pattern library with standard OCR text patterns.
    
    Returns:
        PatternLibrary: Initialized library with standard patterns
    """
    library = PatternLibrary()
    
    # Add date patterns
    date_patterns = create_date_patterns()
    for name, pattern, replacement, description in date_patterns:
        library.add_pattern(name, pattern, replacement, description, category="dates")
    
    # Location + verb patterns
    state_names = r'(?:Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming)'
    
    library.add_pattern(
        'state_verb_past',
        fr'({state_names})([A-Z][a-z]+ed\b)',
        r'\1\n\2',
        'State name followed by past-tense verb',
        category="locations"
    )
    
    library.add_pattern(
        'state_verb_ing',
        fr'({state_names})([A-Z][a-z]+ing\b)',
        r'\1\n\2',
        'State name followed by present participle verb',
        category="locations"
    )
    
    # City patterns
    compound_cities = r'(?:Salt Lake City|New York|Los Angeles|San Francisco|San Diego|San Jose|Las Vegas|St\. Louis|Kansas City)'
    
    library.add_pattern(
        'city_verb',
        fr'({compound_cities})([A-Z][a-z]+)',
        r'\1\n\2',
        'City name followed by capitalized word',
        category="locations"
    )
    
    # Email formatting patterns
    library.add_pattern(
        'email_space_before_at',
        r'(\w+)\s+@(\w+)',
        r'\1@\2',
        'Remove space before @ in email',
        category="contact"
    )
    
    library.add_pattern(
        'email_space_after_at',
        r'(\w+)@\s+(\w+)',
        r'\1@\2',
        'Remove space after @ in email',
        category="contact"
    )
    
    library.add_pattern(
        'email_space_around_at',
        r'(\w+)\s+@\s+(\w+)',
        r'\1@\2',
        'Remove spaces around @ in email',
        category="contact"
    )
    
    # Section header patterns
    library.add_pattern(
        'embedded_skills_header',
        r'([a-z])SKILLS',
        r'\1\n\nSKILLS',
        'Fix embedded SKILLS header',
        category="headers"
    )
    
    library.add_pattern(
        'embedded_experience_header',
        r'([a-z])EXPERIENCE',
        r'\1\n\nEXPERIENCE',
        'Fix embedded EXPERIENCE header',
        category="headers"
    )
    
    # Handle header with a period before it
    library.add_pattern(
        'period_before_header_skills',
        r'\.SKILLS',
        r'.\n\nSKILLS',
        'Fix SKILLS header with period prefix',
        category="headers"
    )
    
    library.add_pattern(
        'period_before_header_experience',
        r'\.EXPERIENCE',
        r'.\n\nEXPERIENCE',
        'Fix EXPERIENCE header with period prefix',
        category="headers"
    )
    
    # Special cases
    library.add_pattern(
        'name_ku_prefix',
        r'([A-Z]+\s+[A-Z]+)\s+KU([A-Z][a-z]+)',
        r'\1\n\2',
        'Fix name with KU prefix pattern',
        category="special_cases"
    )
    
    # Handle single-word name with KU prefix
    library.add_pattern(
        'single_name_ku_prefix',
        r'([A-Z]+)KU([A-Z][a-z]+)',
        r'\1\n\2',
        'Fix single-word name with KU prefix pattern',
        category="special_cases"
    )
    
    library.add_pattern(
        'cowen_jr_pattern',
        r'COWENJRKU([A-Z][a-z]+)',
        r'COWEN JR\n\1',
        'Fix COWENJRKU pattern',
        category="special_cases"
    )
    
    return library
