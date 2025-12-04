# Honestly Frontend - AppWhistler UI

Modern React-based frontend for the AppWhistler Truth Engine, providing a sleek interface for app verification, trust scoring, and claim management.

## 🎨 Features

- **App Dashboard**: Search and browse verified applications
- **Trust Scores**: Visual grade badges (A-F) with detailed breakdowns
- **Claim Verification**: View claims, evidence, and verdicts
- **Real-time Updates**: GraphQL subscriptions for live data
- **Zero-Knowledge Status**: Display ZK-proof verification status
- **Responsive Design**: Mobile-first, works on all devices

## 🛠️ Tech Stack

- **React 18**: Modern React with hooks
- **Vite**: Lightning-fast build tool
- **TailwindCSS**: Utility-first styling
- **Apollo Client**: GraphQL data management
- **React Router**: Client-side routing
- **Lucide React**: Beautiful icon set

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
frontend-app/
├── src/
│   ├── App.jsx           # Main application component
│   ├── main.jsx          # Application entry point
│   ├── index.css         # Global styles
│   ├── components/       # Reusable components (future)
│   ├── pages/            # Page components (future)
│   ├── lib/              # Utilities and helpers (future)
│   └── styles/           # Additional styles (future)
├── public/               # Static assets
├── index.html            # HTML template
├── vite.config.js        # Vite configuration
├── tailwind.config.js    # TailwindCSS configuration
└── package.json          # Dependencies and scripts
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
REACT_APP_GRAPHQL_URI=http://localhost:4000/graphql
```

### Vite Configuration

The `vite.config.js` includes:
- React plugin for Fast Refresh
- GraphQL proxy to backend
- Build optimizations

### TailwindCSS

Custom configuration extends the default theme:
- Custom color: `slate-950` for dark backgrounds
- PurgeCSS for optimal bundle size

## 📝 Available Scripts

```bash
# Development
npm run dev              # Start dev server on port 3000
npm run dev -- --port 3001  # Start on different port

# Production
npm run build            # Build for production
npm run preview          # Preview production build

# Code Quality
npm run lint             # Run ESLint
npm run lint:fix         # Auto-fix linting issues
```

## 🎯 Key Components

### App.jsx

Main application component containing:
- Apollo Client setup
- React Router configuration
- Dashboard and detail pages
- Navigation and layout

### Dashboard

Features:
- App search and filtering
- Grid layout for app cards
- Grade badges
- Trust score display

### AppTruthTerminal

Detailed view showing:
- App header with grade
- Signal analysis breakdown
- Shadow Oracle verification
- Claim verification ledger
- Export functionality for AI agents

## 🔌 GraphQL Integration

The app connects to the GraphQL backend using Apollo Client:

```javascript
const client = new ApolloClient({
  uri: process.env.REACT_APP_GRAPHQL_URI,
  cache: new InMemoryCache(),
});
```

### Main Queries

1. **GET_APPS**: Fetch list of apps
2. **GET_APP_DETAILS**: Fetch detailed app information with claims and score

## 🎨 Styling

### TailwindCSS Utilities

The app uses Tailwind's utility classes for:
- Layout (flexbox, grid)
- Spacing (padding, margins)
- Colors (custom slate theme)
- Animations (fade-in, pulse)
- Responsive design (md:, lg: breakpoints)

### Custom Animations

```css
.animate-fade-in {
  animation: fadeIn 0.5s ease-in;
}
```

## 🌐 Deployment

### Build for Production

```bash
npm run build
```

This creates optimized files in `dist/`:
- Minified JavaScript
- Optimized CSS
- Compressed assets
- Source maps

### Deployment Options

**Static Hosting** (Vercel, Netlify, etc.):
```bash
npm run build
# Deploy the dist/ directory
```

**Docker**:
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

**Nginx**:
```nginx
server {
    listen 80;
    root /var/www/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## 🧪 Testing

```bash
# Run tests (when implemented)
npm test

# Run tests in watch mode
npm test -- --watch

# Coverage report
npm test -- --coverage
```

## 📱 Progressive Web App (PWA)

Future enhancement: Add PWA support for:
- Offline functionality
- Install on home screen
- Background sync
- Push notifications

## 🔒 Security

- CSP headers via Vite
- XSS protection through React
- CORS configuration
- Environment variable protection

## 🐛 Troubleshooting

### Build Errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### GraphQL Connection Issues

Check that:
1. Backend is running on correct port
2. CORS is configured correctly
3. Environment variables are set

### Style Not Loading

```bash
# Rebuild Tailwind
npm run build
```

## 📚 Resources

- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)
- [TailwindCSS Documentation](https://tailwindcss.com)
- [Apollo Client Documentation](https://apollographql.com/docs/react)

## 🤝 Contributing

1. Follow React best practices
2. Use functional components and hooks
3. Keep components small and focused
4. Write meaningful prop types
5. Add comments for complex logic

## 📄 License

See [LICENSE](../LICENSE) in the repository root.
