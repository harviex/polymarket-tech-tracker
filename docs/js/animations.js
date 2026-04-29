// animations.js - GSAP & Particle Animations
const Animations = (() => {
    function initParticles() {
        if (typeof particlesJS !== 'undefined') {
            particlesJS('particles-js', {
                particles: {
                    number: { value: 80, density: { enable: true, value_area: 800 } },
                    color: { value: ['#3b82f6', '#8b5cf6', '#ec4899'] },
                    shape: { type: 'circle' },
                    opacity: { value: 0.5, random: true },
                    size: { value: 3, random: true },
                    line_linked: {
                        enable: true,
                        distance: 150,
                        color: '#3b82f6',
                        opacity: 0.2,
                        width: 1
                    },
                    move: {
                        enable: true,
                        speed: 2,
                        direction: 'none',
                        random: false,
                        straight: false,
                        out_mode: 'out',
                        bounce: false
                    }
                },
                interactivity: {
                    detect_on: 'canvas',
                    events: {
                        onhover: { enable: true, mode: 'repulse' },
                        onclick: { enable: true, mode: 'push' },
                        resize: true
                    }
                },
                retina_detect: true
            });
        }
    }
    
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
        // Wait for libraries to load
        const checkInterval = setInterval(() => {
            if (typeof gsap !== 'undefined' && typeof particlesJS !== 'undefined') {
                clearInterval(checkInterval);
                initParticles();
                initScrollAnimations();
                animateCardHover();
            }
        }, 100);
        
        // Timeout after 5 seconds
        setTimeout(() => clearInterval(checkInterval), 5000);
    }
    
    return {
        init,
        initParticles,
        initScrollAnimations
    };
})();

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => Animations.init(), 500);
});
