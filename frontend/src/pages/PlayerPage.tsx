import { useEffect, useRef, useState } from "react";
import "./PlayerPage.css";

const API_BASE = "http://localhost:8000/api";

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
  setLoop
}: any) {
  const [progress, setProgress] = useState(0);
  const progressRef = useRef<HTMLDivElement>(null);

  const loadFolder = async () => {
    const res = await fetch(`${API_BASE}/load-folder`, {
      method: "POST"
    });

    if (!res.ok) {
      alert("No active source configured.");
      return;
    }

    const data = await res.json();
    setPlaylist(data.files || []);
    setCurrentIndex(0);
  };

  const togglePlay = async () => {
    if (!audioRef.current) return;

    if (audioRef.current.paused) {
      await audioRef.current.play().catch(() => {});
      setIsPlaying(true);
    } else {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  };

  /* ===== Progress Tracking ===== */
  useEffect(() => {
    if (!audioRef.current) return;

    const audio = audioRef.current;

    const update = () => {
      if (!audio.duration) return;
      setProgress((audio.currentTime / audio.duration) * 100);
    };

    audio.addEventListener("timeupdate", update);
    return () => audio.removeEventListener("timeupdate", update);
  }, []);

  /* ===== Seek on Click ===== */
  const handleSeek = (e: React.MouseEvent) => {
    if (!audioRef.current || !progressRef.current) return;

    const rect = progressRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percent = clickX / rect.width;

    audioRef.current.currentTime =
      percent * audioRef.current.duration;
  };

  /* ===== Auto Play on Track Change ===== */
  useEffect(() => {
    if (!audioRef.current) return;
    if (!playlist[currentIndex]) return;

    audioRef.current.src =
      `${API_BASE}/stream/${playlist[currentIndex].id}?filename=${encodeURIComponent(
        playlist[currentIndex].name
      )}`;

    if (isPlaying) {
      audioRef.current.play().catch(() => {});
    }
  }, [currentIndex]);

    return (
      <div className="player-card">
        <div className="glass-container">

          {/* ================= NOW PLAYING CARD ================= */}
          <div className="glass-card now-playing-card">

            <div className="input-row">
              <button onClick={loadFolder}>Load Active Source</button>
            </div>

            {playlist.length > 0 && (
              <>
                <h3 className="track-title">
                  {playlist[currentIndex]?.name}
                </h3>

                <div className="controls">
                  <button onClick={prevTrack}>⏮</button>
                  <button onClick={togglePlay}>
                    {isPlaying ? "⏸" : "▶"}
                  </button>
                  <button onClick={nextTrack}>⏭</button>

                  <button
                    className={shuffle ? "active" : ""}
                    onClick={() => setShuffle(!shuffle)}
                  >
                    🔀
                  </button>

                  <button
                    className={loop ? "active" : ""}
                    onClick={() => setLoop(!loop)}
                  >
                    🔁
                  </button>
                </div>

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
              </>
            )}
          </div>

          {/* ================= PLAYLIST CARDS ================= */}
          {playlist.length > 0 && (
            <div className="song-list-wrapper">
              {playlist.map((file: any, index: number) => (
                <div
                  key={file.id}
                    className={`song-card ${
                      index === currentIndex ? "active-song-card" : ""
                    }`}
                    style={
                      index === currentIndex
                        ? { "--progress-width": `${progress}%` } as React.CSSProperties
                        : {}
                    }
                  onClick={() => setCurrentIndex(index)}
                >
                  <div className="song-name">
                    {file.name}
                  </div>

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
