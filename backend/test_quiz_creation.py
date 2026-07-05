"""
Test Quiz Creation Flow
Tests the exact flow that happens when creating a quiz
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.services.openai_service import OpenAIService

print("=" * 60)
print("Testing Quiz Creation Flow")
print("=" * 60)

try:
    print("\n1. Initializing OpenAI Service...")
    openai_service = OpenAIService()
    print("[OK] OpenAI Service initialized")
    
    print("\n2. Testing quiz name generation...")
    quiz_name = openai_service.generate_quiz_name("Test me on Python basics")
    print(f"[OK] Quiz name generated: {quiz_name}")
    
    print("\n3. Testing question generation...")
    questions = openai_service.generate_quiz_questions(
        prompt="Test me on Python basics",
        difficulty_level="EASY",
        total_questions=2
    )
    print(f"[OK] Generated {len(questions)} questions")
    
    print("\n4. Sample question:")
    if questions:
        q = questions[0]
        print(f"   Text: {q['question_text']}")
        print(f"   Type: {q['question_type']}")
        print(f"   Options: {len(q['options'])}")
    
    print("\n" + "=" * 60)
    print("SUCCESS: Quiz creation flow works correctly!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
    print("\n" + "=" * 60)
    print("FAILED: Quiz creation test failed")
    print("=" * 60)
    
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()

