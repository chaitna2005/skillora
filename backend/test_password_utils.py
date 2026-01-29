"""
Test Password Utilities
Verify that hash_password() and verify_password() are working correctly
"""
from app.utils.auth import hash_password, verify_password


def test_password_hashing():
    """Test password hashing and verification"""
    print("=" * 60)
    print("PASSWORD UTILITIES TEST")
    print("=" * 60)
    
    # Test password
    test_password = "MySecurePassword123!"
    print(f"\n1️⃣  Test Password: {test_password}")
    
    # Hash the password
    print("\n2️⃣  Hashing password...")
    hashed = hash_password(test_password)
    print(f"   ✓ Hash generated: {hashed[:50]}...")
    print(f"   ✓ Hash length: {len(hashed)}")
    print(f"   ✓ Hash starts with 'pbkdf2:sha256': {hashed.startswith('pbkdf2:sha256')}")
    
    # Verify correct password
    print("\n3️⃣  Verifying CORRECT password...")
    is_valid = verify_password(hashed, test_password)
    print(f"   {'✅ PASS' if is_valid else '❌ FAIL'}: verify_password(hash, correct_password) = {is_valid}")
    
    # Verify incorrect password
    print("\n4️⃣  Verifying INCORRECT password...")
    wrong_password = "WrongPassword456!"
    is_invalid = verify_password(hashed, wrong_password)
    print(f"   {'✅ PASS' if not is_invalid else '❌ FAIL'}: verify_password(hash, wrong_password) = {is_invalid}")
    
    # Test multiple hashes are different (salting)
    print("\n5️⃣  Testing salt uniqueness...")
    hash1 = hash_password(test_password)
    hash2 = hash_password(test_password)
    are_different = hash1 != hash2
    print(f"   {'✅ PASS' if are_different else '❌ FAIL'}: Same password produces different hashes (salt working)")
    print(f"   Hash 1: {hash1[:50]}...")
    print(f"   Hash 2: {hash2[:50]}...")
    
    # Both should still verify correctly
    print("\n6️⃣  Verifying both hashes with original password...")
    verify1 = verify_password(hash1, test_password)
    verify2 = verify_password(hash2, test_password)
    print(f"   {'✅ PASS' if verify1 else '❌ FAIL'}: First hash verifies")
    print(f"   {'✅ PASS' if verify2 else '❌ FAIL'}: Second hash verifies")
    
    # Summary
    print("\n" + "=" * 60)
    all_tests_passed = is_valid and not is_invalid and are_different and verify1 and verify2
    if all_tests_passed:
        print("✅ ALL TESTS PASSED - Password utilities working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Check implementation!")
    print("=" * 60)
    
    return all_tests_passed


if __name__ == "__main__":
    try:
        success = test_password_hashing()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
