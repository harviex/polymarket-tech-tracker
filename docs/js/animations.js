// animations.js - GSAP Animations
const Animations = (() => {
    function initScrollAnimations() {
        if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
            console.warn('GSAP or ScrollTrigger not loaded');
            return;
        }
        
        gsap.registerPlugin(ScrollTrigger);
        
        // Animate event cards
        gsap.utils.toArray('.event-card').forEach((card, i) => {
            gsap.from(card, {
                scrollTrigger: {
                    trigger: card,
                    start: 'top 80%',
                    toggleActions: 'play none none reverse'
                },
                y: 50,
                opacity: 0,
                duration: 0.6,
                delay: i * 0.1
            });
        });
        
        // Animate sections
        gsap.utils.toArray('.panel, .tag-group').forEach(section => {
            gsap.from(section, {
                scrollTrigger: {
                    trigger: section,
                    start: 'top 85%'
                },
                y: 30,
                opacity: 0,
                duration: 0.8,
                ease: 'power2.out'
            });
        });
        
        // Hero parallax
        gsap.to('.hero-content', {
            scrollTrigger: {
                trigger: '.hero',
                start: 'top top',
                end: 'bottom top',
                scrub: true
            },
            y: 100,
            opacity: 0.5
        });
    }
    
    function animateCardHover() {
        document.querySelectorAll('.event-card').forEach(card => {
            card.addEventListener('mouseenter', function() {
                gsap.to(this, {
                    scale: 1.02,
                    duration: 0.3,
                    ease: 'power2.out'
                });
            });
            
            card.addEventListener('mouseleave', function() {
                gsap.to(this, {
                    scale: 1,
                    duration: 0.3,
                    ease: 'power2.out'
                });
            });
        });
    }
    
    function init() {
        // Wait for GSAP to load
        const checkInterval = setInterval(() => {
            if (typeof gsap !== 'undefined') {
                clearInterval(checkInterval);
                initScrollAnimations();
                animateCardHover();
            }
        }, 100);
        
        // Timeout after 5 seconds
        setTimeout(() => clearInterval(checkInterval), 5000);
    }
    
    return {
        init,
        initScrollAnimations
    };
})();

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => Animations.init(), 500);
});
