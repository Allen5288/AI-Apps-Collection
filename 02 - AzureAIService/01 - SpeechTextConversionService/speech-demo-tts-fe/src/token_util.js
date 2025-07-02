import axios from "axios";
import Cookie from "universal-cookie";

export async function getTokenOrRefresh() {
  const cookies = new Cookie();
  let tokenData = cookies.get("speechToken");
  
  // Check if token exists and is not expired (tokens are valid for 10 minutes)
  if (tokenData && tokenData.timestamp) {
    const tokenAge = Date.now() - tokenData.timestamp;
    const maxAge = 9 * 60 * 1000; // 9 minutes to be safe
    
    if (tokenAge < maxAge) {
      console.log("Using cached speech token");
      return {
        authToken: tokenData.token,
        region: tokenData.region,
      };
    } else {
      console.log("Speech token expired, fetching new one");
      cookies.remove("speechToken");
    }
  }

  try {
    console.log("Fetching new speech token from backend...");
    const response = await axios.get(
      "http://localhost:5001/api/Voice/get-speech-token",
      {
        timeout: 10000 // 10 second timeout
      }
    );
    
    if (!response.data || !response.data.token || !response.data.region) {
      throw new Error("Invalid token response from backend");
    }
    
    tokenData = {
      ...response.data,
      timestamp: Date.now()
    };
    
    cookies.set("speechToken", tokenData, { 
      path: "/",
      maxAge: 600 // 10 minutes
    });
    
    console.log("Successfully fetched speech token");
    return {
      authToken: tokenData.token,
      region: tokenData.region,
    };
  } catch (error) {
    console.error("Error fetching speech token:", error);
    
    if (error.code === 'ECONNREFUSED') {
      throw new Error("Backend server is not running. Please start the backend server on port 5001.");
    } else if (error.response) {
      throw new Error(`Backend error: ${error.response.status} - ${error.response.data}`);
    } else if (error.request) {
      throw new Error("Unable to reach backend server. Please check if it's running.");
    } else {
      throw new Error(`Token fetch failed: ${error.message}`);
    }
  }
}
