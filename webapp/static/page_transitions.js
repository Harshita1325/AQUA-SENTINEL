// Smooth Page Transitions Script

(function() {
    'use strict';

    // Create transition overlay with submarine animation
    const overlay = document.createElement('div');
    overlay.className = 'page-transition-overlay';
    overlay.innerHTML = `
        <div class="transition-core">
            <div class="submarine-wrapper">
                <svg class="submarine-icon" viewBox="0 0 120 60" xmlns="http://www.w3.org/2000/svg">
                    <g fill="none" fill-rule="evenodd">
                        <ellipse cx="52" cy="30" rx="36" ry="18" fill="rgba(0,217,255,0.25)" />
                        <ellipse cx="52" cy="30" rx="30" ry="14" fill="#00D9FF" />
                        <circle cx="40" cy="30" r="5" fill="#021016" />
                        <circle cx="40" cy="30" r="2" fill="#00D9FF" />
                        <rect x="60" y="22" width="10" height="10" rx="2" fill="#021016" />
                        <rect x="62" y="20" width="6" height="6" rx="1" fill="#00D9FF" />
                        <path d="M20 30 L10 24 L10 36 Z" fill="#00B8CC" />
                        <circle cx="80" cy="26" r="3" fill="#021016" />
                        <circle cx="88" cy="26" r="3" fill="#021016" />
                    </g>
                </svg>
                <div class="submarine-bubble bubble-1"></div>
                <div class="submarine-bubble bubble-2"></div>
                <div class="submarine-bubble bubble-3"></div>
            </div>
            <div class="transition-caption">Deploying Aqua Sentinel</div>
        </div>
    `;
    document.body.appendChild(overlay);

    // Function to handle page transitions
    function handlePageTransition(event) {
        const link = event.currentTarget;
        const href = link.getAttribute('href');
        
        // Skip if it's an external link, anchor link, or JavaScript link
        if (!href || 
            href.startsWith('#') || 
            href.startsWith('javascript:') || 
            href.startsWith('mailto:') ||
            href.startsWith('tel:') ||
            link.target === '_blank' ||
            event.ctrlKey || 
            event.metaKey) {
            return;
        }

        // Prevent default navigation
        event.preventDefault();

        // Show overlay
        overlay.classList.add('active');

        // Navigate after short delay
        setTimeout(() => {
            window.location.href = href;
        }, 300);
    }

    // Add transition to all navigation links
    function initPageTransitions() {
        const navLinks = document.querySelectorAll('.nav-links a, a[href^="/"]');
        
        navLinks.forEach(link => {
            // Skip if already has transition handler
            if (link.dataset.transition === 'true') return;
            
            link.dataset.transition = 'true';
            link.addEventListener('click', handlePageTransition);
        });
    }

    // Mark page as loaded to prevent initial fade animation
    document.body.classList.add('page-loaded');

    // Initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPageTransitions);
    } else {
        initPageTransitions();
    }

    // Add fade-in animation to page content
    window.addEventListener('load', function() {
        const containers = document.querySelectorAll('.container, .container-custom');
        containers.forEach(container => {
            container.classList.add('page-content');
        });

        // Add stagger animation to cards
        const cards = document.querySelectorAll('.model-card, .stat-card, .history-card, .chart-card, .info-section');
        cards.forEach((card, index) => {
            card.classList.add('fade-in-stagger');
        });
    });

    // Handle browser back/forward buttons
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            overlay.classList.remove('active');
        }
    });

    // Remove overlay if page loads quickly
    setTimeout(() => {
        overlay.classList.remove('active');
    }, 500);
})();

