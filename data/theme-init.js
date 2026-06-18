// Applies the saved theme before CSS loads to prevent a light/dark flash.
(() => {
  const savedTheme = localStorage.getItem("notes-theme");

  if (savedTheme === "dark") {
    document.documentElement.dataset.theme = "dark";
  }
})();
