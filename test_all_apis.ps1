# API Testing Script for TestMyKnowledge Backend
# Tests all endpoints and reports success/failure

$baseUrl = "http://localhost:8000"
$results = @()

# Helper function to test API endpoint
function Test-Endpoint {
    param(
        [string]$Method,
        [string]$Endpoint,
        [string]$Description,
        [object]$Body = $null,
        [hashtable]$Headers = @{"Content-Type" = "application/json"}
    )
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Testing: $Description" -ForegroundColor Yellow
    Write-Host "Method: $Method $Endpoint" -ForegroundColor Gray
    
    try {
        $url = "$baseUrl$Endpoint"
        
        if ($Body) {
            $jsonBody = $Body | ConvertTo-Json -Depth 10
            Write-Host "Request Body: $jsonBody" -ForegroundColor Gray
            
            $response = Invoke-RestMethod -Uri $url -Method $Method -Body $jsonBody -Headers $Headers -ErrorAction Stop
        } else {
            $response = Invoke-RestMethod -Uri $url -Method $Method -Headers $Headers -ErrorAction Stop
        }
        
        Write-Host "[SUCCESS]" -ForegroundColor Green
        Write-Host "Response:" -ForegroundColor Gray
        $response | ConvertTo-Json -Depth 10 | Write-Host -ForegroundColor White
        
        $script:results += [PSCustomObject]@{
            Endpoint = $Endpoint
            Method = $Method
            Description = $Description
            Status = "PASS"
            Error = ""
        }
        
        return $response
    }
    catch {
        Write-Host "[FAILED]" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        
        if ($_.ErrorDetails.Message) {
            Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
        }
        
        $script:results += [PSCustomObject]@{
            Endpoint = $Endpoint
            Method = $Method
            Description = $Description
            Status = "FAIL"
            Error = $_.Exception.Message
        }
        
        return $null
    }
}

Write-Host "=====================================" -ForegroundColor Magenta
Write-Host "API TESTING SUITE" -ForegroundColor Magenta
Write-Host "=====================================" -ForegroundColor Magenta

# ============================================
# 1. USER ENDPOINTS
# ============================================
Write-Host "`n`n=== USER ENDPOINTS ===" -ForegroundColor Magenta

# Test 1: Register new user (Student)
$registerStudent = Test-Endpoint -Method "POST" -Endpoint "/users/register" `
    -Description "Register Student User" `
    -Body @{
        first_name = "Test"
        last_name = "Student"
        username = "teststudent$(Get-Random -Maximum 9999)"
        password = "password123"
        email_id = "student$(Get-Random -Maximum 9999)@test.com"
        role = "STUDENT"
    }

# Test 2: Register new user (Teacher)
$registerTeacher = Test-Endpoint -Method "POST" -Endpoint "/users/register" `
    -Description "Register Teacher User" `
    -Body @{
        first_name = "Test"
        last_name = "Teacher"
        username = "testteacher$(Get-Random -Maximum 9999)"
        password = "password123"
        email_id = "teacher$(Get-Random -Maximum 9999)@test.com"
        role = "TEACHER"
    }

# Test 3: Login with existing user (use user from database)
$login = Test-Endpoint -Method "POST" -Endpoint "/users/login" `
    -Description "Login User" `
    -Body @{
        username = "admin"
        password = "admin123"
    }

$userId = if ($login) { $login.user.user_id } else { 1 }

# Test 4: Get user details
$user = Test-Endpoint -Method "GET" -Endpoint "/users/$userId" `
    -Description "Get User by ID"

# ============================================
# 2. QUIZ ENDPOINTS
# ============================================
Write-Host "`n`n=== QUIZ ENDPOINTS ===" -ForegroundColor Magenta

# Test 5: Create a quiz
$createQuiz = Test-Endpoint -Method "POST" -Endpoint "/quiz/create?user_id=$userId" `
    -Description "Create Quiz with AI Questions" `
    -Body @{
        prompt = "Python programming basics"
        difficulty_level = "EASY"
        total_no_questions = 3
    }

$quizId = if ($createQuiz) { $createQuiz.quiz_id } else { 1 }

# Test 6: Get quizzes by user
$userQuizzes = Test-Endpoint -Method "GET" -Endpoint "/quiz/user/$userId" `
    -Description "Get User's Quizzes"

# Test 7: Get quiz by ID (without answers)
$quiz = Test-Endpoint -Method "GET" -Endpoint "/quiz/$quizId" `
    -Description "Get Quiz by ID (No Answers)"

# Test 8: Get quiz with answers
$quizWithAnswers = Test-Endpoint -Method "GET" -Endpoint "/quiz/$quizId/with-answers" `
    -Description "Get Quiz with Answers"

# Test 9: Get assigned quizzes
$assignedQuizzes = Test-Endpoint -Method "GET" -Endpoint "/quiz/assigned/$userId" `
    -Description "Get Assigned Quizzes"

# Test 10: Assign quiz to student
if ($registerStudent) {
    $studentId = $registerStudent.user_id
    $assignment = Test-Endpoint -Method "POST" -Endpoint "/quiz/assign?assigned_by=$userId" `
        -Description "Assign Quiz to Student" `
        -Body @{
            quiz_id = $quizId
            user_id = $studentId
            due_date = "2025-12-31T23:59:59"
        }
    
    $assignmentId = if ($assignment) { $assignment.quiz_assignment_id } else { $null }
}

# ============================================
# 3. TEST ENDPOINTS
# ============================================
Write-Host "`n`n=== TEST ENDPOINTS ===" -ForegroundColor Magenta

# Test 11: Start a test (with assignment)
if ($assignmentId) {
    $startTest = Test-Endpoint -Method "POST" -Endpoint "/test/start?user_id=$studentId" `
        -Description "Start Test (With Assignment)" `
        -Body @{
            quiz_id = $quizId
            quiz_assignment_id = $assignmentId
        }
} else {
    # Try without assignment (should work if quiz_assignment_id is optional)
    $startTest = Test-Endpoint -Method "POST" -Endpoint "/test/start?user_id=$userId" `
        -Description "Start Test (Without Assignment)" `
        -Body @{
            quiz_id = $quizId
            quiz_assignment_id = 0
        }
}

$uqtId = if ($startTest) { $startTest.uqt_id } else { $null }

# Test 12: Get pending tests
$pendingTests = Test-Endpoint -Method "GET" -Endpoint "/test/user/$userId/pending" `
    -Description "Get Pending Tests"

# Test 13: Get completed tests
$completedTests = Test-Endpoint -Method "GET" -Endpoint "/test/user/$userId/completed" `
    -Description "Get Completed Tests"

# Test 14: Get all user tests
$allTests = Test-Endpoint -Method "GET" -Endpoint "/test/user/$userId" `
    -Description "Get All User Tests"

# Test 15: Submit test (if we have a valid test started)
if ($uqtId -and $quiz) {
    # Prepare answers - select first option for each question
    $answers = @()
    foreach ($question in $quiz.questions) {
        $answers += @{
            question_id = $question.question_id
            question_option_ids = @($question.options[0].option_id)
        }
    }
    
    $submitTest = Test-Endpoint -Method "POST" -Endpoint "/test/submit" `
        -Description "Submit Test Answers" `
        -Body @{
            uqt_id = $uqtId
            answers = $answers
        }
}

# Test 16: Get test result (if we have a completed test)
if ($completedTests -and $completedTests.Count -gt 0) {
    $completedUqtId = $completedTests[0].uqt_id
    $testResult = Test-Endpoint -Method "GET" -Endpoint "/test/result/$completedUqtId" `
        -Description "Get Test Result"
}

# Test 17: Get test summary
$testSummary = Test-Endpoint -Method "GET" -Endpoint "/test/summary/$userId" `
    -Description "Get Test Summary"

# ============================================
# SUMMARY REPORT
# ============================================
Write-Host "`n`n=====================================" -ForegroundColor Magenta
Write-Host "TEST SUMMARY REPORT" -ForegroundColor Magenta
Write-Host "=====================================" -ForegroundColor Magenta

$totalTests = $results.Count
$passedTests = ($results | Where-Object { $_.Status -eq "PASS" }).Count
$failedTests = ($results | Where-Object { $_.Status -eq "FAIL" }).Count

Write-Host "`nTotal Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $failedTests" -ForegroundColor Red
Write-Host "Success Rate: $([math]::Round(($passedTests / $totalTests) * 100, 2))%" -ForegroundColor Cyan

Write-Host "`n--- Detailed Results ---" -ForegroundColor Yellow
$results | Format-Table -AutoSize -Wrap

# Export detailed results to file
$results | Export-Csv -Path "api_test_results.csv" -NoTypeInformation
Write-Host "`nDetailed results exported to: api_test_results.csv" -ForegroundColor Green

# Show failed endpoints
$failedEndpoints = $results | Where-Object { $_.Status -eq "FAIL" }
if ($failedEndpoints.Count -gt 0) {
    Write-Host "`n--- FAILED ENDPOINTS ---" -ForegroundColor Red
    foreach ($failed in $failedEndpoints) {
        Write-Host "`n$($failed.Method) $($failed.Endpoint)" -ForegroundColor Red
        Write-Host "Description: $($failed.Description)" -ForegroundColor Yellow
        Write-Host "Error: $($failed.Error)" -ForegroundColor Red
    }
}

Write-Host "`n=====================================" -ForegroundColor Magenta
Write-Host "Testing Complete!" -ForegroundColor Magenta
Write-Host "=====================================" -ForegroundColor Magenta

