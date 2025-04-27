import React, { useState, useEffect, useRef } from 'react';

// 

import "../styles/Chatbot.css";

import { motion, AnimatePresence } from 'framer-motion';
import { ChatBubbleLeftIcon, XMarkIcon, PaperAirplaneIcon, MicrophoneIcon } from '@heroicons/react/24/outline';

import axios from 'axios';

// Ensure credentials (cookies) are sent with every request
axios.defaults.withCredentials = true;

function Chatbot() {
    const [isOpen, setIsOpen] = useState(true);
    const [messages, setMessages] = useState([
        {
        id: 1,
        type: 'bot',
        content: "Hi! I'm your AI travel assistant. How can I help you plan your next adventure?",
        timestamp: new Date(),
        },
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const messageIdRef = useRef(2);

    const getNextId = () => {
        const id = messageIdRef.current;
        messageIdRef.current += 1;
        return id;
      };
    
      useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
      }, [messages]);
    
      const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!inputValue.trim() || isLoading) return;
    
        const userMessage = {
          id: getNextId(),
          type: 'user',
          content: inputValue,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);
        const currentInput = inputValue;
        setInputValue('');
        setIsLoading(true);
    
        try {
          console.log("Sending message to backend:", currentInput);
          const response = await axios.post(
            '/api/chatbot/',
            { message: currentInput },
            { withCredentials: true }
          );
          console.log("Response from backend:", response.data);
          const botMessage = {
            id: getNextId(),
            type: 'bot',
            content: response.data.message,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, botMessage]);
        } catch (error) {
          console.error('Error sending message:', error);
          const errorMessage = {
            id: getNextId(),
            type: 'bot',
            content: "Sorry, I couldn't process your request. Please try again.",
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, errorMessage]);
        } finally {
          setIsLoading(false);
        }
      };

    return (
        <>
            {/* Floating Chat Button */}
            <motion.button
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => setIsOpen(true)}
                className=""
            >
                <ChatBubbleLeftIcon className="" />
            </motion.button>

            {/* Chat Window */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 20, scale: 0.95 }}
                        transition={{ duration: 0.2 }}
                        className=""
                    >
                        {/* Chat Header */}
                        <div className="">
                            <div className="">
                                <div className="">
                                    <span className="">
                                        AI
                                    </span>
                                </div>
                                <div>
                                    <h3 className="">
                                        Travel Assistant
                                    </h3>
                                    <p className="">
                                        Online
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={() => setIsOpen(false)}
                                className=""
                            >
                                <XMarkIcon className="" />
                            </button>
                        </div>

                        {/* Chat Messages */}
                        <div className="">
                            {messages.map((message) => (
                                <motion.div
                                    key={message.id}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.3 }}
                                    className={`flex ${
                                        message.type === "user"
                                            ? ""
                                            : ""
                                    }`}
                                >
                                    <div
                                        className={` ${
                                            message.type === "user"
                                                ? ""
                                                : ""
                                        }`}
                                    >
                                        {message.type === "bot" ? (
                                            <strong className="">
                                                {message.content}
                                            </strong>
                                        ) : (
                                            <p className="">
                                                {message.content}
                                            </p>
                                        )}
                                        <p className="">
                                            {new Date(
                                                message.timestamp
                                            ).toLocaleTimeString([], {
                                                hour: "2-digit",
                                                minute: "2-digit",
                                            })}
                                        </p>
                                    </div>
                                </motion.div>
                            ))}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Chat Input */}
                        <form
                            onSubmit={handleSendMessage}
                            className=""
                        >
                            <div className="">
                                <button
                                    type="button"
                                    className=""
                                >
                                    <MicrophoneIcon className="" />
                                </button>
                                <input
                                    type="text"
                                    value={inputValue}
                                    onChange={(e) =>
                                        setInputValue(e.target.value)
                                    }
                                    placeholder="Type your message..."
                                    className=""
                                />
                                <button
                                    type="submit"
                                    className=""
                                    disabled={!inputValue.trim() || isLoading}
                                >
                                    <PaperAirplaneIcon className="" />
                                </button>
                            </div>
                        </form>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}

export default Chatbot;
