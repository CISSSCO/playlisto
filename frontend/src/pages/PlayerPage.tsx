import { useCallback, useEffect, useRef, useState } from "react";
import "./PlayerPage.css";

const API_BASE = "/api";

export interface Track {
  id: string;
  name: string;
}

interface PlayerPageProps {
  audioRef: React.RefObject<HTMLAudioElement | null>;
  playlist: Track[];
  setPlaylist: React.Dispatch<React.SetStateAction<Track[]>>;
  currentIndex: number;
  setCurrentIndex: React.Dispatch<React.SetStateAction<number>>;
  isPlaying: boolean;
  setIsPlaying: React.Dispatch<React.SetStateAction<boolean>>;
  nextTrack: () => void;
  prevTrack: () => void;
  shuffle: boolean;
  setShuffle: React.Dispatch<React.SetStateAction<boolean>>;
  loop: boolean;
  setLoop: React.Dispatch<React.SetStateAction<boolean>>;
}

export default function PlayerPage({
  audioRef,
  playlist,
  setPlaylist,
  currentIndex,
  setCurrentIndex,
  isPlaying,
  setIsPlaying,
  nextTrack,
  prevTrack,
  shuffle,
  setShuffle,
  loop,
  setLoop,
}: PlayerPageProps) {
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isLoadingSource, setIsLoadingSource] = useState(false);
  const [activeSourceName, setActiveSourceName] = useState<string | null>(null);

  const progressRef = useRef<HTMLDivElement>(null);

  const formatTime = (secs: number) => {
    if (isNaN(secs) || secs < 0) return "0:00";
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  const loadFolder = async () => {
    setIsLoadingSource(true);
    try {
      const res = await fetch(`${API_BASE}/load-folder`, {
        method: "POST",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || "No active source configured.");
        return;
      }

      const data = await res.json();
      setPlaylist(data.files || []);
      setCurrentIndex(0);
      setActiveSourceName(data.name || "Active Source");
    } catch (err) {
      console.error("Error loading folder:", err);
      alert("Failed to connect to backend server.");
    } finally {
      setIsLoadingSource(false);
    }
  };

  const removeActiveSource = () => {
    setPlaylist([]);
    setCurrentIndex(0);
    setActiveSourceName(null);

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
    }
  };

  const togglePlay = useCallback(async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (audio.paused) {
      try {
        await audio.play();
        setIsPlaying(true);
      } catch (e) {
        console.error("Audio playback error:", e);
      }
    } else {
      audio.pause();
      setIsPlaying(false);
    }
  }, [audioRef, setIsPlaying]);

  const toggleMute = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    setIsMuted((prev) => {
      const next = !prev;
      audio.muted = next;
      return next;
    });
  }, [audioRef]);

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    const audio = audioRef.current;
    if (audio) {
      audio.volume = val;
      audio.muted = val === 0;
    }
    setIsMuted(val === 0);
  };

  /* ===== Progress & Duration Tracking ===== */
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const update = () => {
      setCurrentTime(audio.currentTime);
      if (audio.duration && !isNaN(audio.duration) && audio.duration > 0) {
        setDuration(audio.duration);
        setProgress((audio.currentTime / audio.duration) * 100);
      }
    };

    const handleLoadedMetadata = () => {
      if (audio.duration && !isNaN(audio.duration)) {
        setDuration(audio.duration);
      }
    };

    audio.addEventListener("timeupdate", update);
    audio.addEventListener("loadedmetadata", handleLoadedMetadata);
    audio.addEventListener("durationchange", handleLoadedMetadata);

    return () => {
      audio.removeEventListener("timeupdate", update);
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
      audio.removeEventListener("durationchange", handleLoadedMetadata);
    };
  }, [audioRef]);

  /* ===== Seek on Click ===== */
  const handleSeek = (e: React.MouseEvent) => {
    const audio = audioRef.current;
    if (!audio || !progressRef.current || !audio.duration) return;

    const rect = progressRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percent = Math.max(0, Math.min(1, clickX / rect.width));

    audio.currentTime = percent * audio.duration;
  };

  /* ===== Keyboard Shortcuts ===== */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (["INPUT", "TEXTAREA", "SELECT"].includes((e.target as HTMLElement)?.tagName)) {
        return;
      }

      if (e.code === "Space") {
        e.preventDefault();
        togglePlay();
      } else if (e.code === "ArrowRight") {
        e.preventDefault();
        if (audioRef.current) {
          audioRef.current.currentTime = Math.min(
            audioRef.current.currentTime + 5,
            audioRef.current.duration || Infinity
          );
        }
      } else if (e.code === "ArrowLeft") {
        e.preventDefault();
        if (audioRef.current) {
          audioRef.current.currentTime = Math.max(audioRef.current.currentTime - 5, 0);
        }
      } else if (e.code === "KeyM") {
        toggleMute();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [audioRef, togglePlay, toggleMute]);

  return (
    <div className="player-card">
      <div className="glass-container">
        {/* ================= NOW PLAYING CARD ================= */}
        <div className="glass-card now-playing-card">
          <div className="input-row source-bar">
            {!activeSourceName ? (
              <button onClick={loadFolder} disabled={isLoadingSource}>
                {isLoadingSource ? "Loading..." : "Load Active Source"}
              </button>
            ) : (
              <div className="active-source-display">
                <div className="source-left">
                  <span className="drive-icon">📁</span>
                  <span className="source-name">{activeSourceName}</span>
                </div>

                <div className="source-actions">
                  <button
                    className="icon-btn"
                    onClick={loadFolder}
                    title="Reload Source"
                    disabled={isLoadingSource}
                  >
                    {isLoadingSource ? "⌛" : "🔄"}
                  </button>

                  <button
                    className="icon-btn remove"
                    onClick={removeActiveSource}
                    title="Unload Source"
                  >
                    ✕
                  </button>
                </div>
              </div>
            )}
          </div>

          {playlist.length > 0 && (
            <>
              <h3 className="track-title" title={playlist[currentIndex]?.name}>
                {playlist[currentIndex]?.name}
              </h3>

              <div className="controls">
                <button onClick={prevTrack} title="Previous Track">⏮</button>
                <button onClick={togglePlay} title={isPlaying ? "Pause" : "Play"}>
                  {isPlaying ? "⏸" : "▶"}
                </button>
                <button onClick={nextTrack} title="Next Track">⏭</button>

                <button
                  className={shuffle ? "active" : ""}
                  onClick={() => setShuffle(!shuffle)}
                  title={shuffle ? "Shuffle On" : "Shuffle Off"}
                >
                  🔀
                </button>

                <button
                  className={loop ? "active" : ""}
                  onClick={() => setLoop(!loop)}
                  title={loop ? "Repeat On" : "Repeat Off"}
                >
                  🔁
                </button>
              </div>

              {/* PROGRESS BAR & TIME */}
              <div
                className="progress-bar-wrapper"
                ref={progressRef}
                onClick={handleSeek}
              >
                <div
                  className="progress-bar-fill"
                  style={{ width: `${progress}%` }}
                />
              </div>

              <div className="time-display">
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(duration)}</span>
              </div>

              {/* VOLUME BAR */}
              <div className="volume-control">
                <button
                  className="icon-btn mute-btn"
                  onClick={toggleMute}
                  title={isMuted ? "Unmute (M)" : "Mute (M)"}
                >
                  {isMuted || volume === 0 ? "🔇" : volume < 0.5 ? "🔉" : "🔊"}
                </button>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={isMuted ? 0 : volume}
                  onChange={handleVolumeChange}
                  className="volume-slider"
                  title="Volume"
                />
              </div>
            </>
          )}
        </div>

        {/* ================= PLAYLIST CARDS ================= */}
        {playlist.length > 0 && (
          <div className="song-list-wrapper">
            {playlist.map((file, index) => (
              <div
                key={file.id}
                className={`song-card ${
                  index === currentIndex ? "active-song-card" : ""
                }`}
                style={
                  index === currentIndex
                    ? ({ "--progress-width": `${progress}%` } as React.CSSProperties)
                    : {}
                }
                onClick={() => setCurrentIndex(index)}
              >
                <div className="song-name" title={file.name}>{file.name}</div>

                {index === currentIndex && (
                  <div className="playing-indicator">
                    {isPlaying ? "● Playing" : "● Paused"}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
