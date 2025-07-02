import "./App.css";
import React from "react";
import SimpleTextToSpeech from "./SimpleTextToSpeech";

function App() {
  const [text, setText] = React.useState("");

  return (
    <div className="App">
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
  );
}

export default App;
