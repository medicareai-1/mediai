# Local Development Setup

## 🔧 For Local Development

If you want to run the backend locally instead of using the production Render URL:

### Create `.env` file in `frontend/` folder:

```bash
VITE_API_URL=http://localhost:5000
```

This will override the production URL and use your local backend.

### Without `.env` file:
The frontend will automatically use the production backend:
`https://mediai-t6oo.onrender.com`

---

## 📝 Environment Variables

| Variable | Local Development | Production |
|----------|-------------------|------------|
| `VITE_API_URL` | `http://localhost:5000` | `https://mediai-t6oo.onrender.com` |

---

## 🚀 Run Locally

```bash
cd frontend
npm install
npm run dev
```

Then open: http://localhost:5173

---

## 🌐 Production URLs

- **Frontend (Vercel):** Will be assigned after deployment
- **Backend (Render):** https://mediai-t6oo.onrender.com
- **Database:** Firebase (already configured)

