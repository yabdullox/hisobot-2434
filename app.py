from flask import Flask
from threading import Thread
import asyncio
from main import main  # bu sening aiogram main() funksiyang

app = Flask(__name__)

@app.route('/')
def index():
    return "Hisobot bot ishlayapti ✅"

def run_bot():
    asyncio.run(main())

if __name__ == "__main__":
    # Botni alohida oqimda ishga tushiramiz
    Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)
