 document.addEventListener('DOMContentLoaded', function () {
            // DOM Elements
            const mobileMenuBtn = document.getElementById('mobileMenuBtn');
            const navLinks = document.getElementById('navLinks');
            const navButtons = document.querySelectorAll('.nav-link');
            const applyButtons = document.querySelectorAll('#applyNowBtn, #heroApplyBtn');
            const exploreProgramsBtn = document.getElementById('exploreProgramsBtn');
            const chatbotButton = document.getElementById('chatbotButton');
            const chatWindow = document.getElementById('chatWindow');
            const chatOverlay = document.getElementById('chatOverlay');
            const closeButton = document.getElementById('closeButton');
            const minimizeButton = document.getElementById('minimizeButton');
            const sendButton = document.getElementById('sendButton');
            const voiceButton = document.getElementById('voiceButton');
            const messageInput = document.getElementById('messageInput');
            const chatBody = document.getElementById('chatBody');
            const voiceIndicator = document.getElementById('voiceIndicator');
            const notificationBadge = document.getElementById('notificationBadge');
            const quickQuestions = document.getElementById('quickQuestions');
            const notificationSound = document.getElementById('notificationSound');
            const sendSound = document.getElementById('sendSound');
            const inquiryForm = document.getElementById('inquiryForm');

            // Chatbot State Variables
            let isChatOpen = false;
            let isMicActive = false;
            let speechRecognition = null;
            let unreadMessages = 1;
            let isMinimized = false;
            let isMobile = window.innerWidth <= 768;

            // Check screen size
            function checkScreenSize() {
                isMobile = window.innerWidth <= 768;
            }

            window.addEventListener('resize', checkScreenSize);

            // Toggle Mobile Menu
            mobileMenuBtn.addEventListener('click', function () {
                navLinks.classList.toggle('active');
                const icon = mobileMenuBtn.querySelector('i');
                if (navLinks.classList.contains('active')) {
                    icon.classList.remove('fa-bars');
                    icon.classList.add('fa-times');
                } else {
                    icon.classList.remove('fa-times');
                    icon.classList.add('fa-bars');
                }
            });

            // Navigation Button Click Handler
            navButtons.forEach(button => {
                button.addEventListener('click', function (e) {
                    e.preventDefault();
                    const page = this.getAttribute('data-page');

                    // Update active state
                    navButtons.forEach(btn => btn.classList.remove('active'));
                    this.classList.add('active');

                    // Scroll to section
                    if (page === 'home') {
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    } else {
                        const section = document.getElementById(page);
                        if (section) {
                            const offset = 80;
                            const sectionTop = section.offsetTop - offset;
                            window.scrollTo({ top: sectionTop, behavior: 'smooth' });
                        }
                    }

                    // Close mobile menu if open
                    if (navLinks.classList.contains('active')) {
                        navLinks.classList.remove('active');
                        mobileMenuBtn.querySelector('i').classList.remove('fa-times');
                        mobileMenuBtn.querySelector('i').classList.add('fa-bars');
                    }
                });
            });

            // Apply Now Button Handler
            applyButtons.forEach(button => {
                button.addEventListener('click', function () {
                    alert('Redirecting to LGU Admissions Portal...\n\nIn a real implementation, this would open the application form.');

                    // Simulate notification for chatbot
                    unreadMessages++;
                    updateNotificationBadge();

                    // Show chatbot notification
                    setTimeout(() => {
                        showChatbotNotification();
                    }, 1000);
                });
            });

            // Explore Programs Button Handler
            exploreProgramsBtn.addEventListener('click', function () {
                const programsSection = document.getElementById('programs');
                const offset = 80;
                const programsTop = programsSection.offsetTop - offset;
                window.scrollTo({ top: programsTop, behavior: 'smooth' });

                // Update active nav button
                navButtons.forEach(btn => btn.classList.remove('active'));
                document.querySelector('.nav-link[data-page="programs"]').classList.add('active');
            });

            // Inquiry Form Handler
            inquiryForm.addEventListener('submit', function (e) {
                e.preventDefault();

                // Get form values
                const name = document.getElementById('name').value;
                const email = document.getElementById('email').value;
                const program = document.getElementById('program').value;

                // Show success message
                alert(`Thank you ${name}! Your inquiry has been submitted. Our admissions team will contact you at ${email} regarding the ${program} program.`);

                // Reset form
                inquiryForm.reset();

                // Simulate chatbot notification
                unreadMessages++;
                updateNotificationBadge();
            });

            // CHATBOT FUNCTIONALITY

            // Initialize the chat with a welcome message from the bot
            setTimeout(() => {
                addBotMessage("Hello! Welcome to Lahore Garrison University Admissions Assistant. I'm here to help you with all your admission queries. Feel free to ask about programs, eligibility, deadlines, or use the quick buttons above for common questions.");
            }, 1000);

            // Add message to chat
            function addMessage(text, isBot = false, audio_b64 = '') {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isBot ? 'bot-message' : 'user-message'}`;
                if (isBot) {
                    // Expect backend text format: "<Title>\n\n<body>" — bold the title, escape content
                    const parts = text.split(/\n\n/);
                    // helper to remove leading bullets/asterisks/hashes/numbers
                    const normalizeLine = (s) => s.replace(/^[\-\*\u2022\•\#\s]+/, '').replace(/^\d+\.\s*/, '').trim();
                    const titleRaw = parts[0] || '';
                    const title = normalizeLine(titleRaw);
                    const body = parts.slice(1).join('\n\n') || '';

                    if (title) {
                        const titleEl = document.createElement('strong');
                        titleEl.textContent = title;
                        messageDiv.appendChild(titleEl);
                    }

                    if (body) {
                        const br = document.createElement('br');
                        const br2 = document.createElement('br');
                        messageDiv.appendChild(br);
                        messageDiv.appendChild(br2);

                        const bodyEl = document.createElement('div');
                        // preserve line breaks, detect headings and lists
                        const lines = body.split('\n').map(l => normalizeLine(l)).filter(l => l.length > 0);
                        for (let i = 0; i < lines.length; i++) {
                            const line = lines[i];

                            // detect bullet lists
                            if (/^[\-\*\u2022\•]\s+/.test(line) || /^\d+\./.test(line)) {
                                // collect consecutive list items
                                const ul = document.createElement('ul');
                                let j = i;
                                while (j < lines.length && (/^[\-\*\u2022\•]\s+/.test(lines[j]) || /^\d+\./.test(lines[j]))) {
                                    const li = document.createElement('li');
                                    // remove bullet or number
                                    li.textContent = lines[j].replace(/^[\-\*\u2022\•]\s+/, '').replace(/^\d+\.\s*/, '');
                                    ul.appendChild(li);
                                    j++;
                                }
                                bodyEl.appendChild(ul);
                                i = j - 1;
                                continue;
                            }

                            // heading heuristic: short line (<=6 words) or ends with ':' or all-caps
                            const words = line.split(/\s+/).length;
                            const isAllCaps = /^[A-Z0-9 ,()'"-]+$/.test(line) && line.toUpperCase() === line;
                            const looksLikeHeading = line.endsWith(':') || words <= 6 || isAllCaps;

                            if (looksLikeHeading) {
                                const h = document.createElement('div');
                                h.className = 'section-heading';
                                h.textContent = line.replace(/:$/, '');
                                bodyEl.appendChild(h);
                                continue;
                            }

                            const p = document.createElement('div');
                            p.textContent = line;
                            bodyEl.appendChild(p);
                        }

                        messageDiv.appendChild(bodyEl);

                    }

                    // If there is audio provided for this bot message, add a play button (no autoplay)
                    if (audio_b64 && audio_b64.length > 10) {
                        const controls = document.createElement('div');
                        controls.style.marginTop = '8px';
                        const playBtn = document.createElement('button');
                        playBtn.className = 'chat-play-button';
                        playBtn.type = 'button';
                        playBtn.style.cursor = 'pointer';
                        playBtn.style.border = 'none';
                        playBtn.style.background = 'transparent';
                        playBtn.style.color = 'var(--primary-green)';
                        playBtn.innerHTML = '<i class="fas fa-play"></i> Read';
                        playBtn.addEventListener('click', function (e) {
                            e.stopPropagation();
                            playBase64Audio(audio_b64);
                        });
                        controls.appendChild(playBtn);
                        messageDiv.appendChild(controls);
                    }
                } else {
                    messageDiv.textContent = text;
                }

                chatBody.appendChild(messageDiv);
                scrollChatToBottom();

                // Play sound for new messages (no autoplay of TTS)
                if (isBot) {
                    playSound(notificationSound);
                    if (!isChatOpen) {
                        unreadMessages++;
                        updateNotificationBadge();
                    }
                } else {
                    playSound(sendSound);
                }

                return messageDiv;
            }

            // Add bot message with typing indicator
            function addBotMessage(text) {
                // Show typing indicator
                const typingDiv = document.createElement('div');
                typingDiv.className = 'message typing-indicator';
                typingDiv.id = 'typingIndicator';
                typingDiv.innerHTML = 'Typing<span class="typing-dots"><span></span><span></span><span></span></span>';

                chatBody.appendChild(typingDiv);
                scrollChatToBottom();

                // Simulate typing delay
                setTimeout(() => {
                    document.getElementById('typingIndicator')?.remove();
                    addMessage(text, true);
                }, 800 + Math.random() * 800);
            }

            // Scroll chat to bottom
            function scrollChatToBottom() {
                setTimeout(() => {
                    chatBody.scrollTop = chatBody.scrollHeight;
                }, 100);
            }

            // Play sound
            function playSound(audioElement) {
                if (audioElement) {
                    audioElement.currentTime = 0;
                    audioElement.play().catch(e => console.log("Audio play failed:", e));
                }
            }

            // Update notification badge
            function updateNotificationBadge() {
                if (unreadMessages > 0) {
                    notificationBadge.textContent = unreadMessages;
                    notificationBadge.style.display = 'flex';
                } else {
                    notificationBadge.style.display = 'none';
                }
            }

            // Send message to Django backend and return bot response
            async function fetchBotResponse(message) {
                try {
                    const tokenEl = document.querySelector('[name=csrfmiddlewaretoken]');
                    const csrf = tokenEl ? tokenEl.value : '';
                    // prefer sending CSRF token also in header for AJAX
                    const headers = { 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json' };
                    if (csrf) headers['X-CSRFToken'] = csrf;
                    const resp = await fetch('', {
                        method: 'POST',
                        headers,
                        body: new URLSearchParams({ 'csrfmiddlewaretoken': csrf, 'message': message })
                    });
                    const data = await resp.json();
                    return data;
                } catch (err) {
                    console.error('Error fetching bot response from backend:', err);
                    return { botResponse: "Sorry, I couldn't contact the server. Please try again later.", audio_b64: '' };
                }
            }

            function playBase64Audio(base64) {
                try {
                    const binary = atob(base64);
                    const len = binary.length;
                    const bytes = new Uint8Array(len);
                    for (let i = 0; i < len; i++) {
                        bytes[i] = binary.charCodeAt(i);
                    }
                    const blob = new Blob([bytes], { type: 'audio/mpeg' });
                    const url = URL.createObjectURL(blob);
                    const audio = new Audio(url);
                    audio.play().catch(e => console.error('Audio play error:', e));
                } catch (e) {
                    console.error('Failed to play base64 audio:', e);
                }
            }

            // Handle user message by sending it to the server
            function handleUserMessage(message) {
                if (!message) return;

                addMessage(message, false);
                // Show typing indicator
                const typingDiv = document.createElement('div');
                typingDiv.className = 'message typing-indicator';
                typingDiv.id = 'typingIndicator';
                typingDiv.innerHTML = 'Typing<span class="typing-dots"><span></span><span></span><span></span></span>';
                chatBody.appendChild(typingDiv);
                scrollChatToBottom();

                // Request bot response from server
                fetchBotResponse(message).then(data => {
                    document.getElementById('typingIndicator')?.remove();
                    const botResponse = (data && data.botResponse) ? data.botResponse : 'Sorry, no response.';
                    // Pass audio_b64 to addMessage so it can render a play button instead of autoplaying
                    const audio_b64 = (data && data.audio_b64) ? data.audio_b64 : '';
                    addMessage(botResponse, true, audio_b64);
                }).catch(err => {
                    document.getElementById('typingIndicator')?.remove();
                    addMessage("Sorry, something went wrong.", true);
                    console.error(err);
                });
            }

            // Initialize speech recognition
            function initSpeechRecognition() {
                if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                    alert('Speech recognition is not supported in your browser. Please use Chrome or Edge.');
                    return null;
                }

                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';

                return recognition;
            }

            // Toggle chat window
            function toggleChat() {
                isChatOpen = !isChatOpen;
                chatWindow.classList.toggle('active');

                if (isMobile) {
                    chatOverlay.classList.toggle('active');
                    document.body.style.overflow = isChatOpen ? 'hidden' : '';
                }

                // Clear notification badge when opening chat
                if (isChatOpen && unreadMessages > 0) {
                    unreadMessages = 0;
                    updateNotificationBadge();
                }

                // Focus on input field when chat opens
                if (isChatOpen) {
                    setTimeout(() => {
                        messageInput.focus();
                    }, 300);
                }
            }

            // Close chat
            function closeChat() {
                isChatOpen = false;
                chatWindow.classList.remove('active');
                chatOverlay.classList.remove('active');
                document.body.style.overflow = '';
            }

            // Show Chatbot Notification
            function showChatbotNotification() {
                // Create a temporary notification
                const notification = document.createElement('div');
                notification.style.position = 'fixed';
                notification.style.bottom = '100px';
                notification.style.right = '20px';
                notification.style.background = 'var(--gradient-primary)';
                notification.style.color = 'white';
                notification.style.padding = '12px 16px';
                notification.style.borderRadius = 'var(--radius-md)';
                notification.style.boxShadow = 'var(--shadow-medium)';
                notification.style.zIndex = '1004';
                notification.style.maxWidth = '280px';
                notification.style.fontSize = '0.9rem';
                notification.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <i class="fas fa-robot" style="font-size: 1.2rem;"></i>
                        <div>
                            <strong style="display: block; margin-bottom: 4px;">Admissions Assistant</strong>
                            <p style="margin: 0; opacity: 0.9;">Need help with your application? I can guide you!</p>
                        </div>
                    </div>
                `;

                document.body.appendChild(notification);

                // Remove notification after 5 seconds
                setTimeout(() => {
                    notification.style.opacity = '0';
                    notification.style.transition = 'opacity 0.3s';
                    setTimeout(() => {
                        if (notification.parentNode) {
                            document.body.removeChild(notification);
                        }
                    }, 300);
                }, 5000);
            }

            // Event Listeners for Chatbot
            chatbotButton.addEventListener('click', toggleChat);

            closeButton.addEventListener('click', closeChat);

            chatOverlay.addEventListener('click', closeChat);

            minimizeButton.addEventListener('click', function () {
                if (isMobile) {
                    closeChat();
                } else {
                    isMinimized = !isMinimized;
                    if (isMinimized) {
                        chatBody.style.display = 'none';
                        chatFooter.style.display = 'none';
                        minimizeButton.innerHTML = '<i class="fas fa-plus"></i>';
                        chatWindow.style.height = 'auto';
                    } else {
                        chatBody.style.display = 'flex';
                        chatFooter.style.display = 'block';
                        minimizeButton.innerHTML = '<i class="fas fa-minus"></i>';
                        chatWindow.style.height = '500px';
                        scrollChatToBottom();
                    }
                }
            });

            sendButton.addEventListener('click', function () {
                const message = messageInput.value.trim();
                if (message) {
                    handleUserMessage(message);
                    messageInput.value = '';
                }
            });

            messageInput.addEventListener('keypress', function (event) {
                if (event.key === 'Enter') {
                    const message = messageInput.value.trim();
                    if (message) {
                        handleUserMessage(message);
                        messageInput.value = '';
                    }
                }
            });

            // Voice button event listener
            voiceButton.addEventListener('click', function () {
                if (isMicActive) {
                    // Stop speech recognition
                    isMicActive = false;
                    voiceButton.classList.remove('active');
                    voiceIndicator.classList.remove('active');

                    if (speechRecognition) {
                        speechRecognition.stop();
                    }
                } else {
                    // Start speech recognition
                    isMicActive = true;
                    voiceButton.classList.add('active');

                    speechRecognition = initSpeechRecognition();

                    if (speechRecognition) {
                        speechRecognition.start();
                        voiceIndicator.classList.add('active');

                        speechRecognition.onresult = function (event) {
                            const transcript = event.results[0][0].transcript;
                            messageInput.value = transcript;
                            voiceIndicator.classList.remove('active');
                            voiceButton.classList.remove('active');
                            isMicActive = false;

                            // Auto-submit the voice message
                            handleUserMessage(transcript);
                            messageInput.value = '';
                        };

                        speechRecognition.onerror = function (event) {
                            console.error('Speech recognition error:', event.error);
                            voiceIndicator.classList.remove('active');
                            voiceButton.classList.remove('active');
                            isMicActive = false;

                            if (event.error === 'not-allowed') {
                                addBotMessage('Please allow microphone access to use voice input.');
                            }
                        };

                        speechRecognition.onend = function () {
                            voiceIndicator.classList.remove('active');
                            voiceButton.classList.remove('active');
                            isMicActive = false;
                        };
                    }
                }
            });

            // Quick question buttons
            quickQuestions.querySelectorAll('.chat-quick-btn').forEach(button => {
                button.addEventListener('click', function () {
                    const question = this.getAttribute('data-question');
                    handleUserMessage(question);
                });
            });

            // Auto-focus on input when chat opens
            chatWindow.addEventListener('transitionend', function () {
                if (isChatOpen && !isMinimized) {
                    messageInput.focus();
                }
            });

            // Initialize notification badge
            updateNotificationBadge();

            // Show initial chatbot notification after delay
            setTimeout(() => {
                showChatbotNotification();
            }, 2000);

            // Prevent closing chat when clicking inside chat window
            chatWindow.addEventListener('click', function (event) {
                event.stopPropagation();
            });
        });