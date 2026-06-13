/* ==========================================================================
   PART 6: JAVASCRIPT — MAKING IT WORK
   ========================================================================== */

// --------------------------------------------------------------------------
// 6.1 Dark mode toggle with Persistence & System Preferences
// --------------------------------------------------------------------------

const themeToggle = document.querySelector('#theme-toggle');

// Helper functions to manage theme
const enableDarkMode = () => {
    document.body.classList.add('dark');
    themeToggle.textContent = '☀️';
    localStorage.setItem('theme', 'dark');
};

const disableDarkMode = () => {
    document.body.classList.remove('dark');
    themeToggle.textContent = '🌙';
    localStorage.setItem('theme', 'light');
};

// Check for stored theme preference, otherwise check system preference
const savedTheme = localStorage.getItem('theme');
const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
    enableDarkMode();
} else {
    disableDarkMode();
}

// Toggle on button click
themeToggle.addEventListener('click', () => {
    const isDark = document.body.classList.contains('dark');
    if (isDark) {
        disableDarkMode();
    } else {
        enableDarkMode();
    }
});


// --------------------------------------------------------------------------
// 6.2 Back-to-top button
// --------------------------------------------------------------------------

const toTop = document.querySelector('#to-top');

// Only run if button exists (safe execution check)
if (toTop) {
    // Check page scroll and toggle visibility class
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            toTop.classList.add('show');
        } else {
            toTop.classList.remove('show');
        }
    });

    // Click event to glide back to the top smoothly
    toTop.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}


// --------------------------------------------------------------------------
// 6.3 Scroll reveal — elements fade in
// --------------------------------------------------------------------------

const revealItems = document.querySelectorAll('.reveal');

if (revealItems.length > 0) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // When it enters the screen
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target); // Activate once, then stop
            }
        });
    }, { 
        threshold: 0.1, // Trigger slightly earlier for better feel
        rootMargin: '0px 0px -50px 0px' // Offset bottom viewport intersection
    });

    revealItems.forEach((item) => observer.observe(item));
}


// --------------------------------------------------------------------------
// 6.4 Blog read-more expansion
// --------------------------------------------------------------------------

const blogLinks = document.querySelectorAll('.blog-link');

blogLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        
        const card = link.closest('.blog-card');
        if (!card) return;
        
        const excerpt = card.querySelector('.blog-excerpt');
        if (!excerpt) return;
        
        const isExpanded = excerpt.classList.toggle('expanded');
        
        if (isExpanded) {
            link.innerHTML = `Read Less <span class="arrow">←</span>`;
        } else {
            link.innerHTML = `Read More <span class="arrow">→</span>`;
        }
    });
});


// --------------------------------------------------------------------------
// 6.5 Figma Live Preview Toggle (Lazy Loading Embed)
// --------------------------------------------------------------------------

const previewToggles = document.querySelectorAll('.btn-preview-toggle');

previewToggles.forEach(toggle => {
    toggle.addEventListener('click', () => {
        const card = toggle.closest('.card');
        if (!card) return;
        
        const drawer = card.querySelector('.preview-drawer');
        if (!drawer) return;
        
        const iframe = drawer.querySelector('.figma-embed');
        if (!iframe) return;
        
        // Toggle active states
        const isOpen = drawer.classList.toggle('open');
        toggle.classList.toggle('active');
        toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        
        // Lazy load the Figma iframe src if it hasn't been loaded yet
        if (isOpen && !iframe.getAttribute('src')) {
            const dataSrc = iframe.getAttribute('data-src');
            iframe.setAttribute('src', dataSrc);
        }
    });
});


// --------------------------------------------------------------------------
// 6.6 Project Gallery Filter & Count Handler
// --------------------------------------------------------------------------

const projectCards = document.querySelectorAll('.projects-grid .card');
const totalCountEl = document.querySelector('#total-count');
const visibleCountEl = document.querySelector('#visible-count');

if (projectCards.length > 0) {
    if (totalCountEl) totalCountEl.textContent = projectCards.length;
    if (visibleCountEl) visibleCountEl.textContent = projectCards.length;

    const filterButtons = document.querySelectorAll('.filter-btn');

    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons and add to the clicked one
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const filterValue = btn.getAttribute('data-filter');
            let visibleCount = 0;
            
            projectCards.forEach(card => {
                const category = card.getAttribute('data-category');
                
                if (filterValue === 'all' || category === filterValue) {
                    // Show matching card
                    if (card.classList.contains('hide-card')) {
                        card.classList.remove('hide-card');
                        // Force layout reflow so the browser registers the removal of hide-card
                        void card.offsetHeight;
                    }
                    card.classList.remove('fade-out');
                    visibleCount++;
                } else {
                    // Hide non-matching card
                    card.classList.add('fade-out');
                    
                    // Add layout-hiding display state once fade opacity transition completes
                    setTimeout(() => {
                        if (card.classList.contains('fade-out')) {
                            card.classList.add('hide-card');
                        }
                    }, 300); // Synchronized with 0.3s CSS transition
                }
            });
            
            if (visibleCountEl) {
                visibleCountEl.textContent = visibleCount;
            }
        });
    });
}
