(function () {
    const applyDarkMode = (enabled) => {
        document.documentElement.classList.toggle('dark', enabled);
        if (document.body) {
            document.body.classList.toggle('dark', enabled);
        }
    };

    const savedPreference = localStorage.getItem('darkMode');
    applyDarkMode(savedPreference === 'true');

    window.toggleDarkMode = function () {
        const nextState = !document.documentElement.classList.contains('dark');
        applyDarkMode(nextState);
        localStorage.setItem('darkMode', String(nextState));
    };

    window.toggleSidebar = function () {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.toggle('close');
        }
    };
})();
