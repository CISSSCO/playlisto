import { useEffect, useRef, useState } from "react";
import PlayerPage, { type Track } from "./pages/PlayerPage";
import SettingsSidebar from "./pages/SettingsSidebar";
import "./index.css";

const API_BASE = "/api";

export default function App() {
  const audioRef = useRef<HTMLAudioElement>(null);

  const [playlist, setPlaylist] = useState<Track[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [shuffle, setShuffle] = useState(false);
  const [loop, setLoop] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Sync isPlaying state with native audio element events
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

  // Update track source whenever currentIndex or playlist changes
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (playlist.length === 0 || !playlist[currentIndex]) return;

    const currentTrack = playlist[currentIndex];
    const targetSrc = `${API_BASE}/stream/${currentTrack.id}?filename=${encodeURIComponent(
      currentTrack.name
    )}`;

    // Avoid restarting track if already loaded
    const fullTargetUrl = new URL(targetSrc, window.location.origin).href;
    if (audio.src !== fullTargetUrl) {
      audio.src = targetSrc;
      if (isPlaying) {
        audio.play().catch(() => {});
      }
    }
  }, [currentIndex, playlist, isPlaying]);

  const nextTrack = () => {
    const audio = audioRef.current;
    if (!audio || playlist.length === 0) return;

    // 🔁 LOOP MODE — repeat current track
    if (loop) {
      audio.currentTime = 0;
      audio.play().catch(() => {});
      return;
    }

    // 🔀 SHUFFLE MODE
    if (shuffle) {
      if (playlist.length <= 1) {
        audio.currentTime = 0;
        audio.play().catch(() => {});
        return;
      }
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
    const audio = audioRef.current;
    if (!audio || playlist.length === 0) return;

    // 🔁 LOOP MODE — repeat current track
    if (loop) {
      audio.currentTime = 0;
      audio.play().catch(() => {});
      return;
    }

    // 🔀 SHUFFLE MODE
    if (shuffle) {
      if (playlist.length <= 1) {
        audio.currentTime = 0;
        audio.play().catch(() => {});
        return;
      }
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
          title="Settings"
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
