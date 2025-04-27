import { useState } from "react";
import { Link } from "react-router-dom";


import { Heart, Instagram, Twitter, Facebook } from 'lucide-react'; //icon pack xD

function ContactUs() {

    return (
        <footer className="footer">
            <div className="footer-container">
                <div className="footer-grid">
                    {/* Company info */}
                    <div>
                        <h3 className="footer-brand">
                            AI Tour Planner
                        </h3>
                        <p className="footer-description">
                            Creating personalized travel experiences powered
                            by artificial intelligence.
                        </p>
                        <div className="social-links">
                            <a
                                href="#"
                                className="social-link"
                                aria-label="Instagram"
                            >
                                <Instagram className="w-5 h-5" />
                            </a>
                            <a
                                href="#"
                                className="social-link"
                                aria-label="Twitter"
                            >
                                <Twitter className="w-5 h-5" />
                            </a>
                            <a
                                href="#"
                                className="social-link"
                                aria-label="Facebook"
                            >
                                <Facebook className="w-5 h-5" />
                            </a>
                        </div>
                    </div>

                    {/* Quick links */}
                    <div>
                        <h3 className="footer-title">Quick Links</h3>
                        <ul className="footer-links">
                            <li>
                                <Link
                                    to="/"
                                    className="footer-link"
                                >
                                    Home
                                </Link>
                            </li>
                            <li>
                                <Link
                                    to="/about"
                                    className="footer-link"
                                >
                                    About Us
                                </Link>
                            </li>
                            <li>
                                <Link
                                    to="/features"
                                    className="footer-link"
                                >
                                    Features
                                </Link>
                            </li>
                            <li>
                                <Link
                                    to="/pricing"
                                    className="footer-link"
                                >
                                    Pricing
                                </Link>
                            </li>
                            <li>
                                <Link
                                    to="/contact"
                                    className="footer-link"
                                >
                                    Contact
                                </Link>
                            </li>
                        </ul>
                    </div>

                    {/* Resources */}
                    <div>
                        <h3 className="footer-title">Resources</h3>
                        <ul className="footer-links">
                            <li>
                                <Link
                                    to="/blog"
                                    className="footer-link"
                                >
                                    Blog
                                </Link>
                            </li>
                            <li>
                                <Link
                                    to="/help"
                                    className="footer-link"
                                >
                                    Help Center
                                </Link>
                            </li>
                            <li>
                                <Link
                                    to="/faq"
                                    className="footer-link"
                                >
                                    FAQs
                                </Link>
                            </li>
                            <li>
                                <Link
                                    to="/guides"
                                    className="footer-link"
                                >
                                    Travel Guides
                                </Link>
                            </li>
                        </ul>
                    </div>

                    {/* Legal */}
                    <div>
                        <h3 className="footer-title">Legal</h3>
                        <ul className="footer-links">
                            <li>
                                <Link
                                    to="/terms"
                                    className="footer-link"
                                >
                                    Terms of Service
                                </Link>
                            </li>
                            <li>
                                <Link
                                    to="/privacy"
                                    className="footer-link"
                                >
                                    Privacy Policy
                                </Link>
                            </li>
                            <li>
                                <Link
                                    to="/cookies"
                                    className="footer-link"
                                >
                                    Cookie Policy
                                </Link>
                            </li>
                        </ul>
                    </div>
                </div>

                <div className="footer-divider">
                    <div className="footer-bottom">
                        <p className="copyright">
                            &copy; {new Date().getFullYear()} AI Tour Planner.
                            All rights reserved.
                        </p>
                        <p className="footer-tagline">
                            Made with{" "}
                            <Heart className="heart-icon" /> for
                            travelers worldwide
                        </p>
                    </div>
                </div>
            </div>
        </footer>
    );
}

export default ContactUs;
