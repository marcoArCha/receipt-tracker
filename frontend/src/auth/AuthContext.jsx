import { createContext, useContext, useState, useEffect } from "react";
import { userPool } from "./cognito";
import * as authApi from "./auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // undefined = we haven't checked yet, null = checked, nobody logged in,
  // string = the logged-in user's email
  const [user, setUser] = useState(undefined);

  useEffect(() => {
    checkCurrentUser();
  }, []);

  async function checkCurrentUser() {
    const cognitoUser = userPool.getCurrentUser();
    if (!cognitoUser) {
      setUser(null);
      return;
    }
    try {
      const token = await authApi.getIdToken();
      setUser(token ? cognitoUser.getUsername() : null);
    } catch {
      setUser(null);
    }
  }

  async function login(email, password) {
    await authApi.signIn(email, password);
    setUser(email);
  }

  function logout() {
    authApi.signOut();
    setUser(null);
  }

  const value = {
    user,
    isLoading: user === undefined,
    isLoggedIn: Boolean(user),
    login,
    logout,
    signUp: authApi.signUp,
    confirmSignUp: authApi.confirmSignUp,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
