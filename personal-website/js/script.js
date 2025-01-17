// Initialize Particles.js
particlesJS('particles-js', {
    particles: {
        number: {
            value: 80,
            density: {
                enable: true,
                value_area: 800
            }
        },
        color: {
            value: '#3498db'
        },
        shape: {
            type: 'circle'
        },
        opacity: {
            value: 0.5,
            random: false
        },
        size: {
            value: 3,
            random: true
        },
        line_linked: {
            enable: true,
            distance: 150,
            color: '#3498db',
            opacity: 0.4,
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
            onhover: {
                enable: true,
                mode: 'grab'
            },
            onclick: {
                enable: true,
                mode: 'push'
            },
            resize: true
        },
        modes: {
            grab: {
                distance: 140,
                line_linked: {
                    opacity: 1
                }
            },
            push: {
                particles_nb: 4
            }
        }
    },
    retina_detect: true
});

// Load Parallax.js
document.write('<script src="https://cdnjs.cloudflare.com/ajax/libs/parallax-js/3.1.0/parallax.min.js"><\/script>');

// Smooth scroll for all anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const headerOffset = 80; // Adjust based on your navbar height
            const elementPosition = target.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// Navbar background change on scroll
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.style.backgroundColor = 'rgba(44, 62, 80, 0.95)';
    } else {
        navbar.style.backgroundColor = 'var(--primary-color)';
    }
});

// Navbar scroll behavior
let lastScrollTop = 0;
const navbar = document.querySelector('.navbar');
const scrollThreshold = 100;

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
    
    // Handle navbar transparency
    if (currentScroll < scrollThreshold) {
        navbar.classList.add('transparent');
    } else {
        navbar.classList.remove('transparent');
    }
    
    // Handle navbar hide/show
    if (currentScroll > lastScrollTop && currentScroll > 500) {
        // Scrolling down & past threshold
        navbar.classList.add('hidden');
    } else {
        // Scrolling up or at top
        navbar.classList.remove('hidden');
    }
    
    lastScrollTop = currentScroll <= 0 ? 0 : currentScroll;
});

// Unified Intersection Observer for sections and cards
const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.2
};

const intersectionObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            // Handle sections
            if (entry.target.classList.contains('section')) {
                entry.target.classList.add('visible');
            }
            
            // Handle cards
            if (entry.target.classList.contains('card') || entry.target.classList.contains('interactive-card')) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
            
            // Stop observing after animation
            intersectionObserver.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe all sections and cards
document.querySelectorAll('.section, .card, .interactive-card').forEach(element => {
    // Set initial styles for cards
    if (element.classList.contains('card') || element.classList.contains('interactive-card')) {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    }
    intersectionObserver.observe(element);
});

// Initialize Parallax effect
window.addEventListener('load', () => {
    const scene = document.getElementById('scene');
    if (scene) {
        new Parallax(scene, {
            relativeInput: true,
            hoverOnly: true,
            calibrateX: true,
            calibrateY: true
        });
    }
});

// Interactive Cards
document.querySelectorAll('.interactive-card').forEach(card => {
    card.addEventListener('click', function() {
        this.classList.toggle('flipped');
    });

    // Add hover sound effect (optional)
    card.addEventListener('mouseenter', function() {
        const hoverSound = new Audio('data:audio/wav;base64,UklGRjIAAABXQVZFZm10IBIAAAABAAEAQB8AAEAfAAABAAgAAABmYWN0BAAAAAAAAABkYXRhAAAAAA==');
        hoverSound.volume = 0.1;
        hoverSound.play().catch(() => {}); // Catch and ignore autoplay restrictions
    });
});

// Theme Switcher
const themeToggle = document.getElementById('theme-toggle');
const currentTheme = localStorage.getItem('theme');

// Set initial theme
if (currentTheme) {
    document.documentElement.setAttribute('data-theme', currentTheme);
    if (currentTheme === 'dark') {
        themeToggle.checked = true;
    }
}

// Handle theme switching
themeToggle.addEventListener('change', function(e) {
    if (e.target.checked) {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
    }
});

// Typing effect for hero section
const heroText = document.querySelector('.hero-content h1');
if (heroText) {
    const originalText = heroText.textContent;
    heroText.textContent = '';

    function typeWriter(text, element, index = 0) {
        if (index < text.length) {
            element.textContent += text.charAt(index);
            setTimeout(() => typeWriter(text, element, index + 1), 50);
        }
    }

    // Start typing effect when page loads
    window.addEventListener('load', () => {
        setTimeout(() => typeWriter(originalText, heroText), 500);
    });
}

// Animate progress bars when they come into view
const animateProgress = (entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const progressBar = entry.target;
            const percent = progressBar.getAttribute('data-percent');
            progressBar.style.width = percent + '%';
            observer.unobserve(progressBar);
        }
    });
};

const progressObserver = new IntersectionObserver(animateProgress, {
    threshold: 0.3
});

document.querySelectorAll('.progress').forEach(bar => {
    progressObserver.observe(bar);
});
