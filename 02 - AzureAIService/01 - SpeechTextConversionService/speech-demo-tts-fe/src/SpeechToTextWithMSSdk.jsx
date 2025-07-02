import React, { useState, useEffect, useRef } from "react";
import * as sdk from "microsoft-cognitiveservices-speech-sdk";

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

  const startListening = () => {
    if (!isListening && recognizer.current) {
      setIsListening(true);
      recognizer.current.startContinuousRecognitionAsync(() => {
        console.log("Started listening...");
      });
    }
  };

  const stopListening = () => {
    setIsListening(false);
    recognizer.current && recognizer.current.stopContinuousRecognitionAsync(() => {
      console.log("Speech recognition stopped.");
    });
  };

  return (
    <div>
      <button onClick={pauseListening}>Pause Listening</button>
      <button onClick={startListening}>Start Listening</button>
      <button onClick={stopListening}>Stop Listening</button>
      <div>
        <div>Recognizing Transcript :</div>
        <div>
          <textarea
            rows="5"
            cols="40"
            value={recognizingTranscript}
            readOnly
          />
        </div>
        <div>RecognizedTranscript :</div>
        <div>
          <textarea rows="5" cols="40" value={myTranscript} readOnly />
        </div>
      </div>
    </div>
  );
}
