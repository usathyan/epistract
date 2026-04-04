// app.js - Main application coordinator
import { initChat } from './chat.js';
import { initGraph } from './graph.js';
// sources.js removed -- source docs now accessed via dashboard links

// ---------------------------------------------------------------------------
// Panel State -- only one panel visible at a time
// ---------------------------------------------------------------------------
let activePanel = 'chat'; // 'dashboard' | 'chat' | 'graph' | 'sources'

function switchPanel(panel) {
    activePanel = panel;

    const dashboardPanel = document.getElementById('dashboard-panel');
    const chatPanel = document.querySelector('.chat-panel');
    const sidePanel = document.getElementById('side-panel');
    const graphPanel = document.getElementById('graph-panel');
    // Hide all panels
    dashboardPanel.style.display = 'none';
    chatPanel.style.display = 'none';
    sidePanel.style.display = 'none';

    if (panel === 'dashboard') {
        dashboardPanel.style.display = 'flex';
    } else if (panel === 'chat') {
        chatPanel.style.display = 'flex';
    } else if (panel === 'graph') {
        sidePanel.style.display = 'flex';
        sidePanel.classList.add('open');
        graphPanel.style.display = 'flex';
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
// Template-driven initialization helpers
// ---------------------------------------------------------------------------

const PALETTE = ['#6366f1','#f59e0b','#ef4444','#10b981','#8b5cf6','#06b6d4','#64748b','#ec4899','#f97316','#14b8a6','#a855f7','#0ea5e9'];

function populatePageContent(template) {
    // Page title
    document.title = template.title || 'Knowledge Graph Explorer';
    // Sidebar title
    document.getElementById('sidebar-title').textContent = template.title || 'Workbench';
    // Welcome heading
    document.getElementById('welcome-title').textContent = 'Welcome to ' + (template.title || 'Knowledge Graph Explorer');
    // Welcome body
    const welcomeBody = document.getElementById('welcome-body');
    if (welcomeBody) {
        welcomeBody.textContent = template.subtitle
            ? 'Ask questions about ' + template.subtitle.toLowerCase() + '. Choose a starter question below or type your own.'
            : 'Ask questions about the knowledge graph. Choose a starter question below or type your own.';
    }
    // Chat placeholder
    const chatInput = document.getElementById('chat-input');
    if (chatInput) chatInput.placeholder = template.placeholder || 'Ask a question about the knowledge graph...';
}

function populateStarterCards(template) {
    const starterContainer = document.getElementById('starter-cards');
    if (!starterContainer) return;
    let starters = template.starter_questions || [];
    if (starters.length === 0) {
        starters = ['What are the main entities in this knowledge graph?'];
    }
    for (const q of starters) {
        const btn = document.createElement('button');
        btn.className = 'starter-card';
        btn.textContent = q;
        starterContainer.appendChild(btn);
    }
}

async function populateDashboard(template) {
    const dashContent = document.getElementById('dashboard-content');
    if (!dashContent) return;
    try {
        const dashResp = await fetch('/api/dashboard');
        const dashData = await dashResp.json();
        if (dashData.html) {
            dashContent.innerHTML = dashData.html;
        } else {
            // Auto-generate summary
            let autoHtml = '<h2 class="dashboard-title">' + (dashData.title || 'Knowledge Graph Summary') + '</h2>';
            if (dashData.subtitle) autoHtml += '<p class="dashboard-subtitle">' + dashData.subtitle + '</p>';
            autoHtml += '<h3>Entity Summary</h3><div class="dashboard-table-wrap"><table class="dashboard-table"><thead><tr><th>Entity Type</th><th>Count</th></tr></thead><tbody>';
            for (const [type, count] of Object.entries(dashData.entity_counts || {})) {
                autoHtml += '<tr><td>' + type + '</td><td>' + count + '</td></tr>';
            }
            autoHtml += '</tbody></table></div>';
            autoHtml += '<p>Total entities: ' + (dashData.total_nodes || 0) + ' | Total relationships: ' + (dashData.total_edges || 0) + '</p>';
            dashContent.innerHTML = autoHtml;
        }
    } catch (e) {
        dashContent.innerHTML = '<p>Failed to load dashboard content.</p>';
    }
}

async function populateEntityLegend(template) {
    const legendContainer = document.getElementById('entity-legend');
    if (!legendContainer) return;
    try {
        const entityTypesResp = await fetch('/api/graph/entity-types');
        const entityTypesData = await entityTypesResp.json();
        let idx = 0;
        for (const type of Object.keys(entityTypesData.entity_types || {})) {
            const color = (template.entity_colors || {})[type] || PALETTE[idx % PALETTE.length];
            const item = document.createElement('div');
            item.className = 'legend-item';
            item.innerHTML = '<span class="legend-dot" style="background:' + color + '"></span><span class="legend-label">' + type.charAt(0) + type.slice(1).toLowerCase().replace(/_/g, ' ') + '</span>';
            legendContainer.appendChild(item);
            idx++;
        }
    } catch (e) {
        console.warn('Could not load entity types for legend:', e);
    }
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

    // Fetch template for dynamic content
    let template = {};
    try {
        const templateResp = await fetch('/api/template');
        template = await templateResp.json();
    } catch (e) {
        console.warn('Could not load template, using defaults:', e);
    }

    // Populate dynamic content from template
    populatePageContent(template);
    populateStarterCards(template);
    populateDashboard(template);
    populateEntityLegend(template);

    // Initialize panels with template
    initChat({ template, openSources: (docId, section) => {
        switchPanel('sources');
        window.dispatchEvent(new CustomEvent('navigate-source', { detail: { docId, section } }));
    }});
    await initGraph({ template, openChat: (question) => {
        switchPanel('chat');
        window.dispatchEvent(new CustomEvent('ask-question', { detail: { question } }));
    }});
    // Sources panel removed -- docs accessible via dashboard contract links

    // Wire up sidebar nav -- each button switches to its panel
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
