/**
 * Adventures in Deep Space - Privacy-Focused Analytics Tracker
 * Cookie-less and Privacy-Respecting.
 */
(function () {
    // Configurable endpoint. The user should replace this with their own API/webhook URL.
    // Can also be overridden by setting window.ADS_ANALYTICS_ENDPOINT before common.js loads.
    const DEFAULT_ENDPOINT = 'https://analytics.your-personal-server.com/api/event';
    const endpoint = window.ADS_ANALYTICS_ENDPOINT || DEFAULT_ENDPOINT;

    // Helper to send data to the backend
    function sendPayload(payload) {
        // Skip tracking if running locally or tracking is disabled
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log('[Analytics-Dev]', payload);
            return;
        }

        try {
            const data = JSON.stringify(payload);
            if (navigator.sendBeacon) {
                navigator.sendBeacon(endpoint, data);
            } else {
                fetch(endpoint, {
                    method: 'POST',
                    body: data,
                    headers: { 'Content-Type': 'application/json' },
                    keepalive: true
                }).catch(err => console.warn('Analytics send failed:', err));
            }
        } catch (e) {
            console.warn('Analytics error:', e);
        }
    }

    // Helper to track pageview
    function trackPageView() {
        sendPayload({
            event: 'pageview',
            path: window.location.pathname,
            referrer: document.referrer || '',
            title: document.title
        });
    }

    // Helper to track anchor/constellation clicks
    function trackAnchorClick(hash) {
        if (!hash) return;
        sendPayload({
            event: 'anchor_click',
            path: window.location.pathname,
            referrer: '', // Referrer is empty for internal anchor clicks
            details: hash
        });
    }

    // --- 1. Track Page View on Load ---
    if (document.readyState === 'complete') {
        trackPageView();
    } else {
        window.addEventListener('load', trackPageView);
    }

    // --- 2. Track Initial Hash (if user navigated directly to an anchor) ---
    window.addEventListener('load', () => {
        if (window.location.hash) {
            // Wait slightly to ensure page is loaded
            setTimeout(() => {
                trackAnchorClick(window.location.hash.substring(1));
            }, 500);
        }
    });

    // --- 3. Track Hash Changes ---
    window.addEventListener('hashchange', () => {
        if (window.location.hash) {
            trackAnchorClick(window.location.hash.substring(1));
        }
    });

    // --- 4. Intercept Clicks on Anchor Links ---
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a');
        if (link) {
            const href = link.getAttribute('href');
            if (href && href.startsWith('#')) {
                const hash = href.substring(1);
                trackAnchorClick(hash);
            }
        }
    });

    // --- 5. Intercept CSV Export Custom Event ---
    document.addEventListener('ads_csv_export', (e) => {
        sendPayload({
            event: 'csv_export',
            path: e.detail.path || window.location.pathname,
            referrer: '',
            details: 'CSV Download'
        });
    });
})();
