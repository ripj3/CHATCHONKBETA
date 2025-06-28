import React, { useState, useRef, useEffect } from 'react';
import FocusTrap from 'focus-trap-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

interface CoachProps {
  userId: string;
  initialOpen?: boolean;
}

// Utility class for screen-reader-only content
const srOnly = "absolute w-px h-px p-0 -m-1 overflow-hidden clip-rect-0 whitespace-nowrap border-0";

const Coach: React.FC<CoachProps> = ({ userId, initialOpen = false }) => {
  // State management
  const [isOpen, setIsOpen] = useState<boolean>(initialOpen);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState<string>('');
  const [isThinking, setIsThinking] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isListening, setIsListening] = useState<boolean>(false);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);
  
  // Scroll to bottom of messages when new ones are added
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Focus input when chat is opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Handle Escape key press to close chat
  useEffect(() => {
    const handleEscapeKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        toggleChat();
      }
    };
    
    document.addEventListener('keydown', handleEscapeKey);
    return () => {
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, [isOpen]);

  // Add initial greeting when component mounts
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          role: 'assistant',
          content: "Hi! I'm Sara, your ChatChonk assistant. How can I help you today?",
          timestamp: new Date()
        }
      ]);
    }
  }, []);

  // Status text for screen reader announcements
  const getStatusText = () => {
    if (isListening) return "Microphone activated. Listening for input.";
    if (isThinking) return "Sara is thinking.";
    if (isPlaying) return "Sara is speaking.";
    return "";
  };

  // Toggle chat window open/closed
  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  // Handle sending a message
  const handleSendMessage = async () => {
    if (inputValue.trim() === '') return;
    
    // Add user message to chat
    const userMessage: Message = {
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsThinking(true);
    
    try {
      // Send message to backend
      const response = await fetch('/api/coach', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          text_input: userMessage.content,
          session_id: sessionId
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to get response from coach');
      }
      
      // The backend streams audio/mpeg and places the text reply in header
      const replyText = response.headers.get('X-Coach-Text') || '';

      // Persist session id header if provided
      const newSessionId = response.headers.get('X-Session-Id');
      if (!sessionId && newSessionId) {
        setSessionId(newSessionId);
      }

      // Add assistant text reply to chat
      const assistantMessage: Message = {
        role: 'assistant',
        content: replyText,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);

      // ---- Stream and play audio ----
      if (response.body) {
        const reader = response.body.getReader();
        const chunks: Uint8Array[] = [];
        setIsPlaying(true);

        // eslint-disable-next-line no-constant-condition
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          if (value) chunks.push(value);
        }

        // Build a Blob from the streamed chunks
        const audioBlob = new Blob(chunks, { type: 'audio/mpeg' });
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.onended = () => {
          setIsPlaying(false);
          URL.revokeObjectURL(audioUrl);
        };
        audio.play().catch(() => setIsPlaying(false));
      }
    } catch (error) {
      console.error('Error communicating with coach:', error);
      
      // Add error message
      const errorMessage: Message = {
        role: 'assistant',
        content: "I'm sorry, I'm having trouble responding right now. Please try again in a moment.",
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsThinking(false);
    }
  };

  // Handle pressing Enter to send
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Handle microphone button click (placeholder for future voice functionality)
  const handleMicrophoneClick = () => {
    // Browser SpeechRecognition (Web Speech API)
    const SpeechRecognition =
      // @ts-ignore experimental types
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn('SpeechRecognition API not supported in this browser.');
      return;
    }

    // If already listening -> stop
    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setIsListening(true);
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInputValue(transcript);
      // Automatically send the message after recognition
      setTimeout(handleSendMessage, 100);
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Chat toggle button */}
      <button
        onClick={toggleChat}
        className="bg-pink-500 hover:bg-pink-600 text-white rounded-full p-3 shadow-lg flex items-center justify-center"
        aria-label={isOpen ? "Close chat" : "Open chat"}
      >
        {isOpen ? (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        )}
      </button>

      {/* Chat window with focus trap */}
      {isOpen && (
        <FocusTrap active={isOpen}>
          <div 
            className="absolute bottom-16 right-0 w-80 md:w-96 bg-white rounded-lg shadow-xl border border-gray-200 flex flex-col overflow-hidden"
            role="dialog"
            aria-modal="true"
            aria-labelledby="coach-heading"
          >
            {/* Chat header */}
            <div className="bg-pink-500 text-white p-3 flex items-center">
              <div className="h-8 w-8 rounded-full bg-white/20 flex items-center justify-center mr-2">
                <span className="text-sm font-bold">S</span>
              </div>
              <div className="flex-1">
                <h3 id="coach-heading" className="font-medium">Sara</h3>
                <p className="text-xs opacity-80">ChatChonk Assistant</p>
              </div>
            </div>

            {/* Messages area with ARIA live region */}
            <div 
              className="flex-1 p-3 overflow-y-auto max-h-96 bg-gray-50"
              role="log"
              aria-live="polite"
            >
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`mb-3 ${
                    message.role === 'user' ? 'flex justify-end' : 'flex justify-start'
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      message.role === 'user'
                        ? 'bg-blue-500 text-white rounded-br-none'
                        : 'bg-gray-200 text-gray-800 rounded-bl-none'
                    }`}
                  >
                    <p className="text-sm">{message.content}</p>
                    {message.timestamp && (
                      <p className="text-xs opacity-70 mt-1 text-right">
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    )}
                  </div>
                </div>
              ))}
              
              {/* Thinking indicator */}
              {isThinking && (
                <div className="flex justify-start mb-3">
                  <div className="bg-gray-200 text-gray-800 rounded-lg rounded-bl-none p-3 max-w-[80%]">
                    <div className="flex space-x-1 items-center">
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              )}
              {/* Speaking indicator */}
              {isPlaying && !isThinking && (
                <div className="flex justify-start mb-3">
                  <div className="bg-gray-200 text-gray-800 rounded-lg rounded-bl-none p-3 max-w-[80%]">
                    <div className="flex space-x-1 items-center">
                      <div className="w-2 h-2 bg-pink-500 rounded-full animate-ping" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-pink-500 rounded-full animate-ping" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-pink-500 rounded-full animate-ping" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Invisible element to scroll to */}
              <div ref={messagesEndRef} />
            </div>

            {/* Input area */}
            <div className="border-t border-gray-200 p-3 bg-white">
              {/* Visually hidden label */}
              <label htmlFor="coach-input" className={srOnly}>
                Type a message to Sara
              </label>
              
              <div className="flex items-center">
                <input
                  id="coach-input"
                  ref={inputRef}
                  type="text"
                  value={inputValue}
                  onChange={handleInputChange}
                  onKeyPress={handleKeyPress}
                  placeholder={isListening ? 'Listening...' : 'Type your message...'}
                  className="flex-1 border border-gray-300 rounded-l-lg py-2 px-3 focus:outline-none focus:ring-2 focus:ring-pink-500"
                  disabled={isThinking}
                />
                
                {/* Microphone button */}
                <button
                  onClick={handleMicrophoneClick}
                  className={`py-2 px-3 border-t border-b border-gray-300 ${
                    isListening
                      ? 'bg-red-500 animate-pulse text-white'
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
                  }`}
                  aria-label="Voice input"
                  disabled={isThinking}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                </button>
                
                {/* Send button */}
                <button
                  onClick={handleSendMessage}
                  className="bg-pink-500 hover:bg-pink-600 text-white rounded-r-lg py-2 px-4"
                  aria-label="Send message"
                  disabled={isThinking || inputValue.trim() === ''}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </div>
            </div>
            
            {/* Visually hidden live region for status announcements */}
            <div 
              className={srOnly} 
              aria-live="assertive"
              role="status"
            >
              {getStatusText()}
            </div>
          </div>
        </FocusTrap>
      )}
    </div>
  );
};

export default Coach;
