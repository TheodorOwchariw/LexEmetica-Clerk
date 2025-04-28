// Quickstart Frontend Prototype for LexEmetica Clerk

// 1. Create Vite+React app and install Tailwind
// ```bash
// npm create vite@latest lex-emetica-clerk-frontend -- --template react
// cd lex-emetica-clerk-frontend
// npm install
// npm install -D tailwindcss postcss autoprefixer
// npx tailwindcss init -p
// ```

// 2. Configure Tailwind (tailwind.config.cjs)
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: { extend: {} },
  plugins: [],
};

// 3. PostCSS setup (postcss.config.cjs)
module.exports = { plugins: { tailwindcss: {}, autoprefixer: {} } };

// 4. Global styles (src/index.css)
@tailwind base;
@tailwind components;
@tailwind utilities;

// 5. Entry point (src/main.jsx)
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// 6. Main App (src/App.jsx)
import { useState } from 'react';

export default function App() {
  const [text, setText] = useState('');
  const [mode, setMode] = useState('professional');

  const handleGenerate = () => {
    // TODO: integrate API call
    console.log({ text, mode });
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center p-4">
      <h1 className="text-2xl font-bold mb-4">LexEmetica Clerk Prototype</h1>

      <textarea
        className="w-full max-w-xl h-40 p-2 border rounded mb-4"
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
          <option value="professional">Professional Mode</option>
          <option value="student">Student Mode</option>
        </select>
      </div>

      <button
        className="px-4 py-2 bg-blue-600 text-white rounded"
        onClick={handleGenerate}
      >
        Generate Brief
      </button>

      {/* Placeholder for generated brief */}
      <div id="output" className="w-full max-w-xl mt-6" />
    </div>
  );
}
