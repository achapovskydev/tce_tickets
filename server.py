from flask import Flask
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TCE Telegram Monitor</title>
        <meta charset="utf-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
            }
            button {
                width: 100%;
                padding: 15px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                margin-top: 20px;
            }
            button:hover {
                background: #0056b3;
            }
            #result {
                margin-top: 20px;
                padding: 15px;
                border-radius: 5px;
                display: none;
            }
            .success {
                background: #d4edda;
                color: #155724;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📱 TCE Telegram Monitor</h1>
            <p>Нажмите кнопку, чтобы запустить мониторинг событий на tce.by</p>
            <button onclick="runScript()">Запустить мониторинг</button>
            <div id="result"></div>
        </div>
        
        <script>
            function runScript() {
                const btn = event.target;
                const result = document.getElementById('result');
                
                btn.disabled = true;
                btn.textContent = 'Выполняется...';
                result.style.display = 'none';
                
                fetch('/run')
                    .then(response => response.text())
                    .then(data => {
                        result.className = 'success';
                        result.textContent = data;
                        result.style.display = 'block';
                        btn.disabled = false;
                        btn.textContent = 'Запустить мониторинг';
                    })
                    .catch(error => {
                        result.className = 'error';
                        result.textContent = 'Ошибка: ' + error;
                        result.style.display = 'block';
                        btn.disabled = false;
                        btn.textContent = 'Запустить мониторинг';
                    });
            }
        </script>
    </body>
    </html>
    """

@app.route('/run')
def run_script():
    subprocess.run(['python3', 'tce_telegram_monitor.py'])
    return "Скрипт выполнен!"

@app.route('/test')
def test_telegram():
    subprocess.run(['python3', 'test_telegram.py'])
    return "Тестовое сообщение отправлено в Telegram!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
