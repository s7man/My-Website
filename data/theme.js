const themeToggle = document.querySelector("#themeToggle");
const themeToggleText = document.querySelector("#themeToggleText");

// Returns the theme currently applied to the page.
function getCurrentTheme() {
  return document.documentElement.dataset.theme === "dark" ? "dark" : "light";
}

// Updates the button label and accessibility state for the active theme.
function updateThemeButton(theme) {
  const isDark = theme === "dark";

  themeToggle.setAttribute("aria-pressed", String(isDark));
  themeToggle.setAttribute("aria-label", `Switch to ${isDark ? "light" : "dark"} mode`);
  themeToggleText.textContent = isDark ? "Light" : "Dark";
}

// Applies the requested theme and saves it for the next visit.
function setTheme(theme) {
  if (theme === "dark") {
    document.documentElement.dataset.theme = "dark";
  } else {
    document.documentElement.removeAttribute("data-theme");
  }

  localStorage.setItem("notes-theme", theme);
  updateThemeButton(theme);
}

// Switches between light and dark modes when the user clicks the toggle.
function toggleTheme() {
  const nextTheme = getCurrentTheme() === "dark" ? "light" : "dark";
  setTheme(nextTheme);
}

// Starts theme controls only on pages that include the toggle button.
function initThemeToggle() {
  if (!themeToggle || !themeToggleText) return;

  updateThemeButton(getCurrentTheme());
  themeToggle.addEventListener("click", toggleTheme);
}

initThemeToggle();
