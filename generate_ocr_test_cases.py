#!/usr/bin/env python3
"""
Test case generator for OCR text extraction validation.

This script generates text samples with various problematic patterns
commonly found in OCR-extracted resumes to test the robustness of
the text processing pipeline.
"""

import os
import random
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the OCR extractor for testing the fixes
from src.utils.ocr_text_extraction import OCRTextExtractor
from src.utils.text_utils import fix_broken_lines

class OCRTestCaseGenerator:
    """Generator for test cases with common OCR issues."""
    
    def __init__(self):
        """Initialize the test case generator with common patterns."""
        # Sample data for creating test cases
        self.states = [
            'Utah', 'Texas', 'Maine', 'Idaho', 'Ohio', 'Iowa', 'Florida', 'Georgia', 
            'Virginia', 'California', 'Colorado', 'Oregon', 'Washington', 'Arizona'
        ]
        
        self.cities = [
            'Salt Lake City', 'New York', 'Los Angeles', 'San Francisco', 'Chicago',
            'Boston', 'Seattle', 'Austin', 'Denver', 'Phoenix', 'Portland',
            'Atlanta', 'Dallas', 'Houston', 'Miami', 'Philadelphia'
        ]
        
        self.actions = [
            'Acted', 'Developed', 'Managed', 'Coordinated', 'Created', 'Implemented',
            'Designed', 'Led', 'Researched', 'Analyzed', 'Produced', 'Maintained',
            'Operated', 'Supervised', 'Facilitated', 'Spearheaded', 'Conducted'
        ]
        
        self.present_actions = [
            'Acting', 'Developing', 'Managing', 'Coordinating', 'Creating', 'Implementing',
            'Designing', 'Leading', 'Researching', 'Analyzing', 'Producing', 'Maintaining'
        ]
        
        self.section_headers = [
            'SUMMARY', 'PROFILE', 'OBJECTIVE', 'EXPERIENCE', 'EMPLOYMENT',
            'WORK HISTORY', 'EDUCATION', 'SKILLS', 'PROJECTS', 'CERTIFICATIONS'
        ]
        
        self.job_titles = [
            'Software Engineer', 'Project Manager', 'Marketing Specialist',
            'Data Analyst', 'Product Manager', 'Sales Representative', 
            'Customer Service Manager', 'Operations Director', 'Research Analyst',
            'Human Resources Coordinator', 'Executive Assistant'
        ]
        
        self.companies = [
            'Google', 'Microsoft', 'Apple', 'Amazon', 'Meta', 'IBM', 'Intel',
            'Cisco', 'Oracle', 'Salesforce', 'Adobe', 'Twitter', 'Netflix',
            'Uber', 'Airbnb', 'Dell', 'HP', 'Tesla', 'SpaceX', 'LinkedIn'
        ]
        
        self.months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        
        self.years = list(range(2010, 2024))
        
        self.skills = [
            'Python', 'JavaScript', 'SQL', 'Java', 'C++', 'Machine Learning',
            'Data Analysis', 'Project Management', 'Marketing', 'Communication',
            'Leadership', 'Problem Solving', 'Critical Thinking', 'Teamwork',
            'Customer Service', 'Sales', 'Accounting', 'Design', 'Writing'
        ]
        
        self.degrees = [
            'Bachelor of Science', 'Bachelor of Arts', 'Master of Science',
            'Master of Business Administration', 'Associate of Science',
            'Doctor of Philosophy', 'Bachelor of Engineering'
        ]
        
        self.majors = [
            'Computer Science', 'Business Administration', 'Marketing',
            'Engineering', 'English', 'Psychology', 'Biology', 'Economics',
            'Mathematics', 'Physics', 'Chemistry', 'Political Science'
        ]
        
        self.universities = [
            'University of California', 'Stanford University', 'Harvard University',
            'Massachusetts Institute of Technology', 'University of Washington',
            'New York University', 'University of Michigan', 'University of Texas',
            'Georgia Institute of Technology', 'Ohio State University',
            'University of Florida', 'Arizona State University', 'Penn State University'
        ]
        
        # Problematic patterns
        self.ocr_errors = [
            (r' ', ''),  # Remove space
            (r'@', '@ '),  # Add space after @
            (r':', ':'),   # No error for colon
            (r'.', '.*'),  # OCR conversion of period to period-asterisk
            (r'\n', ''),   # Remove newline
        ]
    
    def generate_merged_location_cases(self, count=10):
        """Generate test cases with merged location patterns."""
        test_cases = []
        
        for _ in range(count):
            state = random.choice(self.states)
            action = random.choice(self.actions)
            
            # Create merged pattern (e.g., "UtahDeveloped")
            merged_text = f"{state}{action} as part of the team responsibilities."
            
            test_cases.append({
                'type': 'merged_location',
                'text': merged_text,
                'expected': f"{state}\n{action} as part of the team responsibilities."
            })
            
            # Also generate city+state+text pattern
            city = random.choice(self.cities)
            state_abbr = state[:2].upper()
            merged_city_text = f"{city}, {state_abbr}{action} as part of the role."
            
            test_cases.append({
                'type': 'merged_city_state',
                'text': merged_city_text,
                'expected': f"{city}, {state_abbr}\n{action} as part of the role."
            })
        
        return test_cases
    
    def generate_embedded_header_cases(self, count=10):
        """Generate test cases with embedded section headers."""
        test_cases = []
        
        for _ in range(count):
            header = random.choice(self.section_headers)
            
            # Create text with header embedded after period
            embedded_text = f"Completed all required tasks.{header}Created a new system."
            
            test_cases.append({
                'type': 'embedded_header_after_period',
                'text': embedded_text,
                'expected': f"Completed all required tasks.\n\n{header}\n\nCreated a new system."
            })
            
            # Create text with header embedded within text
            prefix = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(5))
            suffix = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(5))
            embedded_mid_text = f"{prefix}{header}{suffix}"
            
            test_cases.append({
                'type': 'embedded_header_within_text',
                'text': embedded_mid_text,
                'expected': f"{prefix}\n\n{header}\n\n{suffix}"
            })
        
        return test_cases
    
    def generate_date_format_cases(self, count=10):
        """Generate test cases with problematic date formats."""
        test_cases = []
        
        for _ in range(count):
            month1 = random.choice(self.months)
            year1 = random.choice(self.years[:-1])  # Avoid choosing the last year
            month2 = random.choice(self.months)
            # Ensure a valid range of years
            if year1 >= 2023:
                year2 = 2023
            else:
                year2 = random.choice(range(year1 + 1, min(year1 + 5, 2024)))
            
            # Create broken date range with newline
            broken_date = f"{month1} {year1} - {month2}\n{year2}"
            
            test_cases.append({
                'type': 'broken_date_range',
                'text': broken_date,
                'expected': f"{month1} {year1} - {month2} {year2}"
            })
            
            # Create date with missing spaces
            missing_space_date = f"{month1}{year1} - {month2} {year2}"
            
            test_cases.append({
                'type': 'missing_space_date',
                'text': missing_space_date,
                'expected': f"{month1} {year1} - {month2} {year2}"
            })
            
            # Create date with dash prefix
            dash_prefix_date = f"-{month1} {year1} - {month2} {year2}"
            
            test_cases.append({
                'type': 'dash_prefix_date',
                'text': dash_prefix_date,
                'expected': f" - {month1} {year1} - {month2} {year2}"
            })
        
        return test_cases
    
    def generate_email_format_cases(self, count=5):
        """Generate test cases with problematic email formats."""
        test_cases = []
        
        domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'company.com']
        
        for _ in range(count):
            username = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(8))
            domain = random.choice(domains)
            
            # Create email with space after @
            spaced_email = f"{username}@ {domain}"
            
            test_cases.append({
                'type': 'email_space_after_at',
                'text': spaced_email,
                'expected': f"{username}@{domain}"
            })
            
            # Create email with space before @
            pre_space_email = f"{username} @{domain}"
            
            test_cases.append({
                'type': 'email_space_before_at',
                'text': pre_space_email,
                'expected': f"{username}@{domain}"
            })
        
        return test_cases
    
    def generate_broken_line_cases(self, count=10):
        """Generate test cases with broken line continuations."""
        test_cases = []
        
        connectors = ['with', 'for', 'and', 'the', 'to', 'of', 'in', 'as', 'by']
        
        for _ in range(count):
            connector = random.choice(connectors)
            
            # Create text with line broken after connector
            broken_after = f"Collaborated {connector}\nstakeholders to complete the project."
            
            test_cases.append({
                'type': 'broken_line_after_connector',
                'text': broken_after,
                'expected': f"Collaborated {connector} stakeholders to complete the project."
            })
            
            # Create text with line broken before connector
            words = ["Implemented", "the", "system", connector, "users", "across", "departments"]
            break_point = random.randint(1, 3)
            
            broken_before = ' '.join(words[:break_point]) + '\n' + ' '.join(words[break_point:])
            expected = ' '.join(words)
            
            test_cases.append({
                'type': 'broken_line_before_connector',
                'text': broken_before,
                'expected': expected
            })
        
        return test_cases
    
    def generate_multiple_skills_cases(self, count=5):
        """Generate test cases with multiple SKILLS sections."""
        test_cases = []
        
        for _ in range(count):
            # Create text with multiple SKILLS sections
            skills1 = random.sample(self.skills, 3)
            skills2 = random.sample(self.skills, 3)
            
            multiple_skills = f"""SKILLS

{', '.join(skills1)}

Some professional accomplishments here.

SKILLS

{', '.join(skills2)}"""
            
            # Expected: One main SKILLS section with both skill sets
            expected = f"""SKILLS

{', '.join(skills1)}

Some professional accomplishments here.

• SKILLS:

{', '.join(skills2)}"""
            
            test_cases.append({
                'type': 'multiple_skills_sections',
                'text': multiple_skills,
                'expected': expected
            })
        
        return test_cases
    
    def generate_combined_issues_cases(self, count=10):
        """Generate complex test cases combining multiple issues."""
        test_cases = []
        
        for _ in range(count):
            # Select random elements
            state = random.choice(self.states)
            action = random.choice(self.actions)
            job_title = random.choice(self.job_titles)
            company = random.choice(self.companies)
            month1 = random.choice(self.months)
            year1 = random.choice(self.years[:-1])  # Avoid choosing the last year
            month2 = random.choice(self.months)
            # Ensure a valid range of years
            if year1 >= 2023:
                year2 = 2023
            else:
                year2 = random.choice(range(year1 + 1, min(year1 + 5, 2024)))
            username = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(8))
            
            # Create complex case with multiple issues
            complex_text = f"""{job_title}
{company} | {state}{action} as team lead
{month1} {year1} - {month2}\n{year2}
• Improved efficiency by 20% through automation.
• Collaborated with\nstakeholders to develop new products.
Contact: {username}@ gmail.com
SKILLS.Advanced in Python and SQL."""
            
            # Expected corrected text
            expected_text = f"""{job_title}
{company} | {state}
{action} as team lead
{month1} {year1} - {month2} {year2}
• Improved efficiency by 20% through automation.
• Collaborated with stakeholders to develop new products.
Contact: {username}@gmail.com

SKILLS

Advanced in Python and SQL."""
            
            test_cases.append({
                'type': 'combined_issues',
                'text': complex_text,
                'expected': expected_text
            })
        
        return test_cases
    
    def apply_random_ocr_errors(self, text, error_count=2):
        """Apply random OCR errors to the text to simulate OCR issues."""
        result = text
        
        for _ in range(error_count):
            # Select a random error pattern
            pattern, replacement = random.choice(self.ocr_errors)
            
            # Find applicable positions for this pattern
            positions = []
            pos = result.find(pattern)
            while pos >= 0:
                positions.append(pos)
                pos = result.find(pattern, pos + 1)
            
            # Apply the error at a random position if positions found
            if positions:
                pos = random.choice(positions)
                result = result[:pos] + replacement + result[pos + len(pattern):]
        
        return result
    
    def generate_test_file(self, output_path, case_count=5):
        """Generate a test file with various patterns for thorough testing."""
        
        # Generate various test cases
        merged_location_cases = self.generate_merged_location_cases(case_count)
        embedded_header_cases = self.generate_embedded_header_cases(case_count)
        date_format_cases = self.generate_date_format_cases(case_count)
        email_format_cases = self.generate_email_format_cases(case_count)
        broken_line_cases = self.generate_broken_line_cases(case_count)
        multiple_skills_cases = self.generate_multiple_skills_cases(case_count)
        combined_issues_cases = self.generate_combined_issues_cases(case_count)
        
        # Combine all test cases
        all_cases = (
            merged_location_cases + 
            embedded_header_cases + 
            date_format_cases + 
            email_format_cases + 
            broken_line_cases + 
            multiple_skills_cases +
            combined_issues_cases
        )
        
        # Add random OCR errors to some test cases
        for i in range(len(all_cases)):
            if random.random() < 0.3:  # 30% chance to add OCR errors
                all_cases[i]['text'] = self.apply_random_ocr_errors(all_cases[i]['text'])
        
        # Write the test cases to the file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# OCR TEXT EXTRACTION TEST CASES\n\n")
            
            for i, case in enumerate(all_cases):
                f.write(f"## Test Case {i+1}: {case['type']}\n\n")
                f.write("### Input Text:\n```\n")
                f.write(case['text'])
                f.write("\n```\n\n")
                f.write("### Expected Output:\n```\n")
                f.write(case['expected'])
                f.write("\n```\n\n")
                f.write("---\n\n")
        
        logger.info(f"Generated {len(all_cases)} test cases in {output_path}")
        return all_cases
    
    def run_test_cases(self, cases):
        """Run the generated test cases through the OCR text processor and evaluate results."""
        extractor = OCRTextExtractor()
        
        results = {
            'total': len(cases),
            'passed': 0,
            'failed': 0,
            'details': []
        }
        
        for i, case in enumerate(cases):
            # Process the text using the OCR extractor
            processed_text = extractor._process_page_text(case['text'])
            final_text = extractor._final_cleanup(processed_text)
            
            # For broken line cases, apply the specific function
            if case['type'].startswith('broken_line'):
                final_text = fix_broken_lines(final_text)
            
            # Compare with expected output
            # Use a fuzzy match because exact spacing might not matter
            expected_normalized = ' '.join(case['expected'].split())
            actual_normalized = ' '.join(final_text.split())
            
            passed = expected_normalized in actual_normalized
            
            results['details'].append({
                'case_num': i + 1,
                'type': case['type'],
                'passed': passed,
                'input': case['text'],
                'expected': case['expected'],
                'actual': final_text
            })
            
            if passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
        
        results['pass_rate'] = results['passed'] / results['total'] if results['total'] > 0 else 0
        
        return results
    
    def print_test_results(self, results):
        """Print the test results in a readable format."""
        logger.info(f"\n{'=' * 50}")
        logger.info(f"TEST RESULTS SUMMARY")
        logger.info(f"{'=' * 50}")
        logger.info(f"Total test cases:  {results['total']}")
        logger.info(f"Passed:            {results['passed']} ({results['pass_rate']*100:.1f}%)")
        logger.info(f"Failed:            {results['failed']}")
        
        # Print details of failed tests
        if results['failed'] > 0:
            logger.info(f"\n{'=' * 50}")
            logger.info(f"FAILED TEST DETAILS")
            logger.info(f"{'=' * 50}")
            
            for detail in results['details']:
                if not detail['passed']:
                    logger.info(f"\nTest Case {detail['case_num']}: {detail['type']}")
                    logger.info(f"Input:\n{detail['input']}")
                    logger.info(f"Expected:\n{detail['expected']}")
                    logger.info(f"Actual:\n{detail['actual']}")
                    logger.info(f"-" * 50)
        
        # Print summary by case type
        logger.info(f"\n{'=' * 50}")
        logger.info(f"RESULTS BY CASE TYPE")
        logger.info(f"{'=' * 50}")
        
        by_type = {}
        for detail in results['details']:
            case_type = detail['type']
            if case_type not in by_type:
                by_type[case_type] = {'total': 0, 'passed': 0}
            by_type[case_type]['total'] += 1
            if detail['passed']:
                by_type[case_type]['passed'] += 1
        
        for case_type, counts in by_type.items():
            pass_rate = counts['passed'] / counts['total'] if counts['total'] > 0 else 0
            logger.info(f"{case_type}: {counts['passed']}/{counts['total']} ({pass_rate*100:.1f}%)")
        
        # Final verdict
        if results['pass_rate'] >= 0.9:
            logger.info(f"\n✅ TEST SUITE PASSED ({results['pass_rate']*100:.1f}%)")
        elif results['pass_rate'] >= 0.7:
            logger.info(f"\n⚠️ TEST SUITE PARTIALLY PASSED ({results['pass_rate']*100:.1f}%)")
        else:
            logger.info(f"\n❌ TEST SUITE FAILED ({results['pass_rate']*100:.1f}%)")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate and run OCR text extraction test cases")
    parser.add_argument("--output", default="/Users/kj/ResumeRebuild/ocr_test_cases.md", 
                        help="Path to output the test cases file")
    parser.add_argument("--count", type=int, default=5,
                        help="Number of test cases to generate for each pattern type")
    parser.add_argument("--run", action="store_true",
                        help="Run the test cases through the OCR processor")
    args = parser.parse_args()
    
    # Create the generator
    generator = OCRTestCaseGenerator()
    
    # Generate test cases
    cases = generator.generate_test_file(args.output, args.count)
    
    # Run tests if requested
    if args.run:
        logger.info("\nRunning test cases through OCR processor...")
        results = generator.run_test_cases(cases)
        generator.print_test_results(results)

if __name__ == "__main__":
    main()
