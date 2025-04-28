import { useState } from 'react';
import axios from 'axios';

export default function App() {
  const [text, setText] = useState('');
  const [citation, setCitation] = useState('');
  const [mode, setMode] = useState('professional');
  const [brief, setBrief] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerateFromText = async () => {
    if (!text.trim()) {
      setError('Please paste some case text first.');
      return;
    }
    setLoading(true);
    setError(null);
    setBrief(null);

    try {
      const res = await axios.post('/api/brief/from-text', { text, mode, fmt: 'json' });
      setBrief(res.data.sections);
    } catch (err) {
      console.error('JSON request failed:', err.response?.data || err.message);
      setError('Failed to generate JSON brief from text.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdfByCitation = async () => {
    if (!citation.trim()) {
      setError('Please enter a citation (e.g., "410 U.S. 113").');
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      params.append('citation', citation);
      params.append('mode', mode);
      params.append('fmt', 'pdf');

      const res = await axios.post('/api/brief/by-citation', params, {
        responseType: 'blob',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      const caseNameHeader = res.headers['x-case-name'] || citation;
      const safeName = caseNameHeader
       .replace(/\s+/g, '_')         // spaces → underscores
       .replace(/(?<!v)\./g, '')     // remove any “.” not preceded by “v”
       .trim();
      const blob = new Blob([res.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = ${safeName}.pdf;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err.response?.data || err.message);
      setError('Failed to download PDF brief.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center p-4">
      <h1 className="text-2xl font-bold mb-4">LexEmetica Clerk Prototype</h1>

      <textarea
        className="w-full max-w-xl h-40 p-2 border rounded mb-2"
        placeholder="Paste case text here..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <div className="flex items-center mb-4 space-x-2">
        <label>Mode:</label>
        <select
          className="p-2 border rounded"
          value={mode}
          onChange={(e) => setMode(e.target.value)}
        >
          <option value="professional">Professional</option>
          <option value="student">Student</option>
        </select>
      </div>
      <button
        type="button"
        className="px-4 py-2 bg-blue-600 text-white rounded mb-6"
        onClick={handleGenerateFromText}
        disabled={loading}
      >
        {loading ? 'Generating JSON…' : 'Generate JSON Brief'}
      </button>

      {brief && (
        <div className="w-full max-w-xl mt-6 space-y-4">
          {Object.entries(brief).map(([section, content]) => (
            <div key={section}>
              <h2 className="text-lg font-semibold">{section}</h2>
              <p className="whitespace-pre-wrap">{content}</p>
            </div>
          ))}
        </div>
      )}

      <hr className="w-full max-w-xl my-8 border-gray-300" />

      <input
        type="text"
        className="w-full max-w-xl p-2 border rounded mb-2"
        placeholder="Enter citation (e.g., 410 U.S. 113)..."
        value={citation}
        onChange={(e) => setCitation(e.target.value)}
      />
      <button
        type="button"
        className="px-4 py-2 bg-green-600 text-white rounded"
        onClick={handleDownloadPdfByCitation}
        disabled={loading}
      >
        {loading ? 'Downloading PDF…' : 'Download PDF Brief'}
      </button>

      {error && <p className="text-red-500 mt-4">{error}</p>}
    </div>
  );
}