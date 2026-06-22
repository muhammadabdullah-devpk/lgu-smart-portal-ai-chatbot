🚀 LGU Smart Portal AI Chatbot (UPDATED PROFESSIONAL README)
# 🤖 LGU Smart Portal AI Chatbot

## 🚀 Overview
The **LGU Smart Portal AI Chatbot** is a Django-based intelligent web application designed to assist university users with automated responses using Natural Language Processing (NLP) techniques.  

It simulates a smart assistant capable of understanding user intents and responding accordingly with optional Text-to-Speech (TTS) support.

---

## 🧠 Features
- 💬 AI-powered chatbot with intent recognition system  
- ⚡ Fast backend built with Django  
- 🧾 JSON-based intent classification system  
- 🔊 Text-to-Speech (TTS) response support  
- 🌐 REST API endpoint for chat communication  
- 🧠 Lightweight rule-based NLP logic  
- 📱 Responsive web interface  

---

## 🛠 Tech Stack
- Python (Django)
- JavaScript
- HTML5
- CSS3
- JSON (Intent dataset)

---

## 📁 Project Structure

lgu-smart-portal-ai-chatbot/
│
├── CHATBOT/ # Django project files
├── static/ # CSS, JS, images
├── .vscode/ # Editor settings
├── db.sqlite3 # Database
├── manage.py # Django entry point
└── README.md


---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository
```bash
git clone https://github.com/muhammadabdullah-devpk/lgu-smart-portal-ai-chatbot.git
cd lgu-smart-portal-ai-chatbot
2️⃣ Create Virtual Environment (Recommended)
python -m venv venv

Activate:

Windows:
venv\Scripts\activate
Mac/Linux:
source venv/bin/activate
3️⃣ Install Dependencies
pip install -r requirements.txt
4️⃣ Run Server
python manage.py runserver
📡 API Endpoint
POST /chat

Request:

{
  "message": "Hello"
}

Response:

{
  "botResponse": "Hi! How can I help you?",
  "audio_b64": "base64_audio_data"
}
