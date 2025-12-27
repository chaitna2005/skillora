# Quick Setup Instructions

## 🚀 Quick Start (5 minutes)

### Step 1: Database Setup
```bash
# Create database
psql -U postgres
CREATE DATABASE testmyknowledge;
\q

# Load schema
psql -U postgres -d testmyknowledge -f database/schema.sql
```

### Step 2: Backend Setup
```bash
cd backend

# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux

# Edit .env and add:
# - DATABASE_PASSWORD (your postgres password)
# - OPENAI_API_KEY (your OpenAI API key)
```

### Step 3: Frontend Setup
```bash
cd frontend
npm install
```

### Step 4: Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
# Activate venv first
python run.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### Step 5: Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## ✅ Verify Installation

1. Visit http://localhost:8000/health
   - Should return: `{"status": "healthy"}`

2. Visit http://localhost:3000
   - Should show login page

---

## 🔑 Get OpenAI API Key

1. Go to https://platform.openai.com/
2. Sign up / Login
3. Go to API Keys section
4. Create new secret key
5. Copy and paste into `.env` file

---

## 📝 Test Sample Login

After database setup, you can use:
- **Username:** `johnteacher` or `janestudent`
- **Password:** `password`

Or register a new account.

---

## 🐛 Quick Troubleshooting

**Backend won't start:**
- Check if PostgreSQL is running
- Verify `.env` file has correct credentials
- Ensure virtual environment is activated

**Frontend won't start:**
- Run `npm install` again
- Check if port 3000 is available
- Clear npm cache: `npm cache clean --force`

**Can't create quiz:**
- Verify OpenAI API key is valid
- Check API key has credits
- Look at backend logs for errors

---

See `README.md` for detailed documentation.

