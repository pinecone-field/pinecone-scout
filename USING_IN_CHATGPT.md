# Using Pinecone Scout in ChatGPT

This guide explains how to activate and use Pinecone Scout during your ChatGPT conversations.

## Prerequisites

1. ✅ Backend server running and accessible via ngrok or deployed URL
2. ✅ MCP server HTTP endpoint configured (`/mcp`)
3. ✅ ChatGPT Developer Mode enabled
4. ✅ Connector created in ChatGPT

## Step 1: Create/Configure the Connector

1. **Open ChatGPT** (chat.openai.com)

2. **Go to Settings**:
   - Click your profile icon (bottom left)
   - Click **Settings**
   - Go to **Apps & Connectors**

3. **Create a New Connector**:
   - Click **Create** or **Add Connector**
   - Fill in:
     - **Name**: `Pinecone Scout` (or any name you prefer)
     - **Description**: `AI-powered product recommendations`
     - **Connector URL**: `https://your-ngrok-url.ngrok-free.app/mcp`
       - Replace with your actual ngrok URL
       - Make sure to include `/mcp` at the end
   - Click **Create** or **Save**

4. **Verify Connection**:
   - After creating, ChatGPT should show a list of available tools
   - You should see: `recommend`, `submit_feedback`, `get_user_profile`, `predictive_suggest`
   - If you see these tools, the connection is working!

## Step 2: Activate the Tool in a Chat

There are several ways to activate Pinecone Scout in a conversation:

### Method 1: Use the Tools Button (Recommended)

1. **Start a new chat** in ChatGPT
2. **Click the `+` (plus) button** next to the message input box
3. **Look for "Developer Mode"** or "Connectors" section
4. **Toggle ON** your "Pinecone Scout" connector
5. The tool is now active for this conversation

### Method 2: Mention the App by Name

1. **Start a new chat**
2. **Begin your message with the app name**:
   - "Pinecone Scout, I need a vacation"
   - "Using Pinecone Scout, find me a 50-inch TV"
   - ChatGPT should automatically activate the connector

### Method 3: Ask About Tools

1. **Start a new chat**
2. **Ask**: "What tools do you have available?"
3. ChatGPT should list Pinecone Scout tools
4. **Then ask**: "Use Pinecone Scout to find me a TV"

## Step 3: Using the Tools

Once activated, you can use natural language and ChatGPT will automatically call the appropriate tools:

### Get Recommendations

**Example prompts:**
- "I'm looking for a 50-inch TV for my apartment"
- "Find me a sofa for my living room"
- "I need a cruise to the Mediterranean"

ChatGPT will call the `recommend` tool and show you product recommendations.

### Get Predictive Suggestions

**Example prompts:**
- "I need a vacation"
- "I'm planning a trip to Europe"
- "I want to redecorate my living room"

ChatGPT will call the `predictive_suggest` tool and provide contextual suggestions based on your conversation.

### Check Your Profile

**Example prompts:**
- "What are my preferences?"
- "Show me my profile"
- "What products have I liked?"

ChatGPT will call the `get_user_profile` tool.

### Provide Feedback

**Example prompts:**
- "I like the Samsung Frame TV recommendation"
- "I don't like that cruise option"
- "Mark that sofa as liked"

ChatGPT will call the `submit_feedback` tool to update your preferences.

## Step 4: Verify It's Working

### Check Tool Calls

1. **Look for tool indicators** in ChatGPT's response
   - You might see "Using Pinecone Scout..." or similar
   - The response should include actual product recommendations

2. **Check the backend logs**:
   ```bash
   # In your terminal where the backend is running
   # You should see API requests like:
   # POST /api/recommend
   # POST /api/predictive_suggest
   ```

3. **Check ngrok logs**:
   - In your ngrok terminal, you should see requests to `/mcp` and `/api/*`

### Test with a Simple Query

Try this exact prompt:
```
I need a vacation. Can you help me find something?
```

You should get:
- A cruise package recommendation
- Product details (name, price, URL)
- Natural, conversational response

## Troubleshooting

### Tool Not Activating

**Problem**: ChatGPT doesn't seem to be using the tool

**Solutions**:
1. **Verify connector is enabled**:
   - Go to Settings → Apps & Connectors
   - Make sure "Pinecone Scout" is toggled ON
   - Check that it shows "Connected" status

2. **Check the connector URL**:
   - Make sure it's `https://your-ngrok-url.ngrok-free.app/mcp`
   - Test the URL directly: `curl https://your-ngrok-url.ngrok-free.app/mcp`
   - Should return tool information

3. **Restart the chat**:
   - Start a completely new conversation
   - Activate the tool again

### Getting Empty Responses

**Problem**: Tool is called but returns no results

**Solutions**:
1. **Check backend logs** for errors
2. **Verify Pinecone indexes are populated**:
   ```bash
   # Run the populate scripts if needed
   python scripts/populate_items.py
   python scripts/generate_extended_products.py
   ```

3. **Check user_id**:
   - Make sure you're using a valid user_id
   - Try: "I'm user_001 and I need a vacation"

### Tool Not Appearing in List

**Problem**: ChatGPT doesn't show Pinecone Scout tools

**Solutions**:
1. **Check MCP endpoint**:
   ```bash
   curl https://your-ngrok-url.ngrok-free.app/mcp
   ```
   Should return JSON with tools list

2. **Check backend is running**:
   ```bash
   curl https://your-ngrok-url.ngrok-free.app/health
   ```
   Should return `{"status": "healthy"}`

3. **Recreate the connector**:
   - Delete the existing connector
   - Create a new one with the correct URL

## Tips for Best Results

1. **Be specific**: "I need a 50-inch TV" works better than "I need a TV"

2. **Use natural language**: ChatGPT will figure out which tool to call

3. **Provide context**: "I'm looking for a vacation for my family of 4" gives better results

4. **Give feedback**: Like/dislike products to improve future recommendations

5. **Use conversation history**: The predictive_suggest tool works best with ongoing conversations

## Example Conversation Flow

```
You: I'm planning a trip to Europe this spring

ChatGPT: [Calls predictive_suggest]
         "You might want to check out the 14-Day Mediterranean Cruise..."

You: That sounds expensive. Do you have anything cheaper?

ChatGPT: [Calls predictive_suggest with updated context]
         "If you're looking for something more budget-friendly, the 7-Day 
         Mediterranean Discovery Cruise is $4,500..."

You: I like that one

ChatGPT: [Calls submit_feedback]
         "Great! I've saved your preference for the 7-Day Mediterranean 
         Discovery Cruise. I'll keep this in mind for future recommendations."
```

## Next Steps

- **Populate more products**: Add more items to your indexes for better recommendations
- **Customize responses**: Modify the LLM prompts in `predictive_module.py` for different tones
- **Add more categories**: Expand beyond TVs, furniture, cruises, and experiences
- **Deploy to production**: When ready, deploy to Vercel or another platform

