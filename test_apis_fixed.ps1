# API Testing Script for TestMyKnowledge Backend - Fixed Version
$ErrorActionPreference = "Continue"
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
    Write-Host "$Method $Endpoint" -ForegroundColor Gray
    
    try {
        $url = "$baseUrl$Endpoint"
        
        if ($Body) {
            $jsonBody = $Body | ConvertTo-Json -Depth 10
            Write-Host "Body: $jsonBody" -ForegroundColor DarkGray
            
            $response = Invoke-RestMethod -Uri $url -Method $Method -Body $jsonBody -Headers $Headers -ErrorAction Stop
        } else {
            $response = Invoke-RestMethod -Uri $url -Method $Method -Headers $Headers -ErrorAction Stop
        }
        
        Write-Host "[PASS]" -ForegroundColor Green
        $responseJson = $response | ConvertTo-Json -Depth 10
        if ($responseJson.Length -lt 500) {
            Write-Host "Response: $responseJson" -ForegroundColor White
        } else {
            Write-Host "Response: [Large response truncated]" -ForegroundColor White
        }
        
        $script:results += [PSCustomObject]@{
            Endpoint = $Endpoint
            Status = "PASS"
            Error = ""
        }
        
        return $response
    }
    catch {
        Write-Host "[FAIL]" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        
        if ($_.ErrorDetails.Message) {
            $errorDetail = $_.ErrorDetails.Message
            if ($errorDetail.Length -lt 200) {
                Write-Host "Details: $errorDetail" -ForegroundColor DarkRed
            }
        }
        
        $script:results += [PSCustomObject]@{
            Endpoint = $Endpoint
            Status = "FAIL"
            Error = $_.Exception.Message
        }
        
        return $null
    }
}

Write-Host "=====================================" -ForegroundColor Magenta
Write-Host "BACKEND API TESTING SUITE" -ForegroundColor Magenta
Write-Host "=====================================" -ForegroundColor Magenta

# ============================================
# PHASE 1: USER REGISTRATION & LOGIN
# ============================================
Write-Host "`n`n[PHASE 1] USER ENDPOINTS" -ForegroundColor Magenta

$timestamp = Get-Date -Format "yyyyMMddHHmmss"

# Register a new teacher
Write-Host "`n--- Creating Teacher User ---" -ForegroundColor Cyan
$teacherData = @{
    first_name = "Teacher"
    last_name = "Test"
    username = "teacher_$timestamp"
    password = "Test@123"
    email_id = "teacher_$timestamp@test.com"
    role = "TEACHER"
}

$teacher = Test-Endpoint -Method "POST" -Endpoint "/users/register" `
    -Description "Register Teacher" -Body $teacherData

$teacherId = if ($teacher) { $teacher.user_id } else { $null }

# Register a new student
Write-Host "`n--- Creating Student User ---" -ForegroundColor Cyan
$studentData = @{
    first_name = "Student"
    last_name = "Test"
    username = "student_$timestamp"
    password = "Test@123"
    email_id = "student_$timestamp@test.com"
    role = "STUDENT"
}

$student = Test-Endpoint -Method "POST" -Endpoint "/users/register" `
    -Description "Register Student" -Body $studentData

$studentId = if ($student) { $student.user_id } else { $null }

# Try to login with teacher
if ($teacherId) {
    Write-Host "`n--- Testing Login ---" -ForegroundColor Cyan
    $loginData = @{
        username = $teacherData.username
        password = $teacherData.password
    }
    
    $login = Test-Endpoint -Method "POST" -Endpoint "/users/login" `
        -Description "Login as Teacher" -Body $loginData
    
    if ($login -and $login.success) {
        Write-Host "Login successful! User ID: $($login.user.user_id)" -ForegroundColor Green
        $teacherId = $login.user.user_id
    }
}

# Get user by ID
if ($teacherId) {
    $user = Test-Endpoint -Method "GET" -Endpoint "/users/$teacherId" `
        -Description "Get Teacher Profile"
}

if ($studentId) {
    $user = Test-Endpoint -Method "GET" -Endpoint "/users/$studentId" `
        -Description "Get Student Profile"
}

# ============================================
# PHASE 2: QUIZ CREATION & MANAGEMENT
# ============================================
Write-Host "`n`n[PHASE 2] QUIZ ENDPOINTS" -ForegroundColor Magenta

if ($teacherId) {
    Write-Host "`n--- Creating Quiz ---" -ForegroundColor Cyan
    $quizData = @{
        prompt = "Basic Python programming concepts including variables and data types"
        difficulty_level = "EASY"
        total_no_questions = 3
    }
    
    $quiz = Test-Endpoint -Method "POST" -Endpoint "/quiz/create?user_id=$teacherId" `
        -Description "Create Quiz" -Body $quizData
    
    $quizId = if ($quiz) { $quiz.quiz_id } else { $null }
    
    # Get user's quizzes
    $quizzes = Test-Endpoint -Method "GET" -Endpoint "/quiz/user/$teacherId" `
        -Description "Get Teacher's Quizzes"
    
    # If quiz creation failed but we have existing quizzes, use the first one
    if (-not $quizId -and $quizzes -and $quizzes.Count -gt 0) {
        $quizId = $quizzes[0].quiz_id
        Write-Host "Using existing quiz ID: $quizId" -ForegroundColor Yellow
    }
    
    if ($quizId) {
        # Get quiz details
        $quizDetails = Test-Endpoint -Method "GET" -Endpoint "/quiz/$quizId" `
            -Description "Get Quiz (No Answers)"
        
        # Get quiz with answers
        $quizWithAnswers = Test-Endpoint -Method "GET" -Endpoint "/quiz/$quizId/with-answers" `
            -Description "Get Quiz With Answers"
        
        # Assign quiz to student
        if ($studentId) {
            Write-Host "`n--- Assigning Quiz ---" -ForegroundColor Cyan
            $assignmentData = @{
                quiz_id = $quizId
                user_id = $studentId
                due_date = "2025-12-31T23:59:59"
            }
            
            $assignment = Test-Endpoint -Method "POST" -Endpoint "/quiz/assign?assigned_by=$teacherId" `
                -Description "Assign Quiz to Student" -Body $assignmentData
            
            $assignmentId = if ($assignment) { $assignment.quiz_assignment_id } else { $null }
        }
    }
}

# Get assigned quizzes for student
if ($studentId) {
    $assignedQuizzes = Test-Endpoint -Method "GET" -Endpoint "/quiz/assigned/$studentId" `
        -Description "Get Student's Assigned Quizzes"
    
    # If no assignment from above, try to get from list
    if (-not $assignmentId -and $assignedQuizzes -and $assignedQuizzes.Count -gt 0) {
        $assignmentId = $assignedQuizzes[0].quiz_assignment_id
        $quizId = $assignedQuizzes[0].quiz_id
        Write-Host "Using existing assignment ID: $assignmentId" -ForegroundColor Yellow
    }
}

# ============================================
# PHASE 3: TEST TAKING & SUBMISSION
# ============================================
Write-Host "`n`n[PHASE 3] TEST ENDPOINTS" -ForegroundColor Magenta

if ($studentId -and $quizId -and $assignmentId) {
    Write-Host "`n--- Starting Test ---" -ForegroundColor Cyan
    $testStartData = @{
        quiz_id = $quizId
        quiz_assignment_id = $assignmentId
    }
    
    $testStart = Test-Endpoint -Method "POST" -Endpoint "/test/start?user_id=$studentId" `
        -Description "Start Test" -Body $testStartData
    
    $uqtId = if ($testStart) { $testStart.uqt_id } else { $null }
}

# Get pending tests
if ($studentId) {
    $pendingTests = Test-Endpoint -Method "GET" -Endpoint "/test/user/$studentId/pending" `
        -Description "Get Pending Tests"
    
    # If we don't have a test started yet, use an existing one
    if (-not $uqtId -and $pendingTests -and $pendingTests.Count -gt 0) {
        $uqtId = $pendingTests[0].uqt_id
        $quizId = $pendingTests[0].quiz_id
        Write-Host "Using existing pending test ID: $uqtId" -ForegroundColor Yellow
    }
}

# Submit test
if ($uqtId -and $quizId) {
    Write-Host "`n--- Submitting Test ---" -ForegroundColor Cyan
    
    # Get quiz to get question IDs
    $quizForTest = Test-Endpoint -Method "GET" -Endpoint "/quiz/$quizId" `
        -Description "Get Quiz for Test Submission"
    
    if ($quizForTest -and $quizForTest.questions) {
        $answers = @()
        foreach ($question in $quizForTest.questions) {
            if ($question.options -and $question.options.Count -gt 0) {
                # Submit the first option for each question
                $answers += @{
                    question_id = $question.question_id
                    question_option_ids = @($question.options[0].option_id)
                }
            }
        }
        
        $submitData = @{
            uqt_id = $uqtId
            answers = $answers
        }
        
        $submission = Test-Endpoint -Method "POST" -Endpoint "/test/submit" `
            -Description "Submit Test Answers" -Body $submitData
    }
}

# Get completed tests
if ($studentId) {
    $completedTests = Test-Endpoint -Method "GET" -Endpoint "/test/user/$studentId/completed" `
        -Description "Get Completed Tests"
    
    # Get test result if we have a completed test
    if ($completedTests -and $completedTests.Count -gt 0) {
        $completedUqtId = $completedTests[0].uqt_id
        $testResult = Test-Endpoint -Method "GET" -Endpoint "/test/result/$completedUqtId" `
            -Description "Get Test Result Details"
    }
}

# Get all tests
if ($studentId) {
    $allTests = Test-Endpoint -Method "GET" -Endpoint "/test/user/$studentId" `
        -Description "Get All User Tests"
}

# Get test summary
if ($studentId) {
    $summary = Test-Endpoint -Method "GET" -Endpoint "/test/summary/$studentId" `
        -Description "Get Test Summary & Stats"
}

# ============================================
# FINAL SUMMARY
# ============================================
Write-Host "`n`n=====================================" -ForegroundColor Magenta
Write-Host "TEST RESULTS SUMMARY" -ForegroundColor Magenta
Write-Host "=====================================" -ForegroundColor Magenta

$total = $results.Count
$passed = ($results | Where-Object { $_.Status -eq "PASS" }).Count
$failed = ($results | Where-Object { $_.Status -eq "FAIL" }).Count

Write-Host "`nTotal: $total | Passed: $passed | Failed: $failed" -ForegroundColor White
Write-Host "Success Rate: $([math]::Round(($passed / $total) * 100, 2))%" -ForegroundColor Cyan

$failedList = $results | Where-Object { $_.Status -eq "FAIL" }
if ($failedList.Count -gt 0) {
    Write-Host "`n--- FAILED ENDPOINTS ($($failedList.Count)) ---" -ForegroundColor Red
    $failedList | ForEach-Object {
        Write-Host "  - $($_.Endpoint)" -ForegroundColor Red
    }
} else {
    Write-Host "`nALL TESTS PASSED!" -ForegroundColor Green
}

Write-Host "`nTest IDs for reference:" -ForegroundColor Yellow
if ($teacherId) { Write-Host "  Teacher ID: $teacherId" -ForegroundColor Gray }
if ($studentId) { Write-Host "  Student ID: $studentId" -ForegroundColor Gray }
if ($quizId) { Write-Host "  Quiz ID: $quizId" -ForegroundColor Gray }
if ($assignmentId) { Write-Host "  Assignment ID: $assignmentId" -ForegroundColor Gray }
if ($uqtId) { Write-Host "  Test ID (UQT): $uqtId" -ForegroundColor Gray }

Write-Host "`n=====================================" -ForegroundColor Magenta

