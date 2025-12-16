
import { GoogleGenAI, Type } from "@google/genai";
import { AIParseResult, Task } from "../types";

const apiKey = process.env.API_KEY;

if (!apiKey) {
  console.error("API_KEY is missing via process.env.API_KEY");
}

const ai = new GoogleGenAI({ apiKey: apiKey || 'dummy-key-for-dev' });

// Helper to create recursive schema levels
const createSubtaskSchema = (depth: number): any => {
  const baseProperties = {
    id: { type: Type.STRING, description: "Keep existing ID if updating, or use 'NEW'" },
    title: { type: Type.STRING },
    isCompleted: { type: Type.BOOLEAN },
  };

  if (depth === 0) {
    return {
      type: Type.OBJECT,
      properties: baseProperties,
      required: ["title"]
    };
  }
  return {
    type: Type.OBJECT,
    properties: {
      ...baseProperties,
      subtasks: {
        type: Type.ARRAY,
        items: createSubtaskSchema(depth - 1)
      }
    },
    required: ["title"]
  };
};

export const parseTasksFromText = async (textInput: string, currentTasks: Task[]): Promise<AIParseResult> => {
  const currentDate = new Date().toISOString();
  
  // Simplify current tasks for context to save tokens, but keep IDs
  const contextList = currentTasks.map(t => ({
    id: t.id,
    title: t.title,
    dueDate: t.dueDate,
    isCompleted: t.isCompleted,
    subtasks: t.subtasks.map(s => ({ id: s.id, title: s.title, isCompleted: s.isCompleted })) 
  }));

  const prompt = `
    You are an expert Productivity Assistant. 
    Current Date/Time: ${currentDate}.
    
    YOUR GOAL: 
    Organize the user's life into a structured, actionable JSON list based on "User Instructions" and the "Current State".
    
    INPUT DATA:
    1. Current State (JSON): ${JSON.stringify(contextList)}
    2. User Instructions: "${textInput}"
    
    RULES FOR PROCESSING:
    1. **Updates**: Match existing tasks by ID/Title. Update fields if requested. KEEP THE SAME ID.
    2. **New Tasks**: Add new items with ID "NEW".
    3. **Categories**: If the user doesn't specify a category, INFER it from the context. Use one of these standard categories if possible: "Work", "Personal", "Health", "Education", "Finance", "Errands", "Home".
    4. **Dates**: If no time is specified but the task implies urgency (e.g., "urgent", "asap"), set priority to 'High'. If a day is mentioned ("Friday"), calculate the ISO date.
    5. **Completion**: If the user implies completion ("done", "finished", "checked off"), set 'isCompleted' to true.
    
    OUTPUT FORMAT:
    Return a JSON object with a 'tasks' array.
  `;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: prompt,
      config: {
        responseMimeType: 'application/json',
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            tasks: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  id: { type: Type.STRING, description: "Must match existing ID or be 'NEW'" },
                  title: { type: Type.STRING },
                  description: { type: Type.STRING },
                  dueDate: { type: Type.STRING, description: "ISO 8601 date string or null" },
                  priority: { type: Type.STRING, enum: ["High", "Medium", "Low"] },
                  category: { type: Type.STRING, description: "Inferred category (Work, Personal, etc)" },
                  isCompleted: { type: Type.BOOLEAN },
                  subtasks: { 
                    type: Type.ARRAY,
                    items: createSubtaskSchema(5)
                  }
                },
                required: ["title", "priority", "category"]
              }
            }
          },
          required: ["tasks"]
        }
      }
    });

    let text = response.text;
    if (!text) throw new Error("No response from AI");

    // Clean markdown code blocks if present (safeguard against AI formatting)
    if (text.startsWith('```json')) {
        text = text.replace(/^```json\n/, '').replace(/\n```$/, '');
    } else if (text.startsWith('```')) {
        text = text.replace(/^```\n/, '').replace(/\n```$/, '');
    }

    return JSON.parse(text) as AIParseResult;
  } catch (error) {
    console.error("Error parsing tasks with Gemini:", error);
    throw error;
  }
};
