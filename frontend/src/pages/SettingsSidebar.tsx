import { useEffect, useState } from "react";
import "./SettingsSidebar.css";

const API_BASE = "http://localhost:8000/api";

interface Provider {
  id: string;
  name: string;
  type: string;
  active: boolean;
}

interface Source {
  id: string;
  name: string;
  provider_id: string;
}

interface Props {
  closeSidebar: () => void;
  closeApp: () => void;
}

export default function SettingsSidebar({
  closeSidebar,
  closeApp
}: Props) {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [sources, setSources] = useState<any[]>([]);
  const [activeSourceId, setActiveSourceId] = useState<string | null>(null);

  const [providerName, setProviderName] = useState("");
  const [apiKey, setApiKey] = useState("");

  const [sourceName, setSourceName] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [selectedProvider, setSelectedProvider] = useState("");

  const fetchProviders = async () => {
    const res = await fetch(`${API_BASE}/providers`);
    const data = await res.json();
    setProviders(data);
  };

  const fetchSources = async () => {
    const res = await fetch(`${API_BASE}/sources`);
    const data = await res.json();
    setSources(data.sources || []);
    setActiveSourceId(data.active_source_id || null);
  };

  useEffect(() => {
    fetchProviders();
    fetchSources();
  }, []);

  const addProvider = async () => {
    if (!providerName || !apiKey) return;

    await fetch(`${API_BASE}/providers`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: providerName, api_key: apiKey })
    });

    setProviderName("");
    setApiKey("");
    fetchProviders();
  };

  const activateProvider = async (id: string) => {
    await fetch(`${API_BASE}/providers/activate/${id}`, {
      method: "POST"
    });
    fetchProviders();
  };

  const addSource = async () => {
    if (!sourceName || !sourceUrl || !selectedProvider) return;

    await fetch(`${API_BASE}/sources`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: sourceName,
        url: sourceUrl,
        provider_id: selectedProvider
      })
    });

    setSourceName("");
    setSourceUrl("");
    fetchSources();
  };

  const activateSource = async (id: string) => {
    await fetch(`${API_BASE}/sources/activate/${id}`, {
      method: "POST"
    });
    fetchSources();
  };

  const removeSource = async (id: string) => {
    await fetch(`${API_BASE}/sources/${id}`, {
      method: "DELETE"
    });
    fetchSources();
  };

  return (
    <>
      <div className="sidebar-overlay" onClick={closeSidebar} />

      <div className="sidebar">
        <div className="sidebar-header">
          <h2>Settings</h2>
          <span onClick={closeSidebar}>✕</span>
        </div>

        {/* PROVIDERS */}
        <div className="provider-form">
          <input
            placeholder="Provider Name"
            value={providerName}
            onChange={(e) => setProviderName(e.target.value)}
          />
          <input
            placeholder="Google Drive API Key"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
          <button onClick={addProvider}>Add Provider</button>
        </div>

        <div className="provider-list">
          {providers.map((p) => (
            <div key={p.id} className="provider-item">
              <strong>{p.name}</strong>
              {p.active ? (
                <span className="active-badge">Active</span>
              ) : (
                <button onClick={() => activateProvider(p.id)}>
                  Activate
                </button>
              )}
            </div>
          ))}
        </div>

        {/* SOURCES */}
        <div className="provider-form">
          <input
            placeholder="Source Name"
            value={sourceName}
            onChange={(e) => setSourceName(e.target.value)}
          />
          <input
            placeholder="Google Drive Folder URL"
            value={sourceUrl}
            onChange={(e) => setSourceUrl(e.target.value)}
          />
          <select
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
          >
            <option value="">Select Provider</option>
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <button onClick={addSource}>Add Source</button>
        </div>

        {/* SCROLLABLE SOURCE LIST */}
        <div className="source-list-scroll">
          {sources.map((s: any) => (
            <div
              key={s.id}
              className={`provider-item ${
                activeSourceId === s.id ? "active-source" : ""
              }`}
            >
              <strong>{s.name}</strong>

              <div className="source-actions">
                {activeSourceId === s.id ? (
                  <span className="active-badge">Active</span>
                ) : (
                  <button onClick={() => activateSource(s.id)}>
                    Activate
                  </button>
                )}

                <button
                  className="remove-btn"
                  onClick={() => removeSource(s.id)}
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>

        <button className="close-app-btn" onClick={closeApp}>
          Close App
        </button>
      </div>
    </>
  );
}
