# ⚔️ DailyForge

> **Production-Ready Personal Productivity Suite for Striver SDE 180 DSA Preparation**  
> Built for tracking consistency across a 100-day coding challenge with automated morning briefings, streak tracking, and GitHub Profile README sync.

---

## 🌟 Key Features

1. **Daily DSA Practice**: Delivers 2 curated questions every day from the Striver SDE 180 dataset.
2. **Streak & Consistency Engine**: Tracks study streaks, revisions, attempts, and solves with freeze/gap protection.
3. **Morning Briefing via Gmail SMTP**:
   - Sends automated briefings with today's questions, streak statistics, and motivational quotes.
   - Built with secure Gmail SMTP (`smtp.gmail.com:587`, STARTTLS).
   - Reusable standalone sender without database dependencies.
4. **GitHub Profile Integration**: Automatically updates a dedicated section on `geeky-rish/geeky-rish` with live challenge statistics.
5. **Interactive Dashboard**: Modern dark-mode interface for managing questions, reviewing notes, and tracking progress.

---

## 📧 Email Integration & Testing

DailyForge uses Gmail SMTP over port 587 with STARTTLS.

### Environment Variables & GitHub Secrets

| Secret / Env Var | Description | Example |
| :--- | :--- | :--- |
| `SMTP_EMAIL` | Sender Gmail address | `learn.rishipk@gmail.com` |
| `SMTP_APP_PASSWORD` | 16-character Google App Password | `xxxx xxxx xxxx xxxx` |
| `RECIPIENT_EMAIL` | Recipient email address | `hello.rishikulkarni@gmail.com` |

> 🔒 **Security Notice**: Credentials are never hardcoded or printed in logs. Always configure them as GitHub Actions Secrets or local `.env` variables.

### Testing via GitHub Actions

You can trigger a test email on-demand directly from GitHub:
1. Navigate to **Actions** in your GitHub repository.
2. Select the **Test DailyForge Email** workflow.
3. Click **Run workflow** (optionally provide custom subject and body).
4. Inspect the workflow run logs for confirmation.

### Running Test Email Locally

```bash
# Set your environment variables
export SMTP_EMAIL="learn.rishipk@gmail.com"
export SMTP_APP_PASSWORD="your-google-app-password"
export RECIPIENT_EMAIL="hello.rishikulkarni@gmail.com"

# Send test email
python backend/scripts/send_email.py \
  --subject "DailyForge SMTP Test" \
  --body "Your DailyForge email delivery is working."
```

Or run in dry-run mode (validates configuration without sending):
```bash
python backend/scripts/send_email.py --dry-run
```

---

## 🚀 Quickstart

### Backend Setup

```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# Run database migrations
alembic upgrade head

# Run tests
pytest -v

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing

```bash
# Run backend test suite
cd backend
python -m pytest -v
```

---

## 📜 License

MIT License. Designed and maintained by [@geeky-rish](https://github.com/geeky-rish).
