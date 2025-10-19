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


    const baseColors = {
        '--body-color': 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)',
        '--sidebar-color': '#FFF',
        '--primary-color': '#695CFE',
        '--primary-color-light': '#F6F5FF',
        '--text-color': '#707070',
        '--black-color': '#0a0909',
        '--accent-gradient': 'linear-gradient(135deg, #ff8a65 0%, #ffb74d 100%)',
        '--accent-icon-bg': '#ff8a65'
    };

    // Apply light theme as base for everything except dark mode
    Object.entries(baseColors).forEach(([key, value]) => {
        root.style.setProperty(key, value);
    });

    switch (theme) {
        case 'light':
            
            break;


        case 'blue':
            
            root.style.setProperty('--body-color', 'linear-gradient(135deg, #2563eb 0%, #60a5fa 100%)');
            root.style.setProperty('--accent-gradient', 'linear-gradient(135deg, #2563eb 0%, #60a5fa 100%)');
            root.style.setProperty('--accent-icon-bg', '#2563eb');
            break;

        case 'sepia':
            
            root.style.setProperty('--body-color', 'linear-gradient(135deg, #b08457 0%, #d1a054 100%)');
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
