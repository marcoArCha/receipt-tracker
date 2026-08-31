import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import "./LoginPage.css";

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, signUp, confirmSignUp } = useAuth();

  // "login" | "signup" | "confirm"
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (mode === "login") {
        await login(email, password);
        navigate("/");
      } else if (mode === "signup") {
        await signUp(email, password);
        setMode("confirm");
      } else if (mode === "confirm") {
        await confirmSignUp(email, code);
        setMode("login");
        setError(null);
      }
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <h1 className="login-title">Receipts</h1>
        <p className="login-subtitle">
          {mode === "login" && "Log in to your account"}
          {mode === "signup" && "Create an account"}
          {mode === "confirm" &&
            "Enter the code we emailed you to confirm your account"}
        </p>

        <form onSubmit={handleSubmit} className="login-form">
          {mode !== "confirm" && (
            <>
              <label className="login-label">
                Email
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="login-input"
                />
              </label>
              <label className="login-label">
                Password
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  className="login-input"
                />
              </label>
            </>
          )}

          {mode === "confirm" && (
            <label className="login-label">
              Confirmation code
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
                className="login-input"
              />
            </label>
          )}

          {error && <p className="login-error">{error}</p>}

          <button type="submit" className="login-button" disabled={isSubmitting}>
            {isSubmitting
              ? "Please wait…"
              : mode === "login"
              ? "Log in"
              : mode === "signup"
              ? "Sign up"
              : "Confirm account"}
          </button>
        </form>

        {mode === "login" && (
          <button
            type="button"
            className="login-link"
            onClick={() => {
              setMode("signup");
              setError(null);
            }}
          >
            Need an account? Sign up
          </button>
        )}
        {mode === "signup" && (
          <button
            type="button"
            className="login-link"
            onClick={() => {
              setMode("login");
              setError(null);
            }}
          >
            Already have an account? Log in
          </button>
        )}
      </div>
    </div>
  );
}
