document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const logoutButton = document.getElementById("logout-button");
  const authStatus = document.getElementById("auth-status");

  const emailInput = document.getElementById("email");
  const loginEmail = document.getElementById("login-email");
  const loginPassword = document.getElementById("login-password");
  const registerEmail = document.getElementById("register-email");
  const registerPassword = document.getElementById("register-password");
  const registerName = document.getElementById("register-name");

  let currentUser = null;
  const tokenKey = "mhs_access_token";

  function getToken() {
    return localStorage.getItem(tokenKey);
  }

  function setToken(token) {
    localStorage.setItem(tokenKey, token);
  }

  function clearToken() {
    localStorage.removeItem(tokenKey);
  }

  function authHeaders() {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  function showMessage(text, type = "success") {
    messageDiv.textContent = text;
    messageDiv.className = type;
    messageDiv.classList.remove("hidden");

    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  function updateAuthUI() {
    if (currentUser) {
      authStatus.textContent = `Signed in as ${currentUser.full_name} (${currentUser.role})`;
      authStatus.classList.remove("hidden");
      logoutButton.classList.remove("hidden");
      loginForm.parentElement.classList.add("hidden");
      registerForm.parentElement.classList.add("hidden");
      emailInput.value = currentUser.email;
      if (currentUser.role === "student") {
        emailInput.readOnly = true;
      } else {
        emailInput.readOnly = false;
      }
    } else {
      authStatus.classList.add("hidden");
      logoutButton.classList.add("hidden");
      loginForm.parentElement.classList.remove("hidden");
      registerForm.parentElement.classList.remove("hidden");
      emailInput.value = "";
      emailInput.readOnly = false;
    }
  }

  async function refreshUser() {
    const token = getToken();
    if (!token) {
      currentUser = null;
      updateAuthUI();
      return;
    }

    try {
      const response = await fetch("/users/me", {
        headers: authHeaders(),
      });

      if (!response.ok) {
        throw new Error("Invalid token");
      }

      currentUser = await response.json();
    } catch (error) {
      clearToken();
      currentUser = null;
    }

    updateAuthUI();
  }

  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      activitiesList.innerHTML = "";
      activitySelect.innerHTML = `<option value="">-- Select an activity --</option>`;

      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li><span class="participant-email">${email}</span><button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button></li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    if (!currentUser) {
      showMessage("Please login before unregistering.", "error");
      return;
    }

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
          headers: authHeaders(),
        }
      );

      const result = await response.json();
      if (response.ok) {
        showMessage(result.message, "success");
        fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!currentUser) {
      showMessage("Please login before signing up.", "error");
      return;
    }

    const email = emailInput.value;
    const activity = activitySelect.value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
          headers: {
            ...authHeaders(),
            "Content-Type": "application/json",
          },
        }
      );

      const result = await response.json();
      if (response.ok) {
        showMessage(result.message, "success");
        signupForm.reset();
        if (currentUser && currentUser.role === "student") {
          emailInput.value = currentUser.email;
        }
        fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = loginEmail.value;
    const password = loginPassword.value;

    try {
      const response = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const result = await response.json();
      if (response.ok) {
        setToken(result.access_token);
        await refreshUser();
        showMessage(`Logged in as ${result.email}`, "success");
        fetchActivities();
        loginForm.reset();
      } else {
        showMessage(result.detail || "Login failed", "error");
      }
    } catch (error) {
      showMessage("Login request failed. Please try again.", "error");
      console.error("Error logging in:", error);
    }
  });

  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = registerEmail.value;
    const password = registerPassword.value;
    const fullName = registerName.value;

    try {
      const response = await fetch("/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, full_name: fullName }),
      });

      const result = await response.json();
      if (response.ok) {
        showMessage("Registration successful. Please login.", "success");
        registerForm.reset();
      } else {
        showMessage(result.detail || "Registration failed", "error");
      }
    } catch (error) {
      showMessage("Registration request failed. Please try again.", "error");
      console.error("Error registering:", error);
    }
  });

  logoutButton.addEventListener("click", () => {
    clearToken();
    currentUser = null;
    updateAuthUI();
    showMessage("You have been logged out.", "success");
  });

  refreshUser().then(fetchActivities);
});
