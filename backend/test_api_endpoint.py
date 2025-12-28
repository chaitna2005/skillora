"""
Test the actual API endpoint for quiz creation
"""
import httpx
import json

print("=" * 60)
print("Testing Quiz Creation API Endpoint")
print("=" * 60)

# First login to get a user_id
print("\n1. Logging in...")
with httpx.Client() as client:
    login_response = client.post(
        "http://localhost:8000/users/login",
        json={"username": "johnteacher", "password": "password"}
    )

    if login_response.status_code == 200:
        user_data = login_response.json()
        if user_data.get('success'):
            user_id = user_data['user']['user_id']
            print(f"[OK] Logged in as user {user_id}")
            
            # Now try to create a quiz
            print("\n2. Creating quiz...")
            quiz_data = {
                "quiz_name": "API Test Quiz",
                "prompt": "Test me on Python basics",
                "total_no_questions": 3,
                "difficulty_level": "EASY"
            }
            
            try:
                quiz_response = client.post(
                    f"http://localhost:8000/quiz/create?user_id={user_id}",
                    json=quiz_data,
                    timeout=60  # 60 second timeout
                )
                
                print(f"Status Code: {quiz_response.status_code}")
                print(f"Response: {json.dumps(quiz_response.json(), indent=2)}")
                
                if quiz_response.status_code == 201:
                    print("\n" + "=" * 60)
                    print("SUCCESS: Quiz created via API!")
                    print("=" * 60)
                else:
                    print("\n" + "=" * 60)
                    print("FAILED: API returned error")
                    print("=" * 60)
                    
            except Exception as e:
                print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[ERROR] Login failed: {user_data.get('message')}")
    else:
        print(f"[ERROR] Login request failed: {login_response.status_code}")
        print(login_response.text)

