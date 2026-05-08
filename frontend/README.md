# Autonomous Academic Intelligence System (Frontend)

Production-grade Agentic AI Dashboard built with Next.js.

---

# Features

* Live AI agent execution
* Workflow visualization graph
* Student analytics dashboard
* Risk scoring charts
* Real-time WebSocket updates
* AI insights panel
* WhatsApp notification logs
* Framer Motion animations
* Responsive futuristic UI

---

# Tech Stack

* Next.js 15
* TypeScript
* TailwindCSS
* Shadcn UI
* Framer Motion
* Recharts
* React Flow
* Zustand
* Socket.io Client

---

# Folder Structure

```txt
frontend/
│
├── app/
├── components/
├── lib/
├── hooks/
├── store/
├── styles/
├── types/
├── public/
└── package.json
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/your-username/agentic-ai-platform.git
cd frontend
```

---

# Install Dependencies

```bash
npm install
```

---

# Environment Variables

Create:

```txt
.env.local
```

Add:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/workflows
```

---

# Run Development Server

```bash
npm run dev
```

Frontend runs at:

```txt
http://localhost:3000
```

---

# Production Build

```bash
npm run build
npm start
```

---

# Main Pages

## Dashboard

```txt
/dashboard
```

## Workflows

```txt
/workflows
```

## Students

```txt
/students
```

---

# WebSocket Integration

```ts
const socket = new WebSocket(
  process.env.NEXT_PUBLIC_WS_URL!
)

socket.onmessage = (event) => {
  const data = JSON.parse(event.data)
  console.log(data)
}
```

---

# Deployment

## Vercel Deployment

1. Push code to GitHub
2. Import project into Vercel
3. Add environment variables
4. Deploy

---

# Recommended Packages

```bash
npm install reactflow recharts framer-motion zustand socket.io-client lucide-react
```

---

# License

MIT License
