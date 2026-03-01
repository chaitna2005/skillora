# TestMyKnowledge

**AI-Powered Quiz & Knowledge Assessment Platform**

A web application that allows users to create AI-generated quizzes and test their knowledge on any subject using OpenAI's GPT models.

---

## 📋 Table of Contents

- [Features](#features)
- [Technologies](#technologies)
- [System Requirements](#system-requirements)
- [Installation Guide](#installation-guide)
  - [Windows Setup](#windows-setup)
  - [macOS Setup](#macos-setup)
  - [Linux Setup](#linux-setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Running with Docker (Local)](#running-with-docker-local)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

- **User Management**: Register as a teacher or student with role-based functionality
- **AI-Powered Quiz Generation**: Create quizzes from natural language prompts using OpenAI
- **Flexible Question Types**: Support for single-choice (RADIO) and multiple-choice (CHECKLIST) questions
- **Quiz Assignment**: Teachers can assign quizzes to students with due dates
- **Test Taking**: Interactive test-taking interface with progress tracking
- **Detailed Results**: Comprehensive feedback with correct/incorrect answers and performance metrics
- **Dashboard**: Overview of all quizzes, pending tests, and completed tests with statistics
- **Test History**: Track multiple attempts on the same quiz

---

## 🛠 Technologies

### Backend
- **Python 3.8+**
- **FastAPI** - Modern web framework for building APIs
- **PostgreSQL** - Relational database
- **psycopg2** - PostgreSQL adapter
- **OpenAI API** - AI-powered question generation

### Frontend
- **React 18** - UI library
- **React Router** - Client-side routing
- **Fetch API** - HTTP requests

---

## 💻 System Requirements

- **Python**: 3.8 or higher
- **Node.js**: 16.0 or higher
- **npm**: 8.0 or higher
- **PostgreSQL**: 12.0 or higher
- **OpenAI API Key**: Required for quiz generation

---

## 📦 Installation Guide

### Windows Setup

#### 1. Install Python

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer and **check "Add Python to PATH"**
3. Verify installation:
```powershell
python --version
pip --version
```

#### 2. Install Node.js

1. Download Node.js from [nodejs.org](https://nodejs.org/)
2. Run the installer
3. Verify installation:
```powershell
node --version
npm --version
```

#### 3. Install PostgreSQL

1. Download PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Run the installer (remember the password you set for `postgres` user)
3. Add PostgreSQL to PATH:
   - Search for "Environment Variables" in Windows
   - Edit PATH variable and add: `C:\Program Files\PostgreSQL\15\bin`
4. Verify installation:
```powershell
psql --version
```

#### 4. Setup Database

Open PowerShell as Administrator:
```powershell
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE testmyknowledge;

# Exit PostgreSQL
\q
```

#### 5. Clone and Setup Project

```powershell
# Navigate to project directory
cd C:\Users\Admin\OneDrive\Desktop\TestMyKnowledge

# Setup Backend
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure environment file
copy .env.example .env
# Edit .env file with your database credentials and OpenAI API key

# Setup Database Schema
psql -U postgres -d testmyknowledge -f ..\database\schema.sql

# Setup Frontend
cd ..\frontend
npm install
```

---

### macOS Setup

#### 1. Install Homebrew (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. Install Python

```bash
# Install Python
brew install python@3.11

# Verify installation
python3 --version
pip3 --version
```

#### 3. Install Node.js

```bash
# Install Node.js
brew install node

# Verify installation
node --version
npm --version
```

#### 4. Install PostgreSQL

```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Create database
createdb testmyknowledge
```

#### 5. Clone and Setup Project

```bash
# Navigate to project directory
cd ~/Desktop/TestMyKnowledge

# Setup Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy and configure environment file
cp .env.example .env
# Edit .env file with your credentials

# Setup Database Schema
psql -d testmyknowledge -f ../database/schema.sql

# Setup Frontend
cd ../frontend
npm install
```

---

### Linux Setup

#### 1. Install Python (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y

# Verify installation
python3 --version
pip3 --version
```

#### 2. Install Node.js

```bash
# Install Node.js via NodeSource
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Verify installation
node --version
npm --version
```

#### 3. Install PostgreSQL

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database
sudo -u postgres psql
CREATE DATABASE testmyknowledge;
CREATE USER testuser WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE testmyknowledge TO testuser;
\q
```

#### 4. Clone and Setup Project

```bash
# Navigate to project directory
cd ~/TestMyKnowledge

# Setup Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy and configure environment file
cp .env.example .env
# Edit .env file with your credentials

# Setup Database Schema
psql -U testuser -d testmyknowledge -f ../database/schema.sql

# Setup Frontend
cd ../frontend
npm install
```

---

## ⚙️ Configuration

### Backend Configuration (`backend/.env`)

Edit `backend/.env` file with your credentials:

```env
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=testmyknowledge
DATABASE_USER=postgres
DATABASE_PASSWORD=your_postgres_password

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=True
```

### Frontend Configuration (`frontend/.env`)

The frontend `.env` file should contain:

```env
REACT_APP_API_URL=http://localhost:8000
```

---

## 🚀 Running the Application

### Start Backend Server

**Windows:**
```powershell
cd backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**macOS/Linux:**
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### Start Frontend Server

**All Platforms:**
```bash
cd frontend
npm start
```

Frontend will open automatically at: `http://localhost:3000`

---

## 🐳 Running with Docker (Local)

Run the full app (PostgreSQL, backend, frontend) in Docker with no local Python/Node/Postgres install.

### Prerequisites

- **Docker** and **Docker Compose** installed ([docs](https://docs.docker.com/get-docker/))
- **OpenAI API key** for quiz generation

### Setup and run

1. **Create environment file** (from project root):
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set at least:
   - `OPENAI_API_KEY=sk-your-openai-api-key`
   - Optionally change `POSTGRES_PASSWORD` and `SECRET_KEY` for local use.

2. **Start all services**:
   ```bash
   docker compose up --build
   ```
   First run will build the backend and frontend images and create the Postgres database (schema runs automatically from `database/schema.sql`).

3. **Open the app**
   - **App:** [http://localhost:3000](http://localhost:3000)
   - **API:** [http://localhost:8000](http://localhost:8000)
   - **API docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

### Useful commands

- **Run in background:** `docker compose up -d --build`
- **View logs:** `docker compose logs -f`
- **Stop:** `docker compose down`
- **Reset database (delete data):** `docker compose down -v` then `docker compose up -d`

---

## 📚 API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

### Key Endpoints

#### User Management
- `POST /users/register` - Register new user
- `POST /users/login` - User login
- `GET /users/{user_id}` - Get user details

#### Quiz Management
- `POST /quiz/create?user_id={user_id}` - Create quiz with AI-generated questions
- `GET /quiz/user/{user_id}` - Get all quizzes created by user
- `GET /quiz/assigned/{user_id}` - Get quizzes assigned to user
- `GET /quiz/{quiz_id}` - Get quiz details
- `POST /quiz/assign?assigned_by={teacher_id}` - Assign quiz to student

#### Test Management
- `POST /test/start?user_id={user_id}` - Start a test
- `POST /test/submit` - Submit test answers
- `GET /test/result/{uqt_id}` - Get detailed test results
- `GET /test/user/{user_id}` - Get all tests for user
- `GET /test/user/{user_id}/pending` - Get pending tests
- `GET /test/user/{user_id}/completed` - Get completed tests
- `GET /test/summary/{user_id}` - Get test statistics

---

## 🗄 Database Schema

### Tables

**User**
- user_id (PK)
- first_name, last_name
- username (unique)
- password (hashed)
- email_id (unique)
- role (TEACHER/STUDENT)
- created_at

**Quiz**
- quiz_id (PK)
- user_id (FK)
- prompt
- total_no_questions
- difficulty_level (EASY/MEDIUM/HARD)
- quiz_name
- created_date

**Quiz_Assignment**
- quiz_assignment_id (PK)
- user_id (FK) - Student
- assigned_by (FK) - Teacher
- quiz_id (FK)
- assign_date
- due_date

**Question**
- question_id (PK)
- quiz_id (FK)
- question_text
- question_type (RADIO/CHECKLIST)

**QuestionOption**
- question_option_id (PK)
- question_id (FK)
- option_text
- is_correct

**User_Quiz_Take**
- uqt_id (PK)
- user_id (FK)
- quiz_id (FK)
- start_time
- completed_time
- total_correct
- result
- quiz_assignment_id (FK)

**Quiz_Take_Question_Answers**
- qtqa_id (PK)
- uqt_id (FK)
- question_id (FK)
- question_option_id (FK)
- is_correct

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Error:** `could not connect to server`

**Solution:**
- Check PostgreSQL is running:
  - Windows: Check Services
  - macOS: `brew services list`
  - Linux: `sudo systemctl status postgresql`
- Verify credentials in `.env` file
- Check if database exists: `psql -U postgres -l`

#### 2. OpenAI API Errors

**Error:** `Invalid API key` or `Rate limit exceeded`

**Solution:**
- Verify your OpenAI API key in `.env`
- Check API key at [platform.openai.com](https://platform.openai.com/api-keys)
- Ensure you have sufficient credits

#### 3. Port Already in Use

**Error:** `Address already in use`

**Solution:**
- Backend (port 8000):
  - Windows: `netstat -ano | findstr :8000`
  - macOS/Linux: `lsof -i :8000`
  - Kill process or use different port
- Frontend (port 3000): Similar process

#### 4. Module Not Found

**Error:** `ModuleNotFoundError` or `Cannot find module`

**Solution:**
- Backend: Ensure virtual environment is activated and run `pip install -r requirements.txt`
- Frontend: Run `npm install` in frontend directory

#### 5. CORS Errors

**Error:** `CORS policy: No 'Access-Control-Allow-Origin'`

**Solution:**
- Ensure backend is running
- Check `CORS_ORIGINS` in `backend/app/config.py`
- Verify frontend URL matches allowed origins

---

## 📝 Usage Guide

### Creating Your First Quiz

1. **Register** as a teacher or student
2. **Login** with your credentials
3. Navigate to **Create Quiz**
4. Enter a prompt like:
   - "Test me on World War II with 10 medium difficulty questions"
   - "Create easy questions about Indian rivers and states"
   - "Give me hard questions on LLM and AI concepts"
5. Select difficulty level and number of questions
6. Click **Create Quiz** (AI will generate questions)

### Taking a Test

1. Go to **Home** page
2. Find a quiz from **My Quizzes** or **Assigned Quizzes**
3. Click on the quiz card
4. Click **Take Test**
5. Answer questions (use radio buttons for single-answer, checkboxes for multiple)
6. Navigate between questions using Previous/Next or question indicators
7. Click **Submit Test** when done

### Viewing Results

1. After submitting, you'll see:
   - Overall score percentage
   - Number of correct/incorrect answers
   - Performance rating (Excellent/Good/Needs Improvement)
   - Detailed breakdown of each question
   - Your answers vs. correct answers

---

## 👥 User Roles

### Teacher
- Create quizzes
- Assign quizzes to students
- View all created quizzes
- Take self-assessments

### Student
- Take assigned quizzes
- Create personal quizzes
- View test history and scores
- Retake quizzes multiple times

---

## 🔐 Security Notes

- Passwords are hashed using SHA-256
- JWT tokens for authentication
- Change `SECRET_KEY` in production
- Never commit `.env` files to version control
- Use environment variables for sensitive data

---

## 🚀 Deployment (Google Cloud)

Deploy to project **skillora-App** using the Makefile. Full steps: **[DEPLOY.md](DEPLOY.md)**.

**Prerequisites:** [gcloud CLI](https://cloud.google.com/sdk/docs/install), Docker.

**Quick sequence:**
```bash
cp gcp.env.example gcp.env   # set DB_PASSWORD, OPENAI_API_KEY, SECRET_KEY
make gcp-auth && make gcp-apis && make gcp-repo
make gcp-db && make gcp-schema
make gcp-build && make gcp-deploy-backend
# Add BACKEND_URL to gcp.env, then:
make gcp-build-frontend && make gcp-deploy-frontend
make gcp-urls
```

---

## 📄 License

This project is for educational purposes.

---

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Check PostgreSQL logs
4. Review browser console for frontend errors

---

## 🎯 Future Enhancements

- [ ] Timer for tests
- [ ] Question difficulty adjustment
- [ ] Rich text editor for questions
- [ ] Image support in questions
- [ ] Leaderboards
- [ ] Email notifications
- [ ] Quiz categories and tags
- [ ] Export results to PDF
- [ ] Analytics dashboard
- [ ] Mobile app

---

**Happy Learning! 🎓**

