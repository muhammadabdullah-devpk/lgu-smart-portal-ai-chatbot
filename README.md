# 🤖 LGU Smart Portal AI Chatbot

## 🚀 Overview
The LGU Smart Portal AI Chatbot is a Django-based intelligent web application designed to assist university users using Natural Language Processing (NLP) techniques.

It simulates a smart assistant that understands user intents and provides automated responses with optional Text-to-Speech (TTS) support.

---

## 🧠 Features
- 💬 AI-powered chatbot with intent recognition system  
- ⚡ Fast and scalable Django backend  
- 🧾 JSON-based intent classification system  
- 🔊 Text-to-Speech (TTS) support  
- 🌐 REST API for chatbot communication  
- 🧠 Lightweight rule-based NLP system  
- 📱 Responsive web interface  

---

## 🛠 Tech Stack
- Python (Django)
- JavaScript
- HTML5
- CSS3
- JSON (Intent Dataset)

---

## 📁 Project Structure
lgu-smart-portal-ai-chatbot/
│
├── CHATBOT/          Django project files
├── static/           CSS, JS, images
├── .vscode/          Editor settings
├── db.sqlite3        Database
├── manage.py         Django entry point
└── README.md

---

## ⚙️ Installation & Setup

1. Clone Repository:
git clone https://github.com/muhammadabdullah-devpk/lgu-smart-portal-ai-chatbot.git
cd lgu-smart-portal-ai-chatbot

2. Create Virtual Environment:
python -m venv venv

Activate (Windows):
venv\Scripts\activate

Activate (Mac/Linux):
source venv/bin/activate

3. Install Dependencies:
pip install -r requirements.txt

4. Run Server:
python manage.py runserver

---

## 📡 API Endpoint

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

---

## 🎯 Purpose
This project was developed as part of an AI/ML learning journey to practice NLP, Django backend development, API integration, and chatbot system design.

---

## 👨‍💻 Developer
Muhammad Abdullah  
Computer Science Student | AI & ML Enthusiast  
GitHub: https://github.com/muhammadabdullah-devpk  
LinkedIn: https://www.linkedin.com/in/muhammad-abdullah-devpk  

---

## 📈 Future Improvements
- Improve NLP using BERT / transformer models  
- Add chat history with database  
- Deploy on cloud (Render / AWS / Railway)  
- Add authentication system  
- Improve UI/UX design  

---

## ⭐ Support
If you like this project, give it a star ⭐ on GitHub!
