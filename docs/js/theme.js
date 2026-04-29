// theme.js - Dark/Light Theme Toggle
const Theme = (() => {
    let currentTheme = 'dark';
    
    function init() {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        setTheme(savedTheme);
        
        document.getElementById('theme-toggle')?.addEventListener('click', () => {
            toggleTheme();
        });
    }
    
    function setTheme(theme) {
        currentTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        updateThemeIcon();
    }
    
    function toggleTheme() {
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
        
        // Add rotation animation
        const toggle = document.getElementById('theme-toggle');
        toggle.classList.add('theme-toggle-active');
        setTimeout(() => {
            toggle.classList.remove('theme-toggle-active');
        }, 500);
    }
    
    function updateThemeIcon() {
        const icon = document.querySelector('#theme-toggle .theme-icon');
        if (icon) {
            icon.textContent = currentTheme === 'dark' ? '🌙' : '☀️';
        }
    }
    
    function getTheme() {
        return currentTheme;
    }
    
    return {
        init,
        toggleTheme,
        getTheme
    };
})();

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    Theme.init();
});
