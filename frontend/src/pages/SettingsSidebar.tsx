import { useEffect, useState } from "react";
import "./SettingsSidebar.css";

const API_BASE = "/api";

interface Provider {
  id: string;
  name: string;
  type: string;
  active: boolean;
}

interface Source {
  id: string;
  name: string;
  url?: string;
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
  const [sources, setSources] = useState<Source[]>([]);
  const [activeSourceId, setActiveSourceId] = useState<string | null>(null);

  const [providerName, setProviderName] = useState("");
  const [apiKey, setApiKey] = useState("");

  const [sourceName, setSourceName] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [selectedProvider, setSelectedProvider] = useState("");

  const fetchProviders = async () => {
    try {
      const res = await fetch(`${API_BASE}/providers`);
      if (res.ok) {
        const data = await res.json();
        setProviders(data);
        if (!selectedProvider && data.length > 0) {
          const active = data.find((p: Provider) => p.active) || data[0];
          setSelectedProvider(active.id);
        }
      }
    } catch (err) {
      console.error("Error fetching providers:", err);
    }
  };

  const fetchSources = async () => {
    try {
      const res = await fetch(`${API_BASE}/sources`);
      if (res.ok) {
        const data = await res.json();
        setSources(data.sources || []);
        setActiveSourceId(data.active_source_id || null);
      }
    } catch (err) {
      console.error("Error fetching sources:", err);
    }
  };

  useEffect(() => {
    let mounted = true;
    const init = async () => {
      try {
        const [provRes, srcRes] = await Promise.all([
          fetch(`${API_BASE}/providers`),
          fetch(`${API_BASE}/sources`),
        ]);
        if (!mounted) return;
        if (provRes.ok) {
          const provData = await provRes.json();
          setProviders(provData);
          const active = provData.find((p: Provider) => p.active) || provData[0];
          if (active) setSelectedProvider(active.id);
        }
        if (srcRes.ok) {
          const srcData = await srcRes.json();
          setSources(srcData.sources || []);
          setActiveSourceId(srcData.active_source_id || null);
        }
      } catch (err) {
        console.error("Error initializing settings:", err);
      }
    };
    init();
    return () => {
      mounted = false;
    };
  }, []);

  const addProvider = async () => {
    if (!providerName.trim() || !apiKey.trim()) {
      alert("Please provide both Provider Name and API Key.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/providers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: providerName.trim(), api_key: apiKey.trim() })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        alert(`Failed to add provider: ${errData.detail || "Unknown error"}`);
        return;
      }

      setProviderName("");
      setApiKey("");
      fetchProviders();
    } catch (err) {
      console.error("Failed to add provider:", err);
      alert("Network error connecting to backend.");
    }
  };

  const activateProvider = async (id: string) => {
    try {
      await fetch(`${API_BASE}/providers/activate/${id}`, {
        method: "POST"
      });
      fetchProviders();
    } catch (err) {
      console.error("Failed to activate provider:", err);
    }
  };

  const removeProvider = async (id: string) => {
    if (!window.confirm("Are you sure you want to remove this provider?")) return;
    try {
      await fetch(`${API_BASE}/providers/${id}`, {
        method: "DELETE"
      });
      fetchProviders();
    } catch (err) {
      console.error("Failed to delete provider:", err);
    }
  };

  const addSource = async () => {
    if (!sourceName.trim() || !sourceUrl.trim() || !selectedProvider) {
      alert("Please enter a name, Google Drive folder URL/ID, and select a provider.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/sources`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: sourceName.trim(),
          url: sourceUrl.trim(),
          provider_id: selectedProvider
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        alert(`Failed to add source: ${errData.detail || "Unknown error"}`);
        return;
      }

      setSourceName("");
      setSourceUrl("");
      fetchSources();
    } catch (err) {
      console.error("Failed to add source:", err);
      alert("Network error connecting to backend.");
    }
  };

  const activateSource = async (id: string) => {
    try {
      await fetch(`${API_BASE}/sources/activate/${id}`, {
        method: "POST"
      });
      fetchSources();
    } catch (err) {
      console.error("Failed to activate source:", err);
    }
  };

  const removeSource = async (id: string) => {
    try {
      await fetch(`${API_BASE}/sources/${id}`, {
        method: "DELETE"
      });
      fetchSources();
    } catch (err) {
      console.error("Failed to delete source:", err);
    }
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
        <h3 className="section-title">Providers (Google Drive API)</h3>
        <div className="provider-form">
          <input
            placeholder="Provider Name (e.g. My Drive)"
            value={providerName}
            onChange={(e) => setProviderName(e.target.value)}
          />
          <input
            placeholder="Google Drive API Key"
            value={apiKey}
            type="password"
            onChange={(e) => setApiKey(e.target.value)}
          />
          <button onClick={addProvider}>Add Provider</button>
        </div>

        <div className="provider-list">
          {providers.map((p) => (
            <div key={p.id} className="provider-item">
              <div className="provider-info">
                <strong>{p.name}</strong>
                {p.active && <span className="active-badge">Active</span>}
              </div>
              <div className="provider-actions">
                {!p.active && (
                  <button className="activate-btn" onClick={() => activateProvider(p.id)}>
                    Activate
                  </button>
                )}
                <button
                  className="remove-btn"
                  onClick={() => removeProvider(p.id)}
                  title="Remove Provider"
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
          {providers.length === 0 && (
            <p className="empty-hint">No providers yet. Add an API key above.</p>
          )}
        </div>

        {/* SOURCES */}
        <h3 className="section-title" style={{ marginTop: "24px" }}>Folders / Sources</h3>
        <div className="provider-form">
          <input
            placeholder="Source Name (e.g. Rock Collection)"
            value={sourceName}
            onChange={(e) => setSourceName(e.target.value)}
          />
          <input
            placeholder="Google Drive Folder URL or ID"
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
                {p.name} {p.active ? "(Active)" : ""}
              </option>
            ))}
          </select>
          <button onClick={addSource}>Add Source</button>
        </div>

        {/* SCROLLABLE SOURCE LIST */}
        <div className="source-list-scroll">
          {sources.map((s) => (
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
                  title="Remove Source"
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
          {sources.length === 0 && (
            <p className="empty-hint">No sources yet. Add a folder above.</p>
          )}
        </div>

        <button className="close-app-btn" onClick={closeApp}>
          Reset Session
        </button>
      </div>
    </>
  );
}
