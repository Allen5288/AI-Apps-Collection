import React, { useEffect, useRef, useState } from "react";
import { ReactMic } from "react-mic";
import axios from "axios";
import { getTokenOrRefresh } from "./token_util";
import "./custom.css";

const speechsdk = require("microsoft-cognitiveservices-speech-sdk");

export default function UploadAndTrans() {
  const [displayText, setDisplayText] = useState("Ready to test speech...");
  const [player, updatePlayer] = useState({ p: undefined, muted: false });
  const [recording, setRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadOrTranslate, setUploadOrTranslate] = useState("upload");
  const uploadOrTranslateRef = useRef(uploadOrTranslate);
  const fileInputRef = useRef(null);

  useEffect(() => {
    uploadOrTranslateRef.current = uploadOrTranslate;
  }, [uploadOrTranslate]);

  const startRecording = () => {
    setUploadOrTranslate("upload");
    setRecording(true);
  };

  const startTranslateRecording = () => {
    setUploadOrTranslate("translate");
    setRecording(true);
  };

  const stopRecording = () => {
    setRecording(false);
  };

  const onStop = async (recordedBlob) => {
    console.log("Recorded Blob: ", recordedBlob);
    if (recordedBlob && recordedBlob.blob) {
      setLoading(true);
      const formData = new FormData();
      formData.append("file", recordedBlob.blob, "recording.wav");
      const action = uploadOrTranslateRef.current;
      try {
        setDisplayText(`Processing ${action === 'translate' ? 'translation' : 'transcription'}...`);
        const response = await axios.post(
          `http://localhost:5001/api/Voice/${action}`,
          formData,
          {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          }
        );

        const result = response.data.translation || response.data.text || "No result available";
        setDisplayText(result);
      } catch (error) {
        console.error("Error uploading the file:", error);
        setDisplayText(`Error: ${error.response?.data?.message || error.message || "Unknown error occurred"}`);
      } finally {
        setLoading(false);
      }
    } else {
      console.error("Recorded blob is empty or invalid");
      setDisplayText("Error: Recording failed. Please try again.");
    }
  };

  const handleFileChange = async (event) => {
    const audioFile = event.target.files[0];
    if (!audioFile) return;

    setLoading(true);
    setDisplayText("Processing file upload...");
    
    const formData = new FormData();
    formData.append("file", audioFile);

    try {
      const response = await axios.post(
        "http://localhost:5001/api/Voice/upload",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      const result = response.data.DisplayText || response.data.displayText || response.data.text || "No transcription available";
      setDisplayText(result);
    } catch (error) {
      console.error("Error uploading the file:", error);
      setDisplayText(`Error: ${error.response?.data?.message || error.message || "Failed to process file"}`);
    } finally {
      setLoading(false);
    }
  };

  async function textToSpeech() {
    if (!displayText || displayText === "Ready to test speech...") {
      setDisplayText("Error: No text to speak");
      return;
    }

    setLoading(true);
    setDisplayText("Preparing speech synthesis...");

    try {
      const tokenObj = await getTokenOrRefresh();
      
      if (!tokenObj || !tokenObj.authToken || !tokenObj.region) {
        throw new Error("Failed to get speech token. Please check your Azure configuration.");
      }

      console.log("Speech token and region:", tokenObj.authToken ? "Token received" : "No token", tokenObj.region);

      const speechConfig = speechsdk.SpeechConfig.fromAuthorizationToken(
        tokenObj.authToken,
        tokenObj.region
      );
      
      // Set speech synthesis voice (optional - improves quality)
      speechConfig.speechSynthesisVoiceName = "en-US-AriaNeural";
      
      const myPlayer = new speechsdk.SpeakerAudioDestination();
      updatePlayer((p) => ({ ...p, p: myPlayer }));
      
      const audioConfig = speechsdk.AudioConfig.fromSpeakerOutput(myPlayer);

      let synthesizer = new speechsdk.SpeechSynthesizer(
        speechConfig,
        audioConfig
      );

      const originalText = displayText;
      const textToSpeak = displayText.trim();
      
      setDisplayText(`🔊 Speaking: "${textToSpeak.substring(0, 50)}${textToSpeak.length > 50 ? '...' : ''}"`);

      synthesizer.speakTextAsync(
        textToSpeak,
        (result) => {
          let resultText;
          if (result.reason === speechsdk.ResultReason.SynthesizingAudioCompleted) {
            resultText = `✅ Speech synthesis completed successfully for: "${textToSpeak.substring(0, 50)}${textToSpeak.length > 50 ? '...' : ''}"`;
          } else if (result.reason === speechsdk.ResultReason.Canceled) {
            const cancellation = speechsdk.CancellationDetails.fromResult(result);
            resultText = `❌ Speech synthesis cancelled. Reason: ${cancellation.reason}. Error: ${cancellation.errorDetails || result.errorDetails}`;
          } else {
            resultText = `⚠️ Speech synthesis completed with unexpected result: ${result.reason}`;
          }
          
          synthesizer.close();
          synthesizer = undefined;
          setDisplayText(originalText); // Restore original text
          setLoading(false);
          
          // Show result temporarily
          setTimeout(() => {
            if (displayText === originalText) {
              console.log(resultText);
            }
          }, 100);
        },
        function (err) {
          const errorMessage = `❌ Speech synthesis error: ${err}`;
          console.error(errorMessage);
          setDisplayText(originalText); // Restore original text
          setLoading(false);
          
          // Show error temporarily
          setTimeout(() => {
            console.error(errorMessage);
          }, 100);

          synthesizer.close();
          synthesizer = undefined;
        }
      );
    } catch (error) {
      console.error("Text-to-speech setup error:", error);
      setDisplayText(`❌ Error: ${error.message || "Failed to initialize speech synthesis"}`);
      setLoading(false);
    }
  }

  async function handleMute() {
    updatePlayer((p) => {
      if (!p.muted) {
        p.p.pause();
        return { p: p.p, muted: true };
      } else {
        p.p.resume();
        return { p: p.p, muted: false };
      }
    });
  }

  const clearText = () => {
    setDisplayText("Ready to test speech...");
  };

  return (
    <div className="ai-card">
      <div className="ai-card-header">Speech-to-Text & Translation</div>
      <div className="ai-card-body ai-flex-col ai-gap-lg">
        <div className="ai-flex-row ai-gap-md ai-center">
          <div className="ai-mic-container">
            <ReactMic
              record={recording}
              className="ai-sound-wave"
              onStop={onStop}
              mimeType="audio/webm"
              strokeColor="#4F8EF7"
              backgroundColor="#f4f6fa"
            />
            <div className="ai-btn-group ai-mt-md">
              <button 
                className={`ai-btn ${recording ? "ai-btn-danger ai-recording" : "ai-btn-primary"}`} 
                onClick={startRecording}
                disabled={loading}
              >
                <span className="ai-btn-icon">{recording ? "🔴" : "🎤"}</span> Record
              </button>
              <button
                className={`ai-btn ${recording ? "ai-btn-danger ai-recording" : "ai-btn-accent"}`}
                onClick={startTranslateRecording}
                disabled={loading}
              >
                <span className="ai-btn-icon">{recording ? "🔴" : "🌐"}</span> Record & Translate
              </button>
              <button 
                className="ai-btn ai-btn-danger" 
                onClick={stopRecording}
                disabled={!recording}
              >
                <span className="ai-btn-icon">⏹️</span> Stop
              </button>
            </div>
          </div>
          <div className="ai-upload-container ai-flex-col ai-gap-sm">
            <button
              className="ai-btn ai-btn-secondary"
              type="button"
              onClick={() => fileInputRef.current && fileInputRef.current.click()}
              disabled={loading}
            >
              <span className="ai-btn-icon">{loading ? "⏳" : "📁"}</span> 
              {loading ? "Processing..." : "Upload audio file"}
            </button>
            <input
              type="file"
              id="audio-file"
              ref={fileInputRef}
              onChange={handleFileChange}
              style={{ display: "none" }}
              accept="audio/*"
            />
            <span className="ai-hint">
              Convert speech to text from an audio file.
            </span>
          </div>
        </div>
        <div className="ai-flex-row ai-gap-md ai-center ai-mt-md">
          <button 
            className="ai-btn ai-btn-success" 
            onClick={textToSpeech}
            disabled={!displayText || displayText === "Ready to test speech..." || loading}
          >
            <span className="ai-btn-icon">🔊</span> Text to Speech
          </button>
          <button 
            className="ai-btn ai-btn-warning" 
            onClick={handleMute}
            disabled={!player.p}
          >
            <span className="ai-btn-icon">{player.muted ? "▶️" : "⏸️"}</span> 
            {player.muted ? "Resume" : "Pause"}
          </button>
          <button 
            className="ai-btn ai-btn-secondary" 
            onClick={clearText}
            disabled={displayText === "Ready to test speech..."}
          >
            <span className="ai-btn-icon">🗑️</span> Clear
          </button>
        </div>
        <div className="ai-result-container ai-mt-lg">
          <label className="ai-label">
            Result / Translation 
            {loading && <span style={{color: 'var(--ai-primary)'}}>● Processing</span>}
          </label>
          <textarea
            className="ai-output-display"
            value={displayText}
            onChange={(e) => setDisplayText(e.target.value)}
            rows={6}
            placeholder="Speech results will appear here..."
          />
        </div>
      </div>
    </div>
  );
}
