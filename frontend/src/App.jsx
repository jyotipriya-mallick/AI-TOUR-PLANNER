import { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Navbar from "./components/Navbar";
import Home from "./components/Home";
import Reviews from "./components/Reviews";
import ContactUs from "./components/ContactUs";
import Authentication from "./components/Authentication";
import Chatbot from "./components/Chatbot";
import NotFound from "./components/NotFound";
import { AuthProvider } from './components/AuthContext';

import "./App.css";

function App() {

    return (
        <AuthProvider>
            <Router>
                <Navbar />

                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/assist" element={<Chatbot />} />
                    <Route path="/reviews" element={<Reviews />} />
                    <Route path="/contact" element={<ContactUs />} />
                    <Route path="/auth" element={<Authentication />} />
                    <Route path="*" element={<NotFound />} />
                </Routes>

            </Router>
        </AuthProvider>
    );
}

export default App;
