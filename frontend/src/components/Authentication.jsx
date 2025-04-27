import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
// import { useTheme } from "../../context/ThemeContext";
import { useAuth } from "./AuthContext";
import axios from "axios";

function Authentication() {
    const { login } = useAuth();
    const { signup } = useAuth();
    const { isDarkMode } = useState(false);
    const navigate = useNavigate();
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const [signinFormData, setSigninFormData] = useState({
        email: "",
        password: "",
    });

    const [signupFormData, setSignupFormData] = useState({
        username: "",
        first_name: "",
        last_name: "",
        email: "",
        password: "",
        password2: "",
    });

    const handleSigninChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleSignupChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleSigninSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const response = await axios.post("/api/login/", formData, {
                withCredentials: true,
            });
            const data = response.data;
            // The login function should store the user and tokens (access & refresh)
            await login(data.user, data.access, data.refresh);
            navigate("/dashboard");
        } catch (err) {
            console.error("Login error:", err);
            setError(
                err.response?.data?.detail ||
                    "Login failed. Please check your credentials."
            );
        } finally {
            setLoading(false);
        }
    };

    const handleSignupSubmit = async (e) => {
        e.preventDefault();
        setError("");

        if (formData.password !== formData.password2) {
            setError("Passwords do not match");
            return;
        }

        setLoading(true);
        try {
            const response = await axios.post("/api/register/", formData, {
                withCredentials: true,
            });
            const data = response.data;
            // Call the signup function from AuthContext to store user and tokens.
            await signup(data.user, data.access, data.refresh);
            navigate("/dashboard");
        } catch (err) {
            console.error("Signup error:", err);
            setError(err.response?.data?.detail || "Failed to create account");
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <div className="" >
                <div className="">
                    <div className="" >
                        <h2 className="" >
                            Welcome Back
                        </h2>

                        {error && (
                            <div className="">
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleSigninSubmit} className="">
                            <div>
                                <label htmlFor="email" className="" >
                                    Email
                                </label>
                                <input
                                    type="email"
                                    id="email"
                                    name="email"
                                    required
                                    value={signinFormData.email}
                                    onChange={handleSigninChange}
                                    className=""
                                />
                            </div>

                            <div>
                                <label htmlFor="password" className="" >
                                    Password
                                </label>
                                <input
                                    type="password"
                                    id="password"
                                    name="password"
                                    required
                                    value={signinFormData.password}
                                    onChange={handleSigninChange}
                                    className=""
                                />
                            </div>

                            <div className="">
                                <div className="">
                                    <input
                                        id="remember-me"
                                        name="remember-me"
                                        type="checkbox"
                                        className=""
                                    />
                                    <label htmlFor="remember-me" className="" >
                                        Remember me
                                    </label>
                                </div>

                                <Link to="/forgot-password" className="" >
                                    Forgot password?
                                </Link>
                            </div>

                            <button type="submit" disabled={loading} className="" >
                                {loading ? "Signing In..." : "Sign In"}
                            </button>
                        </form>

                        <div className="">
                            <p className="" >
                                Don't have an account?{" "}
                                <Link to="/signup" className="" >
                                    Sign up
                                </Link>
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* // {signup} */}

            <div className="" >
                <div className="">
                    <div className="" >
                        <h2 className="" >
                            Create an Account
                        </h2>

                        {error && (
                            <div className="">
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleSignupSubmit} className="">
                            <div>
                                <label htmlFor="username" className="" >
                                    Username
                                </label>
                                <input
                                    type="text"
                                    id="username"
                                    name="username"
                                    required
                                    value={signupFormData.username}
                                    onChange={handleSignupChange}
                                    className=""
                                />
                            </div>

                            <div>
                                <label htmlFor="first_name" className="" >
                                    First Name
                                </label>
                                <input
                                    type="text"
                                    id="first_name"
                                    name="first_name"
                                    required
                                    value={signupFormData.first_name}
                                    onChange={handleSignupChange}
                                    className=""
                                />
                            </div>

                            <div>
                                <label htmlFor="last_name" className="" >
                                    Last Name
                                </label>
                                <input
                                    type="text"
                                    id="last_name"
                                    name="last_name"
                                    required
                                    value={signupFormData.last_name}
                                    onChange={handleSignupChange}
                                    className=""
                                />
                            </div>

                            <div>
                                <label htmlFor="email" className="" >
                                    Email
                                </label>
                                <input
                                    type="email"
                                    id="email"
                                    name="email"
                                    required
                                    value={signupFormData.email}
                                    onChange={handleSignupChange}
                                    className=""
                                />
                            </div>

                            <div>
                                <label htmlFor="password" className="" >
                                    Password
                                </label>
                                <input
                                    type="password"
                                    id="password"
                                    name="password"
                                    required
                                    value={signupFormData.password}
                                    onChange={handleSignupChange}
                                    className=""
                                />
                            </div>

                            <div>
                                <label htmlFor="password2" className="" >
                                    Confirm Password
                                </label>
                                <input
                                    type="password"
                                    id="password2"
                                    name="password2"
                                    required
                                    value={signupFormData.password2}
                                    onChange={handleSignupChange}
                                    className=""
                                />
                            </div>

                            <div className="">
                                <input
                                    id="terms"
                                    name="terms"
                                    type="checkbox"
                                    required
                                    className=""
                                />
                                <label htmlFor="terms" className="" >
                                    I agree to the{" "}
                                    <Link to="/terms" className="" >
                                        Terms of Service
                                    </Link>{" "}
                                    and{" "}
                                    <Link to="/privacy" className="" >
                                        Privacy Policy
                                    </Link>
                                </label>
                            </div>

                            <button type="submit" disabled={loading} className="" >
                                {loading ? "Creating Account..." : "Create Account"}
                            </button>
                        </form>

                        <div className="">
                            <p className="" >
                                Already have an account?{" "}
                                <Link to="/login" className="" >
                                    Sign in
                                </Link>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}

export default Authentication;
