import "./Homepage.css";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Homepage() {
    const navigate = useNavigate();
    const { user, login, register, logout } = useAuth();

    const [showLogin, setShowLogin] = useState(false);
    const [showSignup, setShowSignup] = useState(false);

    const [showLoginPassword, setShowLoginPassword] = useState(false);
    const [showSignupPassword, setShowSignupPassword] = useState(false);

    const [loginData, setLoginData] = useState({
        email: "",
        password: ""
    });

    const [signupData, setSignupData] = useState({
        name: "",
        email: "",
        department: "",
        gender: "",
        password: ""
    });

    const [loginMessage, setLoginMessage] = useState("");
    const [signupMessage, setSignupMessage] = useState("");
    const [authBusy, setAuthBusy] = useState(false);

    // Open Login popup
    const openLogin = () => {
        setShowLogin(true);
        setShowSignup(false);
        setLoginMessage("");
    };

    // Open Signup popup
    const openSignup = () => {
        setShowSignup(true);
        setShowLogin(false);
        setSignupMessage("");
    };

    // Close both popups
    const closePopups = () => {
        setShowLogin(false);
        setShowSignup(false);
        setLoginMessage("");
        setSignupMessage("");
    };

    // Login input handling
    const handleLoginChange = (e) => {
        setLoginData({
            ...loginData,
            [e.target.name]: e.target.value
        });
    };

    // Signup input handling
    const handleSignupChange = (e) => {
        setSignupData({
            ...signupData,
            [e.target.name]: e.target.value
        });
    };

    const handleLogin = async (e) => {
        e.preventDefault();

        if (!loginData.email || !loginData.password) {
            setLoginMessage("Please enter your email and password.");
            return;
        }

        setAuthBusy(true);
        setLoginMessage("");

        try {
            await login(loginData.email, loginData.password);
            navigate("/dashboard");
        } catch (error) {
            setLoginMessage(error.message || "Invalid email or password.");
        } finally {
            setAuthBusy(false);
        }
    };

    const handleSignup = async (e) => {
        e.preventDefault();

        if (
            !signupData.name ||
            !signupData.email ||
            !signupData.department ||
            !signupData.gender ||
            !signupData.password
        ) {
            setSignupMessage("Please fill in all fields.");
            return;
        }

        setAuthBusy(true);
        setSignupMessage("");

        try {
            await register(signupData);
            navigate("/dashboard");
        } catch (error) {
            setSignupMessage(error.message || "Could not create account.");
        } finally {
            setAuthBusy(false);
        }
    };

    return (
        <div className="homepage">

            {/* Top Navigation */}
            <nav className="homepage-nav">

                <div className="nav-left">
                    {user && (
                        <button
                            className="dashboard-btn"
                            onClick={() => navigate("/dashboard")}
                        >
                            Dashboard
                        </button>
                    )}
                </div>

                <div className="nav-right">
                    {user ? (
                        <button
                            className="login-btn"
                            onClick={async () => {
                                await logout();
                            }}
                        >
                            Logout
                        </button>
                    ) : (
                        <>
                            <button
                                className="login-btn"
                                onClick={openLogin}
                            >
                                Login
                            </button>

                            <button
                                className="signup-btn"
                                onClick={openSignup}
                            >
                                Sign Up
                            </button>
                        </>
                    )}
                </div>

            </nav>

            {/* Main Content */}
            <main className="homepage-content">

                <h1>AI-Integrated IoT Attendance System</h1>

                <p>
                    Smart and automated attendance using AI-powered face recognition.
                </p>

            </main>


            {/* ================= LOGIN MODAL ================= */}
            {showLogin && (
                <div
                    className="auth-overlay"
                    onClick={closePopups}
                >
                    <div
                        className="auth-modal"
                        onClick={(e) => e.stopPropagation()}
                    >

                        <button
                            className="modal-close"
                            onClick={closePopups}
                        >
                            ×
                        </button>

                        <h2>Welcome Back</h2>

                        <p className="auth-subtitle">
                            Login to your account
                        </p>

                        <form onSubmit={handleLogin}>

                            <div className="form-group">
                                <label>Email</label>

                                <input
                                    type="email"
                                    name="email"
                                    placeholder="Enter your email"
                                    value={loginData.email}
                                    onChange={handleLoginChange}
                                />
                            </div>


                            <div className="form-group">
                                <label>Password</label>

                                <div className="password-wrapper">

                                    <input
                                        type={
                                            showLoginPassword
                                                ? "text"
                                                : "password"
                                        }
                                        name="password"
                                        placeholder="Enter your password"
                                        value={loginData.password}
                                        onChange={handleLoginChange}
                                    />

                                    <button
                                        type="button"
                                        className="password-toggle"
                                        onClick={() =>
                                            setShowLoginPassword(
                                                !showLoginPassword
                                            )
                                        }
                                        aria-label={
                                            showLoginPassword
                                                ? "Hide password"
                                                : "Show password"
                                        }
                                    >
                                        {showLoginPassword ? "◉" : "◌"}
                                    </button>

                                </div>
                            </div>


                            {loginMessage && (
                                <p className="auth-message error">
                                    {loginMessage}
                                </p>
                            )}


                            <button
                                type="submit"
                                className="auth-submit-btn"
                                disabled={authBusy}
                            >
                                {authBusy ? "Logging in..." : "Login"}
                            </button>

                        </form>

                        <p className="switch-auth">
                            Don't have an account?{" "}
                            <button
                                onClick={openSignup}
                            >
                                Sign Up
                            </button>
                        </p>

                    </div>
                </div>
            )}


            {/* ================= SIGNUP MODAL ================= */}
            {showSignup && (
                <div
                    className="auth-overlay"
                    onClick={closePopups}
                >
                    <div
                        className="auth-modal signup-modal"
                        onClick={(e) => e.stopPropagation()}
                    >

                        <button
                            className="modal-close"
                            onClick={closePopups}
                        >
                            ×
                        </button>

                        <h2>Create Account</h2>

                        <p className="auth-subtitle">
                            Create your account to get started
                        </p>

                        <form onSubmit={handleSignup}>

                            <div className="form-group">
                                <label>Name</label>

                                <input
                                    type="text"
                                    name="name"
                                    placeholder="Enter your name"
                                    value={signupData.name}
                                    onChange={handleSignupChange}
                                />
                            </div>


                            <div className="form-group">
                                <label>Email</label>

                                <input
                                    type="email"
                                    name="email"
                                    placeholder="Enter your email"
                                    value={signupData.email}
                                    onChange={handleSignupChange}
                                />
                            </div>


                            <div className="form-row">

                                <div className="form-group">
                                    <label>Department</label>

                                    <input
                                        type="text"
                                        name="department"
                                        placeholder="e.g. CSE"
                                        value={signupData.department}
                                        onChange={handleSignupChange}
                                    />
                                </div>


                                <div className="form-group">
                                    <label>Gender</label>

                                    <select
                                        name="gender"
                                        value={signupData.gender}
                                        onChange={handleSignupChange}
                                    >
                                        <option value="">
                                            Select
                                        </option>

                                        <option value="Male">
                                            Male
                                        </option>

                                        <option value="Female">
                                            Female
                                        </option>

                                        <option value="Other">
                                            Other
                                        </option>
                                    </select>
                                </div>

                            </div>


                            <div className="form-group">
                                <label>Password</label>

                                <div className="password-wrapper">

                                    <input
                                        type={
                                            showSignupPassword
                                                ? "text"
                                                : "password"
                                        }
                                        name="password"
                                        placeholder="Create a password"
                                        value={signupData.password}
                                        onChange={handleSignupChange}
                                    />

                                    <button
                                        type="button"
                                        className="password-toggle"
                                        onClick={() =>
                                            setShowSignupPassword(
                                                !showSignupPassword
                                            )
                                        }
                                        aria-label={
                                            showSignupPassword
                                                ? "Hide password"
                                                : "Show password"
                                        }
                                    >
                                        {showSignupPassword ? "◉" : "◌"}
                                    </button>

                                </div>
                            </div>


                            {signupMessage && (
                                <p
                                    className={`auth-message ${
                                        signupMessage.includes("successfully")
                                            ? "success"
                                            : "error"
                                    }`}
                                >
                                    {signupMessage}
                                </p>
                            )}


                            <button
                                type="submit"
                                className="auth-submit-btn"
                                disabled={authBusy}
                            >
                                {authBusy ? "Creating account..." : "Sign Up"}
                            </button>

                        </form>

                        <p className="switch-auth">
                            Already have an account?{" "}
                            <button
                                onClick={openLogin}
                            >
                                Login
                            </button>
                        </p>

                    </div>
                </div>
            )}

        </div>
    );
}

export default Homepage;