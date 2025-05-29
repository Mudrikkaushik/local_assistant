# AI Assistant Flask Web Application

A comprehensive web-based AI assistant that provides shopping assistance, chatbot functionality, local computer task management, and terminal automation.

## Features Overview

### 🛒 Shopping Assistant
- AI-powered product analysis using Google Gemini
- Real-time Amazon product search and scraping
- Rating-based product sorting and filtering
- CSV export of search results with timestamps
- Price comparison and intelligent recommendations

### 💬 AI Chatbot
- Natural language conversations powered by Google Gemini
- File upload and content analysis capabilities
- Markdown support for rich text responses
- Context-aware interactions with file content
- Real-time streaming responses with typing indicators

### 💻 Local Tasks Management
- **Development Tools**: Open VS Code, Terminal, File Explorer
- **System Controls**: Bluetooth management, Audio device connection, System information
- **Media Controls**: YouTube Music, IMDB, Media Player
- Cross-platform support (Windows, macOS, Linux)

### 🖥️ Terminal & File Manager (from test_flask.py)
- Execute terminal commands with GUI automation
- Create and write files using Notepad (Windows) or direct file operations
- PyAutoGUI integration for seamless desktop automation
- Command history and status feedback

## Complete API Endpoint Mapping

### Main Application Routes
- `GET /` - Home page with feature overview
- `GET /shopping` - Shopping assistant interface
- `GET /chatbot` - AI chatbot interface  
- `GET /local-tasks` - Local tasks management panel
- `GET /terminal` - Terminal command and file manager interface

### Shopping Assistant API
```bash
POST /api/search
Content-Type: application/json
{
    "query": "Find the best phone under 12000"
}

Response:
{
    "ai_analysis": "Detailed AI analysis...",
    "products": [
        {
            "title": "Product Name",
            "price": "₹9,999",
            "rating": "4.2 out of 5 stars",
            "rating_value": 4.2,
            "reviews": "1,234 reviews"
        }
    ],
    "csv_file": "results/search_results_20231215_143022.csv"
}
```

### Chatbot API
```bash
POST /api/chat
Content-Type: application/json
{
    "message": "Explain this code",
    "file_content": "optional file content for analysis"
}

Response:
{
    "response": "AI-generated response with markdown formatting"
}
```

### Local Tasks API
```bash
POST /api/local-task/<task_name>

Available tasks:
- open_vscode
- open_terminal  
- open_file_explorer
- toggle_bluetooth
- connect_audio
- show_system_info
- play_youtube_music
- show_movie_details
- open_media_player

Response:
{
    "status": "success|error",
    "message": "Task completion message",
    "data": "optional additional data (for system_info)"
}
```

### Terminal Management API (from test_flask.py)
```bash
POST /run
Content-Type: application/x-www-form-urlencoded or application/json
{
    "cmd": "echo Hello World"
}

Response:
{
    "status": "success|error",
    "message": "Command execution status",
    "output": "command output (Unix systems)"
}
```

```bash
POST /write
Content-Type: application/x-www-form-urlencoded or application/json
{
    "filename": "maddy.txt",
    "content": "File content to write"
}

Response:
{
    "status": "success|error", 
    "message": "File operation status"
}
```

### File Upload API
```bash
POST /api/file-upload
Content-Type: multipart/form-data
file: [uploaded file]

Response:
{
    "status": "success",
    "filename": "document.txt",
    "content": "file content as string",
    "message": "Upload status"
}
```

### System Status API
```bash
GET /api/status

Response:
{
    "status": "running",
    "system_info": {
        "platform": "Windows",
        "platform_version": "10.0.19044",
        "python_version": "3.9.7",
        "processor": "Intel64 Family 6 Model 142 Stepping 10, GenuineIntel",
        "machine": "AMD64"
    },
    "features": {
        "shopping_assistant": true,
        "chatbot": true,
        "local_tasks": true,
        "terminal_commands": true,
        "file_operations": true
    }
}
```

## Backend Architecture

### Class Structure

#### ShoppingAssistant
- `get_edge_version()`: Detect Microsoft Edge version
- `setup_edge_driver()`: Configure Selenium WebDriver
- `search_amazon_products(query)`: Scrape Amazon search results
- `get_ai_analysis(query)`: Generate AI recommendations

#### LocalTasksManager
- Static methods for each local task
- Cross-platform command execution
- Application launching and system control

#### TerminalManager (New from test_flask.py)
- `run_command(cmd)`: Execute terminal commands with GUI automation
- `write_file(filename, content)`: Create files using Notepad automation

#### ChatBot
- `get_response(message, file_content)`: AI conversation handling
- Context-aware responses with file analysis

### Technology Stack

- **Backend Framework**: Flask 2.3.3
- **AI Integration**: Google Gemini API (generative-ai 0.3.2)
- **Web Automation**: Selenium 4.15.2 with Edge WebDriver
- **GUI Automation**: PyAutoGUI 0.9.54
- **Frontend**: Bootstrap 5, jQuery, Font Awesome
- **UI Framework**: PySide6 6.6.0 (for standalone GUI)
- **File Processing**: CSV export, Markdown rendering

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- Microsoft Edge browser (for web scraping)
- Google Gemini API key

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd local-ai_assistant

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### 4. Running the Application

```bash
# Start Flask server
python app.py

# Alternative: Run standalone GUI
python gui.py
```

The web application will be available at `http://localhost:5000`

## GUI to Flask Mapping

### Shopping Functionality
- **GUI**: `WorkerThread` class handles Amazon scraping in separate thread
- **Flask**: `ShoppingAssistant` class provides same functionality via API
- **Endpoint**: `POST /api/search`

### Chat Functionality  
- **GUI**: Direct Gemini API calls with file content integration
- **Flask**: `ChatBot` class with identical functionality
- **Endpoint**: `POST /api/chat`

### Local Tasks
- **GUI**: Direct system calls within GUI application
- **Flask**: `LocalTasksManager` with web interface
- **Endpoint**: `POST /api/local-task/<task_name>`

### Terminal Operations (test_flask.py)
- **Original**: Simple form-based interface with PyAutoGUI
- **Enhanced**: JSON API with modern web interface
- **Endpoints**: `POST /run`, `POST /write`

## Security Considerations

- API keys stored in environment variables
- Local task execution requires appropriate system permissions
- File operations restricted to application directory
- Web scraping respects robots.txt and implements rate limiting
- CORS and input validation for all API endpoints

## Cross-Platform Compatibility

### Windows
- PowerShell commands for system control
- Notepad integration for file editing
- Windows Registry access for Edge version detection

### macOS/Linux  
- Native terminal commands
- Alternative application launching methods
- Unix-style system information gathering

## Development Notes

### Frontend Integration
All Flask endpoints return JSON for seamless frontend integration. The web interface uses:
- AJAX calls for API communication
- Bootstrap components for responsive design
- Real-time status updates and progress indicators
- File upload handling with drag-and-drop support

### Error Handling
- Comprehensive exception handling in all classes
- Graceful degradation when services are unavailable
- User-friendly error messages with troubleshooting hints
- Logging integration for debugging and monitoring

### Performance Optimization
- Threaded operations for long-running tasks
- CSV caching for search results
- Efficient DOM parsing for web scraping
- Connection pooling for API requests

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 