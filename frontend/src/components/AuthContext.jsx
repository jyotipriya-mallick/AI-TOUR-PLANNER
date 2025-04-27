import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [username, setUsername] = useState('');

    // Load auth state from localStorage on initial render
    useEffect(() => {
        const storedUser = localStorage.getItem('username');
        const loggedIn = localStorage.getItem('isLoggedIn') === 'true';

        if (loggedIn && storedUser) {
            setIsLoggedIn(true);
            setUsername(storedUser);
        }
    }, []);

    const login = (user) => {
        setIsLoggedIn(true);
        setUsername(user);
        localStorage.setItem('isLoggedIn', 'true');
        localStorage.setItem('username', user);
    };

    const logout = () => {
        setIsLoggedIn(false);
        setUsername('');
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('username');
    };

    return (
        <AuthContext.Provider value={{ isLoggedIn, username, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};
