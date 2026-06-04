from django.shortcuts import render
from django.http import JsonResponse
from .chat import ChatBot
import logging
from django.views.decorators.csrf import csrf_exempt

# Set up logging
logger = logging.getLogger(__name__)

# Lazy singleton for ChatBot to avoid loading heavy models at import time
chatbot = None

def get_chatbot():
    global chatbot
    if chatbot is None:
        logger.info("Initializing ChatBot instance (lazy)")
        chatbot = ChatBot()
    return chatbot

@csrf_exempt
def new(request):
    # Same behavior as home but render the new.html template
    if request.method == 'POST':
        # Log incoming POST for debugging
        logger.info(f"new POST received. POST keys: {list(request.POST.keys())}")
        sentence = request.POST.get('message')
        if sentence:
            try:
                bot_response = get_chatbot().get_response(sentence)
                # also attempt to generate TTS audio (base64) for the response
                try:
                    audio_b64 = get_chatbot().generate_tts_base64(bot_response)
                except Exception as e:
                    logger.error(f"Error generating TTS: {e}")
                    audio_b64 = ""

                return JsonResponse({'message': sentence, 'botResponse': bot_response, 'audio_b64': audio_b64})
            except Exception as e:
                logger.error(f"Error processing POST request for new: {e}", exc_info=True)
                return JsonResponse({'error': 'An error occurred while processing your request.', 'detail': str(e)}, status=500)
        return JsonResponse({'error': 'No message provided'}, status=400)

    visitor_message = """Hi this is Edward welcome to my site, how can I help you"""
    return render(request, 'new.html', {'visitor_message': visitor_message})
