# PANTUN-AI Frontend

Frontend React + TypeScript + Tailwind + shadcn/ui untuk PANTUN-AI.

## Menjalankan

Jalankan backend Python dari root project:

```bash
uvicorn app.api:api --reload --port 8000
```

Lalu jalankan frontend:

```bash
pnpm install
pnpm run dev
```

Frontend memakai proxy Vite untuk meneruskan request `/api` ke backend Python di `http://127.0.0.1:8000`.
