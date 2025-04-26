// frontend/app/page.jsx (or page.js) - No Image Prompt
'use client'; // Required for components using hooks and browser APIs

import React, { useState } from 'react';
// import './globals.css'; // Handled by Next.js layout

export default function HomePage() {
  // --- State Variables ---
  const [dreamText, setDreamText] = useState('');
  const [apiStatus, setApiStatus] = useState({
    loading: false,
    error: null,
    data: null, // Will hold {sentiment_label, keywords, interpretation}
  });

  // --- Backend API URL ---
  const API_URL = 'http://127.0.0.1:8000/process_dream';

  // --- Event Handlers ---
  const handleInputChange = (event) => {
    setDreamText(event.target.value);
  };

  // Handle form submission using fetch
  const handleSubmit = async () => {
    if (!dreamText.trim()) {
      setApiStatus({ loading: false, error: 'Please enter dream description.', data: null });
      return;
    }
    setApiStatus({ loading: true, error: null, data: null });

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', },
        body: JSON.stringify({ dream_text: dreamText }),
      });
      const responseData = await response.json();
      if (!response.ok) { throw new Error(responseData.detail || `HTTP error ${response.status}`); }
      setApiStatus({ loading: false, error: responseData.error || null, data: responseData });
    } catch (error) {
      console.error("API request failed:", error);
      setApiStatus({ loading: false, error: `Request failed: ${error.message || 'Cannot connect to backend.'}`, data: null });
    }
  };

  // --- Render UI (JSX) ---
  return (
    <div className="AppContainer">
      <header>
        <h1>AI Dream Interpreter <span role="img" aria-label="sparkles">✨</span></h1>
        <p className="disclaimer">Full Stack AI Application Workshop (Daniel Wang)</p>
      </header>

      <main>
        <div className="input-section">
          <textarea
            value={dreamText}
            onChange={handleInputChange}
            placeholder="Describe your dream..."
            rows="5"
            disabled={apiStatus.loading}
            aria-label="Dream Description Input"
          />
          <button onClick={handleSubmit} disabled={apiStatus.loading}>
            {apiStatus.loading ? 'Thinking...' : 'Interpret Dream'}
          </button>
        </div>

        {/* Display Status: Loading or Error */}
        {apiStatus.loading && <div className="status-message loading">Processing your dream... Please wait.</div>}
        {!apiStatus.loading && apiStatus.error && <div className="status-message error">{apiStatus.error}</div>}

        {/* Display Results (only if data exists and not loading) */}
        {apiStatus.data && !apiStatus.loading && (
          <div className="results-section">
            {/* Analysis Card */}
            <div className="result-card">
              <h2>Analysis (HF)</h2>
              <p><strong>Sentiment:</strong> {apiStatus.data.sentiment_label ?? 'N/A'} ({apiStatus.data.sentiment_score?.toFixed(2) ?? 'N/A'})</p>
              <p><strong>Keywords:</strong> {apiStatus.data.keywords?.join(', ') ?? 'N/A'}</p>
            </div>
            {/* Generation Card (Interpretation Only) */}
            <div className="result-card">
              <h2>Generation (OpenAI)</h2>
              <p><strong>Symbolic Interpretation:</strong></p>
              <p className="generated-text">{apiStatus.data.interpretation ?? 'N/A'}</p>
              {/* --- Art Prompt Section REMOVED --- */}
            </div>
          </div>
        )}
      </main>
      <footer>Powered by FastAPI, Next.js, Hugging Face 🤗, OpenAI 🤖</footer>
    </div>
  );
}