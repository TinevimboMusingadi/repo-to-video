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
  ExternalLink,
  MessageSquare,
  HelpCircle,
  Plus,
  Trash2,
  ListChecks,
  ArrowRight,
  SlidersHorizontal,
  Compass
} from 'lucide-react';

const API_BASE = ''; // same-origin when served by FastAPI; Vite proxy handles /api in dev

export default function App() {
  const [activeTab, setActiveTab] = useState('ingest');
  const [repoTarget, setRepoTarget] = useState('.');
  const [selectedStyle, setSelectedStyle] = useState('3b1b');
  const [isScanning, setIsScanning] = useState(false);
  const [isDrafting, setIsDrafting] = useState(false);
  const [digest, setDigest] = useState(null);
  const [intakeQuestions, setIntakeQuestions] = useState(null);

  // Questionnaire / Director Preferences state
  const [preferences, setPreferences] = useState({
    target_depth: 'standard',
    target_audience: 'New Contributors & Open-Source Hackers',
    focus_areas: [],
    custom_notes: '',
    scene_count: 6
  });

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

  // Step 1: Scan Repository & Open Interactive Intake Interview
  const handleScanAndInterview = async () => {
    if (!repoTarget.trim()) return;
    setIsScanning(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_target: repoTarget })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to scan repository');
      }
      const data = await res.json();
      setDigest(data.digest);
      setIntakeQuestions(data.intake_questions);

      // Prepopulate preferences from scan
      const defFocus = data.intake_questions?.default_focus || [];
      setPreferences((prev) => ({
        ...prev,
        focus_areas: defFocus.length > 0 ? defFocus : prev.focus_areas,
        target_audience: data.intake_questions?.audience_options?.[0] || prev.target_audience
      }));

      setActiveTab('intake');
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsScanning(false);
    }
  };

  // Step 1 Fallback: Instant 1-Click Express Analyze
  const handleExpressAnalyze = async () => {
    if (!repoTarget.trim()) return;
    setIsScanning(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_target: repoTarget,
          style: selectedStyle,
          preferences: preferences
        })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to analyze repository');
      }
      const data = await res.json();
      setDigest(data.digest);
      if (data.intake_questions) setIntakeQuestions(data.intake_questions);
      setStoryboard(data.storyboard);
      setActiveTab('storyboard');
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsScanning(false);
    }
  };

  // Step 2: Plan Storyboard based on User Intake Answers
  const handlePlanStoryboard = async () => {
    setIsDrafting(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/draft`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_target: repoTarget,
          style: selectedStyle,
          preferences: preferences
        })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to draft storyboard');
      }
      const data = await res.json();
      setStoryboard(data.storyboard);
      setActiveTab('storyboard');
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsDrafting(false);
    }
  };

  // Toggle candidate module in focus areas
  const toggleFocusModule = (mod) => {
    setPreferences((prev) => {
      const exists = prev.focus_areas.includes(mod);
      return {
        ...prev,
        focus_areas: exists
          ? prev.focus_areas.filter((m) => m !== mod)
          : [...prev.focus_areas, mod]
      };
    });
  };

  // Change video depth setting
  const selectDepth = (depthId, scenesCount) => {
    setPreferences((prev) => ({
      ...prev,
      target_depth: depthId,
      scene_count: scenesCount
    }));
  };

  // Step 3: Storyboard Editing
  const handleSceneChange = (index, field, value) => {
    if (!storyboard) return;
    const updatedScenes = [...storyboard.scenes];
    updatedScenes[index] = { ...updatedScenes[index], [field]: value };
    setStoryboard({ ...storyboard, scenes: updatedScenes });
  };

  const handleAddScene = () => {
    if (!storyboard) return;
    const newId = storyboard.scenes.length + 1;
    const newScene = {
      scene_id: newId,
      title: `Scene ${newId}: Custom Architectural Walk`,
      narration: `In this section, we take a closer look at key subsystem interactions and developer workflows across the codebase.`,
      duration_sec: 18.0,
      visual_style: selectedStyle,
      visual_instructions: 'Node graph highlighting connection paths with animated data flow.',
      diagram_nodes: ['Component A', 'Component B', 'Service Gateway'],
      diagram_edges: ['Component A -> Component B', 'Component B -> Service Gateway'],
      code_snippet: null,
      terminal_command: null
    };
    const updated = [...storyboard.scenes, newScene];
    setStoryboard({
      ...storyboard,
      scenes: updated,
      total_duration_estimate: updated.reduce((acc, s) => acc + (s.duration_sec || 18), 0)
    });
  };

  const handleDeleteScene = (index) => {
    if (!storyboard || storyboard.scenes.length <= 1) return;
    const updated = storyboard.scenes
      .filter((_, i) => i !== index)
      .map((scene, i) => ({ ...scene, scene_id: i + 1 }));
    setStoryboard({
      ...storyboard,
      scenes: updated,
      total_duration_estimate: updated.reduce((acc, s) => acc + (s.duration_sec || 18), 0)
    });
  };

  // Step 4: Trigger Video Render
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
      setJobStatus({ status: 'queued', progress: 0.05, message: 'Job registered with pipeline...' });
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 32px' }}>
      {/* Top Navbar */}
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingBottom: '20px',
          borderBottom: '1px solid var(--border-color)',
          marginBottom: '28px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 16px rgba(56, 189, 248, 0.3)'
            }}
          >
            <Video size={22} color="#090d16" strokeWidth={2.5} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
              Repo-to-Video
            </h1>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Interactive Codebase Onboarding & Narrative Video Director
            </p>
          </div>
        </div>

        {/* Global Controls & Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
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
            }}
          >
            <CheckCircle2 size={14} /> Gemini Audio / TTS Active
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 14px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '20px',
              fontSize: '0.8rem',
              color: 'var(--text-muted)'
            }}
          >
            <Sliders size={14} /> Default Style:
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
              <option value="3b1b" style={{ background: '#0f172a' }}>
                3Blue1Brown (Manim)
              </option>
              <option value="motion" style={{ background: '#0f172a' }}>
                Motion Graphics
              </option>
              <option value="tutorial" style={{ background: '#0f172a' }}>
                Developer Code-Walk
              </option>
            </select>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          padding: '6px',
          background: 'var(--bg-card)',
          borderRadius: '12px',
          border: '1px solid var(--border-color)',
          marginBottom: '28px'
        }}
      >
        <TabButton
          active={activeTab === 'ingest'}
          onClick={() => setActiveTab('ingest')}
          icon={<FolderGit2 size={16} />}
          label="1. Ingest & Scan"
          badge={digest ? `${digest.total_files} files` : null}
        />
        <TabButton
          active={activeTab === 'intake'}
          onClick={() => setActiveTab('intake')}
          icon={<Compass size={16} />}
          label="2. Director Intake (Length & Goals)"
          badge={intakeQuestions ? `${preferences.target_depth}` : null}
          disabled={!digest}
        />
        <TabButton
          active={activeTab === 'storyboard'}
          onClick={() => setActiveTab('storyboard')}
          icon={<Layers size={16} />}
          label="3. Storyboard & Script"
          badge={storyboard ? `${storyboard.scenes.length} scenes` : null}
          disabled={!storyboard}
        />
        <TabButton
          active={activeTab === 'render'}
          onClick={() => setActiveTab('render')}
          icon={<Video size={16} />}
          label="4. Video Player & Export"
          badge={jobStatus?.status === 'completed' ? 'Ready' : null}
        />
      </div>

      {/* Error Alert */}
      {errorMsg && (
        <div
          style={{
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
          }}
        >
          <AlertCircle size={18} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* TAB 1: Ingest & Scan */}
      {activeTab === 'ingest' && (
        <div className="fade-in">
          <div
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '16px',
              padding: '28px',
              marginBottom: '28px'
            }}
          >
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '8px' }}>
              Target Repository
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '20px' }}>
              Enter a GitHub URL or local repository path. We will scan its architecture and launch the Director Questionnaire to customize video length and key focus areas.
            </p>

            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <input
                type="text"
                value={repoTarget}
                onChange={(e) => setRepoTarget(e.target.value)}
                placeholder="e.g. https://github.com/fastapi/fastapi or ."
                style={{
                  flex: '1 1 340px',
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
                onClick={handleScanAndInterview}
                disabled={isScanning}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px 26px',
                  background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
                  color: '#090d16',
                  fontWeight: 700,
                  fontSize: '0.95rem',
                  border: 'none',
                  borderRadius: '10px',
                  cursor: isScanning ? 'wait' : 'pointer',
                  boxShadow: '0 4px 14px rgba(56, 189, 248, 0.25)'
                }}
              >
                {isScanning ? (
                  <>
                    <RefreshCw size={18} className="spin" /> Scanning Codebase...
                  </>
                ) : (
                  <>
                    <Compass size={18} /> Scan & Customize Video
                  </>
                )}
              </button>

              <button
                onClick={handleExpressAnalyze}
                disabled={isScanning}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px 20px',
                  background: '#1e293b',
                  color: 'var(--text-main)',
                  fontWeight: 600,
                  fontSize: '0.92rem',
                  border: '1px solid var(--border-color)',
                  borderRadius: '10px',
                  cursor: isScanning ? 'wait' : 'pointer'
                }}
                title="Skips the intake questions and uses standard defaults immediately."
              >
                <Sparkles size={16} color="var(--accent-blue)" /> Express 1-Click
              </button>
            </div>

            {/* Quick Presets */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '16px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Try Examples:</span>
              <PresetBadge label="Current Repo (d:\repo-to-video)" onClick={() => setRepoTarget('.')} />
              <PresetBadge label="fastapi/fastapi" onClick={() => setRepoTarget('https://github.com/fastapi/fastapi')} />
              <PresetBadge label="psf/requests" onClick={() => setRepoTarget('https://github.com/psf/requests')} />
            </div>
          </div>

          {/* Digest Output if already scanned */}
          {digest && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              <div
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '16px',
                  padding: '24px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FolderGit2 size={18} color="var(--accent-blue)" /> Directory Tree
                  </h3>
                  <span style={{ fontSize: '0.8rem', color: 'var(--accent-emerald)', fontWeight: 600 }}>
                    {digest.total_files} Files Detected
                  </span>
                </div>
                <pre
                  style={{
                    background: '#090d16',
                    padding: '16px',
                    borderRadius: '10px',
                    fontSize: '0.82rem',
                    color: '#93c5fd',
                    maxHeight: '340px',
                    overflowY: 'auto'
                  }}
                >
                  {digest.file_tree || 'No tree found'}
                </pre>
              </div>

              <div
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '16px',
                  padding: '24px'
                }}
              >
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                  <FileText size={18} color="var(--accent-indigo)" /> README Overview
                </h3>
                <div
                  style={{
                    background: '#090d16',
                    padding: '16px',
                    borderRadius: '10px',
                    fontSize: '0.85rem',
                    color: 'var(--text-muted)',
                    lineHeight: '1.6',
                    maxHeight: '340px',
                    overflowY: 'auto',
                    whiteSpace: 'pre-wrap'
                  }}
                >
                  {digest.readme_excerpt || 'No README excerpt found.'}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Director Intake (Interactive Questionnaire & Long Video Planning) */}
      {activeTab === 'intake' && digest && (
        <div className="fade-in">
          <div
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '16px',
              padding: '28px',
              marginBottom: '28px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
              <div>
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '4px 12px',
                    borderRadius: '20px',
                    background: 'rgba(56, 189, 248, 0.12)',
                    color: 'var(--accent-blue)',
                    fontSize: '0.78rem',
                    fontWeight: 700,
                    marginBottom: '8px'
                  }}
                >
                  <Compass size={14} /> AI DIRECTOR INTAKE INTERVIEW
                </span>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>
                  Customize Video Narrative & Depth for {digest.repo_name}
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>
                  Answer these quick questions so Gemini can plan the exact duration, audience perspective, and subsystems to spotlight.
                </p>
              </div>

              <button
                onClick={handlePlanStoryboard}
                disabled={isDrafting}
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
                  cursor: isDrafting ? 'wait' : 'pointer',
                  boxShadow: '0 4px 16px rgba(56, 189, 248, 0.3)'
                }}
              >
                {isDrafting ? (
                  <>
                    <RefreshCw size={18} className="spin" /> Generating Full Storyboard...
                  </>
                ) : (
                  <>
                    <Sparkles size={18} /> Plan Full Narrative ({preferences.scene_count} Scenes) <ArrowRight size={16} />
                  </>
                )}
              </button>
            </div>

            {/* QUESTION 1: Video Length & Depth Options */}
            <div style={{ marginBottom: '28px' }}>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.88rem',
                  fontWeight: 700,
                  color: 'var(--text-main)',
                  marginBottom: '12px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em'
                }}
              >
                1. Target Video Duration & Detail Level
              </label>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                {intakeQuestions?.depth_options?.map((opt) => {
                  const isSelected = preferences.target_depth === opt.id;
                  return (
                    <div
                      key={opt.id}
                      onClick={() => selectDepth(opt.id, opt.scenes)}
                      style={{
                        padding: '18px 20px',
                        borderRadius: '12px',
                        background: isSelected ? 'rgba(56, 189, 248, 0.1)' : '#090d16',
                        border: isSelected ? '2px solid var(--accent-blue)' : '1px solid var(--border-color)',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontWeight: 700, fontSize: '1rem', color: isSelected ? 'var(--accent-blue)' : 'var(--text-main)' }}>
                          {opt.label}
                        </span>
                        <span
                          style={{
                            padding: '3px 8px',
                            background: '#1e293b',
                            borderRadius: '6px',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            color: '#93c5fd'
                          }}
                        >
                          {opt.duration} • {opt.scenes} Scenes
                        </span>
                      </div>
                      <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                        {opt.description}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* QUESTION 2: Target Audience */}
            <div style={{ marginBottom: '28px' }}>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.88rem',
                  fontWeight: 700,
                  color: 'var(--text-main)',
                  marginBottom: '10px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em'
                }}
              >
                2. Target Audience Perspective
              </label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                {intakeQuestions?.audience_options?.map((aud) => {
                  const isSelected = preferences.target_audience === aud;
                  return (
                    <button
                      key={aud}
                      onClick={() => setPreferences({ ...preferences, target_audience: aud })}
                      style={{
                        padding: '8px 16px',
                        borderRadius: '8px',
                        background: isSelected ? 'var(--accent-indigo)' : '#090d16',
                        color: isSelected ? '#fff' : 'var(--text-muted)',
                        border: isSelected ? '1px solid var(--accent-indigo)' : '1px solid var(--border-color)',
                        fontSize: '0.85rem',
                        fontWeight: isSelected ? 700 : 500,
                        cursor: 'pointer'
                      }}
                    >
                      {aud}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* QUESTION 3: Key Subsystems to Spotlight */}
            <div style={{ marginBottom: '28px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <label
                  style={{
                    display: 'block',
                    fontSize: '0.88rem',
                    fontWeight: 700,
                    color: 'var(--text-main)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em'
                  }}
                >
                  3. Key Subsystems & Modules to Spotlight (Select to Focus)
                </label>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
                  {preferences.focus_areas.length} Selected
                </span>
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {intakeQuestions?.candidate_modules?.map((mod) => {
                  const isChecked = preferences.focus_areas.includes(mod);
                  return (
                    <button
                      key={mod}
                      onClick={() => toggleFocusModule(mod)}
                      style={{
                        padding: '6px 14px',
                        borderRadius: '6px',
                        background: isChecked ? 'rgba(52, 211, 153, 0.15)' : '#090d16',
                        border: isChecked ? '1px solid var(--accent-emerald)' : '1px solid var(--border-color)',
                        color: isChecked ? 'var(--accent-emerald)' : 'var(--text-muted)',
                        fontSize: '0.82rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                    >
                      {isChecked && <CheckCircle2 size={13} />}
                      {mod}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* QUESTION 4: Custom Creator Instructions */}
            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.88rem',
                  fontWeight: 700,
                  color: 'var(--text-main)',
                  marginBottom: '8px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em'
                }}
              >
                4. Custom Creator Directions or Special Highlights (Optional)
              </label>
              <textarea
                rows={2}
                value={preferences.custom_notes}
                onChange={(e) => setPreferences({ ...preferences, custom_notes: e.target.value })}
                placeholder="e.g. Focus especially on how the background music ducks under speech, or explain the request lifecycle step-by-step."
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  background: '#090d16',
                  border: '1px solid var(--border-color)',
                  borderRadius: '10px',
                  color: 'var(--text-main)',
                  fontSize: '0.9rem',
                  outline: 'none',
                  resize: 'vertical'
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Storyboard & Script Review */}
      {activeTab === 'storyboard' && storyboard && (
        <div className="fade-in">
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '20px',
              flexWrap: 'wrap',
              gap: '12px'
            }}
          >
            <div>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 800 }}>
                {storyboard.repo_name}: Onboarding Storyboard ({storyboard.scenes.length} Scenes)
              </h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                {storyboard.tagline} • Target: {storyboard.target_audience} • Est. Duration: ~{Math.round(storyboard.total_duration_estimate || 90)}s
              </p>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={handleAddScene}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '10px 18px',
                  background: '#1e293b',
                  color: 'var(--text-main)',
                  fontWeight: 600,
                  fontSize: '0.88rem',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  cursor: 'pointer'
                }}
              >
                <Plus size={15} /> Add Custom Scene
              </button>

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
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {storyboard.scenes.map((scene, idx) => (
              <div
                key={scene.scene_id || idx}
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '14px',
                  padding: '20px'
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '14px',
                    flexWrap: 'wrap',
                    gap: '10px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: '1 1 360px' }}>
                    <span
                      style={{
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
                      }}
                    >
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
                        width: '100%',
                        maxWidth: '480px'
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

                    <span
                      style={{
                        fontSize: '0.8rem',
                        color: 'var(--text-dim)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      <Clock size={13} /> ~{scene.duration_sec || 18}s
                    </span>

                    {storyboard.scenes.length > 1 && (
                      <button
                        onClick={() => handleDeleteScene(idx)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: '#f87171',
                          cursor: 'pointer',
                          padding: '4px',
                          display: 'flex',
                          alignItems: 'center'
                        }}
                        title="Delete Scene"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                </div>

                {/* Narration Script */}
                <div style={{ marginBottom: '14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <label
                      style={{
                        display: 'block',
                        fontSize: '0.78rem',
                        fontWeight: 600,
                        color: 'var(--text-muted)'
                      }}
                    >
                      VOICEOVER NARRATION SCRIPT (PURE SPOKEN SPEECH)
                    </label>
                    <span style={{ fontSize: '0.72rem', color: 'var(--accent-emerald)', fontWeight: 600 }}>
                      ✔ Clean Speech Only (Meta directions stripped)
                    </span>
                  </div>
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
                      {scene.diagram_nodes &&
                        scene.diagram_nodes.map((node, nIdx) => (
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

      {/* TAB 4: Video Player & Export */}
      {activeTab === 'render' && (
        <div className="fade-in">
          {/* Progress Card if Job Active */}
          {jobStatus && jobStatus.status !== 'completed' && jobStatus.status !== 'failed' && (
            <div
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-color)',
                borderRadius: '16px',
                padding: '32px',
                textAlign: 'center',
                marginBottom: '28px'
              }}
            >
              <div
                style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '50%',
                  background: 'rgba(56, 189, 248, 0.1)',
                  color: 'var(--accent-blue)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '16px'
                }}
              >
                <RefreshCw size={26} className="spin" />
              </div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '8px' }}>
                Rendering Onboarding Video...
              </h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '24px' }}>
                {jobStatus.message || 'Synthesizing voiceover, animating scenes, and ducking ambient music...'}
              </p>

              {/* Progress Bar */}
              <div
                style={{
                  width: '100%',
                  maxWidth: '640px',
                  height: '10px',
                  background: '#1e293b',
                  borderRadius: '9999px',
                  margin: '0 auto',
                  overflow: 'hidden'
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${Math.round((jobStatus.progress || 0.1) * 100)}%`,
                    background: 'linear-gradient(90deg, #38bdf8, #818cf8)',
                    transition: 'width 0.4s ease'
                  }}
                />
              </div>
              <div style={{ marginTop: '10px', fontSize: '0.82rem', color: 'var(--text-dim)' }}>
                {Math.round((jobStatus.progress || 0.1) * 100)}% Completed
              </div>
            </div>
          )}

          {/* Current Job Video Player when Complete */}
          {jobStatus?.status === 'completed' && jobStatus?.result && (
            <div
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-color)',
                borderRadius: '16px',
                padding: '28px',
                marginBottom: '32px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <div>
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '4px 10px',
                      borderRadius: '20px',
                      background: 'rgba(52, 211, 153, 0.15)',
                      color: 'var(--accent-emerald)',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      marginBottom: '6px'
                    }}
                  >
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
              <div
                style={{
                  position: 'relative',
                  borderRadius: '12px',
                  overflow: 'hidden',
                  background: '#000',
                  aspectRatio: '16/9',
                  maxHeight: '520px',
                  margin: '0 auto'
                }}
              >
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
                      <div
                        style={{
                          fontSize: '0.9rem',
                          fontWeight: 600,
                          color: 'var(--text-main)',
                          marginBottom: '8px',
                          wordBreak: 'break-all'
                        }}
                      >
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
        <span
          style={{
            padding: '2px 8px',
            background: active ? 'rgba(56, 189, 248, 0.2)' : '#090d16',
            color: active ? '#38bdf8' : '#94a3b8',
            borderRadius: '9999px',
            fontSize: '0.72rem',
            fontWeight: 700
          }}
        >
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
