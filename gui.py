import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                            QLabel, QProgressBar, QFrame, QScrollArea, QTabWidget, QFileDialog, QGroupBox)
from PySide6.QtCore import Qt, QThread, Signal, QPropertyAnimation, QEasingCurve, QSize, QTimer
from PySide6.QtGui import QFont, QIcon, QColor, QPalette, QLinearGradient, QGradient, QPainter, QBrush, QPixmap
import os
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
import platform
import subprocess
import shutil
import requests
import zipfile
import io
import re
import time
import json
import csv
from datetime import datetime
import markdown

class WorkerThread(QThread):
    update_signal = Signal(str)
    progress_signal = Signal(int)
    finished_signal = Signal()

    def __init__(self, query):
        super().__init__()
        self.query = query
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
            
            # Get Edge version
            edge_version = self.get_edge_version()
            if edge_version:
                self.update_signal.emit(f"Detected Edge version: {edge_version}")
            
            # Set up Edge driver
            self.update_signal.emit("Setting up Edge WebDriver...")
            service = Service(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=edge_options)
            return driver
            
        except Exception as e:
            self.update_signal.emit(f"❌ Error setting up Edge: {str(e)}")
            self.update_signal.emit("Attempting to use headless mode...")
            
            try:
                edge_options.add_argument("--headless=new")
                service = Service(EdgeChromiumDriverManager().install())
                driver = webdriver.Edge(service=service, options=edge_options)
                return driver
            except Exception as e2:
                self.update_signal.emit(f"❌ Headless mode also failed: {str(e2)}")
                raise

    def extract_price(self, price_text):
        try:
            # Remove currency symbol and convert to float
            return float(re.sub(r'[^\d.]', '', price_text))
        except:
            return float('inf')

    def search_amazon_products(self, driver, query, model):
        try:
            # Navigate to Amazon
            driver.get("https://www.amazon.in")
            self.update_signal.emit("🔍 Searching on Amazon...")
            
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
            
            for element in product_elements:  # Get all products on the first page
                try:
                    title = element.find_element(By.CSS_SELECTOR, "h2 span").text
                    try:
                        price = element.find_element(By.CSS_SELECTOR, ".a-price-whole").text
                    except:
                        price = "Price not available"
                    
                    try:
                        rating = element.find_element(By.CSS_SELECTOR, ".a-icon-star-small").get_attribute("innerHTML")
                        # Extract numeric rating from HTML
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
                    
                    # Highlight the product
                    driver.execute_script("arguments[0].style.border='3px solid red'", element)
                    
                except Exception as e:
                    continue
            
            # Sort products by rating value
            products.sort(key=lambda x: x['rating_value'], reverse=True)
            return products  # Return all products after sorting
            
        except Exception as e:
            self.update_signal.emit(f"Error searching products: {str(e)}")
            return []

    def save_to_csv(self):
        try:
            # Create results directory if it doesn't exist
            if not os.path.exists('results'):
                os.makedirs('results')

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'results/search_results_{timestamp}.csv'

            # Write to CSV
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'Product Name',
                    'Price (₹)',
                    'Rating',
                    'Number of Reviews',
                    'Search Query',
                    'Search Timestamp',
                    'AI Analysis'
                ])
                
                # Write data
                for product in self.products:
                    writer.writerow([
                        product['title'],
                        product['price'],
                        product['rating'],
                        product['reviews'],
                        self.query,
                        timestamp,
                        product.get('ai_analysis', '')
                    ])

            self.update_signal.emit(f"✅ Results saved to {filename}")
            return filename
        except Exception as e:
            self.update_signal.emit(f"❌ Error saving results: {str(e)}")
            return None

    def run(self):
        try:
            # Initialize Gemini
            load_dotenv()
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            model = genai.GenerativeModel('gemini-1.5-flash')

            # Process query with Gemini
            self.update_signal.emit("🤖 Processing your request...")
            self.progress_signal.emit(20)
            
            response = model.generate_content(f"""
            Analyze this request and provide a structured response:
            {self.query}
            Format the response in a clear, organized way with:
            1. Main recommendations
            2. Key features to consider
            3. Price range analysis
            """)
            
            self.ai_analysis = response.text
            
            self.update_signal.emit("🌐 Opening browser...")
            self.progress_signal.emit(40)

            try:
                driver = self.setup_edge_driver()
                
                # Search and scrape products
                self.products = self.search_amazon_products(driver, self.query, model)
                self.progress_signal.emit(60)

                # Enhanced per-product AI analysis
                for product in self.products:
                    prompt = (
                        f"Product Title: {product['title']}\n"
                        f"Product Description: {product.get('description', '')}\n"
                        f"Price: ₹{product['price']}\n"
                        f"Rating: {product['rating']}\n"
                        f"Reviews: {product['reviews']}\n"
                        "\n"
                        "1. What type of product is this?\n"
                        "2. List the key features and specifications.\n"
                        "3. Summarize the customer reviews (if available).\n"
                        "4. Give a short, clear summary of its pros, cons, and who it is best for."
                    )
                    try:
                        response = model.generate_content(prompt)
                        product['ai_analysis'] = response.text
                    except Exception as e:
                        product['ai_analysis'] = f'AI analysis unavailable: {str(e)}'

                # Format and display results
                self.update_signal.emit("\n=== AI Analysis ===\n")
                self.update_signal.emit(self.ai_analysis)
                
                self.update_signal.emit(f"\n=== {len(self.products)} Products Found ===\n")
                for i, product in enumerate(self.products, 1):
                    self.update_signal.emit(f"\n{i}. {product['title']}")
                    self.update_signal.emit(f"   Price: ₹{product['price']}")
                    self.update_signal.emit(f"   Rating: {product['rating']}")
                    self.update_signal.emit(f"   Reviews: {product['reviews']}")
                    self.update_signal.emit("-" * 50)
                
                # Save results to CSV
                csv_file = self.save_to_csv()
                if csv_file:
                    self.update_signal.emit(f"\n📊 Results have been saved to: {csv_file}")
                
                self.progress_signal.emit(100)
                
                # Keep the browser open for 30 seconds to view results
                time.sleep(30)
                driver.quit()
                
            except Exception as e:
                self.update_signal.emit(f"❌ Browser Error: {str(e)}")
                self.update_signal.emit("\nShowing AI analysis without browser results:")
                self.update_signal.emit(f"\n\n{self.ai_analysis}")
                self.progress_signal.emit(100)

            self.finished_signal.emit()

        except Exception as e:
            self.update_signal.emit(f"❌ Error: {str(e)}")
            self.finished_signal.emit()

class GradientLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont('Segoe UI', 32, QFont.Weight.Bold))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("color: #3498db;")  # Default color

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create gradient
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor("#3498db"))
        gradient.setColorAt(1, QColor("#2ecc71"))
        
        # Set the gradient as the brush
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw the text with gradient
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())

class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(45)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._animation = QPropertyAnimation(self, b"minimumWidth")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def enterEvent(self, event):
        self._animation.setStartValue(self.width())
        self._animation.setEndValue(self.width() + 20)
        self._animation.start()

    def leaveEvent(self, event):
        self._animation.setStartValue(self.width())
        self._animation.setEndValue(self.width() - 20)
        self._animation.start()

class ProductCard(QFrame):
    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.setObjectName("productCard")
        self.setMinimumHeight(200)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Container for title and rating
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel(product['title'])
        title.setWordWrap(True)
        title.setStyleSheet("""
            font-weight: bold;
            font-size: 16px;
            color: #2c3e50;
            margin-bottom: 5px;
        """)
        header_layout.addWidget(title, 7)  # 70% width
        
        # Rating container
        rating_container = QFrame()
        rating_container.setObjectName("ratingContainer")
        rating_layout = QVBoxLayout(rating_container)
        
        # Rating stars
        rating = QLabel("★ " + product['rating'])
        rating.setStyleSheet("""
            color: #f1c40f;
            font-size: 18px;
            font-weight: bold;
        """)
        rating_layout.addWidget(rating)
        
        # Reviews count
        reviews = QLabel(product['reviews'])
        reviews.setStyleSheet("""
            color: #7f8c8d;
            font-size: 12px;
        """)
        rating_layout.addWidget(reviews)
        
        header_layout.addWidget(rating_container, 3)  # 30% width
        layout.addLayout(header_layout)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(divider)
        
        # Price with icon
        price_container = QHBoxLayout()
        price_icon = QLabel("💰")
        price_icon.setStyleSheet("font-size: 20px;")
        price_container.addWidget(price_icon)
        
        price = QLabel(f"₹{product['price']}")
        price.setStyleSheet("""
            color: #e74c3c;
            font-size: 24px;
            font-weight: bold;
        """)
        price_container.addWidget(price)
        price_container.addStretch()
        layout.addLayout(price_container)
        
        # View Details button
        view_button = QPushButton("View Details")
        view_button.setCursor(Qt.CursorShape.PointingHandCursor)
        view_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        layout.addWidget(view_button)
        
        self.setStyleSheet("""
            QFrame#productCard {
                background-color: white;
                border-radius: 15px;
                padding: 20px;
                margin: 10px;
                border: 1px solid #e0e0e0;
            }
            QFrame#productCard:hover {
                border: 2px solid #3498db;
                background-color: #f8f9fa;
                transform: translateY(-2px);
            }
            QFrame#ratingContainer {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 5px;
            }
        """)

class ChatBubble(QFrame):
    def __init__(self, text, is_user=False):
        super().__init__()
        layout = QHBoxLayout(self)
        label = QLabel()
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setText(text)
        label.setFont(QFont("Segoe UI", 12))
        avatar = QLabel()
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if is_user:
            label.setStyleSheet("""
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3498db, stop:1 #6dd5ed);
                color: white;
                border-radius: 16px;
                padding: 12px;
                margin: 4px;
                font-size: 14px;
                box-shadow: 0 2px 8px rgba(52,152,219,0.15);
            """)
            avatar.setText("🧑")
            avatar.setStyleSheet("font-size: 24px;")
            layout.addStretch()
            layout.addWidget(label)
            layout.addWidget(avatar)
        else:
            label.setStyleSheet("""
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e0eafc, stop:1 #cfdef3);
                color: #2c3e50;
                border-radius: 16px;
                padding: 12px;
                margin: 4px;
                font-size: 14px;
                box-shadow: 0 2px 8px rgba(44,62,80,0.10);
            """)
            avatar.setText("🤖")
            avatar.setStyleSheet("font-size: 24px;")
            layout.addWidget(avatar)
            layout.addWidget(label)
            layout.addStretch()
        self.setLayout(layout)
        self.setStyleSheet("background: transparent;")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Shopping Assistant & Chatbot")
        self.setMinimumSize(1200, 800)
        self.setup_ui()
        self.scroll_area = None
        self._pending_scroll = False

    def setup_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Shopping Assistant Tab
        shopping_tab = QWidget()
        shopping_layout = QVBoxLayout(shopping_tab)
        shopping_layout.setSpacing(20)
        shopping_layout.setContentsMargins(30, 30, 30, 30)
        self.setup_shopping_tab(shopping_layout)
        self.tabs.addTab(shopping_tab, "🛒 Shopping Assistant")

        # Chatbot Tab
        chatbot_tab = QWidget()
        chatbot_layout = QVBoxLayout(chatbot_tab)
        chatbot_layout.setSpacing(10)
        chatbot_layout.setContentsMargins(10, 10, 10, 10)
        self.setup_chatbot_tab(chatbot_layout)
        self.tabs.addTab(chatbot_tab, "💬 Chatbot")

    def setup_shopping_tab(self, layout):
        # Header Frame with gradient background
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(15)
        
        # Title with gradient effect
        title = GradientLabel("AI Shopping Assistant")
        header_layout.addWidget(title)

        # Description with icon
        description_container = QHBoxLayout()
        description_icon = QLabel("🤖")
        description_icon.setStyleSheet("font-size: 24px;")
        description_container.addWidget(description_icon)
        
        description = QLabel("Your intelligent shopping companion")
        description.setFont(QFont('Segoe UI', 14))
        description.setStyleSheet("color: #7f8c8d;")
        description_container.addWidget(description)
        description_container.addStretch()
        
        header_layout.addLayout(description_container)
        layout.addWidget(header_frame)

        # Search Frame with enhanced styling
        search_frame = QFrame()
        search_frame.setObjectName("searchFrame")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setSpacing(15)
        
        # Search icon
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 24px;")
        search_layout.addWidget(search_icon)
        
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter your request (e.g., 'Find the best phone under 12000')")
        self.query_input.setFont(QFont('Segoe UI', 11))
        self.query_input.setMinimumHeight(45)
        self.query_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        
        self.search_button = AnimatedButton("Search")
        self.search_button.setFont(QFont('Segoe UI', 11))
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 25px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.search_button.clicked.connect(self.start_search)
        
        search_layout.addWidget(self.query_input)
        search_layout.addWidget(self.search_button)
        layout.addWidget(search_frame)

        # Progress bar with enhanced styling
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                text-align: center;
                height: 25px;
                background-color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3498db, stop:1 #2ecc71);
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Results area with enhanced scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setSpacing(15)
        self.scroll_area.setWidget(self.results_widget)
        layout.addWidget(self.scroll_area)

        # Set window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            QFrame#headerFrame {
                background-color: white;
                border-radius: 20px;
                padding: 30px;
                margin-bottom: 20px;
            }
            QFrame#searchFrame {
                background-color: white;
                border-radius: 15px;
                padding: 20px;
            }
        """)

    def setup_chatbot_tab(self, layout):
        # Import file button
        import_layout = QHBoxLayout()
        self.import_button = QPushButton("📄 Import File")
        self.import_button.setStyleSheet("padding: 6px 16px; font-size: 14px;")
        self.import_button.clicked.connect(self.import_file)
        import_layout.addWidget(self.import_button)
        import_layout.addStretch()
        layout.addLayout(import_layout)

        # Chat history area
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.addStretch()
        self.chat_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f5f7fa, stop:1 #c3cfe2);
        """)
        self.chat_area.setWidget(self.chat_widget)
        self.chat_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        layout.addWidget(self.chat_area, 1)

        # Input area
        input_layout = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type your message...")
        self.input_box.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 18px;
                padding: 12px 16px;
                font-size: 14px;
                background: #fff;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 18px;
                padding: 10px 24px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #217dbb;
            }
        """)
        self.send_button.clicked.connect(self.send_chat_message)
        input_layout.addWidget(self.input_box, 1)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

    def import_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)")
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.chat_file_content = f.read()
                self.add_chat_message(f"File '{os.path.basename(file_path)}' imported and ready for analysis.", is_user=False)
            except Exception as e:
                self.add_chat_message(f"Failed to read file: {str(e)}", is_user=False)
        else:
            self.chat_file_content = None

    def start_search(self):
        query = self.query_input.text().strip()
        if not query:
            return

        self.search_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Clear previous results
        for i in reversed(range(self.results_layout.count())): 
            self.results_layout.itemAt(i).widget().setParent(None)

        self.worker = WorkerThread(query)
        self.worker.update_signal.connect(self.update_results)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self.search_finished)
        self.worker.start()

    def update_results(self, text):
        if text.startswith("=== AI Analysis ==="):
            # Create a styled frame for AI analysis
            frame = QFrame()
            frame.setObjectName("analysisFrame")
            layout = QVBoxLayout(frame)
            layout.setSpacing(15)
            
            # Header with icon
            header_layout = QHBoxLayout()
            ai_icon = QLabel("🤖")
            ai_icon.setStyleSheet("font-size: 24px;")
            header_layout.addWidget(ai_icon)
            
            title = QLabel("AI Analysis")
            title.setFont(QFont('Segoe UI', 18, QFont.Weight.Bold))
            title.setStyleSheet("color: #2c3e50;")
            header_layout.addWidget(title)
            header_layout.addStretch()
            
            layout.addLayout(header_layout)
            
            # Divider
            divider = QFrame()
            divider.setFrameShape(QFrame.Shape.HLine)
            divider.setStyleSheet("background-color: #e0e0e0;")
            layout.addWidget(divider)
            
            content = QLabel(text.replace("=== AI Analysis ===\n", ""))
            content.setWordWrap(True)
            content.setStyleSheet("""
                color: #34495e;
                font-size: 14px;
                line-height: 1.6;
                padding: 10px;
            """)
            layout.addWidget(content)
            
            frame.setStyleSheet("""
                QFrame#analysisFrame {
                    background-color: white;
                    border-radius: 15px;
                    padding: 20px;
                    margin: 10px;
                }
            """)
            
            self.results_layout.addWidget(frame)
            
        elif text.startswith("=== ") and "Products Found ===" in text:
            # Create a styled frame for products
            frame = QFrame()
            frame.setObjectName("productsFrame")
            layout = QVBoxLayout(frame)
            layout.setSpacing(15)
            
            # Header with icon
            header_layout = QHBoxLayout()
            products_icon = QLabel("🏆")
            products_icon.setStyleSheet("font-size: 24px;")
            header_layout.addWidget(products_icon)
            
            # Extract product count from text
            import re
            match = re.search(r"=== (\d+) Products Found ===", text)
            count = match.group(1) if match else "All"
            title = QLabel(f"{count} Products (Sorted by Rating)")
            title.setFont(QFont('Segoe UI', 18, QFont.Weight.Bold))
            title.setStyleSheet("color: #2c3e50;")
            header_layout.addWidget(title)
            header_layout.addStretch()
            
            layout.addLayout(header_layout)
            
            # Divider
            divider = QFrame()
            divider.setFrameShape(QFrame.Shape.HLine)
            divider.setStyleSheet("background-color: #e0e0e0;")
            layout.addWidget(divider)
            
            frame.setStyleSheet("""
                QFrame#productsFrame {
                    background-color: white;
                    border-radius: 15px;
                    padding: 20px;
                    margin: 10px;
                }
            """)
            
            self.results_layout.addWidget(frame)
        else:
            # Regular status updates
            label = QLabel(text)
            label.setStyleSheet("""
                color: #7f8c8d;
                font-size: 13px;
                padding: 5px;
                background-color: #f8f9fa;
                border-radius: 5px;
            """)
            self.results_layout.addWidget(label)

    def search_finished(self):
        self.search_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Scroll to the top of results after search is complete
        if self.scroll_area:
            self.scroll_area.verticalScrollBar().setValue(0)

    def send_chat_message(self):
        user_text = self.input_box.text().strip()
        if not user_text:
            return
        self.add_chat_message(user_text, is_user=True)
        self.input_box.clear()
        self.send_button.setEnabled(False)
        self.send_button.setText("...")
        QApplication.processEvents()
        # Get the full AI response (blocking, but could be threaded for async)
        ai_response = self.get_gemini_response(user_text)
        self.stream_ai_message(ai_response)

    def stream_ai_message(self, full_text):
        import re
        chunks = re.split(r'(\s+)', full_text)  # Split by word, keeping spaces
        self._streamed_text = ""
        self._stream_chunks = chunks
        self._stream_bubble = ChatBubble("", is_user=False)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, self._stream_bubble)
        self._stream_timer = QTimer()
        self._stream_timer.timeout.connect(self._stream_next_chunk)
        self._stream_timer.start(20)  # 20ms per chunk for a fast typewriter effect

    def _stream_next_chunk(self):
        if not self._stream_chunks:
            self._stream_timer.stop()
            # After streaming, convert to HTML and update the bubble for proper formatting
            import markdown
            html = markdown.markdown(self._streamed_text)
            for i in range(self._stream_bubble.layout().count()):
                widget = self._stream_bubble.layout().itemAt(i).widget()
                if isinstance(widget, QLabel) and widget.text() != "🤖":
                    widget.setText(html)
            self.send_button.setEnabled(True)
            self.send_button.setText("Send")
            return
        next_chunk = self._stream_chunks.pop(0)
        self._streamed_text += next_chunk
        for i in range(self._stream_bubble.layout().count()):
            widget = self._stream_bubble.layout().itemAt(i).widget()
            if isinstance(widget, QLabel) and widget.text() != "🤖":
                widget.setText(self._streamed_text)
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())

    def add_chat_message(self, text, is_user=False):
        if not is_user:
            # Convert markdown to HTML for AI responses
            text = markdown.markdown(text)
        bubble = ChatBubble(text, is_user)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())

    def get_gemini_response(self, user_text):
        try:
            load_dotenv()
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            model = genai.GenerativeModel('gemini-1.5-flash')
            # If a file is loaded, include its content in the prompt
            if hasattr(self, 'chat_file_content') and self.chat_file_content:
                prompt = f"Analyze the following file content and answer the user's question.\n\nFile Content:\n{self.chat_file_content}\n\nUser Question: {user_text}"
            else:
                prompt = user_text
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"AI error: {str(e)}"

    def create_task_group(self, title, tasks):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.setSpacing(18)
        layout.setContentsMargins(16, 12, 16, 12)
        for task_name, callback in tasks:
            card = QFrame()
            card.setObjectName("taskCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 10, 18, 10)
            card_layout.setSpacing(0)
            button = QPushButton(task_name)
            button.setMinimumHeight(44)
            button.setFont(QFont('Segoe UI', 13, QFont.Weight.Bold))
            button.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 0px;
                    font-size: 16px;
                    font-weight: bold;
                    letter-spacing: 0.5px;
                }
                QPushButton:hover {
                    background-color: #217dbb;
                }
            """)
            button.clicked.connect(callback)
            card_layout.addWidget(button)
            card.setStyleSheet("""
                QFrame#taskCard {
                    background-color: #f8f9fa;
                    border: 1.5px solid #e0e0e0;
                    border-radius: 12px;
                    margin-bottom: 2px;
                }
            """)
            layout.addWidget(card)
        layout.addStretch()
        return group

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 