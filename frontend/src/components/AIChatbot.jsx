import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, User, Sparkles, AlertCircle, Trash2 } from 'lucide-react';
import { sendAIChatMessage } from '../services/api';

const QUICK_QUESTIONS = [
  'Is the air quality safe today?',
  'Which pollutant is the biggest concern?',
  'Should I exercise outdoors today?',
  'What does PM2.5 mean?',
  'How can I reduce my exposure?',
];

export const AIChatbot = ({ environmentalContext }) => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am your AI Air Quality Assistant. Ask me anything about current atmospheric conditions, pollutant health effects, or outdoor safety precautions.',
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  const handleSendMessage = async (textToSend = inputMessage) => {
    const trimmed = textToSend.trim();
    if (!trimmed || isThinking) return;

    const newHistory = [...messages, { role: 'user', content: trimmed }];
    setMessages(newHistory);
    setInputMessage('');
    setIsThinking(true);
    setErrorMsg(null);

    try {
      // Map context to EnvironmentalContext schema
      const contextPayload = environmentalContext ? {
        latitude: environmentalContext.location?.latitude,
        longitude: environmentalContext.location?.longitude,
        predicted_aqi: environmentalContext.prediction?.aqi,
        aqi_category: environmentalContext.prediction?.category,
        dominant_pollutant: environmentalContext.prediction?.dominant_pollutant,
        pm25: environmentalContext.air_quality?.pm25,
        pm10: environmentalContext.air_quality?.pm10,
        co: environmentalContext.air_quality?.co,
        no2: environmentalContext.air_quality?.no2,
        so2: environmentalContext.air_quality?.so2,
        o3: environmentalContext.air_quality?.o3,
        temperature: environmentalContext.weather?.temperature,
        humidity: environmentalContext.weather?.humidity,
        wind_speed: environmentalContext.weather?.wind_speed,
        pressure: environmentalContext.weather?.pressure,
        observed_at: environmentalContext.observed_at,
      } : null;

      const res = await sendAIChatMessage(trimmed, contextPayload, newHistory);
      if (res && res.reply) {
        setMessages((prev) => [...prev, { role: 'assistant', content: res.reply }]);
      } else {
        throw new Error('AI returned an empty response.');
      }
    } catch (err) {
      const errorText = err.response?.data?.detail || 'AI assistance is temporarily unavailable. Please try again.';
      setErrorMsg(errorText);
    } finally {
      setIsThinking(false);
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: 'Chat cleared. How else can I assist you with air quality and environmental health today?',
      },
    ]);
    setErrorMsg(null);
  };

  return (
    <div className="glass-card ai-feature-card">
      <div className="ai-feature-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div className="ai-badge-icon">
            <Bot size={20} />
          </div>
          <div>
            <h2 className="ai-feature-title">AI Air Quality Assistant</h2>
            <p className="ai-feature-subtitle">Context-aware conversational analysis and safety advice</p>
          </div>
        </div>

        <button 
          className="btn-icon-secondary" 
          onClick={handleClearChat}
          title="Clear conversation history"
          aria-label="Clear chat history"
        >
          <Trash2 size={16} />
        </button>
      </div>

      {/* Quick Prompts */}
      <div className="quick-prompts-container">
        {QUICK_QUESTIONS.map((q, idx) => (
          <button
            key={idx}
            type="button"
            className="quick-prompt-btn"
            onClick={() => handleSendMessage(q)}
            disabled={isThinking}
          >
            <Sparkles size={12} style={{ color: 'var(--accent-cyan)' }} />
            <span>{q}</span>
          </button>
        ))}
      </div>

      {/* Messages Stream */}
      <div className="chat-messages-box">
        {messages.map((msg, index) => (
          <div key={index} className={`chat-message-row ${msg.role}`}>
            <div className={`chat-avatar ${msg.role}`}>
              {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
            </div>
            <div className={`chat-bubble ${msg.role}`}>
              <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
            </div>
          </div>
        ))}

        {isThinking && (
          <div className="chat-message-row assistant">
            <div className="chat-avatar assistant">
              <Bot size={16} />
            </div>
            <div className="chat-bubble assistant thinking">
              <span className="dot-flashing"></span>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginLeft: '8px' }}>
                AI is analyzing environmental telemetry...
              </span>
            </div>
          </div>
        )}

        {errorMsg && (
          <div className="chat-error-banner">
            <AlertCircle size={16} />
            <span>{errorMsg}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
        className="chat-input-form"
      >
        <input
          type="text"
          className="chat-input-field"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Ask a question about air quality, pollutants, or health..."
          disabled={isThinking}
          aria-label="Ask AI Assistant a question"
        />
        <button
          type="submit"
          className="btn-primary"
          disabled={!inputMessage.trim() || isThinking}
          aria-label="Send message"
        >
          <Send size={16} />
          <span>Send</span>
        </button>
      </form>

      <div className="ai-medical-disclaimer">
        ⚠️ General Awareness Notice: Environmental AI responses do not replace medical advice from a qualified healthcare professional.
      </div>
    </div>
  );
};
