# 📋 Resume Test System - Complete Implementation

## Overview

The Resume Test System allows users to exit a test midway and return later to continue exactly where they left off. All progress is automatically saved, including the current question index and all selected answers.

---

## 🎯 Features Implemented

### ✅ Backend Features

1. **Database Schema Enhancement**
   - Added `current_question_index` column to `User_Quiz_Take` table
   - Tracks the user's position in the test (0-based index)
   - Automatically saved on every navigation/answer change

2. **Progress Tracking Model Methods**
   - `update_current_question_index()` - Updates the current question position
   - `save_test_progress()` - Saves complete progress (index + all answers)
   - `get_test_progress()` - Retrieves saved progress for resumption

3. **New API Endpoints**
   - `POST /test/save-progress` - Auto-save progress (called frequently by frontend)
   - `GET /test/progress/{uqt_id}` - Get saved progress for resume
   - `POST /test/restart/{uqt_id}` - Clear progress and restart test

### ✅ Frontend Features

1. **Auto-Save Progress**
   - Automatically saves after every answer change (1-second debounce)
   - Saves current question index + all selected answers
   - Works silently in the background without user interaction

2. **Resume/Restart Dialog**
   - Beautiful modal showing saved progress
   - Shows current question position (e.g., "Question 3 of 10")
   - Three options:
     - **Resume Test** - Continue from saved position
     - **Start Over** - Clear progress and restart from question 1
     - **Cancel** - Go back to dashboard

3. **Seamless Resume Experience**
   - When user returns to test, automatically detects saved progress
   - Shows resume modal if progress exists
   - Loads all previously selected answers
   - Jumps to the last attempted question

---

## 🗂️ File Changes

### Database

- **`database/migration_add_resume_test.sql`** (NEW)
  - Migration script to add `current_question_index` column
  - Adds performance index for resume queries

- **`backend/run_migration_resume_test.py`** (NEW)
  - Python script to run the migration safely

### Backend

- **`backend/app/models/test.py`** (MODIFIED)
  - Added `update_current_question_index()`
  - Added `save_test_progress()`
  - Added `get_test_progress()`

- **`backend/app/schemas/test.py`** (MODIFIED)
  - Added `SaveProgressRequest` schema
  - Added `ProgressResponse` schema
  - Added `ResumeTestResponse` schema

- **`backend/app/routers/test.py`** (MODIFIED)
  - Added `POST /test/save-progress` endpoint
  - Added `GET /test/progress/{uqt_id}` endpoint
  - Added `POST /test/restart/{uqt_id}` endpoint

### Frontend

- **`frontend/src/services/api.js`** (MODIFIED)
  - Added `saveTestProgress()` function
  - Added `getTestProgress()` function
  - Added `restartTest()` function

- **`frontend/src/components/ui/ResumeTestModal.jsx`** (NEW)
  - Beautiful reusable modal component
  - Shows question progress
  - Three action buttons (Resume/Restart/Cancel)

- **`frontend/src/pages/TakeTest.js`** (MODIFIED)
  - Enhanced auto-save to save complete progress
  - Added resume modal state management
  - Added resume/restart handlers
  - Integrated resume modal into UI

---

## 🔄 How It Works

### Starting a Test

1. User clicks "Start Test" or "Take Test"
2. Frontend calls `startTest()` API
3. Backend checks for existing "in_progress" attempt
   - If exists: Returns existing `uqt_id` (resume capability)
   - If not exists: Creates new attempt
4. Frontend fetches quiz questions
5. Frontend calls `getTestProgress(uqt_id)` to check for saved progress
6. If progress exists:
   - Show Resume/Restart modal
   - Wait for user choice
7. If no progress:
   - Start fresh from question 1

### During Test (Auto-Save)

1. User selects an answer
2. Frontend updates local state
3. After 1-second debounce:
   - Frontend calls `saveTestProgress(uqt_id, currentQuestionIndex, answers)`
   - Backend saves:
     - Current question index
     - All selected answers
4. Process repeats for every:
   - Answer change
   - Question navigation (next/previous)

### Exiting Test

1. User navigates away or closes browser
2. All progress is already saved (auto-save)
3. Test remains "in_progress" (not completed)

### Resuming Test

1. User returns and clicks test again
2. Frontend detects saved progress
3. Shows modal: "Resume from question X of Y?"
4. User chooses **Resume**:
   - Loads all saved answers
   - Jumps to saved question index
   - User continues seamlessly
5. User chooses **Start Over**:
   - Calls `restartTest(uqt_id)` API
   - Clears all saved progress
   - Starts from question 1 with empty answers

### Submitting Test

1. User clicks "Submit Test"
2. All progress is finalized
3. Test status changes from "in_progress" to "completed"
4. Progress can no longer be resumed (test is final)

---

## 📊 Database Schema

```sql
-- Added column
ALTER TABLE "User_Quiz_Take" 
ADD COLUMN current_question_index INTEGER DEFAULT 0;

-- Performance index
CREATE INDEX idx_user_quiz_take_resume 
ON "User_Quiz_Take"(user_id, quiz_id, completed_time) 
WHERE completed_time IS NULL;
```

---

## 🧪 API Endpoints

### Save Progress (Auto-Save)

**POST** `/test/save-progress`

**Request:**
```json
{
  "uqt_id": 123,
  "current_question_index": 4,
  "answers": {
    "45": [101, 102],
    "46": [105]
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Progress saved successfully",
  "current_question_index": 4,
  "answers": { ... }
}
```

### Get Progress

**GET** `/test/progress/{uqt_id}`

**Response:**
```json
{
  "success": true,
  "message": "Progress retrieved successfully",
  "current_question_index": 4,
  "answers": {
    "45": [101, 102],
    "46": [105]
  }
}
```

### Restart Test

**POST** `/test/restart/{uqt_id}`

**Response:**
```json
{
  "success": true,
  "message": "Test restarted successfully",
  "uqt_id": 123
}
```

---

## 🎨 UI Components

### ResumeTestModal

**Props:**
- `open` - Boolean to show/hide modal
- `onResume` - Callback when "Resume Test" clicked
- `onRestart` - Callback when "Start Over" clicked
- `onCancel` - Callback when "Cancel" clicked
- `questionIndex` - Current saved question index (0-based)
- `totalQuestions` - Total number of questions in quiz

**Example:**
```jsx
<ResumeTestModal
  open={showResumeModal}
  onResume={handleResumeTest}
  onRestart={handleRestartTest}
  onCancel={handleCancelResume}
  questionIndex={3}
  totalQuestions={10}
/>
```

---

## ⚡ Performance & Optimization

### Auto-Save Debouncing
- 1-second delay after last change
- Prevents excessive API calls
- Smooth user experience

### Conditional Saving
- Only saves when:
  - Test is in progress (not completed)
  - Answers have changed
  - Quiz is loaded
  - Not showing resume modal

### Fallback Mechanisms
- If `saveTestProgress()` fails, tries `saveAnswer()` for current question
- Silent failures don't block user interaction
- User can continue taking test even if save fails temporarily

---

## 🚫 Important Rules

### Only ONE Active Attempt Per User Per Quiz

- Backend enforces single "in_progress" attempt
- `startTest()` API checks for existing attempt first
- Prevents duplicate attempts

### Never Reset Progress Unless Explicitly Requested

- Progress is never cleared automatically
- Only cleared when:
  - User clicks "Start Over" (restart)
  - User submits test (completion)
  - User deletes pending test

### Must Auto-Save Continuously

- Don't wait for submit to save
- Save after every interaction
- Enables seamless resume

---

## 🧪 Testing the Feature

### Test Case 1: Basic Resume

1. Start a new test
2. Answer questions 1-3
3. Navigate to question 4
4. Close browser/navigate away
5. Return to test
6. **Expected:** Modal shows "Question 4 of X"
7. Click "Resume Test"
8. **Expected:** All answers 1-3 are selected, on question 4

### Test Case 2: Restart

1. Have progress saved (e.g., question 5)
2. Return to test
3. Modal appears
4. Click "Start Over"
5. **Expected:** All answers cleared, on question 1

### Test Case 3: Auto-Save

1. Start test
2. Select answer for question 1
3. Wait 2 seconds
4. Check network tab
5. **Expected:** POST to `/test/save-progress` was called

### Test Case 4: Multiple Sessions

1. User A starts test, answers 3 questions
2. User B starts same test, answers 2 questions
3. User A returns
4. **Expected:** User A's progress (3 questions) is loaded, not User B's

### Test Case 5: Completed Test

1. Complete and submit a test
2. Try to access test again
3. **Expected:** Cannot resume (test is completed)

---

## 🔒 Security & Data Integrity

### User Isolation

- Progress is tied to `uqt_id` (unique attempt ID)
- Each user has their own attempt
- No cross-user contamination

### Completed Test Protection

- Cannot save progress on completed tests
- Cannot restart completed tests
- API checks `completed_time IS NULL` before allowing updates

### Consistent State

- Question index and answers always saved together
- Atomic updates prevent partial saves
- Database transactions ensure consistency

---

## 📚 Developer Notes

### Adding Resume to New Pages

To add resume functionality to other quiz/test pages:

1. Import API functions:
   ```javascript
   import { saveTestProgress, getTestProgress, restartTest } from '../services/api';
   import ResumeTestModal from '../components/ui/ResumeTestModal';
   ```

2. Add state:
   ```javascript
   const [showResumeModal, setShowResumeModal] = useState(false);
   const [savedProgress, setSavedProgress] = useState(null);
   ```

3. Check for progress on load:
   ```javascript
   const progressData = await getTestProgress(uqt_id);
   if (progressData.current_question_index > 0 || hasAnswers) {
     setSavedProgress(progressData);
     setShowResumeModal(true);
   }
   ```

4. Add auto-save:
   ```javascript
   useEffect(() => {
     const timer = setTimeout(() => {
       saveTestProgress(uqtId, currentIndex, answers);
     }, 1000);
     return () => clearTimeout(timer);
   }, [answers, currentIndex]);
   ```

### Extending the Feature

Possible enhancements:

- **Progress Bar:** Show % completion in resume modal
- **Time Tracking:** Show elapsed time since last save
- **Multiple Saves:** Allow users to save multiple "checkpoints"
- **Cloud Sync:** Sync progress across devices
- **Offline Support:** Save progress locally when offline

---

## ✅ Feature Status

**Status:** ✅ **COMPLETE**

All requirements from the original specification have been implemented:

- ✅ Database model for test attempts (using existing `User_Quiz_Take`)
- ✅ Tracks current question index
- ✅ Stores answers persistently
- ✅ Status management (in_progress, completed)
- ✅ Auto-save on every interaction
- ✅ Resume existing attempt on return
- ✅ Optional restart functionality
- ✅ Resume/Restart dialog popup
- ✅ Only ONE active attempt per user per quiz
- ✅ Never reset progress automatically
- ✅ Prevents duplicate attempts

---

## 🎉 Summary

The Resume Test System is now fully operational! Users can:

- Start a test and leave anytime
- Return later and pick up exactly where they left off
- Choose to restart if they want a fresh attempt
- All progress is automatically saved without any manual action

The system is robust, secure, and provides a seamless experience for students taking quizzes on your platform.

---

## 📞 Support

If you encounter any issues or need modifications:

1. Check the browser console for `[RESUME]` and `[AUTO-SAVE]` logs
2. Verify the migration ran successfully
3. Ensure backend is returning progress data correctly
4. Test the resume modal appears with valid data

Happy testing! 🚀
