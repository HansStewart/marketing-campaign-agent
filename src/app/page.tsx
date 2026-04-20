"use client";

import React, { useState, useRef, useEffect } from "react";

const API_BASE_URL =
  (process.env.NEXT_PUBLIC_API_BASE_URL as string | undefined) ??
  "http://localhost:8000";

type EmailItem = { subject: string; body: string; send_day: number };
type VariantScore = { variant: string; score: number; reasoning?: string };
type CampaignResponse = {
  best_variant?: string | null;
  all_variants?: string[] | null;
  evaluation_scores?: number[] | null;
  variant_scores?: VariantScore[] | null;
  best_variant_score?: number | null;
  email_sequence?: EmailItem[] | null;
};
type HistoryItem = { id: string; ts: string; platform: string };

const PLATFORMS = ["LinkedIn", "Instagram", "Facebook", "Email", "SMS", "Google Ad", "Cold DM", "Twitter/X", "YouTube", "TikTok"];
const TONES = ["Professional", "Conversational", "Authoritative", "Urgent", "Empathetic", "Bold", "Story-Driven", "Witty", "Minimalist"];
const FORMATS = ["short_post", "long_post", "story", "email", "sms", "ad_copy", "cold_dm", "thread"];
const FORMAT_LABELS: Record<string, string> = {
  short_post: "Short Post", long_post: "Long Post", story: "Story",
  email: "Email", sms: "SMS", ad_copy: "Ad Copy", cold_dm: "Cold DM", thread: "Thread"
};
const FORMAT_ICONS: Record<string, string> = {
  short_post: "▪", long_post: "▬", story: "◯", email: "□",
  sms: "◷", ad_copy: "◈", cold_dm: "◫", thread: "≡"
};
const INDUSTRIES = [
  "Technology & SaaS", "E-Commerce & Retail", "Finance & Fintech",
  "Healthcare & Wellness", "Education & Coaching", "Real Estate",
  "Food & Beverage", "Travel & Hospitality", "Creative & Media",
  "Professional Services", "Non-Profit", "Other"
];
const REFINE_SUGGESTIONS = [
  "Make it shorter", "Make it longer", "Change CTA to book a call",
  "Make the hook stronger", "More conversational tone", "Add more urgency",
  "Focus more on the pain point", "Simplify the language",
];

export default function MarketingCampaignAgent() {
  const [platform, setPlatform] = useState<string[]>([]);
  const [industry, setIndustry] = useState("");
  const [audience, setAudience] = useState("");
  const [offer, setOffer] = useState("");
  const [brief, setBrief] = useState("");
  const [persona, setPersona] = useState({ name: "", role: "", pain: "" });
  const [tone, setTone] = useState<string[]>([]);
  const [formats, setFormats] = useState<string[]>([]);
  const [variants, setVariants] = useState(3);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [fileContext, setFileContext] = useState("");
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CampaignResponse | null>(null);
  const [allVariants, setAllVariants] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [refinementText, setRefinementText] = useState<Record<number, string>>({});
  const [refining, setRefining] = useState<Record<number, boolean>>({});
  const [refineError, setRefineError] = useState<Record<number, string>>({});
  const [refineOpen, setRefineOpen] = useState<Record<number, boolean>>({});
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/history`)
      .then(r => r.json())
      .then(d => setHistory(d.history || []))
      .catch(() => {});
  }, []);

  function toggleItem(arr: string[], val: string, set: React.Dispatch<React.SetStateAction<string[]>>) {
    if (arr.includes(val)) set(arr.filter(x => x !== val));
    else set([...arr, val]);
  }

  const handleFileUpload = async (file: File) => {
    setUploading(true);
    setUploadedFile(file);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API_BASE_URL}/upload`, { method: "POST", body: formData });
      const data = await res.json();
      if (data.text_content) setFileContext(data.text_content);
    } catch {
      // file uploaded but no text extracted
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async () => {
    if (!platform.length || !audience || !offer || !brief) {
      setError("Required: select at least one channel, and fill in audience, offer, and brief.");
      return;
    }
    setLoading(true); setError(""); setResult(null); setAllVariants([]); setActiveTab(0);
    setRefinementText({}); setRefining({}); setRefineError({}); setRefineOpen({});
    try {
      const res = await fetch(`${API_BASE_URL}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          platform: platform.join(", "),
          industry,
          target_audience: audience,
          offer,
          campaign_brief: brief,
          persona_name: persona.name,
          persona_role: persona.role,
          persona_pain: persona.pain,
          tone: tone.join(", "),
          output_formats: formats,
          num_variants: variants,
          file_context: fileContext,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setResult(data);
      setAllVariants(data.all_variants || []);
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
      fetch(`${API_BASE_URL}/history`).then(r => r.json()).then(d => setHistory(d.history || [])).catch(() => {});
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleRefine = async (index: number) => {
    const instruction = refinementText[index]?.trim();
    if (!instruction) return;
    setRefining(prev => ({ ...prev, [index]: true }));
    setRefineError(prev => ({ ...prev, [index]: "" }));
    try {
      const res = await fetch(`${API_BASE_URL}/refine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          variant: allVariants[index],
          instruction,
          platform: platform.join(", "),
          target_audience: audience,
          offer,
          campaign_brief: brief,
          tone: tone.join(", "),
          industry,
          file_context: fileContext,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setAllVariants(prev => {
        const updated = [...prev];
        updated[index] = data.refined_variant;
        return updated;
      });
      setRefinementText(prev => ({ ...prev, [index]: "" }));
      setRefineOpen(prev => ({ ...prev, [index]: false }));
    } catch (e: unknown) {
      setRefineError(prev => ({
        ...prev,
        [index]: e instanceof Error ? e.message : "Refinement failed. Try again.",
      }));
    } finally {
      setRefining(prev => ({ ...prev, [index]: false }));
    }
  };

  const scores = result?.variant_scores || [];

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

        :root {
          --bg: #0b0a09;
          --s1: #111009;
          --s2: #161412;
          --s3: #1c1916;
          --s4: #221f1b;
          --b1: rgba(210,185,155,0.04);
          --b2: rgba(210,185,155,0.09);
          --b3: rgba(210,185,155,0.16);
          --copper: #c4844e;
          --copper-lt: #d49a68;
          --copper-dim: rgba(196,132,78,0.09);
          --copper-border: rgba(196,132,78,0.28);
          --copper-glow: rgba(196,132,78,0.15);
          --text: #ede6da;
          --text2: #b8af9f;
          --muted: #7a7168;
          --mono: "JetBrains Mono", monospace;
          --sans: "Space Grotesk", system-ui, sans-serif;
          --r: 0.625rem;
          --r-sm: 0.375rem;
        }

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        html { -webkit-font-smoothing: antialiased; scroll-behavior: smooth; }

        body {
          background: var(--bg);
          color: var(--text);
          font-family: var(--sans);
          font-size: 15px;
          line-height: 1.6;
          min-height: 100dvh;
          overflow-x: hidden;
        }

        body::after {
          content: "";
          position: fixed;
          inset: 0;
          background:
            radial-gradient(ellipse 70% 50% at 50% -10%, rgba(196,132,78,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(196,132,78,0.04) 0%, transparent 60%);
          pointer-events: none;
          z-index: 0;
        }

        @keyframes fadeUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }
        @keyframes scanline { 0% { transform: translateY(0); } 100% { transform: translateY(90px); } }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes slideDown { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }

        .nav {
          position: fixed; top: 0; left: 0; right: 0; z-index: 100;
          background: rgba(11,10,9,0.92);
          backdrop-filter: blur(20px);
          border-bottom: 1px solid var(--b2);
          height: 52px;
          display: flex; align-items: center;
        }
        .nav-inner {
          max-width: 1040px; margin: 0 auto; padding: 0 1.75rem;
          width: 100%; display: flex; align-items: center; justify-content: space-between;
        }
        .nav-brand { display: flex; align-items: center; gap: 0.75rem; text-decoration: none; }
        .nav-brand-mark {
          width: 26px; height: 26px;
          border: 1.5px solid var(--copper-border);
          border-radius: 6px;
          display: flex; align-items: center; justify-content: center;
          font-family: var(--mono); font-size: 0.65rem; font-weight: 700;
          color: var(--copper); background: var(--copper-dim);
        }
        .nav-brand-text {
          font-family: var(--mono); font-size: 0.7rem; font-weight: 600;
          color: var(--text2); letter-spacing: 0.08em; text-transform: uppercase;
        }
        .nav-right { display: flex; align-items: center; gap: 0.5rem; }
        .nav-pill {
          font-family: var(--mono); font-size: 0.65rem; color: var(--muted);
          background: none; border: 1px solid var(--b2);
          padding: 0.28rem 0.75rem; border-radius: 999px;
          cursor: pointer; letter-spacing: 0.08em; text-transform: uppercase;
          transition: color 0.18s, border-color 0.18s;
          text-decoration: none; display: inline-block;
        }
        .nav-pill:hover { color: var(--copper); border-color: var(--copper-border); }

        .page { max-width: 1040px; margin: 0 auto; padding: 72px 1.75rem 5rem; position: relative; z-index: 1; }

        .hero {
          padding: 3.5rem 0 2.5rem;
          display: flex; align-items: flex-end; justify-content: space-between; gap: 2rem;
          border-bottom: 1px solid var(--b1);
          margin-bottom: 2.5rem;
          animation: fadeUp 0.5s ease both;
        }
        .hero-left { flex: 1; }
        .hero-eyebrow {
          font-family: var(--mono); font-size: 0.62rem; font-weight: 500;
          color: var(--copper); letter-spacing: 0.2em; text-transform: uppercase;
          margin-bottom: 0.9rem;
          display: flex; align-items: center; gap: 0.6rem;
        }
        .hero-eyebrow::before { content: ""; display: block; width: 20px; height: 1px; background: var(--copper); }
        .hero h1 {
          font-family: var(--mono);
          font-size: clamp(2rem, 4vw, 2.9rem);
          font-weight: 700; line-height: 1.05;
          letter-spacing: -0.04em; color: var(--text); margin-bottom: 1rem;
        }
        .hero h1 em { color: var(--copper); font-style: normal; }
        .hero-sub { font-size: 0.9rem; color: var(--muted); max-width: 46ch; line-height: 1.7; }
        .hero-stats { display: flex; flex-direction: column; gap: 0.5rem; align-items: flex-end; flex-shrink: 0; }
        .hero-stat {
          font-family: var(--mono); font-size: 0.62rem; color: var(--muted);
          letter-spacing: 0.1em; text-transform: uppercase;
          display: flex; align-items: center; gap: 0.5rem;
        }
        .hero-stat-dot { width: 4px; height: 4px; background: var(--copper); border-radius: 50%; animation: pulse 2.5s ease infinite; }

        .steps {
          display: grid; grid-template-columns: repeat(7, 1fr);
          gap: 0; margin-bottom: 2rem;
          border: 1px solid var(--b2); border-radius: var(--r);
          overflow: hidden; animation: fadeUp 0.5s ease 0.1s both;
        }
        .step {
          padding: 0.75rem 0.6rem;
          border-right: 1px solid var(--b2);
          display: flex; flex-direction: column; align-items: center; gap: 0.3rem;
        }
        .step:last-child { border-right: none; }
        .step-num { font-family: var(--mono); font-size: 0.55rem; color: var(--muted); letter-spacing: 0.1em; }
        .step-label { font-family: var(--mono); font-size: 0.6rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; text-align: center; }
        .step.done .step-num, .step.done .step-label { color: var(--copper); }
        .step.done { background: var(--copper-dim); }

        .card {
          background: var(--s1); border: 1px solid var(--b2);
          border-radius: var(--r); padding: 1.75rem;
          margin-bottom: 0.875rem; animation: fadeUp 0.5s ease 0.15s both;
        }

        .sec { margin-bottom: 1.75rem; }
        .sec:last-child { margin-bottom: 0; }
        .sec-head { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
        .sec-num { font-family: var(--mono); font-size: 0.58rem; color: var(--muted); letter-spacing: 0.1em; min-width: 2.5rem; }
        .sec-title { font-family: var(--mono); font-size: 0.65rem; font-weight: 600; color: var(--text2); letter-spacing: 0.12em; text-transform: uppercase; flex: 1; }
        .sec-divider { flex: 1; height: 1px; background: var(--b2); max-width: 100%; }

        .chips { display: flex; flex-wrap: wrap; gap: 0.4rem; }
        .chip {
          font-family: var(--mono); font-size: 0.68rem; font-weight: 500;
          color: var(--muted); background: var(--s2); border: 1px solid var(--b2);
          padding: 0.38rem 0.8rem; border-radius: 999px; cursor: pointer;
          letter-spacing: 0.05em;
          transition: color 0.15s, border-color 0.15s, background 0.15s;
          -webkit-user-select: none; user-select: none;
          appearance: none; -webkit-appearance: none; line-height: 1.4; outline: none;
        }
        .chip:hover { color: var(--text); border-color: var(--b3); }
        .chip.on { color: var(--copper); border-color: var(--copper-border); background: var(--copper-dim); }

        .g2 { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 0.75rem; }
        .g3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.75rem; }

        .field { display: flex; flex-direction: column; gap: 0.3rem; }
        .lbl { font-family: var(--mono); font-size: 0.58rem; color: var(--muted); letter-spacing: 0.12em; text-transform: uppercase; }
        .inp, .sel, .ta {
          width: 100%; background: var(--s2); border: 1px solid var(--b2);
          border-radius: var(--r-sm); padding: 0.72rem 0.9rem;
          font-family: var(--mono); font-size: 0.82rem; color: var(--text);
          outline: none; transition: border-color 0.18s, box-shadow 0.18s, background 0.18s;
        }
        .inp::placeholder, .ta::placeholder { color: var(--muted); }
        .inp:focus, .sel:focus, .ta:focus {
          border-color: var(--copper-border);
          box-shadow: 0 0 0 3px var(--copper-glow);
          background: var(--s3);
        }
        .sel { appearance: none; cursor: pointer; }
        .sel option { background: var(--s2); color: var(--text); }
        .ta { resize: vertical; min-height: 84px; line-height: 1.65; }

        .fmt-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.45rem; }
        .fmt-item { position: relative; }
        .fmt-item input { position: absolute; opacity: 0; width: 0; height: 0; }
        .fmt-lbl {
          display: flex; flex-direction: column; align-items: center; gap: 0.25rem;
          background: var(--s2); border: 1px solid var(--b2);
          border-radius: var(--r-sm); padding: 0.65rem 0.35rem;
          cursor: pointer; text-align: center;
          transition: border-color 0.15s, background 0.15s, transform 0.1s;
          user-select: none;
        }
        .fmt-lbl:hover { border-color: var(--b3); transform: translateY(-1px); }
        .fmt-item input:checked + .fmt-lbl { border-color: var(--copper-border); background: var(--copper-dim); }
        .fmt-icon { font-size: 0.9rem; color: var(--muted); line-height: 1; }
        .fmt-item input:checked + .fmt-lbl .fmt-icon { color: var(--copper); }
        .fmt-name { font-family: var(--mono); font-size: 0.55rem; color: var(--muted); letter-spacing: 0.06em; text-transform: uppercase; }
        .fmt-item input:checked + .fmt-lbl .fmt-name { color: var(--copper); }

        .upload-zone {
          display: flex; flex-direction: column; align-items: center; justify-content: center;
          gap: 0.5rem; background: var(--s2); border: 1.5px dashed var(--b3);
          border-radius: var(--r); padding: 2rem 1rem;
          cursor: pointer; transition: border-color 0.18s, background 0.18s;
          text-align: center; position: relative;
        }
        .upload-zone:hover { border-color: var(--copper-border); background: var(--s3); }
        .upload-zone.has-file { border-color: var(--copper-border); background: var(--copper-dim); border-style: solid; }
        .upload-icon { font-size: 1.4rem; color: var(--muted); line-height: 1; transition: color 0.18s; }
        .upload-zone.has-file .upload-icon { color: var(--copper); }
        .upload-title { font-family: var(--mono); font-size: 0.72rem; font-weight: 600; color: var(--text2); letter-spacing: 0.06em; transition: color 0.18s; }
        .upload-zone.has-file .upload-title { color: var(--copper); }
        .upload-sub { font-family: var(--mono); font-size: 0.6rem; color: var(--muted); max-width: 40ch; line-height: 1.5; }
        .upload-badge {
          display: inline-flex; align-items: center; gap: 0.4rem;
          background: var(--copper-dim); border: 1px solid var(--copper-border);
          border-radius: 999px; padding: 0.2rem 0.65rem;
          font-family: var(--mono); font-size: 0.6rem; color: var(--copper); letter-spacing: 0.06em;
        }
        .upload-remove {
          background: none; border: none; font-family: var(--mono); font-size: 0.6rem;
          color: var(--muted); cursor: pointer; text-decoration: underline;
          margin-top: 0.25rem; padding: 0; letter-spacing: 0.06em; transition: color 0.15s;
        }
        .upload-remove:hover { color: var(--copper); }
        .upload-spinner {
          width: 14px; height: 14px; border: 1.5px solid var(--b3);
          border-top-color: var(--copper); border-radius: 50%;
          animation: spin 0.7s linear infinite; display: inline-block;
        }

        .range-row { display: flex; align-items: center; gap: 1rem; }
        .range { flex: 1; -webkit-appearance: none; appearance: none; height: 2px; background: var(--b3); border-radius: 999px; outline: none; cursor: pointer; }
        .range::-webkit-slider-thumb { -webkit-appearance: none; width: 14px; height: 14px; background: var(--copper); border-radius: 50%; box-shadow: 0 0 0 3px var(--copper-dim); }
        .range-val { font-family: var(--mono); font-size: 1rem; font-weight: 700; color: var(--copper); min-width: 1.2rem; text-align: center; }

        .btn-generate {
          width: 100%; display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem;
          background: var(--copper); color: #0b0a09;
          font-family: var(--mono); font-size: 0.78rem; font-weight: 700;
          letter-spacing: 0.14em; text-transform: uppercase;
          padding: 0.9rem 1.5rem; border-radius: var(--r-sm);
          border: none; cursor: pointer;
          transition: opacity 0.18s, transform 0.14s, box-shadow 0.14s;
        }
        .btn-generate:hover { opacity: 0.9; transform: translateY(-1px); box-shadow: 0 12px 32px rgba(0,0,0,0.5); }
        .btn-generate:active { transform: none; box-shadow: none; opacity: 1; }
        .btn-generate:disabled { opacity: 0.3; cursor: not-allowed; transform: none; box-shadow: none; }
        .hint { font-family: var(--mono); font-size: 0.62rem; color: var(--muted); margin-top: 0.5rem; text-align: center; }
        .err {
          background: rgba(220,80,60,0.06); border: 1px solid rgba(220,80,60,0.2);
          border-radius: var(--r); padding: 0.9rem 1.1rem; margin-top: 0.75rem;
          font-family: var(--mono); font-size: 0.78rem; color: #ffcdc5;
          animation: fadeUp 0.3s ease;
        }

        .loading { padding: 3.5rem 0; text-align: center; animation: fadeUp 0.4s ease; }
        .loader-box { width: 180px; height: 100px; margin: 0 auto 1.5rem; border: 1px solid var(--copper-border); border-radius: 14px; background: var(--s1); overflow: hidden; position: relative; }
        .loader-scan { position: absolute; left: 0; right: 0; height: 1.5px; background: linear-gradient(90deg, transparent, var(--copper), transparent); box-shadow: 0 0 8px var(--copper-glow); animation: scanline 1.6s ease-in-out infinite alternate; }
        .loader-label { font-family: var(--mono); font-size: 0.72rem; color: var(--copper); letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 0.5rem; }
        .dots span { display: inline-block; width: 4px; height: 4px; background: var(--copper); border-radius: 50%; margin: 0 2px; animation: pulse 1s ease infinite; }
        .dots span:nth-child(2) { animation-delay: 0.18s; }
        .dots span:nth-child(3) { animation-delay: 0.36s; }

        .results { animation: fadeUp 0.45s ease both; }
        .results-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 0.75rem; }
        .results-title { font-family: var(--mono); font-size: 0.65rem; font-weight: 600; color: var(--copper); letter-spacing: 0.16em; text-transform: uppercase; }
        .results-meta { font-family: var(--mono); font-size: 0.65rem; color: var(--muted); }
        .results-meta b { color: var(--copper); font-weight: 600; }
        .tabs { display: flex; gap: 0.35rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
        .tab {
          font-family: var(--mono); font-size: 0.65rem; color: var(--muted);
          background: var(--s2); border: 1px solid var(--b2);
          padding: 0.3rem 0.8rem; border-radius: 999px; cursor: pointer;
          letter-spacing: 0.08em; text-transform: uppercase;
          transition: color 0.15s, border-color 0.15s, background 0.15s;
        }
        .tab:hover { color: var(--text); border-color: var(--b3); }
        .tab.on { color: var(--copper); border-color: var(--copper-border); background: var(--copper-dim); }
        .output-box {
          background: var(--s2); border: 1px solid var(--b2); border-radius: var(--r);
          padding: 1.5rem; white-space: pre-wrap;
          font-family: var(--mono); font-size: 0.8rem; color: var(--text);
          line-height: 1.8; max-height: 400px; overflow-y: auto;
        }
        .output-box::-webkit-scrollbar { width: 4px; }
        .output-box::-webkit-scrollbar-thumb { background: var(--b3); border-radius: 999px; }
        .score-wrap { margin-top: 0.75rem; }
        .score-row { display: flex; justify-content: space-between; font-family: var(--mono); font-size: 0.62rem; color: var(--muted); margin-bottom: 0.3rem; }
        .score-row b { color: var(--copper); font-weight: 600; }
        .score-bar { height: 2px; background: var(--b2); border-radius: 999px; overflow: hidden; }
        .score-fill { height: 100%; background: var(--copper); border-radius: 999px; transition: width 0.7s ease; }
        .score-reason { font-family: var(--mono); font-size: 0.68rem; color: var(--muted); margin-top: 0.5rem; line-height: 1.65; }

        /* REFINE */
        .refine-toggle {
          width: 100%; display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem;
          background: var(--copper-dim); color: var(--copper);
          border: 1px solid var(--copper-border);
          font-family: var(--mono); font-size: 0.72rem; font-weight: 600;
          letter-spacing: 0.12em; text-transform: uppercase;
          padding: 0.72rem 1.25rem; border-radius: var(--r-sm);
          cursor: pointer; margin-top: 1rem;
          transition: background 0.18s, color 0.18s, transform 0.12s;
        }
        .refine-toggle:hover { background: var(--copper); color: #0b0a09; transform: translateY(-1px); }
        .refine-toggle:active { transform: none; }

        .refine-panel {
          margin-top: 0.75rem;
          background: var(--s3);
          border: 1px solid var(--b2);
          border-radius: var(--r);
          padding: 1.25rem 1.5rem;
          animation: slideDown 0.25s ease both;
        }

        .refine-section-label {
          font-family: var(--mono); font-size: 0.58rem; font-weight: 600;
          color: var(--muted); letter-spacing: 0.16em; text-transform: uppercase;
          margin-bottom: 0.5rem;
        }

        .refine-desc {
          font-family: var(--mono); font-size: 0.68rem; color: var(--muted);
          line-height: 1.7; margin-bottom: 1rem;
          padding: 0.65rem 0.9rem;
          background: var(--s2); border: 1px solid var(--b1);
          border-radius: var(--r-sm);
        }

        .refine-suggestions { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-bottom: 1.25rem; }
        .refine-suggestion {
          font-family: var(--mono); font-size: 0.6rem; color: var(--muted);
          background: var(--s2); border: 1px solid var(--b2);
          padding: 0.28rem 0.7rem; border-radius: 999px; cursor: pointer;
          letter-spacing: 0.04em;
          transition: color 0.15s, border-color 0.15s, background 0.15s;
        }
        .refine-suggestion:hover { color: var(--copper); border-color: var(--copper-border); background: var(--copper-dim); }

        .refine-guided-grid {
          display: grid; grid-template-columns: 1fr 1fr; gap: 0.65rem;
          margin-bottom: 1.25rem;
        }

        .refine-full-label {
          font-family: var(--mono); font-size: 0.58rem; color: var(--muted);
          letter-spacing: 0.12em; text-transform: uppercase;
          margin-bottom: 0.35rem;
        }
        .refine-full-hint {
          font-family: var(--mono); font-size: 0.58rem; color: var(--muted);
          margin-top: 0.3rem; opacity: 0.65;
        }

        .refine-textarea {
          width: 100%; background: var(--s2); border: 1px solid var(--b2);
          border-radius: var(--r-sm); padding: 0.85rem 1rem;
          font-family: var(--mono); font-size: 0.8rem; color: var(--text);
          outline: none; resize: vertical; min-height: 160px; line-height: 1.75;
          transition: border-color 0.18s, box-shadow 0.18s, background 0.18s;
        }
        .refine-textarea::placeholder { color: var(--muted); opacity: 0.7; }
        .refine-textarea:focus {
          border-color: var(--copper-border);
          box-shadow: 0 0 0 3px var(--copper-glow);
          background: var(--s4);
        }

        .refine-actions {
          display: flex; align-items: center; justify-content: space-between;
          margin-top: 0.75rem; gap: 0.5rem; flex-wrap: wrap;
        }
        .refine-char-count {
          font-family: var(--mono); font-size: 0.6rem; color: var(--muted);
        }
        .refine-action-btns { display: flex; gap: 0.45rem; }

        .btn-refine {
          display: inline-flex; align-items: center; justify-content: center; gap: 0.4rem;
          background: var(--copper); color: #0b0a09;
          border: none;
          font-family: var(--mono); font-size: 0.72rem; font-weight: 700;
          letter-spacing: 0.12em; text-transform: uppercase;
          padding: 0.65rem 1.25rem; border-radius: var(--r-sm);
          cursor: pointer;
          transition: opacity 0.18s, transform 0.12s;
        }
        .btn-refine:hover { opacity: 0.88; transform: translateY(-1px); }
        .btn-refine:active { transform: none; opacity: 1; }
        .btn-refine:disabled { opacity: 0.3; cursor: not-allowed; transform: none; }

        .btn-clear {
          font-family: var(--mono); font-size: 0.65rem; color: var(--muted);
          background: var(--s2); border: 1px solid var(--b2);
          padding: 0.62rem 0.9rem; border-radius: var(--r-sm); cursor: pointer;
          letter-spacing: 0.08em; text-transform: uppercase;
          transition: color 0.15s, border-color 0.15s;
        }
        .btn-clear:hover { color: var(--copper); border-color: var(--copper-border); }

        .refine-spinner {
          width: 11px; height: 11px; border: 1.5px solid rgba(196,132,78,0.3);
          border-top-color: #0b0a09; border-radius: 50%;
          animation: spin 0.7s linear infinite; display: inline-block;
        }
        .refine-err { font-family: var(--mono); font-size: 0.7rem; color: #ffcdc5; margin-top: 0.65rem; }

        .refine-divider {
          height: 1px; background: var(--b2); margin: 1.1rem 0;
        }

        .email-item { background: var(--s2); border: 1px solid var(--b2); border-radius: var(--r); padding: 1.25rem 1.5rem; margin-bottom: 0.7rem; }
        .email-meta { font-family: var(--mono); font-size: 0.6rem; color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.45rem; }
        .email-subj { font-family: var(--mono); font-size: 0.85rem; font-weight: 600; color: var(--copper); margin-bottom: 0.7rem; }
        .email-body { font-family: var(--sans); font-size: 0.87rem; color: var(--text); line-height: 1.75; white-space: pre-wrap; }
        .copy-btn {
          font-family: var(--mono); font-size: 0.6rem; color: var(--muted);
          background: var(--s1); border: 1px solid var(--b2);
          padding: 0.28rem 0.7rem; border-radius: 999px; cursor: pointer;
          letter-spacing: 0.08em; text-transform: uppercase;
          transition: color 0.15s, border-color 0.15s;
        }
        .copy-btn:hover { color: var(--copper); border-color: var(--copper-border); }

        .drawer {
          position: fixed; top: 0; right: 0; bottom: 0; width: 300px;
          background: var(--s1); border-left: 1px solid var(--b2);
          z-index: 300; padding: 1.5rem; overflow-y: auto;
          transform: translateX(100%); transition: transform 0.28s ease;
          box-shadow: -20px 0 60px rgba(0,0,0,0.5);
        }
        .drawer.open { transform: translateX(0); }
        .drawer-head {
          font-family: var(--mono); font-size: 0.65rem; font-weight: 600;
          color: var(--copper); letter-spacing: 0.14em; text-transform: uppercase;
          margin-bottom: 1.25rem; padding-bottom: 0.7rem; border-bottom: 1px solid var(--b1);
          display: flex; align-items: center; justify-content: space-between;
        }
        .drawer-close { background: none; border: none; color: var(--muted); cursor: pointer; font-size: 1rem; line-height: 1; }
        .hist-item { background: var(--s2); border: 1px solid var(--b2); border-radius: var(--r-sm); padding: 0.7rem 0.9rem; margin-bottom: 0.45rem; }
        .hist-platform { font-family: var(--mono); font-size: 0.7rem; color: var(--copper); margin-bottom: 0.2rem; }
        .hist-ts { font-family: var(--mono); font-size: 0.6rem; color: var(--muted); }

        .footer { text-align: center; padding: 2rem 0; border-top: 1px solid var(--b1); margin-top: 2rem; }
        .footer p { font-family: var(--mono); font-size: 0.62rem; color: var(--muted); letter-spacing: 0.08em; }

        @media (max-width: 680px) {
          .hero { flex-direction: column; align-items: flex-start; }
          .hero-stats { flex-direction: row; align-items: flex-start; }
          .steps { grid-template-columns: repeat(4, 1fr); }
          .g2, .g3, .refine-guided-grid { grid-template-columns: 1fr; }
          .fmt-grid { grid-template-columns: repeat(2, 1fr); }
          .page { padding: 64px 1rem 4rem; }
          .card { padding: 1.25rem; }
          .drawer { width: 100%; }
          .refine-actions { flex-direction: column; align-items: flex-start; }
          .refine-action-btns { width: 100%; }
          .btn-refine, .btn-clear { flex: 1; }
        }
      `}</style>

      {/* NAV */}
      <nav className="nav">
        <div className="nav-inner">
          <a href="/" className="nav-brand">
            <div className="nav-brand-mark">MC</div>
            <span className="nav-brand-text">Campaign Agent</span>
          </a>
          <div className="nav-right">
            <button type="button" className="nav-pill" onClick={() => setHistoryOpen(true)}>History</button>
          </div>
        </div>
      </nav>

      {/* HISTORY DRAWER */}
      <div className={`drawer ${historyOpen ? "open" : ""}`} role="dialog" aria-label="Campaign history">
        <div className="drawer-head">
          <span>History</span>
          <button type="button" className="drawer-close" onClick={() => setHistoryOpen(false)} aria-label="Close">✕</button>
        </div>
        {history.length === 0
          ? <p style={{ fontFamily: "var(--mono)", fontSize: "0.75rem", color: "var(--muted)" }}>No history yet.</p>
          : history.map(h => (
            <div key={h.id} className="hist-item">
              <div className="hist-platform">{h.platform}</div>
              <div className="hist-ts">{h.ts}</div>
            </div>
          ))}
      </div>

      <div className="page">

        {/* HERO */}
        <header className="hero">
          <div className="hero-left">
            <div className="hero-eyebrow">Multi-Agent Pipeline</div>
            <h1>Marketing Copy,<br /><em>Generated.</em></h1>
            <p className="hero-sub">Select your channels, define your brief, upload context files. The agent pipeline writes, evaluates, and ranks per-channel variants.</p>
          </div>
          <div className="hero-stats">
            <div className="hero-stat"><div className="hero-stat-dot" />Multi-channel support</div>
            <div className="hero-stat"><div className="hero-stat-dot" style={{ animationDelay: "0.4s" }} />Per-format variants</div>
            <div className="hero-stat"><div className="hero-stat-dot" style={{ animationDelay: "0.8s" }} />Inline refinement</div>
          </div>
        </header>

        {/* STEP INDICATOR */}
        <div className="steps">
          {[
            ["01", "Channel"], ["02", "Brief"], ["03", "Persona"],
            ["04", "Tone"], ["05", "Format"], ["06", "Files"], ["07", "Generate"],
          ].map(([n, l], i) => {
            const filled =
              (i === 0 && platform.length > 0) ||
              (i === 1 && !!(audience && offer && brief)) ||
              (i === 2 && !!(persona.name || persona.role || persona.pain)) ||
              (i === 3 && tone.length > 0) ||
              (i === 4 && formats.length > 0) ||
              (i === 5 && !!uploadedFile);
            return (
              <div key={n} className={`step ${filled ? "done" : ""}`}>
                <span className="step-num">{n}</span>
                <span className="step-label">{l}</span>
              </div>
            );
          })}
        </div>

        {/* FORM */}
        <div className="card">

          {/* 01 CHANNEL */}
          <div className="sec">
            <div className="sec-head">
              <span className="sec-num">01</span>
              <span className="sec-title">Channel &amp; Industry</span>
              <div className="sec-divider" />
            </div>
            <div className="chips" style={{ marginBottom: "0.75rem" }}>
              {PLATFORMS.map(p => (
                <button key={p} type="button" className={`chip${platform.includes(p) ? " on" : ""}`}
                  onClick={() => toggleItem(platform, p, setPlatform)}>{p}</button>
              ))}
            </div>
            <div className="field">
              <label className="lbl">Industry (optional)</label>
              <select className="sel" value={industry} onChange={e => setIndustry(e.target.value)}>
                <option value="">Select industry</option>
                {INDUSTRIES.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </div>
          </div>

          {/* 02 BRIEF */}
          <div className="sec">
            <div className="sec-head">
              <span className="sec-num">02</span>
              <span className="sec-title">Campaign Brief</span>
              <div className="sec-divider" />
            </div>
            <div className="g2">
              <div className="field">
                <label className="lbl">Target Audience *</label>
                <input className="inp" placeholder="e.g. B2B marketing managers" value={audience} onChange={e => setAudience(e.target.value)} />
              </div>
              <div className="field">
                <label className="lbl">Offer / Product *</label>
                <input className="inp" placeholder="e.g. project management tool" value={offer} onChange={e => setOffer(e.target.value)} />
              </div>
            </div>
            <div className="field">
              <label className="lbl">Campaign Brief *</label>
              <textarea className="ta"
                placeholder="e.g. Launch campaign for Q3. Goal is signups. Highlight time savings and ease of use. Avoid technical jargon."
                value={brief} onChange={e => setBrief(e.target.value)} />
            </div>
          </div>

          {/* 03 PERSONA */}
          <div className="sec">
            <div className="sec-head">
              <span className="sec-num">03</span>
              <span className="sec-title">Target Persona</span>
              <div className="sec-divider" />
            </div>
            <div className="g3">
              <div className="field">
                <label className="lbl">First Name</label>
                <input className="inp" placeholder="e.g. Sarah" value={persona.name} onChange={e => setPersona({ ...persona, name: e.target.value })} />
              </div>
              <div className="field">
                <label className="lbl">Job Title</label>
                <input className="inp" placeholder="e.g. Ops Director" value={persona.role} onChange={e => setPersona({ ...persona, role: e.target.value })} />
              </div>
              <div className="field">
                <label className="lbl">Core Pain Point</label>
                <input className="inp" placeholder="e.g. missed deadlines" value={persona.pain} onChange={e => setPersona({ ...persona, pain: e.target.value })} />
              </div>
            </div>
          </div>

          {/* 04 TONE */}
          <div className="sec">
            <div className="sec-head">
              <span className="sec-num">04</span>
              <span className="sec-title">Tone &amp; Voice</span>
              <div className="sec-divider" />
            </div>
            <div className="chips">
              {TONES.map(t => (
                <button key={t} type="button" className={`chip${tone.includes(t) ? " on" : ""}`}
                  onClick={() => toggleItem(tone, t, setTone)}>{t}</button>
              ))}
            </div>
          </div>

          {/* 05 FORMATS */}
          <div className="sec">
            <div className="sec-head">
              <span className="sec-num">05</span>
              <span className="sec-title">Output Formats</span>
              <div className="sec-divider" />
            </div>
            <div className="fmt-grid">
              {FORMATS.map(f => (
                <div key={f} className="fmt-item">
                  <input type="checkbox" id={`f-${f}`} checked={formats.includes(f)} onChange={() => toggleItem(formats, f, setFormats)} />
                  <label htmlFor={`f-${f}`} className="fmt-lbl">
                    <span className="fmt-icon">{FORMAT_ICONS[f]}</span>
                    <span className="fmt-name">{FORMAT_LABELS[f]}</span>
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* 06 FILE UPLOAD */}
          <div className="sec">
            <div className="sec-head">
              <span className="sec-num">06</span>
              <span className="sec-title">
                Reference Files&nbsp;
                <span style={{ color: "var(--muted)", fontWeight: 400, textTransform: "none", letterSpacing: 0 }}>(optional)</span>
              </span>
              <div className="sec-divider" />
            </div>
            <label className={`upload-zone${uploadedFile ? " has-file" : ""}`}>
              <input type="file" style={{ display: "none" }} accept=".txt,.md,.csv,.pdf,.docx"
                onChange={e => { const f = e.target.files?.[0]; if (f) handleFileUpload(f); }} />
              {uploading ? (
                <><div className="upload-spinner" /><div className="upload-title">Processing file…</div><div className="upload-sub">Extracting text content</div></>
              ) : uploadedFile ? (
                <><div className="upload-icon">✓</div><div className="upload-title">{uploadedFile.name}</div><div className="upload-badge"><span>✓</span><span>{fileContext ? "Text extracted" : "File attached"}</span></div></>
              ) : (
                <><div className="upload-icon">↑</div><div className="upload-title">Upload brand guide, brief, or reference doc</div><div className="upload-sub">.txt and .md files will be read as context · .pdf and .docx attached as reference</div></>
              )}
            </label>
            {uploadedFile && !uploading && (
              <button type="button" className="upload-remove"
                onClick={() => { setUploadedFile(null); setFileContext(""); }}>
                Remove file
              </button>
            )}
          </div>

          {/* 07 VARIANTS */}
          <div className="sec">
            <div className="sec-head">
              <span className="sec-num">07</span>
              <span className="sec-title">Copy Variants Per Channel</span>
              <div className="sec-divider" />
            </div>
            <div className="range-row">
              <input type="range" min={1} max={5} value={variants} className="range"
                onChange={e => setVariants(Number(e.target.value))} />
              <span className="range-val">{variants}</span>
            </div>
          </div>

          <button type="button" className="btn-generate" onClick={handleSubmit} disabled={loading}>
            {loading ? "Running pipeline…" : "→ Generate Campaign"}
          </button>
          <p className="hint">Avg. 45–90 seconds · Generates labeled variants per channel and format selected</p>
          {error && <div className="err">⚠ {error}</div>}
        </div>

        {/* LOADING */}
        {loading && (
          <div className="loading">
            <div className="loader-box"><div className="loader-scan" /></div>
            <div className="loader-label">Running Agent Pipeline</div>
            <div className="dots"><span /><span /><span /></div>
          </div>
        )}

        {/* RESULTS */}
        {result && !loading && (
          <div className="card results" ref={resultRef}>
            <div className="results-header">
              <div className="results-title">Campaign Output</div>
              <div className="results-meta"><b>{allVariants.length || 1}</b> variant{allVariants.length !== 1 ? "s" : ""} generated</div>
            </div>

            {allVariants.length > 0 && (
              <>
                <div className="tabs">
                  {allVariants.map((_, i) => (
                    <button key={i} type="button" className={`tab${activeTab === i ? " on" : ""}`} onClick={() => setActiveTab(i)}>
                      V{i + 1}{result.best_variant && allVariants[i] === result.best_variant ? " ★" : ""}
                    </button>
                  ))}
                  {result.email_sequence?.length ? (
                    <button type="button" className={`tab${activeTab === allVariants.length ? " on" : ""}`}
                      onClick={() => setActiveTab(allVariants.length)}>Email Seq.</button>
                  ) : null}
                </div>

                {activeTab < allVariants.length && (
                  <>
                    <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "0.5rem" }}>
                      <button type="button" className="copy-btn" onClick={() => navigator.clipboard.writeText(allVariants[activeTab])}>Copy</button>
                    </div>

                    <div className="output-box">{allVariants[activeTab]}</div>

                    {scores[activeTab] && (
                      <div className="score-wrap">
                        <div className="score-row">
                          <span>Quality Score</span>
                          <b>{Math.round((scores[activeTab].score || 0) * 100)}%</b>
                        </div>
                        <div className="score-bar">
                          <div className="score-fill" style={{ width: `${(scores[activeTab].score || 0) * 100}%` }} />
                        </div>
                        {scores[activeTab].reasoning && (
                          <div className="score-reason">{scores[activeTab].reasoning}</div>
                        )}
                      </div>
                    )}

                    {/* ── REFINE TOGGLE ── */}
                    <button
                      type="button"
                      className="refine-toggle"
                      onClick={() => setRefineOpen(prev => ({ ...prev, [activeTab]: !prev[activeTab] }))}
                    >
                      {refineOpen[activeTab] ? "▲ Close Refine Panel" : "◈ Refine This Variant"}
                    </button>

                    {/* ── REFINE PANEL ── */}
                    {refineOpen[activeTab] && (
                      <div className="refine-panel">

                        {/* Description */}
                        <div className="refine-desc">
                          Give the agent specific instructions to rewrite this variant. You can use the quick picks or guided fields to build your instruction, or write a detailed multi-line prompt directly. Be as specific as you want — the more context you provide, the more precise the rewrite.
                        </div>

                        {/* Quick picks */}
                        <div className="refine-section-label">Quick picks — click to append</div>
                        <div className="refine-suggestions">
                          {REFINE_SUGGESTIONS.map(s => (
                            <button key={s} type="button" className="refine-suggestion"
                              onClick={() => setRefinementText(prev => ({
                                ...prev,
                                [activeTab]: prev[activeTab]?.trim()
                                  ? `${prev[activeTab].trim()}\n${s}`
                                  : s
                              }))}>
                              + {s}
                            </button>
                          ))}
                        </div>

                        <div className="refine-divider" />

                        {/* Guided shorthand fields */}
                        <div className="refine-section-label">Guided fields — fills instruction box on blur</div>
                        <div className="refine-guided-grid">
                          {[
                            { id: "change", label: "What to change", placeholder: "e.g. The hook, the CTA, remove bullet 2", prefix: "Change" },
                            { id: "keep",   label: "What to keep",   placeholder: "e.g. The opening line and tone",           prefix: "Keep" },
                            { id: "tdx",    label: "Tone direction", placeholder: "e.g. More direct, peer-to-peer",           prefix: "Tone" },
                            { id: "length", label: "Target length",  placeholder: "e.g. Cut to 3 sentences, under 150 words", prefix: "Length" },
                            { id: "cta",    label: "CTA rewrite",    placeholder: "e.g. End with 'Reply YES to get started'", prefix: "CTA" },
                            { id: "extra",  label: "Additional notes", placeholder: "e.g. Avoid the word 'transform'",        prefix: "Note" },
                          ].map(({ id, label, placeholder, prefix }) => (
                            <div className="field" key={id}>
                              <label className="lbl">{label}</label>
                              <input
                                className="inp"
                                placeholder={placeholder}
                                onBlur={e => {
                                  const val = e.target.value.trim();
                                  if (val) {
                                    setRefinementText(prev => ({
                                      ...prev,
                                      [activeTab]: prev[activeTab]?.trim()
                                        ? `${prev[activeTab].trim()}\n${prefix}: ${val}`
                                        : `${prefix}: ${val}`
                                    }));
                                    e.target.value = "";
                                  }
                                }}
                              />
                            </div>
                          ))}
                        </div>

                        <div className="refine-divider" />

                        {/* Full instruction box */}
                        <div className="refine-full-label">Full instruction — edit freely or write from scratch</div>
                        <textarea
                          className="refine-textarea"
                          placeholder={`Write your full refinement instruction here. Quick picks and guided fields above will append to this box.\n\nExamples of detailed instructions:\n\n"Rewrite the hook to lead with the pain point, not the product. Keep the 3-bullet structure but tighten each bullet to one line. Change the CTA from a statement to a question. Cut total length to under 160 words. Do not use the word 'streamline'."\n\n"Make the tone feel like advice from a peer, not a pitch. Remove all urgency language. End with a soft ask — something that invites a conversation rather than demanding a click."`}
                          value={refinementText[activeTab] || ""}
                          onChange={e => setRefinementText(prev => ({ ...prev, [activeTab]: e.target.value }))}
                          onKeyDown={e => {
                            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleRefine(activeTab);
                          }}
                        />

                        <div className="refine-actions">
                          <span className="refine-char-count">
                            {(refinementText[activeTab] || "").length} chars · Cmd/Ctrl+Enter to submit
                          </span>
                          <div className="refine-action-btns">
                            <button type="button" className="btn-clear"
                              onClick={() => setRefinementText(prev => ({ ...prev, [activeTab]: "" }))}>
                              Clear
                            </button>
                            <button
                              type="button"
                              className="btn-refine"
                              onClick={() => handleRefine(activeTab)}
                              disabled={refining[activeTab] || !refinementText[activeTab]?.trim()}
                            >
                              {refining[activeTab]
                                ? <><div className="refine-spinner" /> Refining…</>
                                : <>◈ Apply Refinement</>}
                            </button>
                          </div>
                        </div>

                        {refineError[activeTab] && (
                          <div className="refine-err">⚠ {refineError[activeTab]}</div>
                        )}
                      </div>
                    )}
                  </>
                )}

                {activeTab === allVariants.length && result.email_sequence && (
                  <div>
                    {result.email_sequence.map((email, i) => (
                      <div key={i} className="email-item">
                        <div className="email-meta">Day {email.send_day} · Email {i + 1}</div>
                        <div className="email-subj">{email.subject}</div>
                        <div className="email-body">{email.body}</div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {!allVariants.length && result.best_variant && (
              <>
                <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "0.5rem" }}>
                  <button type="button" className="copy-btn" onClick={() => navigator.clipboard.writeText(result.best_variant || "")}>Copy</button>
                </div>
                <div className="output-box">{result.best_variant}</div>
              </>
            )}
          </div>
        )}

        <div className="footer">
          <p>Marketing Campaign Agent · AI-powered copy generation pipeline</p>
        </div>
      </div>
    </>
  );
}