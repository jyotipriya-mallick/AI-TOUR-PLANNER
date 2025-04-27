import { useState } from "react";
import { Link } from "react-router-dom";

// import ""
import { useAuth } from './AuthContext';

import "../styles/Navbar.css";

import { Home, LogIn, LogOut, Brain } from 'lucide-react'; //icon pack xD

function Navbar() {

    const { isLoggedIn, username, login, logout } = useAuth();

    return (
        <nav className="main-nav">
            <div className="main-nav-branding">
                <Link to="/" className="branding-link" aria-label="Home">
                    <Home className="home-icon" />
                    <span className="branding-text">AI Tour Planner</span>
                </Link>
            </div>


            <div className="main-nav-links">
                <Link to="/" className="" aria-label="HOME">
                    <span className="">Home</span>
                </Link>

                <Link to="/reviews" className="" aria-label="REVIEWS">
                    <span className="">Reviews</span>
                </Link>

                <Link to="/contact" className="" aria-label="CONTACT US">
                    <span className="">Contact Us</span>
                </Link>
            </div>

            <div className="main-nav-feature">
                <Link to="/assist" className="chatbot-link" aria-label="CHATBOT">
                    <Brain className="chatbot-icon" />
                    <span className="chatbot-button">Assist</span>
                </Link>
                {
                    isLoggedIn ? (
                        <Link onClick={logout} className="logout-link" aria-label="LOGOUT">
                            <LogOut className="logout-icon" />
                            <span className="logout-text"> {username} </span>
                        </Link>
                    ) : (
                        <Link to="/auth" onClick={()=>login("Jam")} className="login-link" aria-label="LOGIN">
                            <LogIn className="login-icon" />
                            <span className="login-text">Login</span>
                        </Link>
                    )
                }
            </div>
        </nav>
    );
}

export default Navbar;
