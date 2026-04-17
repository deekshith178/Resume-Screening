import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))

from nlp.nlp_intake import NLPIntakePipeline

def test_name_extraction():
    pipeline = NLPIntakePipeline()
    
    print("Testing Name Extraction Logic...")
    
    cases = [
        # Case 1: Standard header
        (
            """
            John Doe
            Software Engineer
            123 Main St
            """, 
            "john@example.com", 
            "John Doe"
        ),
        # Case 2: Resume title first (Old logic would fail here possibly, or pick 'Resume')
        (
            """
            RESUME
            
            Jane Smith
            Data Scientist
            """, 
            "jane@example.com", 
            "Jane Smith"
        ),
        # Case 3: Explicit Name label
        (
            """
            Name: Alice Wonderland
            Email: alice@example.com
            """, 
            "alice@example.com", 
            "Alice Wonderland"
        ),
        # Case 4: Address first (should be skipped due to digits)
        (
            """
            1234 Road St, City, State
            01/01/2023
            
            Bob The Builder
            Constructor
            """, 
            "bob@example.com", 
            "Bob The Builder"
        ),
        # Case 5: Email on first line (should be skipped)
        (
            """
            charlie@example.com
            
            Charlie Brown
            Manager
            """, 
            "charlie@example.com", 
            "Charlie Brown"
        ),
         # Case 6: Title Case check (UPPERCASE name should pass)
        (
            """
            CURRICULUM VITAE
            
            DAVID BOWIE
            Musician
            """, 
            "david@example.com", 
            "DAVID BOWIE"
        )
    ]
    
    passed = 0
    for i, (text, email, expected) in enumerate(cases):
        result = pipeline.infer_name(text, email)
        status = "PASS" if result == expected else f"FAIL (Expected '{expected}', Got '{result}')"
        print(f"Case {i+1}: {status}")
        if result == expected:
            passed += 1
            
    print(f"\nPassed {passed}/{len(cases)} tests.")

if __name__ == "__main__":
    test_name_extraction()
