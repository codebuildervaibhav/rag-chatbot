# AI Chatbot (Unified Frontend) 🤖

This project is a modern, web-based chatbot interface built with a **React/TypeScript frontend** that directly communicates with a local Ollama instance. It provides a sleek, responsive, and feature-rich chat experience with Google's Gemma or any other supported Ollama model.

The UI is heavily inspired by leading AI chat interfaces, featuring a polished dark theme, real-time message streaming, and excellent markdown rendering.

## Features ✨

-   **Modern Tech Stack**: React, TypeScript, and Tailwind CSS for the frontend; npm as the package manager.
-   **Direct Ollama Integration**: Frontend directly interacts with the Ollama API for chat and streaming.
-   **Real-time Streaming**: HTTP streaming from Ollama provides token-by-token responses for a smooth "live typing" effect.
-   **Rich Markdown Rendering**: Beautifully formats code blocks with syntax highlighting, lists, bold/italic text, and other markdown elements.
-   **Custom System Instructions**: Easily configure the model's persona, rules, and objectives directly in the frontend's `App.tsx` or `useChatSocket.ts`.
-   **Dark Theme UI**: A professionally designed, responsive, and aesthetically pleasing dark mode interface.
-   **Connection Status**: The UI provides clear, real-time feedback on the Ollama server connection status.

-----

## Project Structure 📂

The project is now a single-application structure:

```
.
├── public/
├── src/
│   ├── components/
│   │   ├── ChatInput.tsx
│   │   ├── ChatView.tsx
│   │   ├── Header.tsx
│   │   └── Message.tsx
│   ├── hooks/
│   │   └── useChatSocket.ts  # Now handles direct Ollama communication
│   ├── App.tsx
│   ├── index.css
│   └── main.tsx
├── index.html
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── tsconfig.json
├── tsconfig.node.json
└── .gitignore
```

-----

## How It Works ⚙️

### Frontend (`src/`)

The frontend is a single-page application built with React and TypeScript. It now directly manages communication with the Ollama server.

-   **`src/App.tsx`**: The root component that assembles the UI and manages the overall application state. It initializes the `useChatSocket` hook.
-   **`src/hooks/useChatSocket.ts`**: This custom hook now encapsulates all logic for direct HTTP communication with the Ollama API.
    -   It checks the Ollama server's availability.
    -   It maintains the conversation history (including a system instruction).
    -   It sends user messages to the Ollama `/api/chat` endpoint.
    -   It handles streaming responses from Ollama, updating the UI token-by-token.
-   **`src/components/`**: Reusable UI components for the header, chat view, message bubbles, and input form.
    -   **`Message.tsx`**: Uses `react-markdown` and `react-syntax-highlighter` to correctly render streamed markdown content.

-----

## Getting Started 🚀

### Prerequisites

-   **Node.js and npm**: Ensure Node.js is installed, which includes npm. ([Download](https://nodejs.org/))
-   **Ollama**: Ensure Ollama is installed and running. ([Download](https://ollama.com/))
-   **A Model**: Pull the desired Gemma model from Ollama (e.g., `ollama pull gemma3:270m`).

### Installation

1.  **Clone the repository (if you haven't already):**

    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Install dependencies** using npm (from the project root):

    ```bash
    npm install
    ```

### Running the Application

You'll need to run the Ollama server and then the React frontend.

1.  **Start the Ollama Server (in a WSL terminal):**
    First, set the `OLLAMA_HOST` environment variable to allow external connections, then start the server.
    ```bash
    export OLLAMA_HOST=0.0.0.0
    ollama serve
    ```
    Make sure you have the `gemma3:270m` model pulled: `ollama pull gemma3:270m` (if not already present).

2.  **Start the React Frontend Development Server (in a new terminal):**
    Navigate to the project root directory and start the frontend development server.
    ```bash
    npm run dev
    ```
    The frontend will typically be available at `http://localhost:5173`.

3.  **Open your browser** and navigate to **`http://localhost:5173`** (or the port indicated by your frontend dev server) to start chatting!

### Important Notes on Ollama and CORS

-   The frontend directly calls `http://localhost:11434`. If you encounter **CORS (Cross-Origin Resource Sharing) errors** in your browser's console, you might need to configure Ollama to allow requests from your frontend's origin (`http://localhost:5173`).
-   Ollama typically allows `localhost` origins by default, but if issues arise, you can set the `OLLAMA_ORIGINS` environment variable before starting Ollama:
    ```bash
    export OLLAMA_ORIGINS="http://localhost:5173"
    export OLLAMA_HOST=0.0.0.0
    ollama serve
    ```
    Replace `http://localhost:5173` with the actual URL your frontend is running on if it's different.