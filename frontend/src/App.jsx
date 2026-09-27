import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  Image as ImageIcon,
  Video as VideoIcon,
  FileText,
  Layers,
  Play,
  Clock,
  Sparkles,
  RefreshCw,
  FolderOpen,
  Copy,
  Check,
  X,
  AlertCircle,
  FileQuestion,
  ChevronRight
} from 'lucide-react';
import './App.css';

const QUICK_PROMPTS = [
  "Instructor explaining code on a whiteboard",
  "Terminal window with C++ compilation output",
  "Slide showing time complexity Big O notation",
  "Video where someone runs a Python script",
  "OOP concepts like classes and inheritance explained",
  "Data structures like linked list or binary tree diagram",
  "A woman standing with a cat",
  "Hot morning beverage with latte art"
];

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatTime(seconds) {
  if (seconds === null || seconds === undefined) return '';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export default function App() {
  const [query, setQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [results, setResults] = useState([]);
  const [totalResults, setTotalResults] = useState(0);
  const [loading, setLoading] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [indexStatus, setIndexStatus] = useState(null);
  const [showStatusBanner, setShowStatusBanner] = useState(false);
  const [copiedPath, setCopiedPath] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  const videoRef = useRef(null);
  const pollIntervalRef = useRef(null);
  const bannerDismissRef = useRef(null);
  // Track whether the user triggered indexing in THIS browser session.
  // We never show the banner for stale DB state on a cold page load.
  const sessionIndexTriggeredRef = useRef(false);

  // Fetch indexing status once; only start polling if status is RUNNING
  const fetchIndexStatus = async (startPolling = false) => {
    try {
      const res = await fetch('/api/index/status');
      if (res.ok) {
        const data = await res.json();
        setIndexStatus(data);

        const isTerminal = data.status === 'COMPLETED' || data.status === 'FAILED';
        const isRunning  = data.status === 'RUNNING';

        // Only show the banner if the user triggered a scan this session,
        // or if indexing is actively running (covers the case where the page
        // was refreshed mid-run).
        if (isRunning || sessionIndexTriggeredRef.current) {
          setShowStatusBanner(true);
        }

        if (isRunning) {
          // Auto-poll only when indexing is genuinely active
          if (!pollIntervalRef.current) {
            pollIntervalRef.current = setInterval(() => fetchIndexStatus(false), 1500);
          }
          // Cancel any pending auto-dismiss while running
          if (bannerDismissRef.current) {
            clearTimeout(bannerDismissRef.current);
            bannerDismissRef.current = null;
          }
        } else {
          // Stop polling for terminal / idle states
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          // Auto-dismiss the banner after 4 s for terminal states
          if (isTerminal && sessionIndexTriggeredRef.current) {
            if (bannerDismissRef.current) clearTimeout(bannerDismissRef.current);
            bannerDismissRef.current = setTimeout(() => setShowStatusBanner(false), 4000);
          }
        }
      }
    } catch (e) {
      console.error("Status fetch error", e);
    }
  };

  // Load all assets or run search
  const loadAssets = async (type = filterType) => {
    setLoading(true);
    setResults([]);          // clear stale results immediately
    try {
      const res = await fetch(`/api/assets?limit=50&type=${type}`);
      if (res.ok) {
        const data = await res.json();
        const mapped = data.assets.map(a => ({
          asset_id: a.id,
          filename: a.filename,
          file_type: a.file_type,
          path: a.path,
          size_bytes: a.size_bytes,
          relevance_score: 1.0,
          matched_sources: ['catalog'],
          explanation: `Catalog item (${a.status.toLowerCase()})`,
          thumbnail_url: a.thumbnail_url,
          preview_url: `/api/media/${a.id}`
        }));
        setResults(mapped);
        setTotalResults(data.total);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setIsInitialLoad(false);
    }
  };

  const handleSearch = async (searchQuery = query, type = filterType) => {
    const trimmed = searchQuery.trim();
    if (!trimmed) {
      loadAssets(type);
      return;
    }
    setLoading(true);
    setResults([]);          // clear stale results immediately
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(trimmed)}&type=${type}&limit=30`);
      if (res.ok) {
        const data = await res.json();
        setResults(data.results || []);
        setTotalResults(data.total_results || 0);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setIsInitialLoad(false);
    }
  };

  const triggerIndexing = async () => {
    sessionIndexTriggeredRef.current = true;  // mark session as user-initiated
    try {
      const res = await fetch('/api/index/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      if (res.ok) {
        fetchIndexStatus();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const triggerRetry = async () => {
    try {
      await fetch('/api/index/retry-failed', { method: 'POST' });
      fetchIndexStatus();
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    // On mount: fetch status once (shows last-run banner if needed) and load assets.
    // We do NOT start a polling loop here — polling only activates when the
    // user clicks "Scan Media Folder" and the server responds with RUNNING.
    fetchIndexStatus();
    loadAssets('all');
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      if (bannerDismissRef.current) clearTimeout(bannerDismissRef.current);
    };
  }, []);

  const onFilterSelect = (type) => {
    setFilterType(type);
    if (query.trim()) {
      handleSearch(query, type);
    } else {
      loadAssets(type);
    }
  };

  const onQuickPromptClick = (p) => {
    setQuery(p);
    handleSearch(p, filterType);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedPath(true);
    setTimeout(() => setCopiedPath(false), 2000);
  };

  // Video auto-seek when modal opens
  // Video seek is now handled via onLoadedMetadata on the <video> element below.
  // Setting currentTime here (before metadata loads) was silently dropped by the browser.

  const isIndexingRunning = indexStatus?.status === 'RUNNING';

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="brand-section">
          <div className="logo-badge">
            <Sparkles size={24} />
          </div>
          <div>
            <h1 className="brand-title">
              AssetLens
              <span className="version-pill">Local Multimodal DAM</span>
            </h1>
            <p className="brand-subtitle">
              Natural-language content discovery across images, videos, and PDF brochures
            </p>
          </div>
        </div>

        <div className="header-actions">
          <button
            className={`index-trigger-btn ${isIndexingRunning ? 'running' : ''}`}
            onClick={triggerIndexing}
            disabled={isIndexingRunning}
          >
            <RefreshCw size={16} className={isIndexingRunning ? 'spin' : ''} />
            {isIndexingRunning ? 'Scanning & Indexing...' : 'Scan Media Folder'}
          </button>
        </div>
      </header>

      {/* Indexing Progress Banner — shown while RUNNING, or briefly after COMPLETED/FAILED */}
      {indexStatus && indexStatus.status !== 'IDLE' && showStatusBanner && (
        <section className="status-panel">
          <div className="status-panel-header">
            <div className="status-title">
              <RefreshCw size={16} className={isIndexingRunning ? 'spin' : ''} />
              <span>Indexing Status: <strong>{indexStatus.status}</strong></span>
            </div>
            <div className="status-metrics">
              <span className="metric-tag">
                <strong>{indexStatus.indexed_files}</strong> indexed
              </span>
              <span className="metric-tag">
                <strong>{indexStatus.skipped_files}</strong> unchanged
              </span>
              {indexStatus.failed_files > 0 && (
                <span className="metric-tag" style={{ color: 'var(--danger)' }}>
                  <strong>{indexStatus.failed_files}</strong> failed
                  <button onClick={triggerRetry} style={{ color: 'var(--accent)', textDecoration: 'underline', marginLeft: 6 }}>
                    Retry
                  </button>
                </span>
              )}
              {indexStatus.duplicate_files > 0 && (
                <span className="metric-tag">
                  <strong>{indexStatus.duplicate_files}</strong> duplicate
                </span>
              )}
              {/* Manual dismiss — only for terminal states, not while running */}
              {!isIndexingRunning && (
                <button
                  onClick={() => {
                    if (bannerDismissRef.current) clearTimeout(bannerDismissRef.current);
                    setShowStatusBanner(false);
                  }}
                  title="Dismiss"
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--text-muted)', marginLeft: 8, padding: '0 2px',
                    display: 'flex', alignItems: 'center'
                  }}
                >
                  <X size={14} />
                </button>
              )}
            </div>
          </div>
          <div className="progress-bar-bg">
            <div
              className="progress-bar-fill"
              style={{ width: `${indexStatus.progress_percent}%` }}
            />
          </div>
        </section>
      )}

      {/* Main Search Bar */}
      <section className="search-section">
        <form onSubmit={(e) => { e.preventDefault(); handleSearch(); }}>
          <div className="search-input-wrapper">
            <Search size={22} className="search-icon-left" />
            <input
              type="text"
              className="main-search-input"
              placeholder="Search with natural language (e.g. 'A woman standing with a cat', 'construction activity', 'modern living room')..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button type="submit" className="search-btn-inside" disabled={loading}>
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </form>

        <div className="quick-prompts">
          <span className="quick-prompts-label">Example Prompts:</span>
          {QUICK_PROMPTS.map((p, idx) => (
            <button
              key={idx}
              className="prompt-chip"
              onClick={() => onQuickPromptClick(p)}
            >
              {p}
            </button>
          ))}
        </div>
      </section>

      {/* Filters & Results Meta */}
      <div className="filter-bar">
        <div className="filter-tabs">
          <button
            className={`filter-tab ${filterType === 'all' ? 'active' : ''}`}
            onClick={() => onFilterSelect('all')}
          >
            <Layers size={15} /> All Media
          </button>
          <button
            className={`filter-tab ${filterType === 'image' ? 'active' : ''}`}
            onClick={() => onFilterSelect('image')}
          >
            <ImageIcon size={15} /> Images
          </button>
          <button
            className={`filter-tab ${filterType === 'video' ? 'active' : ''}`}
            onClick={() => onFilterSelect('video')}
          >
            <VideoIcon size={15} /> Videos
          </button>
          <button
            className={`filter-tab ${filterType === 'pdf' ? 'active' : ''}`}
            onClick={() => onFilterSelect('pdf')}
          >
            <FileText size={15} /> PDFs & Documents
          </button>
        </div>

        <div className="results-meta">
          Showing <strong>{results.length}</strong> {query ? 'matches' : 'catalog items'}
        </div>
      </div>

      {/* Results Grid — show skeleton cards while loading, real cards after */}
      {loading ? (
        <div className="results-grid">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="asset-card skeleton-card">
              <div className="card-media-wrapper skeleton-media" />
              <div className="card-body">
                <div className="skeleton-line skeleton-title" />
                <div className="skeleton-line skeleton-meta" />
                <div className="skeleton-line skeleton-explanation" />
              </div>
            </div>
          ))}
        </div>
      ) : results.length > 0 ? (
        <div className="results-grid">
          {results.map((asset) => {
            const isVideo = asset.file_type === 'VIDEO';
            const isPdf = asset.file_type === 'PDF';
            const isImage = asset.file_type === 'IMAGE';
            const typeClass = asset.file_type.toLowerCase();

            return (
              <div
                key={asset.asset_id}
                className="asset-card"
                onClick={() => setSelectedAsset(asset)}
              >
                <div className="card-media-wrapper">
                  <img
                    src={asset.thumbnail_url}
                    alt={asset.filename}
                    className="card-thumbnail"
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                  <span className={`type-badge ${typeClass}`}>
                    {asset.file_type}
                  </span>

                  {query && (
                    <span className="relevance-pill">
                      {Math.round(asset.relevance_score * 100)}% match
                    </span>
                  )}

                  {isVideo && asset.matched_timestamp_sec !== null && asset.matched_timestamp_sec !== undefined && (
                    <span className="temporal-marker">
                      <Clock size={12} /> {formatTime(asset.matched_timestamp_sec)}
                    </span>
                  )}

                  {isPdf && asset.matched_page_number && (
                    <span className="temporal-marker">
                      Page {asset.matched_page_number}
                    </span>
                  )}
                </div>

                <div className="card-body">
                  <h3 className="card-title" title={asset.filename}>
                    {asset.filename}
                  </h3>

                  <div className="card-meta-row">
                    <span>{formatBytes(asset.size_bytes)}</span>
                    <div className="source-badges">
                      {asset.matched_sources?.map((s) => (
                        <span key={s} className="source-badge">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="explanation-box">
                    {asset.explanation}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="empty-state">
          <FileQuestion size={48} style={{ opacity: 0.4, marginBottom: 16 }} />
          <h3>No relevant assets found</h3>
          <p>
            {query
              ? "No assets met the relevance threshold for your query. Try broadening your terms or removing modality filters."
              : "No media files indexed yet. Click 'Scan Media Folder' to index your collection."}
          </p>
        </div>
      )}

      {/* Asset Preview Modal */}
      {selectedAsset && (
        <div className="modal-overlay" onClick={() => setSelectedAsset(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="card-title" style={{ fontSize: 18 }}>
                {selectedAsset.filename}
              </h2>
              <button onClick={() => setSelectedAsset(null)}>
                <X size={22} color="var(--text-muted)" />
              </button>
            </div>

            <div className="modal-body">
              <div className="modal-media-stage">
                {selectedAsset.file_type === 'IMAGE' && (
                  <img
                    src={selectedAsset.preview_url}
                    alt={selectedAsset.filename}
                  />
                )}

                {selectedAsset.file_type === 'VIDEO' && (() => {
                  const ts = selectedAsset.matched_timestamp_sec || 0;
                  // Media Fragments URI: appending #t=N makes Chrome issue a
                  // byte-range request starting at that timestamp directly.
                  // Works for faststart MP4s; poster covers end-moov files.
                  const videoSrc = `${selectedAsset.preview_url}#t=${Math.floor(ts)}`;
                  let _seekDone = false;
                  const doSeek = () => {
                    if (_seekDone || !videoRef.current) return;
                    _seekDone = true;
                    videoRef.current.currentTime = ts;
                    videoRef.current.play().catch(() => {});
                  };
                  return (
                    <video
                      ref={videoRef}
                      key={selectedAsset.asset_id}
                      src={videoSrc}
                      poster={selectedAsset.thumbnail_url}
                      controls
                      onLoadedMetadata={doSeek}
                      onCanPlay={doSeek}
                    />
                  );
                })()}


                {selectedAsset.file_type === 'PDF' && (
                  <iframe
                    src={selectedAsset.preview_url}
                    title={selectedAsset.filename}
                    style={{ width: '100%', height: '100%', border: 'none' }}
                  />
                )}
              </div>

              <div className="modal-sidebar">
                <div>
                  <div className="sidebar-section-title">Original File Location</div>
                  <div className="path-box">{selectedAsset.path}</div>
                  <button
                    className="copy-btn"
                    onClick={() => copyToClipboard(selectedAsset.path)}
                  >
                    {copiedPath ? <Check size={14} /> : <Copy size={14} />}
                    {copiedPath ? 'Copied to clipboard' : 'Copy original path'}
                  </button>
                </div>

                <div>
                  <div className="sidebar-section-title">Asset Metadata</div>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <div>Type: <strong>{selectedAsset.file_type}</strong></div>
                    <div>File Size: <strong>{formatBytes(selectedAsset.size_bytes)}</strong></div>
                    {selectedAsset.matched_timestamp_sec !== null && selectedAsset.matched_timestamp_sec !== undefined && (
                      <div>Matched Timestamp: <strong>{formatTime(selectedAsset.matched_timestamp_sec)} ({selectedAsset.matched_timestamp_sec}s)</strong></div>
                    )}
                    {selectedAsset.matched_page_number && (
                      <div>Matched Page: <strong>Page {selectedAsset.matched_page_number}</strong></div>
                    )}
                  </div>
                </div>

                <div>
                  <div className="sidebar-section-title">Search Retrieval Analysis</div>
                  <div className="explanation-box" style={{ marginTop: 0 }}>
                    {selectedAsset.explanation}
                  </div>
                  {selectedAsset.matched_snippet && (
                    <div style={{ marginTop: 10, fontSize: 12, color: 'var(--text-muted)' }}>
                      <strong>Excerpt:</strong> "{selectedAsset.matched_snippet}"
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
