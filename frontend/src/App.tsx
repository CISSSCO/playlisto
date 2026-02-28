import { useEffect, useRef, useState } from "react";
import PlayerPage from "./pages/PlayerPage";
import SettingsSidebar from "./pages/SettingsSidebar";
import "./index.css";

const API_BASE = "http://localhost:8000/api";

export default function App() {
  const audioRef = useRef<HTMLAudioElement>(null);

  const [playlist, setPlaylist] = useState<any[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [shuffle, setShuffle] = useState(false);
  const [loop, setLoop] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

    //testing effect
useEffect(() => {

  const audio = audioRef.current;
  if (!audio) return;

  const handlePlay = () => setIsPlaying(true);
  const handlePause = () => setIsPlaying(false);

  audio.addEventListener("play", handlePlay);
  audio.addEventListener("pause", handlePause);

  return () => {
    audio.removeEventListener("play", handlePlay);
    audio.removeEventListener("pause", handlePause);
  };
}, []);

    useEffect(() => {
      const audio = audioRef.current;
      if (!audio) return;

      const handleStall = () => {
        audio.play().catch(() => {});
      };

      audio.addEventListener("stalled", handleStall);
      audio.addEventListener("waiting", handleStall);

      return () => {
        audio.removeEventListener("stalled", handleStall);
        audio.removeEventListener("waiting", handleStall);
      };
    }, []);



  // ONLY change src when track changes
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
  }, [currentIndex, playlist]);

const nextTrack = () => {
  if (!audioRef.current) return;
  if (playlist.length === 0) return;

  // 🔁 LOOP MODE — repeat current track
  if (loop) {
    audioRef.current.currentTime = 0;
    audioRef.current.play().catch(() => {});
    return;
  }

  // 🔀 SHUFFLE MODE
  if (shuffle) {
    let random = currentIndex;
    while (random === currentIndex) {
      random = Math.floor(Math.random() * playlist.length);
    }
    setCurrentIndex(random);
    return;
  }

  // ▶ NORMAL NEXT
  if (currentIndex + 1 < playlist.length) {
    setCurrentIndex(currentIndex + 1);
  } else {
    setIsPlaying(false);
  }
};

const prevTrack = () => {
  if (!audioRef.current) return;
  if (playlist.length === 0) return;

  // 🔁 LOOP MODE — repeat current track
  if (loop) {
    audioRef.current.currentTime = 0;
    audioRef.current.play().catch(() => {});
    return;
  }

  // 🔀 SHUFFLE MODE (same logic as next)
  if (shuffle) {
    let random = currentIndex;
    while (random === currentIndex) {
      random = Math.floor(Math.random() * playlist.length);
    }
    setCurrentIndex(random);
    return;
  }

  // ◀ NORMAL PREVIOUS
  if (currentIndex > 0) {
    setCurrentIndex(currentIndex - 1);
  }
};
const closeApp = () => {
  if (audioRef.current) {
    audioRef.current.pause();
    audioRef.current.src = "";
  }

  setPlaylist([]);
  setIsPlaying(false);
  setCurrentIndex(0);
  setShowSettings(false);
};
  return (
    <div className="app-root">
        <audio
          ref={audioRef}
          onEnded={nextTrack}
          preload="auto"
        />

      {/* HEADER */}
      <div className="global-header">
        <div className="header-spacer" />
        <div className="brand-title">Playlisto</div>
        <div
          className="hamburger"
          onClick={() => setShowSettings(!showSettings)}
        >
          ☰
        </div>
      </div>

      <PlayerPage
        audioRef={audioRef}
        playlist={playlist}
        setPlaylist={setPlaylist}
        currentIndex={currentIndex}
        setCurrentIndex={setCurrentIndex}
        isPlaying={isPlaying}
        setIsPlaying={setIsPlaying}
        shuffle={shuffle}
        setShuffle={setShuffle}
        loop={loop}
        setLoop={setLoop}
        nextTrack={nextTrack}
        prevTrack={prevTrack}
      />

      {showSettings && (
        <SettingsSidebar
          closeSidebar={() => setShowSettings(false)}
          closeApp={closeApp}
        />
      )}
    </div>
  );
}
