import "./App.css";
import React from "react";
import SimpleTextToSpeech from "./SimpleTextToSpeech";
import { SpeechToTextWithMSSdk } from "./SpeechToTextWithMSSdk";

function App() {
  const [text, setText] = React.useState("");

  return (
    <div className="App">
      <div className="display-section">
        <h1>Text to Speech Demo with SimpleTextToSpeech</h1>
        <div className="group">
          <textarea
            rows="10"
            value={text}
            onChange={(e) => setText(e.target.value)}
          ></textarea>
        </div>
        <div>
          <h1>Simple TTS without extra library</h1>
          <SimpleTextToSpeech text={text} />
          <p>{text}</p>
        </div>
      </div>
      <div className="display-section">
        <h1>Speech to Text Demo with SpeechToTextWithMSSdk</h1>
        <SpeechToTextWithMSSdk />
      </div>
    </div>
  );
}

export default App;
