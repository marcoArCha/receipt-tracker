import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import LoginPage from "./LoginPage";
import { useAuth } from "../auth/AuthContext";

// Mock the auth context entirely - these tests are about the form's
// behavior, not about real Cognito calls.
vi.mock("../auth/AuthContext", () => ({
  useAuth: vi.fn(),
}));

function renderLoginPage() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>
  );
}

describe("LoginPage", () => {
  let mockLogin;
  let mockSignUp;
  let mockConfirmSignUp;

  beforeEach(() => {
    mockLogin = vi.fn();
    mockSignUp = vi.fn();
    mockConfirmSignUp = vi.fn();
    useAuth.mockReturnValue({
      login: mockLogin,
      signUp: mockSignUp,
      confirmSignUp: mockConfirmSignUp,
    });
  });

  it("shows the login form by default", () => {
    renderLoginPage();

    expect(screen.getByText("Log in to your account")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Log in" })).toBeInTheDocument();
  });

  it("calls login with the entered email and password", async () => {
    const user = userEvent.setup();
    mockLogin.mockResolvedValue();
    renderLoginPage();

    await user.type(screen.getByLabelText("Email"), "test@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(mockLogin).toHaveBeenCalledWith("test@example.com", "password123");
  });

  it("shows an error message when login fails", async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValue(new Error("Incorrect username or password."));
    renderLoginPage();

    await user.type(screen.getByLabelText("Email"), "test@example.com");
    await user.type(screen.getByLabelText("Password"), "wrong-password");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(
      await screen.findByText("Incorrect username or password.")
    ).toBeInTheDocument();
  });

  it("switches to signup mode and back", async () => {
    const user = userEvent.setup();
    renderLoginPage();

    await user.click(screen.getByText("Need an account? Sign up"));
    expect(screen.getByText("Create an account")).toBeInTheDocument();

    await user.click(screen.getByText("Already have an account? Log in"));
    expect(screen.getByText("Log in to your account")).toBeInTheDocument();
  });

  it("moves to confirm mode after successful signup", async () => {
    const user = userEvent.setup();
    mockSignUp.mockResolvedValue();
    renderLoginPage();

    await user.click(screen.getByText("Need an account? Sign up"));
    await user.type(screen.getByLabelText("Email"), "new@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: "Sign up" }));

    expect(
      await screen.findByText(
        "Enter the code we emailed you to confirm your account"
      )
    ).toBeInTheDocument();
    expect(mockSignUp).toHaveBeenCalledWith(
      "new@example.com",
      "password123"
    );
  });
});
