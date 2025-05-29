from flask import Flask, request
import subprocess
import pyautogui
import time
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <h2>💻 Terminal Command</h2>
    <form method="POST" action="/run">
        <input name="cmd" placeholder="Enter command (e.g. echo Hello Maddy)" style="width: 300px;">
        <button type="submit">Run</button>
    </form>

    <h2>📄 Create & Write File</h2>
    <form method="POST" action="/write">
        <input name="filename" placeholder="Filename (e.g. maddy.txt)" style="width: 300px;"><br><br>
        <textarea name="content" rows="10" cols="60" placeholder="Type your code or note for Maddy 🥺💕"></textarea><br><br>
        <button type="submit">Write & Close</button>
    </form>
    '''

@app.route('/run', methods=['POST'])
def run_cmd():
    cmd = request.form['cmd']

    # Open CMD
    subprocess.Popen("start cmd", shell=True)
    time.sleep(1.5)  # Wait for CMD to open

    # Type the command and press Enter
    pyautogui.typewrite(cmd)
    pyautogui.press("enter")

    return f'<p>Typed into CMD: <code>{cmd}</code> 😘</p><a href="/">Go back</a>'

@app.route('/write', methods=['POST'])
def write_file():
    filename = request.form['filename']
    content = request.form['content']

    filepath = os.path.abspath(filename)

    # Step 1: Create empty file
    with open(filepath, 'w') as f:
        pass

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

    return f'<p>Wrote into file <code>{filename}</code> and closed it 💋</p><a href="/">Go back</a>'

if __name__ == '__main__':
    app.run(debug=True)
