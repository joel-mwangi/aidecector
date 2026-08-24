# Frontend for Misinformation Detection System

Modern React + Material-UI frontend for the misinformation detection API.

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The frontend will run at `http://localhost:3000`

### 3. Build for Production

```bash
npm run build
```

Output will be in `frontend/dist/`

## Features

### 📤 Media Upload & Analysis
- **File Upload**: Upload images, videos, or audio files
- **URL Input**: Alternatively, provide a media URL
- **Claim Input**: Add associated claim text for verification
- **Real-time Status**: Live analysis progress updates

### 🔍 Analysis Results
- **Media Classification**: Authentic, Likely Authentic, Uncertain, Likely Manipulated, Manipulated, AI-Generated
- **Forensic Scores**:
  - Manipulation Probability
  - Synthetic Media Probability
  - Audio Manipulation Probability
  - Lip-Sync Inconsistency
  - Overall Confidence
  - Evidence Quality
- **Processing Time**: See how long analysis took
- **Evidence List**: View supporting/contradicting sources

### 📋 Analysis History
- **Task List**: View all past analyses
- **Quick Status**: See status at a glance (Queued, Processing, Completed, Failed)
- **Details View**: Open detailed results for any task
- **Delete Tasks**: Remove completed analyses
- **Auto-Refresh**: Updates every 5 seconds

### 📊 Visual Indicators
- **Classification Badges**: Color-coded authenticity scores
- **Progress Bars**: Visual representation of confidence levels
- **Status Chips**: Real-time task status
- **Evidence Tables**: Organized evidence presentation

## Architecture

```
frontend/
├── src/
│   ├── App.jsx           # Main application component
│   ├── main.jsx          # React entry point
│   └── components/       # Reusable UI components
├── index.html            # HTML template
├── vite.config.js        # Vite configuration
├── package.json          # Dependencies
└── README.md             # This file
```

## API Integration

The frontend communicates with the API at `http://localhost:8000/api/v1`

### Key Endpoints Used:
- `POST /analyze` - Submit media for analysis
- `GET /status/{task_id}` - Check analysis status
- `GET /results/{task_id}` - Get analysis results
- `GET /tasks` - List all tasks
- `DELETE /tasks/{task_id}` - Delete a task

## Environment Setup

### Development
```bash
VITE_API_URL=http://localhost:8000/api/v1
```

### Production
```bash
VITE_API_URL=https://api.yourdomain.com/api/v1
```

## Deployment

### Docker
```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY frontend .
RUN npm install && npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Standalone
```bash
npm run build
npx serve -s dist -l 3000
```

### Vercel/Netlify
```bash
npm run build
# Deploy the dist/ folder
```

## Features by Tab

### Tab 1: Upload & Analyze
1. Select media type (Image, Video, Audio)
2. Add claim text (optional)
3. Upload file or provide URL
4. Click "Analyze Media"
5. Wait for analysis to complete
6. View detailed results

### Tab 2: History
1. View all past analyses
2. Filter by status
3. Click "View" to see details
4. Click "Delete" to remove task
5. Auto-refreshes every 5 seconds

## Component Structure

### AnalysisForm
- Media type selector
- Claim text input
- File upload widget
- URL input field
- Submit button with loading state

### ResultsPanel
- Classification badges
- Forensic scores with progress bars
- Detailed metrics
- Evidence table
- Explanation text

### TasksHistory
- Task list table
- Status indicators
- Action buttons
- Details dialog

### StatusChip
- Real-time status display
- Color-coded indicators
- Animated loading state

### ClassificationBadge
- Color-coded classifications
- Text formatting
- Styled badge component

## Styling

Material-UI (MUI) for:
- Components
- Styling system
- Icons
- Responsive design
- Dark/Light theme support

## Performance

- **Code Splitting**: Vendor bundle separated
- **Lazy Loading**: Results load on demand
- **Polling**: Efficient status updates
- **Caching**: API responses cached

## Error Handling

- API error alerts
- Network timeout handling
- Upload validation
- Form validation
- User feedback

## Accessibility

- Semantic HTML
- ARIA labels
- Keyboard navigation
- Color contrast compliant
- Screen reader friendly

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers

## Development

### Add New Feature
1. Create component in `src/components/`
2. Import in App.jsx
3. Add to tab or layout
4. Test with API

### Styling Guide
- Use Material-UI theme
- Maintain consistent spacing
- Follow color scheme
- Responsive design first

### Testing
```bash
# Manual testing with development server
npm run dev

# Test build
npm run build
npm run preview
```

## Troubleshooting

### API Connection Issues
- Ensure API is running on port 8000
- Check CORS configuration
- Verify proxy settings in vite.config.js

### Upload Issues
- Check file size limit (500MB max)
- Verify MIME type
- Check browser console for errors

### Results Not Showing
- Check browser console
- Verify API response format
- Check network tab for failed requests

## Next Steps

1. **Add Authentication**: Implement user login/signup
2. **Add Notifications**: Toast notifications for updates
3. **Add Export**: Export results as PDF/CSV
4. **Add Analytics**: Track analysis statistics
5. **Add Themes**: Dark mode support
6. **Add Internationalization**: Multi-language support

## License

Same as main project - see LICENSE file

## Support

For issues or feature requests, see main project repository.
