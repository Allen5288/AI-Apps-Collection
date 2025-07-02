import React, { useState, useEffect, useRef } from "react";
import * as sdk from "microsoft-cognitiveservices-speech-sdk";
import "./custom.css";

export function SpeechToTextWithMSSdk() {
  const [isListening, setIsListening] = useState(false);
  const speechConfig = useRef(null);
  const audioConfig = useRef(null);
  const recognizer = useRef(null);
  const [tokenData, setTokenData] = useState(null);

  const [myTranscript, setMyTranscript] = useState("");
  const [recognizingTranscript, setRecTranscript] = useState("");

  const processRecognizedTranscript = (event) => {
    const result = event.result;
    console.log("Recognition result:", result);

    if (result.reason === sdk.ResultReason.RecognizedSpeech) {
      const transcript = result.text;
      console.log("Transcript: -->", transcript);
      setMyTranscript(transcript);
    }
  };

  const processRecognizingTranscript = (event) => {
    const result = event.result;
    console.log("Recognition result:", result);
    if (result.reason === sdk.ResultReason.RecognizingSpeech) {
      const transcript = result.text;
      console.log("Transcript: -->", transcript);
      setRecTranscript(transcript);
    }
  };

  const initRecognizer = () => {
    if (!tokenData) return;
    console.log("Speech token and region:", tokenData.token);
    console.log("Speech region:", tokenData.region);

    speechConfig.current = sdk.SpeechConfig.fromAuthorizationToken(
      tokenData.token,
      tokenData.region
    );
    speechConfig.current.speechRecognitionLanguage = "en-US";
    audioConfig.current = sdk.AudioConfig.fromDefaultMicrophoneInput();
    recognizer.current = new sdk.SpeechRecognizer(
      speechConfig.current,
      audioConfig.current
    );
    recognizer.current.recognized = (s, e) => processRecognizedTranscript(e);
    recognizer.current.recognizing = (s, e) => processRecognizingTranscript(e);
    recognizer.current.startContinuousRecognitionAsync(() => {
      console.log("Speech recognition started.");
      setIsListening(true);
    });
    return () => {
      recognizer.current.stopContinuousRecognitionAsync(() => {
        setIsListening(false);
      });
    };
  };

  useEffect(() => {
    // Fetch token from backend
    fetch("http://localhost:5001/api/Voice/get-speech-token")
      .then((res) => res.json())
      .then((data) => setTokenData(data))
      .catch((err) => console.error("Failed to fetch speech token:", err));
  }, []);

  useEffect(() => {
    if (tokenData) {
      initRecognizer();
    }
    // eslint-disable-next-line
  }, [tokenData]);

  const pauseListening = () => {
    setIsListening(false);
    recognizer.current && recognizer.current.stopContinuousRecognitionAsync();
    console.log("Paused listening.");
  };

  const clearTranscript = () => {
    setMyTranscript("");
    setRecTranscript("");
  };

  return (
    <div className="ai-card">
      <div className="ai-card-header">Live Speech-to-Text (Microphone)</div>
      <div className="ai-card-body ai-flex-col ai-gap-lg">
        <div className="ai-flex-row ai-gap-md ai-center">
          <button
            className={`ai-btn ${
              isListening ? "ai-btn-danger ai-recording" : "ai-btn-primary"
            }`}
            onClick={isListening ? pauseListening : initRecognizer}
            disabled={!tokenData}
          >
            <span className="ai-btn-icon">
              {isListening ? "⏹️" : "🎤"}
            </span>
            {isListening ? "Stop Listening" : "Start Listening"}
          </button>
          <button
            className="ai-btn ai-btn-secondary"
            onClick={clearTranscript}
            disabled={!myTranscript && !recognizingTranscript}
          >
            <span className="ai-btn-icon">🗑️</span>
            Clear
          </button>
        </div>
        <div className="ai-result-container ai-mt-lg">
          <label className="ai-label">
            Live Transcript {isListening && <span style={{color: 'var(--ai-danger)'}}>● Recording</span>}
          </label>
          <textarea
            className="ai-output-display"
            value={recognizingTranscript || myTranscript || (tokenData ? "Ready to listen..." : "Loading speech service...")}
            readOnly
            rows={6}
            placeholder="Speech will appear here..."
          />
        </div>
      </div>
    </div>
  );
}
