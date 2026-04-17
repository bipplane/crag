import React, { useState } from 'react';
import { Upload, Search, FileText } from 'lucide-react';
import './index.css';

function App() {
  const [tenantId, setTenantId] = useState('professor-smith');
  const [moduleId, setModuleId] = useState('chapter-1-biology');
  
  // Upload State
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setUploadStatus('');

    const formData = new FormData();
    formData.append('tenant_id', tenantId);
    formData.append('module_id', moduleId);
    formData.append('file', file);

    try {
      const response = await fetch('http://127.0.0.1:8000/rag/ingest', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        setUploadStatus(`Success! Document indexed with ID: ${data.result.doc_id}`);
      } else {
        setUploadStatus(`Error: ${data.detail || 'Failed to upload'}`);
      }
    } catch (err: any) {
      console.error(err);
      setUploadStatus(`Connection Error: Make sure backend is running.`);
    } finally {
      setUploading(false);
    }
  };

  // Query State
  const [query, setQuery] = useState('what is my group number?');
  const [querying, setQuerying] = useState(false);
  const [answer, setAnswer] = useState('');

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;

    setQuerying(true);
    setAnswer('');

    try {
      const response = await fetch('http://127.0.0.1:8000/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: tenantId,
          module_id: moduleId,
          query: query,
        }),
      });
      const data = await response.json();
      if (response.ok) {
        setAnswer(data.answer);
      } else {
        setAnswer(`Error: ${data.detail || 'Failed to query'}`);
      }
    } catch (err: any) {
      console.error(err);
      setAnswer(`Connection Error: Make sure backend is running.`);
    } finally {
      setQuerying(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8 text-gray-900 font-sans">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">CRAG: Educational RAG Tester</h1>
          <p className="text-gray-500 mt-2">Test multi-tenant document ingestion and retrieval securely.</p>
        </div>

        {/* Global Context Config */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Tenant ID</label>
            <input 
              type="text" 
              value={tenantId}
              onChange={(e) => setTenantId(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 outline-none bg-white"
            />
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Module ID</label>
            <input 
              type="text" 
              value={moduleId}
              onChange={(e) => setModuleId(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 outline-none bg-white"
            />
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          
          {/* Left Column: Upload */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center gap-2 mb-4">
              <Upload className="w-5 h-5 text-blue-600" />
              <h2 className="text-xl font-semibold">1. Upload Context</h2>
            </div>
            <p className="text-sm text-gray-500 mb-4">Upload a document (.txt, .md, .pdf) to serve as knowledge for the selected module.</p>
            
            <form onSubmit={handleFileUpload} className="space-y-4">
              <div className="border-2 border-dashed border-blue-200 rounded-lg p-4 text-center hover:bg-blue-50 transition-colors bg-white">
                <input 
                  type="file" 
                  accept=".txt,.md,.csv,.pdf"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-100 file:text-blue-700 hover:file:bg-blue-200 cursor-pointer"
                />
              </div>
              <button 
                type="submit" 
                disabled={!file || uploading}
                className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium disabled:opacity-50 transition-colors"
              >
                {uploading ? 'Ingesting...' : 'Ingest Document'}
              </button>
              {uploadStatus && (
                <div className={`p-3 rounded-md text-sm border font-medium ${uploadStatus.includes('Error') ? 'bg-red-50 text-red-700 border-red-200' : 'bg-green-50 text-green-700 border-green-200'}`}>
                  {uploadStatus}
                </div>
              )}
            </form>
          </div>

          {/* Right Column: Query */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center gap-2 mb-4">
              <Search className="w-5 h-5 text-indigo-600" />
              <h2 className="text-xl font-semibold">2. Ask Question</h2>
            </div>
            <p className="text-sm text-gray-500 mb-4">Query the LLM. It will only access documents matching the tenant and module ID above.</p>
            
            <form onSubmit={handleQuery} className="space-y-4">
              <div>
                <textarea 
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask a question about the uploaded document..."
                  className="w-full p-3 border border-gray-300 rounded-md min-h-[108px] focus:ring-2 focus:ring-indigo-500 outline-none resize-none bg-white"
                />
              </div>
              <button 
                type="submit" 
                disabled={!query || querying}
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md font-medium disabled:opacity-50 transition-colors"
              >
                {querying ? 'Retrieving Answer...' : 'Generate Answer'}
              </button>
            </form>
          </div>

        </div>

        {/* Answer Display */}
        {answer && (
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center gap-2 mb-3">
              <FileText className="w-5 h-5 text-emerald-600" />
              <h3 className="font-semibold text-gray-800">Generated Response</h3>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg text-gray-800 whitespace-pre-wrap border border-gray-200 text-sm leading-relaxed">
              {answer}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default App;