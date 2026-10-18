# ⚔️ DailyForge

> **Production-Ready Personal Productivity Suite for Striver SDE 180 DSA Preparation**  
> Built for tracking consistency across a 100-day coding challenge with automated morning briefings, streak tracking, and GitHub Profile README sync.

---

## 🌐 Production URLs

| Component | Target Platform | Live URL |
| :--- | :--- | :--- |
| **Frontend** | GitHub Pages | [https://geeky-rish.github.io/DailyForge/](https://geeky-rish.github.io/DailyForge/) |
| **Backend API** | Render (Free Tier) | `https://dailyforge-backend.onrender.com` |
| **Health Check** | Render | `https://dailyforge-backend.onrender.com/health` |
| **Readiness Check** | Render | `https://dailyforge-backend.onrender.com/ready` |

---

## 🌟 Key Features

1. **Daily DSA Practice**: Delivers 2 curated questions every day from the Striver SDE 180 dataset in sheet order.
2. **Persistent Tracking**: Full history of attempted, solved, deferred, and revision-flagged questions.
   - Solved questions are never repeated as new assignments.
   - Solving extra questions does not reduce the next day's 2-question allocation.
3. **Streak & Consistency Engine**: Tracks study streaks, revisions, attempts, and solves with freeze/gap protection.
4. **Render Cold-Start Protection ("Activate Backend")**:
   - Modern dashboard detects sleeping Render free instances.
   - Live retry counter and auto-reconnect with health polling.
5. **Morning Briefing via Gmail SMTP**:
   - Automated delivery every morning at **07:00 AM Asia/Kolkata (01:30 AM UTC)** via GitHub Actions.
   - Uses `smtp.gmail.com:587` with STARTTLS encryption.
   - Idempotent delivery with bounded retry backoff.
6. **GitHub Profile README Sync**:
   - Records genuine study sessions and updates the designated section of `geeky-rish/geeky-rish` between `<!-- DAILYFORGE:START -->` and `<!-- DAILYFORGE:END -->`.
7. **Strict Server-Side Security**:
   - Server validates numeric GitHub ID for `geeky-rish`. Unauthorized accounts are rejected with 403.
   - Supports both HTTP-only cookies and Authorization Bearer headers for seamless cross-origin hosting.

---

## ⚙️ External Configuration Guide

### 1. GitHub OAuth App Setup
To enable one-click GitHub login for your account:
1. Go to **[GitHub Developer Settings -> OAuth Apps](https://github.com/settings/developers)**.
2. Click **New OAuth App**.
3. Fill in the details:
   - **Application name**: `DailyForge`
   - **Homepage URL**: `https://geeky-rish.github.io/DailyForge/`
   - **Authorization callback URL**: `https://dailyforge-backend.onrender.com/auth/github/callback`
4. Click **Register application**.
5. Copy the **Client ID** and generate a **Client Secret**.

### 2. Render Backend Deployment (`render.yaml`)
1. Create a free account at **[Render.com](https://render.com)**.
2. Click **New +** -> **Blueprint**.
3. Connect repository `geeky-rish/DailyForge`.
4. Render will detect `render.yaml` and provision:
   - Web Service: `dailyforge-backend`
   - PostgreSQL Database: `dailyforge-db`
5. Fill in the required environment secrets when prompted:
   - `GITHUB_CLIENT_ID`: (from step 1)
   - `GITHUB_CLIENT_SECRET`: (from step 1)
   - `GITHUB_WRITE_TOKEN`: A Personal Access Token (classic or fine-grained) with `repo:contents:write` on `geeky-rish/geeky-rish`.
   - `SMTP_EMAIL`: `learn.rishipk@gmail.com`
   - `SMTP_APP_PASSWORD`: (16-character Google App Password)
   - `RECIPIENT_EMAIL`: `hello.rishikulkarni@gmail.com`

### 3. GitHub Profile README Setup
In your profile repository `geeky-rish/geeky-rish`, add the following markers anywhere in your `README.md`:

```markdown
<!-- DAILYFORGE:START -->
<!-- DAILYFORGE:END -->
```
DailyForge will automatically manage only the content between these markers.

---

## 📧 Email Integration & Automation

### Secrets Configured in GitHub Repository
- `SMTP_EMAIL`: `learn.rishipk@gmail.com`
- `SMTP_APP_PASSWORD`: `**** **** **** ****`
- `RECIPIENT_EMAIL`: `hello.rishikulkarni@gmail.com`

### Workflows in `.github/workflows/`
1. **`test-email.yml`**: Manual test workflow to verify Gmail SMTP delivery anytime.
2. **`daily-briefing.yml`**: Automated morning briefing scheduled for 07:00 IST (01:30 UTC), with manual `workflow_dispatch` trigger.
3. **`deploy-pages.yml`**: Automated build and deployment of the frontend to GitHub Pages on every push to `main`.

---

## 🧪 Local Testing & Development

### Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate      # Windows
# source venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
cp .env.example .env

# Run full backend test suite (67 tests)
python -m pytest -v

# Run local development server
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install

# Run frontend unit tests
npm test

# Build production bundle
npm run build

# Start local dev server
npm run dev
```

---

## 📜 License
MIT License. Crafted by [@geeky-rish](https://github.com/geeky-rish).
