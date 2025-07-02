# Azure Speech Token Backend API

This is a simple Express.js backend for securely issuing Azure Cognitive Services Speech API tokens to your frontend applications.

## Features

- Issues short-lived Azure Speech API tokens to clients
- Keeps your Azure subscription key secure (never exposed to frontend)
- CORS enabled for local development

## How It Works

- The backend exposes a single endpoint: `/api/Voice/get-speech-token`
- It uses your Azure Speech subscription key and region to request a token from Azure
- Returns a JSON response: `{ token: <token>, region: <region> }`

## Setup

1. Install dependencies:

   ```bash
   npm install
   ```

2. Create a `.env` file in the project root with your Azure credentials:

   ```env
   AZURE_SPEECH_KEY=your-azure-speech-key-here
   AZURE_REGION=your-azure-region-here
   ```

3. Start the server:

   ```bash
   node index.js
   ```

   The server will run on `http://localhost:5001` by default.

## Endpoint

- `GET /api/Voice/get-speech-token`
  - Returns: `{ token: <token>, region: <region> }`

## Security Note

- Never expose your Azure Speech subscription key to the frontend or client-side code.
- This backend ensures your key is kept secret and only issues short-lived tokens.

## References

- [Azure Cognitive Services Speech Authentication](https://learn.microsoft.com/azure/ai-services/authentication)
- [Azure Speech Service Documentation](https://learn.microsoft.com/azure/cognitive-services/speech-service/)

## License

MIT
