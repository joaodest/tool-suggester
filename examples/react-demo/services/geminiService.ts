import { GoogleGenAI } from "@google/genai";

const apiKey = process.env.API_KEY;

// Initialize the Gemini client
const ai = new GoogleGenAI({ apiKey: apiKey });

export const generateChatResponse = async (
  history: { role: string; text: string }[],
  userMessage: string
): Promise<string> => {
  if (!apiKey) {
    throw new Error("API Key not found in environment variables.");
  }

  try {
    const modelId = 'gemini-2.5-flash';
    
    const systemInstruction = `
      You are an intelligent assistant integrated into a platform that has access to specific tools.
      The user interface actively suggests tools to the user as they type.
      Your goal is to be helpful, answer questions, and if the user's intent strongly aligns with a known tool, 
      you can acknowledge it or ask for confirmation to proceed.
      
      Think deeply before answering complex queries.
    `;

    const contents = [
      ...history.map(msg => ({
        role: msg.role,
        parts: [{ text: msg.text }]
      })),
      {
        role: 'user',
        parts: [{ text: userMessage }]
      }
    ];

    const response = await ai.models.generateContent({
      model: modelId,
      contents: contents,
      config: {
        systemInstruction: systemInstruction,
        thinkingConfig: {
          thinkingBudget: 24576 // Max thinking budget for gemini 3 pro
        }
      }
    });

    return response.text || "I'm sorry, I couldn't generate a response.";

  } catch (error) {
    console.error("Gemini API Error:", error);
    return "Error communicating with the AI service. Please try again.";
  }
};
