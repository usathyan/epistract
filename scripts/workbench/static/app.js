// app.js - Main application coordinator
import { initChat } from './chat.js';
import { initGraph } from './graph.js';
import { initSources } from './sources.js';

// ---------------------------------------------------------------------------
// Panel State
// ---------------------------------------------------------------------------
let activeSidePanel = null; // 'graph' | 'sources' | null

function toggleSidePanel(panel) {
    const sidePanel = document.getElementById('side-panel');
    const graphPanel = document.getElementById('graph-panel');
    const sourcesPanel = document.getElementById('sources-panel');

    if (activeSidePanel === panel) {
        // Close panel
        sidePanel.classList.remove('open');
        activeSidePanel = null;
        updateNavLinks(null);
        return;
    }

    activeSidePanel = panel;
    sidePanel.classList.add('open');
    graphPanel.style.display = panel === 'graph' ? 'flex' : 'none';
    sourcesPanel.style.display = panel === 'sources' ? 'flex' : 'none';
    updateNavLinks(panel);

    // Update panel tabs
    document.querySelectorAll('.panel-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === panel);
    });

    // Notify graph panel when opened (vis.js needs resize)
    if (panel === 'graph') {
        window.dispatchEvent(new CustomEvent('graph-panel-opened'));
    }
}

function updateNavLinks(active) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.toggle('active', link.dataset.panel === active || (active === null && link.dataset.panel === 'chat'));
    });
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
    // Check server health
    try {
        const health = await fetch('/api/health').then(r => r.json());
        console.log('Workbench health:', health);
        if (!health.has_api_key) {
            console.warn('ANTHROPIC_API_KEY not set - chat will not work');
        }
    } catch (e) {
        console.error('Server health check failed:', e);
    }

    // Initialize panels
    initChat({ openSources: (docId, section) => {
        toggleSidePanel('sources');
        window.dispatchEvent(new CustomEvent('navigate-source', { detail: { docId, section } }));
    }});
    initGraph({ openChat: (question) => {
        if (activeSidePanel) toggleSidePanel(activeSidePanel);
        window.dispatchEvent(new CustomEvent('ask-question', { detail: { question } }));
    }});
    initSources();

    // Wire up sidebar nav
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            const panel = link.dataset.panel;
            if (panel === 'chat') {
                if (activeSidePanel) toggleSidePanel(activeSidePanel);
            } else {
                toggleSidePanel(panel);
            }
        });
    });

    // Wire up panel tabs (graph/sources toggle within side panel)
    document.querySelectorAll('.panel-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const panel = tab.dataset.tab;
            if (activeSidePanel !== panel) {
                toggleSidePanel(activeSidePanel); // close current
                toggleSidePanel(panel); // open new
            }
        });
    });

    // Hamburger menu for mobile
    const hamburger = document.getElementById('hamburger');
    const sidebar = document.getElementById('sidebar');
    if (hamburger && sidebar) {
        hamburger.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // Set chat nav as active initially
    updateNavLinks(null);
});

// Export for use by other modules
export { toggleSidePanel };
