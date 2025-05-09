<!DOCTYPE html>
<html>
<head>
</head>
<body>
<table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
     <tr>
     <td>
          <div  align="center">
          <img src="https://github.com/style-genie/agent505/blob/main/docs/agent505_logo2.png?raw=true" align="center" alt="Agent505 Logo" style="width: 70px; height: auto;">
          </div>
     </td>
     <td> <img width=800/>
          <p>Agent505 is a framework designed to simplify the management and orchestration of AI agents, providing tools for building autonomous systems with feedback loops. It integrates seamlessly with FastAPI for easy deployment and offers features for session management, message handling, context sharing, and supervision of agents.</p>
     </td>
</tr>
     <tr>
<h2>Agent505</h2>
</tr>
     <tr>
        <th style="padding: 10px; background-color: #f5f5f5; border: 1px solid #ddd;">Features</th>
        <th style="padding: 10px; background-color: #f5f5f5; border: 1px solid #ddd;">Description</th>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd;">Agent505 - Agent Orchestrator</td>
        <td style="padding: 10px; border: 1px solid #ddd;">
            <ul style="margin: 0; padding-left: 20px;">
                <li>Framework for managing agents, crews and supervisors</li>
                <li>Simple integration with FastAPI</li>
                <li>Share context between agents</li>
                <li>Supervise agents</li>
                <li>Build autonomous agents with feedback loops</li>
            </ul>
        </td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd;">Session Manager</td>
        <td style="padding: 10px; border: 1px solid #ddd;">Manages agent sessions for faster interaction</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd;">Message Manager</td>
        <td style="padding: 10px; border: 1px solid #ddd;">Manages messages between agents, tools and supervisors and websockets asynchronously</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd;">Context Registry</td>
        <td style="padding: 10px; border: 1px solid #ddd;">
            <ul style="margin: 0; padding-left: 20px;">
                <li>Manages context between agents</li>
                <li>Allows for context to be shared between agents</li>
                <li>Provides a simple way to supervise agents by calling the responsible supervisor, or custom event-based user-callbacks</li>
            </ul>
        </td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd;">LiteLLM Implementation</td>
        <td style="padding: 10px; border: 1px solid #ddd;">
            Provides a simple way to use LiteLLM models and providers
            <ul style="margin: 10px 0 0 20px; padding-left: 0;">
                <li>Gemini</li>
                <li>open_router</li>
                <li>ollama_local</li>
                <li>openwebui</li>
                <li>HuggingFace</li>
            </ul>
        </td>
    </tr>
</table>
</body>
</html>


## Setup and Installation

-  **Clone the repository:**

    ```bash
    git clone https://github.com/style-genie/agent505
    cd agent505
    ```
### export api keys
```bash
export OPENROUTER_API_KEY=...
export OLLAMA_API_KEY=...
export OPENWEBUI_API_KEY=...
export GEMINI_API_KEY=...
```
### docker
- you might need to change the image in the compose file to python:3.11.3-alpine3.17
```bash
docker compose up 
```

### without docker
-  **Create a virtual environment (optional but recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```

-  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

The project uses environment variables for configuration. Create a `.env` file based on the `.env.sample` file and set the appropriate values.

## Usage
### Local
```bash
cd example
python e1.py
```
### Docker
```bash
docker compose up
```

## Examples

The `example/` directory contains example scripts that demonstrate how to use the project.

*   `example/advisor1.py`: This script is a FastAPI application that provides a style advisor. It initializes a session, interacts with a ModelContextProtocol, and uses a websocket for communication. It also defines a greeting message and sets up CORS middleware.
*   `example/tools.py`: This script defines several tools, including `internet_search_tool`, `wiki`, `fetch_elements_from_vector_db`, `get_json_element_by_id`, `read_user_data`, `write_user_data`, and `init_user_database`. These tools are used to search the internet, retrieve Wikipedia pages, fetch elements from a vector database, get JSON elements by ID, and manage user data in a database.

## Dependencies (including example)

The project depends on the following packages:

*   `setuptools>=61.0`
*   `python-dotenv==1.1.0`
*   `fastapi<0.114.0,>=0.113.0`
*   `pydantic<3.0.0,>=2.7.0`
*   `uvicorn==0.34.0`
*   `python-multipart==0.0.20`
*   `openai==1.76.0`
*   `litellm==1.67.1`
*   `fastapi-sessions==0.3.2`
*   `crewai==0.118.0`
*   `pathlib`
*   `mysql-connector-python==9.3.0`
*   `langchain==0.3.25`
*   `langchain-community==0.3.23`
*   `duckduckgo-search==8.0.1`
*   `wikipedia==1.4.0`
