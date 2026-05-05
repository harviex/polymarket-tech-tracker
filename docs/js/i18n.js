// i18n.js - Multilingual Support (EN/CH)
const I18n = (() => {
    let currentLang = 'en';
    let translations = {};
    
    // Load translations
    async function init() {
        const savedLang = localStorage.getItem('lang') || 'en';
        await loadLanguage(savedLang);
        applyTranslations();
        updateLangButton();
    }
    
    async function loadLanguage(lang) {
        try {
            const response = await fetch(`locales/${lang}.json`);
            translations = await response.json();
            currentLang = lang;
            localStorage.setItem('lang', lang);
            
            // Update HTML lang attribute
            document.documentElement.lang = lang === 'zh' ? 'zh-Hant' : 'en';
        } catch (error) {
            console.error('Failed to load language:', lang, error);
        }
    }
    
    function t(key) {
        return translations[key] || key;
    }
    
    function applyTranslations() {
        document.querySelectorAll('[id]').forEach(el => {
            const key = el.id;
            if (translations[key]) {
                if (el.tagName === 'INPUT' && el.type === 'text') {
                    el.placeholder = translations[key];
                } else {
                    el.textContent = translations[key];
                }
            }
        });
    }
    
    async function switchLanguage() {
        // EN ↔ CH toggle
        const newLang = currentLang === 'en' ? 'zh' : 'en';
        await loadLanguage(newLang);
        applyTranslations();
        updateLangButton();
    }
    
    function updateLangButton() {
        const btn = document.getElementById('current-lang');
        if (btn) {
            btn.textContent = currentLang === 'en' ? 'EN' : 'CH';
        }
    }
    
    return {
        init,
        t,
        switchLanguage,
        getCurrentLang: () => currentLang
    };
})();

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    I18n.init();
    document.getElementById('lang-toggle')?.addEventListener('click', () => {
        I18n.switchLanguage();
    });
});
