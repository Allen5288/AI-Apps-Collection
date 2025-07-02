# Speech-to-Text and Text-to-Speech Demo (Azure Cognitive Services)

This project demonstrates how to use Azure Cognitive Services for both speech-to-text and text-to-speech in a React application. It includes:

- **Text to Speech**: Convert typed text into spoken audio using a simple component.
- **Speech to Text**: Use Azure's Speech SDK to transcribe spoken words into text in real time.

## Features

- Simple text-to-speech without extra libraries
- Speech-to-text using Microsoft Cognitive Services Speech SDK
- React functional components and hooks
- Environment variable support for Azure keys

## Getting Started

### Prerequisites

- Node.js and npm installed
- Azure Cognitive Services Speech resource (get your key and region from the Azure portal)

### Setup

1. Clone this repository.
2. Install dependencies:

   ```bash
   npm install
   ```

3. Create a `.env` file in the project root with your Azure credentials:

   ```env
   REACT_APP_SPEECH_KEY=your-azure-speech-key-here
   REACT_APP_SPEECH_REGION=your-azure-region-here
   ```

   **Note:** No spaces around the `=` sign.
4. Start the development server:

   ```bash
   npm start
   ```

## Project Structure

- `src/App.js` — Main app component, integrates both demos
- `src/SimpleTextToSpeech.js` — Simple text-to-speech React component
- `src/SpeechToTextWithMSSdk.jsx` — Speech-to-text using Azure SDK

## Scripts

- `npm start` — Run the app in development mode
- `npm test` — Run tests
- `npm run build` — Build for production

## References

- [Azure Cognitive Services Speech SDK](https://learn.microsoft.com/azure/cognitive-services/speech-service/)
- [Create React App Documentation](https://create-react-app.dev/)

## License

MIT
