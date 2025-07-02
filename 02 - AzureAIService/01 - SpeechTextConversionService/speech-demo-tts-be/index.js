const express = require("express");
const axios = require("axios");
const cors = require("cors");
require("dotenv").config();

const app = express();
const port = 5001;

// Enable CORS for all routes
app.use(
  cors({
    origin: "http://localhost:3000",
  })
);

app.get("/api/Voice/get-speech-token", async (req, res, next) => {
  res.setHeader("Content-Type", "application/json");
  const speechKey = process.env.AZURE_SPEECH_KEY;
  const speechRegion = process.env.AZURE_REGION;

  // Refer to https://learn.microsoft.com/en-us/azure/ai-services/authentication
  try {
    const response = await axios.post(
      `https://${speechRegion}.api.cognitive.microsoft.com/sts/v1.0/issueToken`,
      null,
      {
        headers: {
          "Ocp-Apim-Subscription-Key": speechKey,
        },
      }
    );
    res.json({ token: response.data, region: speechRegion });
  } catch (error) {
    console.error("Error fetching speech token:", error);
    res.status(500).json({ error: "Failed to fetch speech token" });
  }
});

app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
