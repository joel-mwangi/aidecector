import React, { useState, useCallback } from 'react';
import axios from 'axios';
import {
  Container,
  Paper,
  TextField,
  Button,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  LinearProgress,
  Chip,
  Grid,
  Divider,
  Alert,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import PendingIcon from '@mui/icons-material/Pending';

const API_BASE = 'http://localhost:8000/api/v1';

const UploadBox = styled(Paper)(({ theme }) => ({
  border: `2px dashed ${theme.palette.primary.main}`,
  borderRadius: theme.spacing(2),
  padding: theme.spacing(3),
  textAlign: 'center',
  cursor: 'pointer',
  transition: 'all 0.3s ease',
  '&:hover': {
    borderColor: theme.palette.primary.dark,
    backgroundColor: theme.palette.action.hover,
  },
}));

const StatusChip = ({ status }) => {
  const statusConfig = {
    queued: { label: 'Queued', color: 'warning', icon: <PendingIcon /> },
    processing: { label: 'Processing', color: 'info', icon: <CircularProgress size={20} /> },
    completed: { label: 'Completed', color: 'success', icon: <CheckCircleIcon /> },
    failed: { label: 'Failed', color: 'error', icon: <ErrorIcon /> },
  };

  const config = statusConfig[status] || statusConfig.queued;
  return <Chip label={config.label} color={config.color} icon={config.icon} />;
};

const ClassificationBadge = ({ classification }) => {
  const colors = {
    AUTHENTIC: '#4caf50',
    LIKELY_AUTHENTIC: '#8bc34a',
    UNCERTAIN: '#ff9800',
    LIKELY_MANIPULATED: '#ff5722',
    MANIPULATED: '#f44336',
    AI_GENERATED: '#e91e63',
  };

  return (
    <Box
      sx={{
        display: 'inline-block',
        padding: '8px 16px',
        borderRadius: '20px',
        backgroundColor: colors[classification] || '#999',
        color: 'white',
        fontWeight: 'bold',
      }}
    >
      {classification?.replace(/_/g, ' ') || 'UNKNOWN'}
    </Box>
  );
};

const AnalysisForm = ({ onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    media_type: 'image',
    claim: '',
    media_url: '',
  });
  const [file, setFile] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    // Auto-detect media type
    if (selectedFile) {
      const type = selectedFile.type.split('/')[0];
      setFormData(prev => ({ ...prev, media_type: type === 'text' ? 'audio' : type }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (file) {
      const reader = new FileReader();
      reader.onload = async (event) => {
        const data = new Uint8Array(event.target.result);
        await onSubmit({ ...formData, media_data: data });
      };
      reader.readAsArrayBuffer(file);
    } else if (formData.media_url) {
      await onSubmit(formData);
    } else {
      alert('Please upload a file or provide a URL');
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          📤 Upload Media for Analysis
        </Typography>
        
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
          <Grid container spacing={3}>
            {/* Media Type */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                select
                label="Media Type"
                name="media_type"
                value={formData.media_type}
                onChange={handleInputChange}
                SelectProps={{ native: true }}
              >
                <option value="image">Image</option>
                <option value="video">Video</option>
                <option value="audio">Audio</option>
              </TextField>
            </Grid>

            {/* Claim */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Associated Claim (Optional)"
                name="claim"
                placeholder="e.g., 'President announced a new policy yesterday'"
                value={formData.claim}
                onChange={handleInputChange}
              />
            </Grid>

            {/* Upload Area */}
            <Grid item xs={12}>
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Upload File
                </Typography>
                <UploadBox>
                  <input
                    accept={formData.media_type === 'image' ? 'image/*' : 
                           formData.media_type === 'video' ? 'video/*' : 'audio/*'}
                    style={{ display: 'none' }}
                    id="file-upload"
                    type="file"
                    onChange={handleFileChange}
                  />
                  <label htmlFor="file-upload" style={{ cursor: 'pointer' }}>
                    <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
                    <Typography variant="body1">
                      {file ? file.name : 'Click to upload or drag and drop'}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Max size: 500MB
                    </Typography>
                  </label>
                </UploadBox>
              </Box>
            </Grid>

            {/* Or URL */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Or Enter Media URL"
                name="media_url"
                placeholder="https://example.com/media.jpg"
                value={formData.media_url}
                onChange={handleInputChange}
                disabled={!!file}
              />
            </Grid>

            {/* Submit Button */}
            <Grid item xs={12}>
              <Button
                fullWidth
                variant="contained"
                size="large"
                type="submit"
                disabled={loading || (!file && !formData.media_url)}
                sx={{ py: 1.5 }}
              >
                {loading ? (
                  <>
                    <CircularProgress size={20} sx={{ mr: 1 }} />
                    Analyzing...
                  </>
                ) : (
                  'Analyze Media'
                )}
              </Button>
            </Grid>
          </Grid>
        </Box>
      </CardContent>
    </Card>
  );
};

const ResultsPanel = ({ results, loading }) => {
  const [expandedResult, setExpandedResult] = useState(null);

  if (!results) return null;

  const result = results.result || results;

  const mediaAssessment = result.media_assessment || {};
  const claimAssessment = result.claim_assessment || {};
  const classification = result.classification || 'UNKNOWN';
  const infoClassification = result.info_classification || 'UNKNOWN';

  return (
    <Card sx={{ mt: 3 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          🔍 Analysis Results
        </Typography>

        {loading && (
          <Box sx={{ mb: 2 }}>
            <LinearProgress />
            <Typography variant="caption" color="textSecondary" sx={{ mt: 1 }}>
              Analysis in progress...
            </Typography>
          </Box>
        )}

        {/* Classification */}
        <Box sx={{ mb: 3, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
          <Typography variant="subtitle2" gutterBottom>
            Media Classification
          </Typography>
          <Box sx={{ mb: 2 }}>
            <ClassificationBadge classification={classification} />
          </Box>

          <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
            Information Classification
          </Typography>
          <ClassificationBadge classification={infoClassification} />
        </Box>

        {/* Key Metrics */}
        <Typography variant="subtitle1" gutterBottom sx={{ mt: 3, mb: 2 }}>
          📊 Key Metrics
        </Typography>

        <Grid container spacing={2} sx={{ mb: 3 }}>
          {/* Manipulation Probability */}
          <Grid item xs={12} sm={6}>
            <Paper sx={{ p: 2, backgroundColor: '#fff3e0' }}>
              <Typography variant="caption" color="textSecondary">
                Manipulation Probability
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <Typography variant="h6" sx={{ mr: 2, fontWeight: 'bold' }}>
                  {(mediaAssessment.manipulation_probability * 100).toFixed(0)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={mediaAssessment.manipulation_probability * 100}
                  sx={{ flex: 1, height: 8, borderRadius: 4 }}
                />
              </Box>
            </Paper>
          </Grid>

          {/* Synthetic Media Probability */}
          <Grid item xs={12} sm={6}>
            <Paper sx={{ p: 2, backgroundColor: '#fce4ec' }}>
              <Typography variant="caption" color="textSecondary">
                Synthetic Media Probability
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <Typography variant="h6" sx={{ mr: 2, fontWeight: 'bold' }}>
                  {(mediaAssessment.synthetic_media_probability * 100).toFixed(0)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={mediaAssessment.synthetic_media_probability * 100}
                  sx={{ flex: 1, height: 8, borderRadius: 4 }}
                  color="secondary"
                />
              </Box>
            </Paper>
          </Grid>

          {/* Overall Confidence */}
          <Grid item xs={12} sm={6}>
            <Paper sx={{ p: 2, backgroundColor: '#e8f5e9' }}>
              <Typography variant="caption" color="textSecondary">
                Overall Confidence
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <Typography variant="h6" sx={{ mr: 2, fontWeight: 'bold' }}>
                  {(result.overall_confidence * 100).toFixed(0)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={result.overall_confidence * 100}
                  sx={{ flex: 1, height: 8, borderRadius: 4 }}
                  color="success"
                />
              </Box>
            </Paper>
          </Grid>

          {/* Evidence Quality */}
          <Grid item xs={12} sm={6}>
            <Paper sx={{ p: 2, backgroundColor: '#e3f2fd' }}>
              <Typography variant="caption" color="textSecondary">
                Evidence Quality
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <Typography variant="h6" sx={{ mr: 2, fontWeight: 'bold' }}>
                  {(result.evidence_quality * 100).toFixed(0)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={result.evidence_quality * 100}
                  sx={{ flex: 1, height: 8, borderRadius: 4 }}
                  color="info"
                />
              </Box>
            </Paper>
          </Grid>
        </Grid>

        {/* Additional Scores */}
        <Typography variant="subtitle2" gutterBottom sx={{ mt: 3, mb: 2 }}>
          🎯 Additional Analysis
        </Typography>

        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="textSecondary">
                Audio Manipulation
              </Typography>
              <Typography variant="h6" sx={{ mt: 1, fontWeight: 'bold' }}>
                {(mediaAssessment.audio_manipulation_probability * 100).toFixed(0)}%
              </Typography>
            </Paper>
          </Grid>

          <Grid item xs={12} sm={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="textSecondary">
                Lip-Sync Inconsistency
              </Typography>
              <Typography variant="h6" sx={{ mt: 1, fontWeight: 'bold' }}>
                {(mediaAssessment.lip_sync_inconsistency * 100).toFixed(0)}%
              </Typography>
            </Paper>
          </Grid>

          <Grid item xs={12} sm={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="textSecondary">
                Processing Time
              </Typography>
              <Typography variant="h6" sx={{ mt: 1, fontWeight: 'bold' }}>
                {result.processing_time_seconds?.toFixed(2)}s
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Explanation */}
        {result.explanation && (
          <Box sx={{ mt: 3, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom>
              📝 Explanation
            </Typography>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
              {result.explanation}
            </Typography>
          </Box>
        )}

        {/* Evidence */}
        {result.evidence && result.evidence.length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              📚 Evidence ({result.evidence.length} items)
            </Typography>
            <TableContainer sx={{ mt: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                    <TableCell>Source</TableCell>
                    <TableCell>Relationship</TableCell>
                    <TableCell align="right">Reliability</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {result.evidence.slice(0, 5).map((item, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{item.source}</TableCell>
                      <TableCell>
                        <Chip
                          label={item.relationship}
                          size="small"
                          color={
                            item.relationship === 'supports'
                              ? 'success'
                              : item.relationship === 'contradicts'
                              ? 'error'
                              : 'default'
                          }
                        />
                      </TableCell>
                      <TableCell align="right">
                        {(item.reliability * 100).toFixed(0)}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

const TasksHistory = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  React.useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/tasks`);
      setTasks(response.data.tasks || []);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (taskId) => {
    try {
      const response = await axios.get(`${API_BASE}/results/${taskId}`);
      setSelectedTask(response.data);
      setDialogOpen(true);
    } catch (error) {
      alert('Failed to load task details');
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        await axios.delete(`${API_BASE}/tasks/${taskId}`);
        fetchTasks();
      } catch (error) {
        alert('Failed to delete task');
      }
    }
  };

  return (
    <Card sx={{ mt: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5">
            📋 Analysis History ({tasks.length})
          </Typography>
          <Button
            variant="outlined"
            size="small"
            onClick={fetchTasks}
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>

        {tasks.length === 0 ? (
          <Alert severity="info">No analysis tasks yet. Submit media to get started!</Alert>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                  <TableCell>Type</TableCell>
                  <TableCell>Claim</TableCell>
                  <TableCell align="center">Status</TableCell>
                  <TableCell align="right">Created</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {tasks.map((task) => (
                  <TableRow key={task.id} hover>
                    <TableCell>
                      <Chip
                        label={task.media_type}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {task.claim || '(No claim)'}
                    </TableCell>
                    <TableCell align="center">
                      <StatusChip status={task.status} />
                    </TableCell>
                    <TableCell align="right">
                      {new Date(task.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell align="center">
                      <Button
                        size="small"
                        variant="text"
                        onClick={() => handleViewDetails(task.id)}
                      >
                        View
                      </Button>
                      <Button
                        size="small"
                        variant="text"
                        color="error"
                        onClick={() => handleDeleteTask(task.id)}
                      >
                        Delete
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </CardContent>

      {/* Task Details Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Analysis Details</DialogTitle>
        <DialogContent>
          {selectedTask && (
            <Box sx={{ mt: 2 }}>
              <ResultsPanel results={selectedTask} />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
};

export default function App() {
  const [activeTab, setActiveTab] = useState(0);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalysisSubmit = async (formData) => {
    try {
      setError(null);
      setAnalysisLoading(true);

      const response = await axios.post(`${API_BASE}/analyze`, formData);
      const taskId = response.data.task_id;

      // Poll for results
      let attempts = 0;
      const maxAttempts = 120; // 2 minutes
      const pollInterval = setInterval(async () => {
        attempts++;

        try {
          const statusResponse = await axios.get(`${API_BASE}/status/${taskId}`);

          if (statusResponse.data.status === 'completed') {
            clearInterval(pollInterval);
            const resultsResponse = await axios.get(`${API_BASE}/results/${taskId}`);
            setAnalysisResults(resultsResponse.data);
            setAnalysisLoading(false);
            setActiveTab(0); // Show results
          } else if (statusResponse.data.status === 'failed') {
            clearInterval(pollInterval);
            setError(`Analysis failed: ${statusResponse.data.error}`);
            setAnalysisLoading(false);
          }
        } catch (err) {
          console.error('Poll error:', err);
        }

        if (attempts >= maxAttempts) {
          clearInterval(pollInterval);
          setError('Analysis timeout. Please try again.');
          setAnalysisLoading(false);
        }
      }, 1000); // Poll every second
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      setAnalysisLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 'bold' }}>
          🔍 Misinformation Detector
        </Typography>
        <Typography variant="subtitle1" color="textSecondary">
          Analyze media authenticity and verify claims using advanced AI forensics
        </Typography>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, val) => setActiveTab(val)}>
          <Tab label="📤 Upload & Analyze" />
          <Tab label="📋 History" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {activeTab === 0 && (
        <Box>
          <AnalysisForm onSubmit={handleAnalysisSubmit} loading={analysisLoading} />
          <ResultsPanel results={analysisResults} loading={analysisLoading} />
        </Box>
      )}

      {activeTab === 1 && <TasksHistory />}

      {/* Footer */}
      <Box sx={{ mt: 6, pt: 3, borderTop: 1, borderColor: 'divider', textAlign: 'center' }}>
        <Typography variant="caption" color="textSecondary">
          Multimodal Misinformation Detection System • API v1.0
        </Typography>
      </Box>
    </Container>
  );
}
