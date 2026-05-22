# JARVIS App

Modern React application built with Vite and TailwindCSS.

## Features

- React 18 with hooks
- Vite for fast development
- TailwindCSS for styling
- React Router for navigation
- Zustand for state management
- Axios for API calls
- ESLint + Prettier for code quality
- Vitest for testing

## Getting Started

### Prerequisites

- Node.js >= 18.0.0
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

### Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |
| `npm run format` | Format with Prettier |
| `npm test` | Run tests |

## Project Structure

```
build_real_0521_2143/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Page components
│   ├── hooks/          # Custom React hooks
│   ├── services/       # API services
│   ├── store/          # Zustand state management
│   ├── utils/          # Helper functions
│   ├── App.jsx         # Root component
│   └── main.jsx        # Entry point
├── public/             # Static assets
└── index.html          # HTML template
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=JARVIS App
```

## License

MIT License - 2026
