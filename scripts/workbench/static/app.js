// app.js - Main application coordinator
import { initChat } from './chat.js';
import { initGraph } from './graph.js';
import { initSources } from './sources.js';

// ---------------------------------------------------------------------------
// Panel State — only one panel visible at a time
// ---------------------------------------------------------------------------
let activePanel = 'chat'; // 'chat' | 'graph' | 'sources'

function switchPanel(panel) {
    activePanel = panel;

    const chatPanel = document.querySelector('.chat-panel');
    const sidePanel = document.getElementById('side-panel');
    const graphPanel = document.getElementById('graph-panel');
    const sourcesPanel = document.getElementById('sources-panel');

    if (panel === 'chat') {
        chatPanel.style.display = 'flex';
        sidePanel.style.display = 'none';
    } else {
        chatPanel.style.display = 'none';
        sidePanel.style.display = 'flex';
        sidePanel.classList.add('open');
        graphPanel.style.display = panel === 'graph' ? 'flex' : 'none';
        sourcesPanel.style.display = panel === 'sources' ? 'flex' : 'none';
    }

    updateNavLinks(panel);
    updatePanelTabs(panel);

    // Notify graph panel when shown (vis.js needs resize)
    if (panel === 'graph') {
        window.dispatchEvent(new CustomEvent('graph-panel-opened'));
    }
}

function updateNavLinks(active) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.toggle('active', link.dataset.panel === active);
    });
}

function updatePanelTabs(active) {
    document.querySelectorAll('.panel-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === active);
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
            console.warn('No API key set - chat will not work');
        }
    } catch (e) {
        console.error('Server health check failed:', e);
    }

    // Initialize panels
    initChat({ openSources: (docId, section) => {
        switchPanel('sources');
        window.dispatchEvent(new CustomEvent('navigate-source', { detail: { docId, section } }));
    }});
    initGraph({ openChat: (question) => {
        switchPanel('chat');
        window.dispatchEvent(new CustomEvent('ask-question', { detail: { question } }));
    }});
    initSources();

    // Wire up sidebar nav — each button switches to its panel
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            switchPanel(link.dataset.panel);
        });
    });

    // Wire up panel tabs (graph/sources toggle within side panel)
    document.querySelectorAll('.panel-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            switchPanel(tab.dataset.tab);
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

    // Start on chat
    switchPanel('chat');
});

// Export for use by other modules
export { switchPanel };
