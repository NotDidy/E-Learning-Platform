// Toggle the visibility of the theme selection menu
function toggleThemeMenu(e) {
    e.preventDefault();
    const menu = document.getElementById('themeMenu');
    menu.classList.toggle('active');
}

// Apply the selected theme
function setTheme(theme) {
    const root = document.documentElement;
    document.body.className = ''; 
    document.body.classList.add(`${theme}-theme`);

    switch(theme) {
        case 'light':
            root.style.setProperty('--body-color', 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)');
            root.style.setProperty('--sidebar-color', '#FFF');
            root.style.setProperty('--primary-color', '#695CFE');
            root.style.setProperty('--primary-color-light', '#F6F5FF');
            root.style.setProperty('--text-color', '#707070');
            root.style.setProperty('--black-color', '#0a0909');
            root.style.setProperty('--accent-gradient', 'linear-gradient(135deg, #ff8a65 0%, #ffb74d 100%)');
            root.style.setProperty('--accent-icon-bg', '#ff8a65');
            break;

        case 'dark':
            root.style.setProperty('--body-color', 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)');
            root.style.setProperty('--sidebar-color', '#242526');
            root.style.setProperty('--primary-color', '#8c7ae6');
            root.style.setProperty('--primary-color-light', '#3a3b3c');
            root.style.setProperty('--text-color', '#ccc');
            root.style.setProperty('--black-color', '#fff');
            root.style.setProperty('--accent-gradient', 'linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%)');
            root.style.setProperty('--accent-icon-bg', '#9b59b6');
            break;

        case 'blue':
            root.style.setProperty('--body-color', 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)');
            root.style.setProperty('--sidebar-color', '#eaf2ff');
            root.style.setProperty('--primary-color', '#1e40af');
            root.style.setProperty('--primary-color-light', '#dbeafe');
            root.style.setProperty('--text-color', '#334155');
            root.style.setProperty('--black-color', '#0f172a');
            root.style.setProperty('--accent-gradient', 'linear-gradient(135deg, #2563eb 0%, #60a5fa 100%)');
            root.style.setProperty('--accent-icon-bg', '#2563eb');
            break;

        case 'sepia':
            root.style.setProperty('--body-color', 'linear-gradient(135deg, #e0c097 0%, #cbb994 100%)');
            root.style.setProperty('--sidebar-color', '#f5deb3');
            root.style.setProperty('--primary-color', '#704214');
            root.style.setProperty('--primary-color-light', '#f0e0c6');
            root.style.setProperty('--text-color', '#5c4033');
            root.style.setProperty('--black-color', '#3e2723');
            root.style.setProperty('--accent-gradient', 'linear-gradient(135deg, #b08457 0%, #d1a054 100%)');
            root.style.setProperty('--accent-icon-bg', '#b08457');
            break;
    }

    localStorage.setItem('selectedTheme', theme);
    document.getElementById('themeMenu').classList.remove('active');
}

// Load saved theme when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('selectedTheme');
    if (saved) setTheme(saved);
});
