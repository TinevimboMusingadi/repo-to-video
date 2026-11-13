import React, { useState, useEffect } from 'react';
import {
  Video,
  Layers,
  FolderGit2,
  Code2,
  Volume2,
  Terminal,
  Download,
  RefreshCw,
  Sparkles,
  Clock,
  Play,
  CheckCircle2,
  AlertCircle,
  FileText,
  Sliders,
  ChevronRight,
  ExternalLink
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function App() {
  const [activeTab, setActiveTab] = useState('ingest');
  const [repoTarget, setRepoTarget] = useState('.');
  const [selectedStyle, setSelectedStyle] = useState('3b1b');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [digest, setDigest] = useState(null);
  const [storyboard, setStoryboard] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [existingVideos, setExistingVideos] = useState([]);
  const [errorMsg, setErrorMsg] = useState(null);

  // Load existing videos on startup
  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/videos`);
      const data = await res.json();
      if (data && data.videos) {
        setExistingVideos(data.videos);
      }
    } catch (err) {
      console.warn('Backend not yet reachable:', err);
    }
  };

  // Poll job status during rendering
  useEffect(() => {
    if (!jobId || jobStatus?.status === 'completed' || jobStatus?.status === 'failed') return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);
        const data = await res.json();
        setJobStatus(data);
        if (data.status === 'completed') {
          fetchVideos();
        }
      } catch (err) {
        console.error('Error polling job status:', err);
      }
    }, 1200);

    return () => clearInterval(interval);
  }, [jobId, jobStatus?.status]);

  // Step 1: Analyze Repository
  const handleAnalyze = async () => {
    if (!repoTarget.trim()) return;
    setIsAnalyzing(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_target: repoTarget, style: selectedStyle })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to analyze repository');
      }
      const data = await res.json();
      setDigest(data.digest);
      setStoryboard(data.storyboard);
      setActiveTab('storyboard');
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Step 2: Update Scene in Storyboard
  const handleSceneChange = (index, field, value) => {
    if (!storyboard) return;
    const updatedScenes = [...storyboard.scenes];
    updatedScenes[index] = { ...updatedScenes[index], [field]: value };
    setStoryboard({ ...storyboard, scenes: updatedScenes });
  };

  // Step 3: Trigger Video Render
  const handleRender = async () => {
    if (!storyboard) return;
    setErrorMsg(null);
    setActiveTab('render');
    try {
      const res = await fetch(`${API_BASE}/api/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ storyboard, style: selectedStyle })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to start render');
      }
      const data = await res.json();
      setJobId(data.job_id);
      setJobStatus({ status: 'queued', progress: 0.05, message: 'Job registered...' });
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 32px' }}>
      {/* Top Navbar */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingBottom: '20px',
        borderBottom: '1px solid var(--border-color)',
        marginBottom: '28px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 16px rgba(56, 189, 248, 0.3)'
          }}>
            <Video size={22} color="#090d16" strokeWidth={2.5} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
              Repo-to-Video
            </h1>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Codebase-to-Video Onboarding Agent Harness
            </p>
          </div>
        </div>

        {/* Global Controls & Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 14px',
            background: 'rgba(52, 211, 153, 0.1)',
            border: '1px solid rgba(52, 211, 153, 0.25)',
            borderRadius: '20px',
            fontSize: '0.8rem',
            color: 'var(--accent-emerald)',
            fontWeight: 600
          }}>
            <CheckCircle2 size={14} /> Gemini 2.5 Active
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 14px',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: '20px',
            fontSize: '0.8rem',
            color: 'var(--text-muted)'
          }}>
            <Sliders size={14} /> Style:
            <select
              value={selectedStyle}
              onChange={(e) => setSelectedStyle(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-main)',
                fontWeight: 600,
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              <option value="3b1b" style={{ background: '#0f172a' }}>3Blue1Brown (Manim)</option>
              <option value="motion" style={{ background: '#0f172a' }}>Motion Graphics</option>
              <option value="tutorial" style={{ background: '#0f172a' }}>Developer Code-Walk</option>
            </select>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div style={{
        display: 'flex',
        gap: '8px',
        padding: '6px',
        background: 'var(--bg-card)',
        borderRadius: '12px',
        border: '1px solid var(--border-color)',
        marginBottom: '28px'
      }}>
        <TabButton
          active={activeTab === 'ingest'}
          onClick={() => setActiveTab('ingest')}
          icon={<FolderGit2 size={16} />}
          label="1. Ingest & Analyze"
          badge={digest ? `${digest.total_files} files` : null}
        />
        <TabButton
          active={activeTab === 'storyboard'}
          onClick={() => setActiveTab('storyboard')}
          icon={<Layers size={16} />}
          label="2. Storyboard & Script"
          badge={storyboard ? `${storyboard.scenes.length} scenes` : null}
          disabled={!storyboard}
        />
        <TabButton
          active={activeTab === 'render'}
          onClick={() => setActiveTab('render')}
          icon={<Video size={16} />}
          label="3. Video Player & Export"
          badge={jobStatus?.status === 'completed' ? 'Ready' : null}
        />
      </div>

      {/* Error Alert */}
      {errorMsg && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '12px 18px',
          background: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '10px',
          color: '#fca5a5',
          marginBottom: '24px',
          fontSize: '0.9rem'
        }}>
          <AlertCircle size={18} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* TAB 1: Ingest & Analyze */}
      {activeTab === 'ingest' && (
        <div className="fade-in">
          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: '16px',
            padding: '28px',
            marginBottom: '28px'
          }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '8px' }}>
              Target Repository
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '20px' }}>
              Provide a public Git URL or local folder path to analyze its architecture and draft an explainer video.
            </p>

            <div style={{ display: 'flex', gap: '12px' }}>
              <input
                type="text"
                value={repoTarget}
                onChange={(e) => setRepoTarget(e.target.value)}
                placeholder="e.g. https://github.com/fastapi/fastapi or ."
                style={{
                  flex: 1,
                  padding: '12px 18px',
                  background: '#090d16',
                  border: '1px solid var(--border-accent)',
                  borderRadius: '10px',
                  color: 'var(--text-main)',
                  fontSize: '0.95rem',
                  outline: 'none'
                }}
              />
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px 28px',
                  background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
                  color: '#090d16',
                  fontWeight: 700,
                  fontSize: '0.95rem',
                  border: 'none',
                  borderRadius: '10px',
                  cursor: isAnalyzing ? 'wait' : 'pointer',
                  boxShadow: '0 4px 14px rgba(56, 189, 248, 0.25)'
                }}
              >
                {isAnalyzing ? (
                  <>
                    <RefreshCw size={18} className="spin" /> Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles size={18} /> Analyze & Draft
                  </>
                )}
              </button>
            </div>

            {/* Quick Presets */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '16px' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Try Examples:</span>
              <PresetBadge label="Current Repo (d:\repo-to-video)" onClick={() => setRepoTarget('.')} />
              <PresetBadge label="fastapi/fastapi" onClick={() => setRepoTarget('https://github.com/fastapi/fastapi')} />
              <PresetBadge label="psf/requests" onClick={() => setRepoTarget('https://github.com/psf/requests')} />
            </div>
          </div>

          {/* Digest Output if already analyzed */}
          {digest && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-color)',
                borderRadius: '16px',
                padding: '24px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FolderGit2 size={18} color="var(--accent-blue)" /> Directory Tree
                  </h3>
                  <span style={{ fontSize: '0.8rem', color: 'var(--accent-emerald)', fontWeight: 600 }}>
                    {digest.total_files} Files Detected
                  </span>
                </div>
                <pre style={{
                  background: '#090d16',
                  padding: '16px',
                  borderRadius: '10px',
                  fontSize: '0.82rem',
                  color: '#93c5fd',
                  maxHeight: '340px',
                  overflowY: 'auto'
                }}>
                  {digest.file_tree || 'No tree found'}
                </pre>
              </div>

              <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-color)',
                borderRadius: '16px',
                padding: '24px'
              }}>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                  <FileText size={18} color="var(--accent-indigo)" /> README Overview
                </h3>
                <div style={{
                  background: '#090d16',
                  padding: '16px',
                  borderRadius: '10px',
                  fontSize: '0.85rem',
                  color: 'var(--text-muted)',
                  lineHeight: '1.6',
                  maxHeight: '340px',
                  overflowY: 'auto',
                  whiteSpace: 'pre-wrap'
                }}>
                  {digest.readme_excerpt || 'No README excerpt found.'}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Storyboard & Script Review */}
      {activeTab === 'storyboard' && storyboard && (
        <div className="fade-in">
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '20px'
          }}>
            <div>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 800 }}>
                {storyboard.repo_name}: Onboarding Storyboard
              </h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                {storyboard.tagline} • Target: {storyboard.target_audience}
              </p>
            </div>

            <button
              onClick={handleRender}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 28px',
                background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
                color: '#090d16',
                fontWeight: 700,
                fontSize: '0.95rem',
                border: 'none',
                borderRadius: '10px',
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(56, 189, 248, 0.25)'
              }}
            >
              <Play size={16} fill="#090d16" /> Render Video Now
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {storyboard.scenes.map((scene, idx) => (
              <div
                key={scene.scene_id}
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '14px',
                  padding: '20px'
                }}
              >
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '14px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '28px',
                      height: '28px',
                      borderRadius: '8px',
                      background: '#1e293b',
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      color: 'var(--accent-blue)'
                    }}>
                      {idx + 1}
                    </span>
                    <input
                      type="text"
                      value={scene.title}
                      onChange={(e) => handleSceneChange(idx, 'title', e.target.value)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-main)',
                        fontSize: '1.05rem',
                        fontWeight: 700,
                        outline: 'none',
                        width: '380px'
                      }}
                    />
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <select
                      value={scene.visual_style || selectedStyle}
                      onChange={(e) => handleSceneChange(idx, 'visual_style', e.target.value)}
                      style={{
                        background: '#090d16',
                        border: '1px solid var(--border-accent)',
                        borderRadius: '6px',
                        padding: '4px 8px',
                        fontSize: '0.8rem',
                        color: 'var(--text-muted)'
                      }}
                    >
                      <option value="3b1b">3Blue1Brown (Manim)</option>
                      <option value="motion">Motion Graphics</option>
                      <option value="tutorial">Developer Tutorial</option>
                    </select>

                    <span style={{
                      fontSize: '0.8rem',
                      color: 'var(--text-dim)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}>
                      <Clock size={13} /> ~{scene.duration_sec || 18}s
                    </span>
                  </div>
                </div>

                {/* Narration Script */}
                <div style={{ marginBottom: '14px' }}>
                  <label style={{
                    display: 'block',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    marginBottom: '6px'
                  }}>
                    VOICEOVER NARRATION SCRIPT (GEMINI TTS)
                  </label>
                  <textarea
                    rows={3}
                    value={scene.narration}
                    onChange={(e) => handleSceneChange(idx, 'narration', e.target.value)}
                    style={{
                      width: '100%',
                      background: '#090d16',
                      border: '1px solid var(--border-color)',
                      borderRadius: '8px',
                      padding: '10px 14px',
                      color: 'var(--text-main)',
                      fontSize: '0.9rem',
                      lineHeight: '1.5',
                      outline: 'none',
                      resize: 'vertical'
                    }}
                  />
                </div>

                {/* Visual Directives */}
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '14px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '4px' }}>
                      VISUAL ANIMATION CUES
                    </label>
                    <input
                      type="text"
                      value={scene.visual_instructions}
                      onChange={(e) => handleSceneChange(idx, 'visual_instructions', e.target.value)}
                      style={{
                        width: '100%',
                        background: '#090d16',
                        border: '1px solid var(--border-color)',
                        borderRadius: '6px',
                        padding: '6px 10px',
                        color: 'var(--text-muted)',
                        fontSize: '0.82rem'
                      }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '4px' }}>
                      DIAGRAM NODES
                    </label>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {scene.diagram_nodes && scene.diagram_nodes.map((node, nIdx) => (
                        <span
                          key={nIdx}
                          style={{
                            padding: '3px 8px',
                            background: '#1e293b',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            color: '#93c5fd'
                          }}
                        >
                          {node}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: Video Player & Export */}
      {activeTab === 'render' && (
        <div className="fade-in">
          {/* Progress Card if Job Active */}
          {jobStatus && jobStatus.status !== 'completed' && jobStatus.status !== 'failed' && (
            <div style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '16px',
              padding: '32px',
              textAlign: 'center',
              marginBottom: '28px'
            }}>
              <div style={{
                width: '56px',
                height: '56px',
                borderRadius: '50%',
                background: 'rgba(56, 189, 248, 0.1)',
                color: 'var(--accent-blue)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px'
              }}>
                <RefreshCw size={26} className="spin" />
              </div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '8px' }}>
                Rendering Onboarding Video...
              </h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '24px' }}>
                {jobStatus.message || 'Synthesizing voiceover, animating scenes, and ducking ambient music...'}
              </p>

              {/* Progress Bar */}
              <div style={{
                width: '100%',
                maxWidth: '640px',
                height: '10px',
                background: '#1e293b',
                borderRadius: '9999px',
                margin: '0 auto',
                overflow: 'hidden'
              }}>
                <div style={{
                  height: '100%',
                  width: `${Math.round((jobStatus.progress || 0.1) * 100)}%`,
                  background: 'linear-gradient(90deg, #38bdf8, #818cf8)',
                  transition: 'width 0.4s ease'
                }} />
              </div>
              <div style={{ marginTop: '10px', fontSize: '0.82rem', color: 'var(--text-dim)' }}>
                {Math.round((jobStatus.progress || 0.1) * 100)}% Completed
              </div>
            </div>
          )}

          {/* Current Job Video Player when Complete */}
          {jobStatus?.status === 'completed' && jobStatus?.result && (
            <div style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '16px',
              padding: '28px',
              marginBottom: '32px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <div>
                  <span style={{
                    display: 'inline-block',
                    padding: '4px 10px',
                    borderRadius: '20px',
                    background: 'rgba(52, 211, 153, 0.15)',
                    color: 'var(--accent-emerald)',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    marginBottom: '6px'
                  }}>
                    READY
                  </span>
                  <h3 style={{ fontSize: '1.3rem', fontWeight: 800 }}>
                    {jobStatus.result.video_filename}
                  </h3>
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <a
                    href={`${API_BASE}${jobStatus.result.video_url}`}
                    download
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '10px 20px',
                      background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
                      color: '#090d16',
                      fontWeight: 700,
                      fontSize: '0.88rem',
                      borderRadius: '8px',
                      textDecoration: 'none'
                    }}
                  >
                    <Download size={16} /> Download MP4
                  </a>
                  {jobStatus.result.subtitles_url && (
                    <a
                      href={`${API_BASE}${jobStatus.result.subtitles_url}`}
                      download
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '10px 18px',
                        background: '#1e293b',
                        color: 'var(--text-main)',
                        fontWeight: 600,
                        fontSize: '0.88rem',
                        borderRadius: '8px',
                        textDecoration: 'none'
                      }}
                    >
                      <FileText size={16} /> Subtitles (.srt)
                    </a>
                  )}
                </div>
              </div>

              {/* Video Player */}
              <div style={{
                position: 'relative',
                borderRadius: '12px',
                overflow: 'hidden',
                background: '#000',
                aspectRatio: '16/9',
                maxHeight: '520px',
                margin: '0 auto'
              }}>
                <video
                  src={`${API_BASE}${jobStatus.result.video_url}`}
                  controls
                  autoPlay
                  style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                />
              </div>
            </div>
          )}

          {/* Past Generated Videos Gallery */}
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '16px' }}>
              Generated Videos Library
            </h3>
            {existingVideos.length === 0 ? (
              <p style={{ color: 'var(--text-dim)', fontSize: '0.88rem' }}>No generated videos yet.</p>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '20px' }}>
                {existingVideos.map((vid, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '12px',
                      overflow: 'hidden'
                    }}
                  >
                    <video
                      src={`${API_BASE}${vid.url}`}
                      controls
                      style={{ width: '100%', aspectRatio: '16/9', background: '#000' }}
                    />
                    <div style={{ padding: '14px' }}>
                      <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px', wordBreak: 'break-all' }}>
                        {vid.filename}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
                          {(vid.size_bytes / (1024 * 1024)).toFixed(2)} MB
                        </span>
                        <a
                          href={`${API_BASE}${vid.url}`}
                          download
                          style={{
                            fontSize: '0.8rem',
                            color: 'var(--accent-blue)',
                            textDecoration: 'none',
                            fontWeight: 600,
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}
                        >
                          <Download size={14} /> Download
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function TabButton({ active, onClick, icon, label, badge, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        padding: '10px 16px',
        borderRadius: '8px',
        border: 'none',
        background: active ? '#1e293b' : 'transparent',
        color: active ? '#f8fafc' : disabled ? '#475569' : '#94a3b8',
        fontWeight: active ? 700 : 500,
        fontSize: '0.88rem',
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.15s ease'
      }}
    >
      {icon}
      <span>{label}</span>
      {badge && (
        <span style={{
          padding: '2px 8px',
          background: active ? 'rgba(56, 189, 248, 0.2)' : '#090d16',
          color: active ? '#38bdf8' : '#94a3b8',
          borderRadius: '9999px',
          fontSize: '0.72rem',
          fontWeight: 700
        }}>
          {badge}
        </span>
      )}
    </button>
  );
}

function PresetBadge({ label, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: '#162038',
        border: '1px solid var(--border-accent)',
        borderRadius: '6px',
        padding: '4px 10px',
        fontSize: '0.78rem',
        color: '#93c5fd',
        cursor: 'pointer'
      }}
    >
      {label}
    </button>
  );
}
