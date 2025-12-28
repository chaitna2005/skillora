"""
Test OpenAI API Connection
Run this script to verify OpenAI API key and connection
"""
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')

print("=" * 60)
print("OpenAI Connection Test")
print("=" * 60)
print(f"\nAPI Key found: {api_key[:20]}..." if api_key else "No API key found!")
print(f"API Key length: {len(api_key) if api_key else 0}")

try:
    print("\nInitializing OpenAI client...")
    client = OpenAI(api_key=api_key)
    print("[OK] Client initialized successfully")
    
    print("\nTesting API connection with a simple request...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Say 'Hello, API is working!'"}
        ],
        max_tokens=20
    )
    
    print("[OK] API call successful!")
    print(f"\nResponse: {response.choices[0].message.content}")
    print("\n" + "=" * 60)
    print("SUCCESS: OpenAI API is working correctly!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[ERROR] Error occurred: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print("\n" + "=" * 60)
    print("FAILED: OpenAI API test failed")
    print("=" * 60)
    
    # Additional debugging info
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()

