# Frontend Setup Guide

Complete instructions for running the Misinformation Detector frontend.

## 🚀 Quick Start (5 minutes)

### Option 1: Development Mode

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev

# 4. Open browser
# http://localhost:3000
```

### Option 2: Docker (Recommended)

```bash
# 1. Start entire stack (API + Frontend + Database)
docker compose -f docker-compose.full.yml up -d

# 2. Open browser
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

### Option 3: Build & Run Locally

```bash
# 1. Build frontend
cd frontend
npm run build

# 2. Serve built files
npx serve -s dist -l 3000

# 3. Open browser
# http://localhost:3000
```

---

## 📋 System Requirements

- **Node.js**: 18+ (for development)
- **npm**: 9+ (for development)
- **Docker**: 20+ (optional, for containerized setup)
- **API Server**: Running on `http://localhost:8000`

---

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── App.jsx                 # Main application component
│   ├── main.jsx                # React entry point
│   └── components/             # UI components (organized)
├── index.html                  # HTML template
├── vite.config.js              # Vite build configuration
├── nginx.conf                  # Nginx configuration
├── Dockerfile                  # Docker image definition
├── package.json                # Dependencies
├── package-lock.json           # Locked versions
└── README.md                   # Component documentation
```

---

## 🎨 Key Features

### 1. Upload & Analyze Tab

```
┌─────────────────────────────────────┐
│  Media Type Selector (Image/Video)  │
├─────────────────────────────────────┤
│  Claim Input Field (Optional)       │
├─────────────────────────────────────┤
│  File Upload Area (Drag & Drop)     │
├─────────────────────────────────────┤
│  Or URL Input                       │
├─────────────────────────────────────┤
│  [Analyze Media] Button             │
└─────────────────────────────────────┘
```

**Features:**
- Automatic media type detection
- Drag-and-drop file upload
- URL input alternative
- Real-time upload progress
- File size validation (500MB max)

### 2. Results Display

```
Classification:
  ├─ Media: LIKELY_MANIPULATED (color-coded badge)
  └─ Information: LIKELY_FALSE (color-coded badge)

Forensic Scores:
  ├─ Manipulation Probability: [████████  ] 85%
  ├─ Synthetic Media Probability: [██████    ] 65%
  ├─ Overall Confidence: [██████████] 92%
  └─ Evidence Quality: [███████   ] 75%

Additional Metrics:
  ├─ Audio Manipulation: 18%
  ├─ Lip-Sync Inconsistency: 82%
  └─ Processing Time: 2.45s

Evidence Table:
  ├─ Source 1: supports (85% reliability)
  ├─ Source 2: contradicts (92% reliability)
  └─ Source 3: uncertain (65% reliability)

Explanation:
  └─ Human-readable analysis summary
```

### 3. History Tab

```
┌────────────────────────────────────┐
│  Analysis History (12 items)       │
│  [Refresh Button]                  │
├────────────────────────────────────┤
│ Type  │ Claim │ Status │ Date │    │
├───────┼───────┼────────┼──────┼────┤
│ Image │ Claim │ Done   │ Today│View│
│ Video │ ...   │ Processing│...|View│
│ Audio │ ...   │ Failed │ ...  │View│
└────────────────────────────────────┘
```

**Features:**
- Real-time status updates
- Auto-refresh every 5 seconds
- Quick view for task details
- Delete completed tasks
- Filter by status (optional)

---

## 🔧 Configuration

### Environment Variables

Create `.env` file in `frontend/` directory:

```bash
# API Configuration
VITE_API_URL=http://localhost:8000/api/v1

# Optional: For production
VITE_API_URL=https://api.yourdomain.com/api/v1
```

### Development Server

Vite serves on port 3000 by default:

```bash
# Custom port
npm run dev -- --port 5000

# Expose to network
npm run dev -- --host
```

### Production Build

```bash
# Build optimized version
npm run build

# Output: frontend/dist/

# Preview build locally
npm run preview
```

---

## 🐳 Docker Deployment

### Build Docker Image

```bash
cd frontend
docker build -t misinformation-frontend:latest .
```

### Run Standalone Container

```bash
docker run -d \
  --name misinformation-frontend \
  -p 3000:80 \
  -e VITE_API_URL=http://localhost:8000/api/v1 \
  misinformation-frontend:latest
```

### Run Full Stack with Docker Compose

```bash
# From project root
docker compose -f docker-compose.full.yml up -d

# View logs
docker compose -f docker-compose.full.yml logs -f frontend

# Stop all services
docker compose -f docker-compose.full.yml down
```

---

## 📦 Dependencies

### Core UI Framework
- **React** 18.2.0 - UI library
- **Material-UI** 5.14.0 - Component library
- **Emotion** 11.11.0 - CSS-in-JS styling

### Data & Networking
- **Axios** 1.6.0 - HTTP client
- **Recharts** 2.10.0 - Charting library (future)

### Build Tools
- **Vite** 5.0.0 - Build tool & dev server
- **@vitejs/plugin-react** - React support

### Update Dependencies

```bash
# Check for updates
npm outdated

# Update all
npm update

# Update specific package
npm install package-name@latest
```

---

## 🧪 Testing & Development

### Development Workflow

```bash
# 1. Start API
docker compose up -d api redis postgres

# 2. Start frontend dev server
cd frontend && npm run dev

# 3. Open http://localhost:3000

# 4. Make changes - hot reload automatic

# 5. Test with API
# Submit form → check results
```

### Build & Test Locally

```bash
# Build production bundle
npm run build

# Test production build
npm run preview

# Open http://localhost:4173
```

### Browser DevTools

```javascript
// Check API communication in Console
// All requests to /api/ are logged

// Check Network tab for:
// POST /api/v1/analyze
// GET /api/v1/status/{task_id}
// GET /api/v1/results/{task_id}
```

---

## 🌐 API Integration Points

### Endpoint: POST /api/v1/analyze

**Request:**
```json
{
  "media_type": "image",
  "claim": "President announced a policy",
  "media_url": "https://example.com/image.jpg"
}
```

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

### Endpoint: GET /api/v1/status/{task_id}

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": { ... }
}
```

### Endpoint: GET /api/v1/results/{task_id}

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "media_assessment": { ... },
  "claim_assessment": { ... },
  "classification": "LIKELY_MANIPULATED",
  "overall_confidence": 0.89,
  ...
}
```

---

## 🚀 Deployment to Production

### Option 1: Vercel (Recommended for Frontend)

```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Deploy
cd frontend
vercel

# 3. Configure API URL
# Set environment variable in Vercel dashboard
```

### Option 2: Netlify

```bash
# 1. Build
npm run build

# 2. Drag dist/ folder to Netlify
# Or use CLI:
npm i -g netlify-cli
netlify deploy --prod --dir=dist
```

### Option 3: Docker to Server

```bash
# 1. Build image
docker build -t myregistry/misinformation-frontend:latest .

# 2. Push to registry
docker push myregistry/misinformation-frontend:latest

# 3. Deploy on server
docker run -d \
  --name frontend \
  -p 80:80 \
  -e VITE_API_URL=https://api.yourdomain.com/api/v1 \
  myregistry/misinformation-frontend:latest
```

### Option 4: Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: misinformation-frontend:latest
        ports:
        - containerPort: 80
        env:
        - name: VITE_API_URL
          value: "https://api.yourdomain.com/api/v1"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
```

---

## 🐛 Troubleshooting

### Issue: API Connection Refused

```
Error: connect ECONNREFUSED 127.0.0.1:8000
```

**Solution:**
1. Check if API is running: `docker ps | grep api`
2. Start API: `docker compose up -d api`
3. Verify port: `curl http://localhost:8000/health`
4. Check VITE_API_URL in `.env`

### Issue: CORS Error

```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:**
1. Check API CORS config
2. Verify proxy in vite.config.js
3. Use full URL in VITE_API_URL
4. Check browser console for actual error

### Issue: Blank Page After Build

**Solution:**
1. Check browser console for errors
2. Verify index.html exists in dist/
3. Clear browser cache: `Ctrl+Shift+Delete`
4. Check nginx.conf is correct
5. Verify nginx is serving files: `docker exec frontend ls -la /usr/share/nginx/html`

### Issue: Slow Upload

**Solution:**
1. Check file size (500MB limit)
2. Verify network speed
3. Try different browser
4. Check API performance
5. Review Docker resource limits

### Issue: Results Not Updating

**Solution:**
1. Check browser console for errors
2. Verify API is responding: `curl http://localhost:8000/api/v1/status/{task_id}`
3. Check polling interval (1 second)
4. Increase timeout if API is slow
5. Check browser developer tools Network tab

---

## 📊 Performance Optimization

### Build Size

```bash
# Check bundle size
npm run build

# Analyze bundle
npm install -D rollup-plugin-visualizer
# Add to vite.config.js and rebuild
```

### Runtime Performance

- Images: Lazy load results
- Polling: Efficient status updates (1s interval)
- Caching: Browser caches static assets (1 year)
- Compression: gzip enabled in nginx

---

## 🔐 Security

### Input Validation
- File size limits (500MB max)
- MIME type validation
- URL validation
- Claim text sanitization

### Network Security
- HTTPS in production (configured via nginx)
- CORS headers set by API
- No sensitive data in localStorage
- API calls over encrypted connection

### Build Security
- No secrets in frontend code
- Environment variables for API URL
- Dependencies audited: `npm audit`
- Docker image from alpine base

---

## 📚 Next Steps

1. **Start Development**
   ```bash
   npm install
   npm run dev
   ```

2. **Test with API**
   - Submit analysis
   - Check results display
   - Verify all endpoints work

3. **Customize**
   - Update colors in main.jsx theme
   - Add your logo/branding
   - Modify copy/labels

4. **Deploy**
   - Build production bundle
   - Deploy to chosen platform
   - Set API URL environment variable

5. **Monitor**
   - Check browser console for errors
   - Monitor API response times
   - Track user interactions

---

## 📖 Additional Resources

- **Material-UI Docs**: https://mui.com/
- **React Docs**: https://react.dev/
- **Vite Docs**: https://vitejs.dev/
- **Nginx Docs**: https://nginx.org/en/docs/

## Support

For issues or questions about the frontend, check:
1. Browser console (F12)
2. Network tab (see API calls)
3. Docker logs: `docker logs misinformation-frontend`
4. Main project README

---

**You're ready to run the complete system!** 🎉
