from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import subprocess
import platform
import webbrowser
import time
import json
import csv
from datetime import datetime
import markdown
from dotenv import load_dotenv
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
import threading
import pyautogui

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Load environment variables
load_dotenv()

class ShoppingAssistant:
    def __init__(self):
        self.products = []
        self.ai_analysis = ""

    def get_edge_version(self):
        try:
            if platform.system() == "Windows":
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Edge\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                return version
            else:
                process = subprocess.Popen(['microsoft-edge', '--version'], stdout=subprocess.PIPE)
                output = process.communicate()[0].decode('utf-8')
                return output.strip().split()[-1]
        except Exception:
            return None

    def setup_edge_driver(self):
        try:
            edge_options = Options()
            edge_options.add_argument("--start-maximized")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--disable-extensions")
            edge_options.add_argument("--disable-popup-blocking")
            edge_options.add_argument("--disable-blink-features=AutomationControlled")
            
            service = Service(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=edge_options)
            return driver
            
        except Exception as e:
            try:
                edge_options.add_argument("--headless=new")
                service = Service(EdgeChromiumDriverManager().install())
                driver = webdriver.Edge(service=service, options=edge_options)
                return driver
            except Exception as e2:
                raise Exception(f"Failed to setup Edge driver: {str(e2)}")

    def search_amazon_products(self, query):
        try:
            driver = self.setup_edge_driver()
            
            # Navigate to Amazon
            driver.get("https://www.amazon.in")
            
            # Wait for search box and enter query
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "twotabsearchtextbox"))
            )
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            
            # Wait for results to load
            time.sleep(3)
            
            # Extract product information
            products = []
            product_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
            
            for element in product_elements[:10]:  # Get first 10 products
                try:
                    title = element.find_element(By.CSS_SELECTOR, "h2 span").text
                    try:
                        price = element.find_element(By.CSS_SELECTOR, ".a-price-whole").text
                    except:
                        price = "Price not available"
                    
                    try:
                        rating = element.find_element(By.CSS_SELECTOR, ".a-icon-star-small").get_attribute("innerHTML")
                        rating_match = re.search(r'(\d+\.?\d*)', rating)
                        rating_value = float(rating_match.group(1)) if rating_match else 0
                    except:
                        rating = "No rating"
                        rating_value = 0
                    
                    try:
                        reviews = element.find_element(By.CSS_SELECTOR, ".a-size-small .a-link-normal").text
                    except:
                        reviews = "No reviews"
                    
                    products.append({
                        "title": title,
                        "price": price,
                        "rating": rating,
                        "rating_value": rating_value,
                        "reviews": reviews
                    })
                    
                except Exception as e:
                    continue
            
            # Sort products by rating value
            products.sort(key=lambda x: x['rating_value'], reverse=True)
            
            driver.quit()
            return products
            
        except Exception as e:
            return []

    def get_ai_analysis(self, query):
        try:
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            response = model.generate_content(f"""
            Analyze this request and provide a structured response:
            {query}
            Format the response in a clear, organized way with:
            1. Main recommendations
            2. Key features to consider
            3. Price range analysis
            """)
            
            return response.text
        except Exception as e:
            return f"AI analysis unavailable: {str(e)}"

class LocalTasksManager:
    @staticmethod
    def open_vscode():
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["code"])
            else:
                subprocess.Popen(["code", "."])
            return {"status": "success", "message": "VS Code launched successfully"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to launch VS Code: {str(e)}"}

    @staticmethod
    def open_terminal():
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["cmd"])
            else:
                subprocess.Popen(["gnome-terminal"])
            return {"status": "success", "message": "Terminal launched successfully"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to launch terminal: {str(e)}"}

    @staticmethod
    def open_file_explorer():
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["explorer"])
            else:
                subprocess.Popen(["nautilus"])
            return {"status": "success", "message": "File Explorer launched successfully"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to launch File Explorer: {str(e)}"}

    @staticmethod
    def toggle_bluetooth():
        try:
            if platform.system() == "Windows":
                subprocess.run(["powershell", "-Command", "Get-Service -Name bthserv | Set-Service -StartupType Manual"])
                subprocess.run(["powershell", "-Command", "Start-Service bthserv"])
            else:
                subprocess.run(["bluetoothctl", "power", "on"])
            return {"status": "success", "message": "Bluetooth toggled successfully"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to toggle Bluetooth: {str(e)}"}

    @staticmethod
    def connect_audio():
        try:
            if platform.system() == "Windows":
                # Simplified audio connection for Windows
                subprocess.run(["powershell", "-Command", "Start-Process ms-settings:connecteddevices"])
            else:
                subprocess.run(["bluetoothctl", "scan", "on"])
            return {"status": "success", "message": "Opening audio device settings..."}
        except Exception as e:
            return {"status": "error", "message": f"Failed to open audio settings: {str(e)}"}

    @staticmethod
    def show_system_info():
        try:
            if platform.system() == "Windows":
                info = subprocess.check_output(["systeminfo"], shell=True).decode()
            else:
                info = subprocess.check_output(["uname", "-a"]).decode()
            return {"status": "success", "message": f"System Information retrieved", "data": info}
        except Exception as e:
            return {"status": "error", "message": f"Failed to get system information: {str(e)}"}

    @staticmethod
    def play_youtube_music():
        try:
            webbrowser.open("https://music.youtube.com")
            return {"status": "success", "message": "Opening YouTube Music..."}
        except Exception as e:
            return {"status": "error", "message": f"Failed to open YouTube Music: {str(e)}"}

    @staticmethod
    def show_movie_details():
        try:
            webbrowser.open("https://www.imdb.com")
            return {"status": "success", "message": "Opening IMDB..."}
        except Exception as e:
            return {"status": "error", "message": f"Failed to open IMDB: {str(e)}"}

    @staticmethod
    def open_media_player():
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["wmplayer"])
            else:
                subprocess.Popen(["vlc"])
            return {"status": "success", "message": "Media player launched successfully"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to launch media player: {str(e)}"}

class TerminalManager:
    """Handles terminal command execution and file operations from test_flask.py"""
    
    @staticmethod
    def run_command(cmd):
        try:
            # Open CMD and run command
            if platform.system() == "Windows":
                subprocess.Popen("start cmd", shell=True)
                time.sleep(1.5)  # Wait for CMD to open
                
                # Type the command and press Enter
                pyautogui.typewrite(cmd)
                pyautogui.press("enter")
                
                return {"status": "success", "message": f"Command '{cmd}' executed in terminal"}
            else:
                # For Unix-like systems, run command directly
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                return {"status": "success", "message": f"Command executed", "output": result.stdout}
        except Exception as e:
            return {"status": "error", "message": f"Failed to execute command: {str(e)}"}
    
    @staticmethod
    def write_file(filename, content):
        try:
            filepath = os.path.abspath(filename)
            
            # Step 1: Create empty file
            with open(filepath, 'w', encoding='utf-8') as f:
                pass
            
            if platform.system() == "Windows":
                # Step 2: Open in Notepad
                subprocess.Popen(['notepad.exe', filepath])
                time.sleep(1.5)
                
                # Step 3: Type the content
                pyautogui.typewrite(content, interval=0.02)
                time.sleep(0.5)
                
                # Step 4: Close Notepad with save
                pyautogui.hotkey('alt', 'f4')
                time.sleep(0.5)
                pyautogui.press('left')  # Choose 'Save'
                pyautogui.press('enter')
            else:
                # For Unix-like systems, write directly
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return {"status": "success", "message": f"File '{filename}' created and written successfully"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to write file: {str(e)}"}

class ChatBot:
    @staticmethod
    def get_response(message, file_content=None):
        try:
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            if file_content:
                prompt = f"Analyze the following file content and answer the user's question.\n\nFile Content:\n{file_content}\n\nUser Question: {message}"
            else:
                prompt = message
                
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"AI error: {str(e)}"

# Initialize instances
shopping_assistant = ShoppingAssistant()
local_tasks = LocalTasksManager()
terminal_manager = TerminalManager()
chatbot = ChatBot()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/shopping')
def shopping():
    return render_template('shopping.html')

@app.route('/chatbot')
def chatbot_page():
    return render_template('chatbot.html')

@app.route('/local-tasks')
def local_tasks_page():
    return render_template('local_tasks.html')

@app.route('/api/search', methods=['POST'])
def search_products():
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    try:
        # Get AI analysis
        ai_analysis = shopping_assistant.get_ai_analysis(query)
        
        # Search products (this might take time, so we'll do it in background)
        products = shopping_assistant.search_amazon_products(query)
        
        # Save results to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'results/search_results_{timestamp}.csv'
        
        if not os.path.exists('results'):
            os.makedirs('results')
            
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Product Name', 'Price (₹)', 'Rating', 'Number of Reviews', 'Search Query', 'Search Timestamp'])
            
            for product in products:
                writer.writerow([
                    product['title'],
                    product['price'],
                    product['rating'],
                    product['reviews'],
                    query,
                    timestamp
                ])
        
        return jsonify({
            "ai_analysis": ai_analysis,
            "products": products,
            "csv_file": filename
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')
    file_content = data.get('file_content', None)
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    try:
        response = chatbot.get_response(message, file_content)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/local-task/<task_name>', methods=['POST'])
def execute_local_task(task_name):
    try:
        if task_name == 'open_vscode':
            result = local_tasks.open_vscode()
        elif task_name == 'open_terminal':
            result = local_tasks.open_terminal()
        elif task_name == 'open_file_explorer':
            result = local_tasks.open_file_explorer()
        elif task_name == 'toggle_bluetooth':
            result = local_tasks.toggle_bluetooth()
        elif task_name == 'connect_audio':
            result = local_tasks.connect_audio()
        elif task_name == 'show_system_info':
            result = local_tasks.show_system_info()
        elif task_name == 'play_youtube_music':
            result = local_tasks.play_youtube_music()
        elif task_name == 'show_movie_details':
            result = local_tasks.show_movie_details()
        elif task_name == 'open_media_player':
            result = local_tasks.open_media_player()
        else:
            return jsonify({"error": "Unknown task"}), 400
            
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/terminal')
def terminal_page():
    """Terminal command and file writing interface from test_flask.py"""
    return render_template('terminal.html')

@app.route('/run', methods=['POST'])
def run_cmd():
    """Execute terminal command from test_flask.py"""
    if request.content_type == 'application/x-www-form-urlencoded':
        cmd = request.form['cmd']
    else:
        data = request.get_json()
        cmd = data.get('cmd', '')
    
    if not cmd:
        return jsonify({"status": "error", "message": "Command is required"}), 400
    
    try:
        result = terminal_manager.run_command(cmd)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/write', methods=['POST'])
def write_file():
    """Create and write file from test_flask.py"""
    if request.content_type == 'application/x-www-form-urlencoded':
        filename = request.form['filename']
        content = request.form['content']
    else:
        data = request.get_json()
        filename = data.get('filename', '')
        content = data.get('content', '')
    
    if not filename or not content:
        return jsonify({"status": "error", "message": "Filename and content are required"}), 400
    
    try:
        result = terminal_manager.write_file(filename, content)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/file-upload', methods=['POST'])
def upload_file():
    """Handle file uploads for chatbot analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Read file content
        content = file.read().decode('utf-8')
        
        return jsonify({
            "status": "success",
            "filename": file.filename,
            "content": content,
            "message": f"File '{file.filename}' uploaded successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get application status and system information"""
    try:
        system_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "machine": platform.machine(),
        }
        
        return jsonify({
            "status": "running",
            "system_info": system_info,
            "features": {
                "shopping_assistant": True,
                "chatbot": True,
                "local_tasks": True,
                "terminal_commands": True,
                "file_operations": True
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 