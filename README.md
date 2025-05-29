# Local AI Assistant

This application integrates Google's Gemini model with local system automation to perform web-based tasks based on user instructions.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory and add your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```

3. Make sure you have Google Chrome installed on your system.

## Usage

Run the application:
```bash
python main.py
```

Then you can give instructions like:
- "Find the best phone under 12000"
- "Search for the latest laptops on Amazon"
- "Compare prices of gaming monitors"

The assistant will:
1. Process your request using Gemini
2. Open Chrome browser
3. Navigate to relevant websites
4. Perform searches
5. Gather and present information

## Features

- Integration with Google's Gemini model
- Automated web browsing
- Price comparison
- Product research
- Natural language processing of user requests 