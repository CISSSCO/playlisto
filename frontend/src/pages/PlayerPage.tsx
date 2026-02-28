import { useEffect, useState } from "react";
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

  const loadFolder = async () => {
    const res = await fetch(`${API_BASE}/load-folder`, {
      method: "POST"
    });

    if (!res.ok) {
      alert("No active source configured. Add and activate one in Settings.");
      return;
    }

    const data = await res.json();
    setPlaylist(data.files || []);
    setCurrentIndex(0);
  };

  const togglePlay = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }

    setIsPlaying(!isPlaying);
  };

  useEffect(() => {
    if (!audioRef.current) return;

    const audio = audioRef.current;

    const update = () => {
      setProgress((audio.currentTime / audio.duration) * 100 || 0);
    };

    audio.addEventListener("timeupdate", update);
    return () => audio.removeEventListener("timeupdate", update);
  }, []);

  useEffect(() => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.play().catch(() => {});
    }
  }, [currentIndex]);

  return (
    <div className="player-card">
      <div className="glass-container">
        <div className="glass-card">

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

              <div className="progress-bar-wrapper">
                <div
                  className="progress-bar-fill"
                  style={{ width: `${progress}%` }}
                />
              </div>

              <ul className="playlist">
                {playlist.map((file: any, index: number) => (
                  <li
                    key={file.id}
                    className={index === currentIndex ? "active" : ""}
                    onClick={() => setCurrentIndex(index)}
                  >
                    {file.name}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
