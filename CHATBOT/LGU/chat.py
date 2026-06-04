import json
from pathlib import Path
import os
import torch
import numpy as np
import logging
import re
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import requests
import html as _html
import time
import base64
import tempfile

try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
except Exception:
    TTS = None
    TTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTS3_AVAILABLE = True
except Exception:
    pyttsx3 = None
    PYTTS3_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

# How many sentences to keep when summarizing Groq answers
GROQ_SUMMARY_SENTENCES = int(os.environ.get('GROQ_SUMMARY_SENTENCES', '2'))


def normalize_text(s: str) -> str:
    """Lowercase and remove punctuation for robust matching."""
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def summarize_text(text: str, sentences: int = GROQ_SUMMARY_SENTENCES) -> str:
    """Very small heuristic summarizer: keep first N sentences."""
    if not text:
        return text
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(parts) <= sentences:
        return text.strip()
    summary = " ".join(parts[:sentences]).strip()
    return summary


class ChatBot:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Legacy tokenizer/model (kept as fallback)
        self.qa_model_name = 'sentence-transformers/all-MiniLM-L6-v2'
        self.qa_tokenizer = AutoTokenizer.from_pretrained(
            self.qa_model_name, 
            clean_up_tokenization_spaces=True
        )
        self.qa_model = AutoModel.from_pretrained(self.qa_model_name).to(self.device)

        # Main similarity acceptance threshold
        self.similarity_threshold_main = float(os.environ.get('SIMILARITY_THRESHOLD_MAIN', '0.60'))

        # Use a stronger SentenceTransformer model for embeddings
        self.sentence_model = SentenceTransformer(
            os.environ.get('SENTENCE_MODEL', 'all-mpnet-base-v2')
        )

        # Load data and initialize embeddings
        self.load_data()
        
    def query_groq(self, user_question):
        """Use Groq REST API as a fallback LLM when other sources don't have an answer."""
        groq_api_key = os.environ.get('GROQ_API_KEY')
        if not groq_api_key:
            logger.warning("GROQ_API_KEY not set; cannot query Groq API.")
            return ""

        api_url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "openai/gpt-oss-120b",
            "messages": [
                {
                    "role": "user", 
                    "content": f"Only provide the summary of answer in clean format. Don't use any symbols or markdown in answer: {user_question}"
                }
            ],
            "max_tokens": 1024,
            "temperature": 1,
            "top_p": 1,
            "stream": False
        }

        retries = 3
        backoff = 2
        for attempt in range(1, retries + 1):
            try:
                resp = requests.post(api_url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        try:
                            content = data["choices"][0]["message"]["content"]
                        except Exception:
                            try:
                                content = data["choices"][0]["text"]
                            except Exception:
                                content = ""

                        # Clean HTML and unescape entities
                        try:
                            cleaned = re.sub(r'<[^>]+>', '', content)
                            cleaned = _html.unescape(cleaned)
                            return cleaned.strip()
                        except Exception:
                            return content.strip() if isinstance(content, str) else ""
                    else:
                        logger.warning(f"Unexpected Groq response format: {data}")
                        return ""
                elif resp.status_code in (500, 502, 503, 504):
                    logger.warning(f"Server error from Groq (status {resp.status_code}), attempt {attempt}")
                    if attempt < retries:
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    return ""
                elif resp.status_code == 429:
                    logger.warning("Rate limited by Groq API.")
                    return ""
                else:
                    logger.error(f"Groq API returned status {resp.status_code}: {resp.text}")
                    return ""
            except requests.RequestException as e:
                logger.warning(f"RequestException querying Groq: {e}, attempt {attempt}")
                if attempt < retries:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                return ""

    def generate_tts_base64(self, text: str, language: str = 'en') -> str:
        """Generate professional multilingual TTS audio and return base64-encoded audio bytes.
        
        Args:
            text: Text to convert to speech
            language: Language code (en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko, hi)
        """
        if not text:
            return ""

        # 1) Prefer Coqui TTS with XTTS-v2 (multilingual, professional quality)
        if TTS_AVAILABLE:
            try:
                if not hasattr(self, '_tts') or self._tts is None:
                    gpu_flag = torch.cuda.is_available()
                    
                    # Try XTTS-v2 first - best multilingual model with natural voices
                    try:
                        model_name = 'tts_models/multilingual/multi-dataset/xtts_v2'
                        self._tts = TTS(model_name=model_name, progress_bar=False, gpu=gpu_flag)
                        self._tts_type = 'xtts'
                        logger.info("Loaded XTTS-v2 multilingual model (professional quality)")
                    except Exception as e1:
                        logger.warning(f"XTTS-v2 failed: {e1}, trying YourTTS...")
                        # Fallback to YourTTS - also multilingual and natural
                        try:
                            model_name = 'tts_models/multilingual/multi-dataset/your_tts'
                            self._tts = TTS(model_name=model_name, progress_bar=False, gpu=gpu_flag)
                            self._tts_type = 'yourtts'
                            logger.info("Loaded YourTTS multilingual model")
                        except Exception as e2:
                            logger.warning(f"YourTTS failed: {e2}, trying VITS...")
                            # Fallback to English VITS with natural voices
                            model_name = 'tts_models/en/vctk/vits'
                            self._tts = TTS(model_name=model_name, progress_bar=False, gpu=gpu_flag)
                            self._tts_type = 'vits'
                            logger.info("Loaded VITS English model")

                tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                tmp_path = tmp.name
                tmp.close()
                
                try:
                    # Generate speech based on model type
                    if self._tts_type == 'xtts':
                        # XTTS-v2: Best quality, supports multiple languages
                        # Use default speaker for consistent professional voice
                        self._tts.tts_to_file(
                            text=text, 
                            file_path=tmp_path,
                            language=language,
                            speaker_wav=None  # Uses default professional voice
                        )
                    elif self._tts_type == 'yourtts':
                        # YourTTS: Good multilingual support
                        self._tts.tts_to_file(
                            text=text,
                            file_path=tmp_path,
                            language=language
                        )
                    elif self._tts_type == 'vits':
                        # VITS: English only, multiple speakers
                        # p236 = professional female, p245 = professional male
                        # p260 = calm female, p270 = warm male
                        speaker = os.environ.get('TTS_SPEAKER', 'p236')
                        self._tts.tts_to_file(
                            text=text,
                            file_path=tmp_path,
                            speaker=speaker
                        )
                    else:
                        # Generic fallback
                        self._tts.tts_to_file(text=text, file_path=tmp_path)
                    
                    with open(tmp_path, 'rb') as f:
                        audio_bytes = f.read()
                    return base64.b64encode(audio_bytes).decode('utf-8')
                finally:
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Coqui TTS generation failed: {e}")

        # 2) Fallback to pyttsx3 with improved voice settings (limited languages)
        if PYTTS3_AVAILABLE:
            try:
                tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                tmp_path = tmp.name
                tmp.close()

                engine = pyttsx3.init()
                
                # Get available voices and select the best quality one
                voices = engine.getProperty('voices')
                
                # Priority: Microsoft voices > other SAPI5 voices
                best_voice = None
                for voice in voices:
                    voice_name = voice.name.lower()
                    # Prefer Microsoft David/Zira/Mark (better quality)
                    if 'david' in voice_name or 'zira' in voice_name or 'mark' in voice_name:
                        best_voice = voice.id
                        break
                    # Second choice: any female voice
                    elif 'female' in voice_name and best_voice is None:
                        best_voice = voice.id
                
                if best_voice:
                    engine.setProperty('voice', best_voice)
                
                # Professional settings for natural speech
                rate = int(os.environ.get('TTS_RATE', '165'))  # Slower = more professional
                engine.setProperty('rate', rate)
                engine.setProperty('volume', 0.95)
                
                engine.save_to_file(text, tmp_path)
                engine.runAndWait()
                
                with open(tmp_path, 'rb') as f:
                    audio_bytes = f.read()
                
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                    
                return base64.b64encode(audio_bytes).decode('utf-8')
            except Exception as e:
                logger.error(f"pyttsx3 TTS generation failed: {e}")

        logger.warning('No TTS available. Install Coqui TTS (`pip install TTS`) for professional multilingual voices.')
        return ""

    def load_data(self):
        """Load intents data from JSON file."""
        # Resolve intents JSON path robustly: prefer package-relative `static/`,
        # fall back to current working directory `static/` if necessary.
        try:
            base_dir = Path(__file__).resolve().parent.parent
            intent_path = base_dir / 'static' / 'intents1.json'
            if not intent_path.exists():
                # fallback: project root `static/`
                intent_path = Path(os.getcwd()) / 'static' / 'intents1.json'

            logger.info(f"Loading intents JSON from {intent_path} (exists={intent_path.exists()}) cwd={Path.cwd()}")
            with open(intent_path, 'r', encoding='utf-8') as file:
                self.intent_data = json.load(file)
        except Exception as e:
            logger.error(f"Failed to load intents JSON from {intent_path}: {e}")
            raise

        self.intents = self.intent_data['intents']
        self.patterns = {}
        self.responses = {}
        
        for intent in self.intents:
            tag = intent['tag']
            self.patterns[tag] = intent['patterns']
            self.responses[tag] = intent['responses']

        self.pattern_list = [
            (pattern, tag) 
            for tag, pats in self.patterns.items() 
            for pattern in pats
        ]

        self.precompute_embeddings()

    def precompute_embeddings(self):
        """Precompute embeddings for all patterns."""
        self.initialize_embeddings()

    def initialize_embeddings(self):
        """Use SentenceTransformer to compute semantic embeddings for all intent patterns."""
        patterns = [pat for pat, _ in self.pattern_list]
        try:
            embs = self.sentence_model.encode(patterns, convert_to_numpy=True)
            self.pattern_embeddings = embs.astype('float32')
            self.question_embeddings = self.pattern_embeddings
            self.pattern_texts = patterns
        except Exception as e:
            logger.error(f"Failed to compute pattern embeddings: {e}")
            # Fallback to previous tokenizer/model
            embs = self.get_batch_embeddings([pat for pat, _ in self.pattern_list])
            self.pattern_embeddings = embs.astype('float32')
            self.question_embeddings = self.pattern_embeddings
            self.pattern_texts = patterns

    def get_batch_embeddings(self, texts):
        """Get embeddings for a batch of texts."""
        try:
            embs = self.sentence_model.encode(texts, convert_to_numpy=True)
            return embs.astype('float32')
        except Exception:
            # Fallback to transformer tokenizer/model
            inputs = self.qa_tokenizer(
                texts, 
                return_tensors='pt', 
                truncation=True, 
                padding=True, 
                max_length=512
            )
            inputs = {key: value.to(self.device) for key, value in inputs.items()}
            
            with torch.no_grad():
                outputs = self.qa_model(**inputs)
            
            embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
            return embeddings

    def get_embedding(self, text):
        """Get embedding for a single text."""
        try:
            emb = self.sentence_model.encode(text, convert_to_numpy=True)
            return emb.astype('float32')
        except Exception:
            return self.get_batch_embeddings([text])[0]

    def get_best_answer(self, user_question):
        """Find the best answer for the user's question."""
        # Quick keyword overrides for high-priority topics (fees/payments)
        try:
            q_norm_override = normalize_text(user_question or "")
            q_tokens_override = set(q_norm_override.split())
            payment_keywords_tokens = {'fee', 'fees', 'payment', 'challan', 'pay'}
            
            if (('fee structure' in q_norm_override) or 
                ('fee schedule' in q_norm_override) or 
                (q_tokens_override & payment_keywords_tokens)):
                
                if 'lgu_payment_fees' in getattr(self, 'responses', {}):
                    logger.info("Payment override matched; returning 'lgu_payment_fees' intent")
                    return np.random.choice(self.responses.get('lgu_payment_fees', [""]))
                
                for tag in getattr(self, 'responses', {}).keys():
                    if 'fee' in tag or 'payment' in tag:
                        logger.info(f"Payment override matched tag fallback -> {tag}")
                        return np.random.choice(self.responses.get(tag, [""]))
        except Exception:
            logger.debug("Payment override check failed", exc_info=True)

        # 1) Semantic-first: use SentenceTransformer embeddings to match against intent patterns
        try:
            if not hasattr(self, 'pattern_embeddings') or self.pattern_embeddings is None:
                self.initialize_embeddings()

            user_emb = self.get_embedding(user_question)
            pattern_embs = np.array(self.pattern_embeddings)
            
            # Compute cosine similarity
            user_norm = np.linalg.norm(user_emb) + 1e-12
            pattern_norms = np.linalg.norm(pattern_embs, axis=1) + 1e-12
            dots = np.dot(pattern_embs, user_emb.T).flatten()
            cosine_sims = dots / (pattern_norms * user_norm)
            
            best_idx = int(np.argmax(cosine_sims))
            best_sim = float(cosine_sims[best_idx])
            sem_thresh = float(os.environ.get('INTENT_SEMANTIC_THRESHOLD', '0.70'))
            
            if best_sim >= sem_thresh:
                best_pattern, best_tag = self.pattern_list[best_idx]
                logger.info(
                    f"Intent match (semantic-first) -> tag={best_tag} "
                    f"sim={best_sim:.3f} pattern='{best_pattern}'"
                )
                return np.random.choice(self.responses.get(best_tag, [""]))
        except Exception:
            logger.debug("Semantic-first intent matching failed", exc_info=True)

        # 2) Conservative token / substring fallback
        try:
            q_norm = normalize_text(user_question)
            q_tokens = set(q_norm.split())
            
            for pattern, tag in getattr(self, 'pattern_list', []):
                if not pattern:
                    continue
                    
                p_norm = normalize_text(pattern)
                p_tokens = set(p_norm.split())

                # Exact normalized match
                if p_norm and p_norm == q_norm:
                    logger.info(f"Intent match (exact fallback) -> tag={tag} pattern='{pattern}'")
                    return np.random.choice(self.responses.get(tag, [""]))

                # Token overlap with strict coverage
                if p_tokens and q_tokens:
                    intersection = p_tokens.intersection(q_tokens)
                    coverage = len(intersection) / max(1, len(p_tokens))
                    if len(intersection) >= 2 and coverage >= 0.6:
                        logger.info(f"Intent match (tokens fallback) -> tag={tag} pattern='{pattern}'")
                        return np.random.choice(self.responses.get(tag, [""]))

                # Substring containment only for long patterns
                if p_norm and len(p_tokens) >= 5 and p_norm in q_norm:
                    logger.info(f"Intent match (substring fallback) -> tag={tag} pattern='{pattern}'")
                    return np.random.choice(self.responses.get(tag, [""]))
        except Exception:
            logger.debug("Error during fallback pattern matching", exc_info=True)

        # 3) If no intent match, query Groq LLM for an answer
        try:
            groq_answer = self.query_groq(user_question)
            if groq_answer:
                summary = summarize_text(groq_answer)
                logger.info(f"Groq provided answer (summarized to {len(summary.split())} words)")
                return summary
        except Exception:
            logger.debug("Groq query failed", exc_info=True)

        # 4) Final fallback: embedding similarity
        if self.question_embeddings is None:
            raise ValueError("Question embeddings are not initialized.")

        user_embedding = self.get_embedding(user_question).reshape(1, -1)
        similarities = np.dot(self.question_embeddings, user_embedding.T).flatten()
        best_idx = similarities.argmax()
        best_similarity = similarities[best_idx] / (
            np.linalg.norm(user_embedding) * 
            np.linalg.norm(self.question_embeddings[best_idx])
        )

        if best_similarity >= self.similarity_threshold_main:
            best_pattern, best_tag = self.pattern_list[best_idx]
            return np.random.choice(self.responses[best_tag])

        return ""

    def get_response(self, sentence):
        """Get response for user input."""
        try:
            response_text = self.get_best_answer(sentence)
            if response_text is None or response_text.strip() == "":
                response_text = (
                    "Your question is not related to the allowed topic of discussions. "
                    "Would you like to speak to a live consultant?"
                )
            else:
                response_text = self.clean_and_format(response_text)
        except Exception as e:
            response_text = (
                "Your question is not related to the allowed topic of discussions. "
                "Would you like to speak to a live consultant?"
            )
            logger.error(f"Error getting best answer: {e}")

        return response_text

    def clean_and_format(self, text: str) -> str:
        """Clean raw model output and format with title and body."""
        if not text:
            return text

        # Normalize whitespace and strip control characters
        cleaned = re.sub(r"\s+", " ", text).strip()
        # Split into sentences
        parts = re.split(r'(?<=[.!?])\s+', cleaned, maxsplit=1)

        if len(parts) == 0:
            return cleaned

        first = parts[0].strip()
        rest = parts[1].strip() if len(parts) > 1 else ""

        # Decide on title
        if len(first.split()) <= 10:
            title = first.rstrip('.!?')
            body = rest
        else:
            # Create a short title from the first 6 words
            title_words = first.split()[:6]
            title = ' '.join(title_words).rstrip('.!?')
            body = cleaned

        # Capitalize title properly
        title = title[0].upper() + title[1:] if title else "Answer"

        # Ensure body is readable
        body = re.sub(r'\s*\.\s*', '. ', body).strip()

        # Return title then body separated by two newlines
        formatted = f"{title}\n\n{body}"
        return formatted