# 🚀 Deployment Guide: FraudShield Platform

This guide outlines how to deploy FraudShield for free online.

---

## 1. Deploy on Streamlit Community Cloud (Recommended - 100% Free)

Streamlit Community Cloud gives you a permanent public URL (e.g., `https://fraud-shield.streamlit.app`) connected directly to your GitHub repository.

### Step-by-Step Instructions:
1. Ensure your latest changes are pushed to GitHub:
   ```bash
   git push origin main
   ```
2. Navigate to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account (`muskan5572`).
3. Click **"New app"**.
4. In the setup window:
   - **Repository:** `muskan5572/fraud-detection-financial-transactions`
   - **Branch:** `main`
   - **Main file path:** `app/streamlit_app.py` (or `streamlit_app.py`)
5. Click **"Deploy!"**.
6. Streamlit Cloud installs `requirements.txt` and provisions the app in ~2 minutes.

---

## 2. Deploy on Render (Free Web Service / Docker)

Render supports both native Python web services and Docker containers.

### Deploying the REST API:
1. Go to [render.com](https://render.com/) and connect your GitHub repo.
2. Select **"New Web Service"**.
3. Choose Docker as the runtime (Render will automatically detect `Dockerfile`).
4. Set Start Command: `uvicorn api.server:app --host 0.0.0.0 --port 10000`
5. Select the **Free Tier** and deploy.

---

## 3. Local Docker Deployment

Run both the dashboard and API simultaneously on any machine with Docker installed:

```bash
# Build and run containers in background
docker compose up -d --build

# View container logs
docker compose logs -f

# Stop containers
docker compose down
```

- **Dashboard:** [http://localhost:8501](http://localhost:8501)
- **REST API:** [http://localhost:8000](http://localhost:8000)
