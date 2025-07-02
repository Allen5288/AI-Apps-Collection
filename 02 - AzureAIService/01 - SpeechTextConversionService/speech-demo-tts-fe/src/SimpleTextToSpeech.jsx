import React, { useState, useEffect } from "react";
import "./custom.css";

const SimpleTextToSpeech = ({ text }) => {
  const [isPaused, setIsPaused] = useState(false);
  const [utterance, setUtterance] = useState(null);

  useEffect(() => {
    const synth = window.speechSynthesis;
    const u = new SpeechSynthesisUtterance(text);
    setUtterance(u);
    return () => {
      synth.cancel();
    };
  }, [text]);

  const handlePlay = () => {
    const synth = window.speechSynthesis;
    if (isPaused) {
      synth.resume();
    }
    synth.speak(utterance);
    setIsPaused(false);
  };

  const handlePause = () => {
    window.speechSynthesis.pause();
    setIsPaused(true);
  };

  const handleStop = () => {
    window.speechSynthesis.cancel();
    setIsPaused(false);
  };

  return (
    <div className="ai-card">
      <div className="ai-card-header">Text to Speech Controls</div>
      <div className="ai-card-body ai-flex-col ai-gap-md ai-center">
        <div className="ai-btn-group">
          <button className="ai-btn ai-btn-success" onClick={handlePlay}>
            <span className="ai-btn-icon">{isPaused ? "▶️" : "🔊"}</span>{" "}
            {isPaused ? "Resume" : "Play"}
          </button>
          <button className="ai-btn ai-btn-warning" onClick={handlePause}>
            <span className="ai-btn-icon">⏸️</span> Pause
          </button>
          <button className="ai-btn ai-btn-danger" onClick={handleStop}>
            <span className="ai-btn-icon">⏹️</span> Stop
          </button>
        </div>
      </div>
    </div>
  );
};

export default SimpleTextToSpeech;
