#!/usr/bin/env python3
"""
Unit tests for the Chat Workspace functionality (no GUI display needed)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_mock_classes():
    """Test that mock classes work correctly."""
    print("Testing mock classes...")
    
    try:
        from src.utils.mock_classes import (
            MockResumeAPIIntegration,
            MockPDFContentReplacer,
            MockConnectionType
        )
        
        # Test API integration
        api = MockResumeAPIIntegration()
        response = api.improve_resume("test content", feedback="make it better")
        assert "Mock improved content" in response["improved_resume"]
        print("✓ Mock API integration works")
        
        # Test PDF replacer
        pdf_replacer = MockPDFContentReplacer()
        analysis = pdf_replacer.analyze_resume("test.pdf")
        assert "Mock resume content" in analysis["basic_resume"]
        print("✓ Mock PDF replacer works")
        
        # Test connection types
        assert hasattr(MockConnectionType, 'LOCAL_SERVER')
        assert hasattr(MockConnectionType, 'MANAGE_AI')
        print("✓ Mock connection types work")
        
        return True
    except Exception as e:
        print(f"✗ Mock classes test failed: {e}")
        return False

def test_chat_message_processing():
    """Test chat message processing logic."""
    print("Testing chat message processing...")
    
    try:
        from src.utils.mock_classes import MockResumeAPIIntegration
        
        api = MockResumeAPIIntegration()
        
        # Test different types of messages
        test_cases = [
            "How can I improve my resume?",
            "Tailor this resume for a software engineer position",
            "What are the strongest parts of my resume?",
            "Help me fix formatting issues"
        ]
        
        for message in test_cases:
            response = api.improve_resume("sample resume content", feedback=message)
            assert response is not None
            assert "improved_resume" in response
            print(f"✓ Processed: '{message[:30]}...'")
        
        return True
    except Exception as e:
        print(f"✗ Chat message processing test failed: {e}")
        return False

def test_imports():
    """Test that imports work with fallback to mocks."""
    print("Testing import fallback mechanism...")
    
    try:
        # Test the import logic from gui.py
        try:
            from utils.pdf_extractor import PDFExtractor
            print("✓ Real PDFExtractor imported")
        except ImportError:
            from src.utils.mock_classes import MockPDFExtractor as PDFExtractor
            print("✓ Mock PDFExtractor imported as fallback")
        
        try:
            from utils.resume_api_integration import ResumeAPIIntegration
            print("✓ Real ResumeAPIIntegration imported")
        except ImportError:
            from src.utils.mock_classes import MockResumeAPIIntegration as ResumeAPIIntegration
            print("✓ Mock ResumeAPIIntegration imported as fallback")
        
        return True
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def run_all_tests():
    """Run all tests."""
    print("="*50)
    print("Running Chat Workspace Tests")
    print("="*50)
    
    tests = [
        test_imports,
        test_mock_classes,
        test_chat_message_processing
    ]
    
    passed = 0
    for test in tests:
        print(f"\n--- {test.__name__} ---")
        if test():
            passed += 1
            print("PASSED")
        else:
            print("FAILED")
    
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{len(tests)} tests passed")
    print("="*50)
    
    return passed == len(tests)

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)