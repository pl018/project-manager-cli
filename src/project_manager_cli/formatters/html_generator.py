"""HTML page generator for project list display."""

import html
import json
import os
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class HTMLGenerator:
    """Generates a modern dark-themed HTML page for project list display."""

    # Tag colors matching the TUI/table formatter
    TAG_COLORS = {
        "frontend": "#3b82f6",
        "backend": "#22c55e",
        "fullstack": "#8b5cf6",
        "api": "#f59e0b",
        "cli": "#06b6d4",
        "library": "#ec4899",
        "tool": "#64748b",
        "app": "#14b8a6",
        "mobile": "#f97316",
        "web": "#6366f1",
    }

    DEFAULT_TAG_COLOR = "#94a3b8"

    def __init__(self, output_dir: Optional[str] = None):
        """Initialize the HTML generator.
        
        Args:
            output_dir: Directory to save the HTML file. Uses temp dir if not specified.
        """
        self.output_dir = output_dir or tempfile.gettempdir()

    def generate(self, projects: List[Dict[str, Any]], open_browser: bool = True) -> str:
        """Generate an HTML page with the project list.
        
        Args:
            projects: List of project dictionaries from the database
            open_browser: Whether to open the generated HTML in the default browser
            
        Returns:
            Path to the generated HTML file
        """
        html_content = self._build_html(projects)
        
        # Save to file
        output_path = Path(self.output_dir) / "project_manager_projects.html"
        output_path.write_text(html_content, encoding="utf-8")
        
        if open_browser:
            webbrowser.open(f"file://{output_path.resolve()}")
        
        return str(output_path)

    def _collect_all_tags(self, projects: List[Dict[str, Any]]) -> List[str]:
        """Collect all unique tags from projects."""
        all_tags: Set[str] = set()
        for project in projects:
            tags = project.get("tags", [])
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except (json.JSONDecodeError, TypeError):
                    tags = []
            for tag in tags:
                all_tags.add(tag)
        return sorted(all_tags)

    def _build_html(self, projects: List[Dict[str, Any]]) -> str:
        """Build the complete HTML document."""
        project_cards = self._build_project_cards(projects)
        stats = self._calculate_stats(projects)
        all_tags = self._collect_all_tags(projects)
        tag_filters_html = self._build_tag_filters(all_tags)
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Manager - Projects</title>
    <style>
{self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="header-content">
                <h1 class="title">
                    <span class="title-icon">&#128194;</span>
                    Project Manager
                </h1>
                <p class="subtitle">Your development projects at a glance</p>
            </div>
            <div class="stats">
                <div class="stat-item">
                    <span class="stat-value" id="visible-count">{stats['total']}</span>
                    <span class="stat-label">Showing</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">{stats['total']}</span>
                    <span class="stat-label">Total</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">{stats['favorites']}</span>
                    <span class="stat-label">Favorites</span>
                </div>
            </div>
        </header>
        
        <div class="toolbar">
            <div class="search-container">
                <span class="search-icon">&#128269;</span>
                <input type="text" id="search-input" class="search-input" placeholder="Search projects by name, path, description, notes, or tags..." autocomplete="off">
                <button class="clear-btn" id="clear-search" title="Clear search">&#10005;</button>
            </div>
            <div class="tag-filters">
                <span class="filter-label">Filter by tag:</span>
                <button class="tag-filter-btn active" data-tag="all">All</button>
                {tag_filters_html}
            </div>
        </div>
        
        <main class="main">
            <div class="projects-grid" id="projects-grid">
                {project_cards}
            </div>
            <div class="no-results" id="no-results" style="display: none;">
                <div class="no-results-icon">&#128269;</div>
                <p class="no-results-text">No projects match your search</p>
                <button class="reset-btn" onclick="resetFilters()">Reset Filters</button>
            </div>
        </main>
        
        <footer class="footer">
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by Project Manager CLI</p>
        </footer>
    </div>
    
    <div id="toast" class="toast"></div>
    
    <script>
{self._get_javascript()}
    </script>
</body>
</html>"""

    def _build_tag_filters(self, tags: List[str]) -> str:
        """Build the tag filter buttons HTML."""
        buttons = []
        for tag in tags:
            color = self.TAG_COLORS.get(tag.lower(), self.DEFAULT_TAG_COLOR)
            tag_escaped = html.escape(tag)
            buttons.append(
                f'<button class="tag-filter-btn" data-tag="{tag_escaped}" '
                f'style="--tag-color: {color};">{tag_escaped}</button>'
            )
        return "\n                ".join(buttons)

    def _get_css(self) -> str:
        """Return the embedded CSS for dark mode styling."""
        return """
        :root {
            --bg-primary: #0f0f14;
            --bg-secondary: #16161d;
            --bg-card: #1c1c26;
            --bg-card-hover: #232330;
            --accent-primary: #7c3aed;
            --accent-secondary: #a78bfa;
            --accent-glow: rgba(124, 58, 237, 0.3);
            --text-primary: #f0f0f5;
            --text-secondary: #a0a0b0;
            --text-muted: #606070;
            --border-color: #2a2a3a;
            --success: #22c55e;
            --warning: #f59e0b;
            --favorite: #fbbf24;
            --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.3);
            --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
            --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);
            --radius-sm: 6px;
            --radius-md: 12px;
            --radius-lg: 16px;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1.5rem;
            padding: 2rem;
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-card) 100%);
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-lg);
        }

        .header-content {
            flex: 1;
        }

        .title {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-secondary) 0%, var(--accent-primary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .title-icon {
            font-size: 2rem;
            -webkit-text-fill-color: initial;
        }

        .subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
            margin-top: 0.5rem;
        }

        .stats {
            display: flex;
            gap: 1.5rem;
        }

        .stat-item {
            text-align: center;
            padding: 0.75rem 1.25rem;
            background: var(--bg-primary);
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
        }

        .stat-value {
            display: block;
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--accent-secondary);
        }

        .stat-label {
            display: block;
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Toolbar */
        .toolbar {
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: var(--bg-card);
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
        }

        .search-container {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem 1rem;
            background: var(--bg-primary);
            border-radius: var(--radius-sm);
            border: 2px solid var(--border-color);
            margin-bottom: 1rem;
            transition: border-color 0.2s ease;
        }

        .search-container:focus-within {
            border-color: var(--accent-primary);
        }

        .search-icon {
            color: var(--text-muted);
            font-size: 1.1rem;
        }

        .search-input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: var(--text-primary);
            font-size: 1rem;
            font-family: inherit;
        }

        .search-input::placeholder {
            color: var(--text-muted);
        }

        .clear-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            padding: 0.25rem 0.5rem;
            font-size: 1rem;
            border-radius: var(--radius-sm);
            transition: all 0.2s ease;
            opacity: 0;
        }

        .clear-btn.visible {
            opacity: 1;
        }

        .clear-btn:hover {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        .tag-filters {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .filter-label {
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-right: 0.5rem;
        }

        .tag-filter-btn {
            padding: 0.4rem 0.9rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
        }

        .tag-filter-btn:hover {
            border-color: var(--tag-color, var(--accent-primary));
            color: var(--tag-color, var(--accent-primary));
        }

        .tag-filter-btn.active {
            background: var(--tag-color, var(--accent-primary));
            border-color: var(--tag-color, var(--accent-primary));
            color: white;
        }

        .tag-filter-btn[data-tag="all"] {
            --tag-color: var(--accent-primary);
        }

        .main {
            margin-bottom: 3rem;
        }

        .projects-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 1.5rem;
        }

        .project-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 1.5rem;
            transition: all 0.2s ease;
            cursor: default;
            position: relative;
            overflow: hidden;
        }

        .project-card.hidden {
            display: none;
        }

        .project-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
            opacity: 0;
            transition: opacity 0.2s ease;
        }

        .project-card:hover {
            background: var(--bg-card-hover);
            transform: translateY(-2px);
            box-shadow: var(--shadow-md), 0 0 20px var(--accent-glow);
            border-color: var(--accent-primary);
        }

        .project-card:hover::before {
            opacity: 1;
        }

        .project-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.75rem;
        }

        .project-name {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
            word-break: break-word;
        }

        .favorite-badge {
            font-size: 1.25rem;
            color: var(--favorite);
            filter: drop-shadow(0 0 4px var(--favorite));
        }

        .project-description {
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-bottom: 1rem;
            font-style: italic;
            line-height: 1.5;
        }

        .project-notes {
            background: var(--bg-primary);
            border-left: 3px solid var(--accent-primary);
            border-radius: var(--radius-sm);
            padding: 0.75rem;
            margin-bottom: 1rem;
        }

        .notes-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
            color: var(--accent-secondary);
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .notes-icon {
            font-size: 1rem;
        }

        .notes-content {
            color: var(--text-secondary);
            font-size: 0.85rem;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .project-path-container {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .project-path {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem;
            background: var(--bg-primary);
            border-radius: var(--radius-sm);
            flex: 1;
            cursor: pointer;
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }

        .project-path:hover {
            border-color: var(--accent-primary);
            background: var(--bg-secondary);
        }

        .project-path:active {
            transform: scale(0.99);
        }

        .path-icon {
            color: var(--text-muted);
            font-size: 1rem;
            flex-shrink: 0;
        }

        .path-text {
            font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
            font-size: 0.8rem;
            color: var(--text-secondary);
            word-break: break-all;
            flex: 1;
        }

        .copy-hint {
            font-size: 0.7rem;
            color: var(--text-muted);
            opacity: 0;
            transition: opacity 0.2s ease;
            white-space: nowrap;
        }

        .project-path:hover .copy-hint {
            opacity: 1;
        }

        .open-folder-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.35rem;
            padding: 0.75rem 1rem;
            background: var(--accent-primary);
            border: none;
            border-radius: var(--radius-sm);
            color: white;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            white-space: nowrap;
        }

        .open-folder-btn:hover {
            background: var(--accent-secondary);
            transform: scale(1.02);
        }

        .open-folder-btn:active {
            transform: scale(0.98);
        }

        .project-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .tag {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: lowercase;
            letter-spacing: 0.3px;
            border: 1px solid;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .tag:hover {
            transform: scale(1.05);
            filter: brightness(1.2);
        }

        .project-stats {
            display: flex;
            justify-content: space-between;
            padding-top: 1rem;
            border-top: 1px solid var(--border-color);
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .project-stat {
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }

        .project-stat-icon {
            opacity: 0.7;
        }

        .footer {
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.85rem;
            border-top: 1px solid var(--border-color);
        }

        .toast {
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: var(--accent-primary);
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: var(--radius-md);
            font-weight: 500;
            box-shadow: var(--shadow-lg);
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 1000;
        }

        .toast.show {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }

        .no-results {
            text-align: center;
            padding: 4rem 2rem;
            color: var(--text-muted);
        }

        .no-results-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }

        .no-results-text {
            font-size: 1.25rem;
            margin-bottom: 1.5rem;
        }

        .reset-btn {
            padding: 0.75rem 1.5rem;
            background: var(--accent-primary);
            border: none;
            border-radius: var(--radius-sm);
            color: white;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .reset-btn:hover {
            background: var(--accent-secondary);
        }

        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            color: var(--text-muted);
        }

        .empty-state-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }

        .empty-state-text {
            font-size: 1.25rem;
        }

        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }

            .header {
                flex-direction: column;
                gap: 1.5rem;
            }

            .stats {
                width: 100%;
                justify-content: space-around;
            }

            .projects-grid {
                grid-template-columns: 1fr;
            }

            .title {
                font-size: 1.75rem;
            }

            .project-path-container {
                flex-direction: column;
            }

            .open-folder-btn {
                width: 100%;
            }
        }
"""

    def _get_javascript(self) -> str:
        """Return the embedded JavaScript for interactivity."""
        return """
        // State
        let activeTag = 'all';
        let searchQuery = '';

        // DOM Elements
        const searchInput = document.getElementById('search-input');
        const clearBtn = document.getElementById('clear-search');
        const projectsGrid = document.getElementById('projects-grid');
        const noResults = document.getElementById('no-results');
        const visibleCount = document.getElementById('visible-count');
        const tagBtns = document.querySelectorAll('.tag-filter-btn');

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            searchInput.addEventListener('input', handleSearch);
            clearBtn.addEventListener('click', clearSearch);
            
            tagBtns.forEach(btn => {
                btn.addEventListener('click', () => handleTagFilter(btn.dataset.tag));
            });
        });

        function handleSearch(e) {
            searchQuery = e.target.value.toLowerCase().trim();
            clearBtn.classList.toggle('visible', searchQuery.length > 0);
            filterProjects();
        }

        function clearSearch() {
            searchInput.value = '';
            searchQuery = '';
            clearBtn.classList.remove('visible');
            filterProjects();
            searchInput.focus();
        }

        function handleTagFilter(tag) {
            activeTag = tag;
            
            // Update active button state
            tagBtns.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.tag === tag);
            });
            
            filterProjects();
        }

        function filterProjects() {
            const cards = document.querySelectorAll('.project-card');
            let visibleCount = 0;

            cards.forEach(card => {
                const name = (card.dataset.name || '').toLowerCase();
                const path = (card.dataset.path || '').toLowerCase();
                const description = (card.dataset.description || '').toLowerCase();
                const notes = (card.dataset.notes || '').toLowerCase();
                const tags = (card.dataset.tags || '').toLowerCase().split(',');

                // Check search query
                const matchesSearch = !searchQuery ||
                    name.includes(searchQuery) ||
                    path.includes(searchQuery) ||
                    description.includes(searchQuery) ||
                    notes.includes(searchQuery) ||
                    tags.some(t => t.includes(searchQuery));

                // Check tag filter
                const matchesTag = activeTag === 'all' || tags.includes(activeTag.toLowerCase());

                const isVisible = matchesSearch && matchesTag;
                card.classList.toggle('hidden', !isVisible);

                if (isVisible) visibleCount++;
            });

            // Update count and show/hide no results message
            document.getElementById('visible-count').textContent = visibleCount;
            noResults.style.display = visibleCount === 0 ? 'block' : 'none';
            projectsGrid.style.display = visibleCount === 0 ? 'none' : 'grid';
        }

        function resetFilters() {
            searchInput.value = '';
            searchQuery = '';
            clearBtn.classList.remove('visible');
            activeTag = 'all';
            tagBtns.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.tag === 'all');
            });
            filterProjects();
        }

        function copyToClipboard(path) {
            navigator.clipboard.writeText(path).then(() => {
                showToast('Path copied to clipboard!');
            }).catch(err => {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = path;
                textArea.style.position = 'fixed';
                textArea.style.left = '-9999px';
                document.body.appendChild(textArea);
                textArea.select();
                try {
                    document.execCommand('copy');
                    showToast('Path copied to clipboard!');
                } catch (e) {
                    showToast('Failed to copy path');
                }
                document.body.removeChild(textArea);
            });
        }

        function openInExplorer(path) {
            // Copy the explorer command to clipboard
            const command = `explorer "${path}"`;
            navigator.clipboard.writeText(command).then(() => {
                showToast('Command copied! Paste in terminal: ' + command);
            }).catch(err => {
                // Fallback
                const textArea = document.createElement('textarea');
                textArea.value = command;
                textArea.style.position = 'fixed';
                textArea.style.left = '-9999px';
                document.body.appendChild(textArea);
                textArea.select();
                try {
                    document.execCommand('copy');
                    showToast('Command copied! Paste in terminal');
                } catch (e) {
                    showToast('Failed to copy command');
                }
                document.body.removeChild(textArea);
            });
        }

        function filterByTag(tag) {
            handleTagFilter(tag);
            // Scroll to top of projects
            window.scrollTo({ top: document.querySelector('.toolbar').offsetTop - 20, behavior: 'smooth' });
        }

        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }

        // Add keyboard accessibility
        document.querySelectorAll('.project-path').forEach(el => {
            el.setAttribute('tabindex', '0');
            el.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    el.click();
                }
            });
        });

        // Keyboard shortcut: / to focus search
        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && document.activeElement !== searchInput) {
                e.preventDefault();
                searchInput.focus();
            }
            if (e.key === 'Escape') {
                if (searchQuery) {
                    clearSearch();
                } else {
                    searchInput.blur();
                }
            }
        });
"""

    def _build_project_cards(self, projects: List[Dict[str, Any]]) -> str:
        """Build HTML for all project cards."""
        if not projects:
            return """
            <div class="empty-state">
                <div class="empty-state-icon">&#128234;</div>
                <p class="empty-state-text">No projects found</p>
            </div>
            """

        cards = []
        for project in projects:
            cards.append(self._build_project_card(project))
        
        return "\n".join(cards)

    def _build_project_card(self, project: Dict[str, Any]) -> str:
        """Build HTML for a single project card."""
        name = html.escape(project.get("ai_app_name") or project.get("name", "Unknown"))
        description = html.escape(project.get("description") or project.get("ai_app_description") or "")
        root_path = project.get("root_path", "")
        root_path_escaped = html.escape(root_path)
        is_favorite = project.get("favorite", False)
        
        # Parse tags
        tags = project.get("tags", [])
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except (json.JSONDecodeError, TypeError):
                tags = []
        
        # Build tags HTML (clickable to filter)
        tags_html = ""
        tags_data = ",".join(tags) if tags else ""
        for tag in tags:
            color = self.TAG_COLORS.get(tag.lower(), self.DEFAULT_TAG_COLOR)
            tag_escaped = html.escape(tag)
            tags_html += f'<span class="tag" style="background: {color}20; color: {color}; border-color: {color}40;" onclick="filterByTag(\'{tag_escaped}\')" title="Click to filter by {tag_escaped}">{tag_escaped}</span>'
        
        if not tags_html:
            tags_html = '<span class="tag" style="background: #64748b20; color: #64748b; border-color: #64748b40;">untagged</span>'
        
        # Format dates
        last_opened = project.get("last_opened", "")
        if last_opened:
            try:
                if isinstance(last_opened, str):
                    dt = datetime.fromisoformat(last_opened)
                else:
                    dt = last_opened
                last_opened_str = dt.strftime("%b %d, %Y")
            except (ValueError, TypeError, AttributeError):
                last_opened_str = "Never"
        else:
            last_opened_str = "Never"
        
        open_count = project.get("open_count", 0)
        
        favorite_badge = '<span class="favorite-badge">&#9733;</span>' if is_favorite else ''
        description_html = f'<p class="project-description">{description}</p>' if description else ''

        # Notes section
        notes = project.get("notes", "")
        notes_escaped = html.escape(notes) if notes else ""
        notes_html = ""
        if notes:
            # Truncate notes for preview
            notes_preview = notes[:150] + "..." if len(notes) > 150 else notes
            notes_preview_escaped = html.escape(notes_preview)
            notes_html = f'''
                <div class="project-notes">
                    <div class="notes-header">
                        <span class="notes-icon">&#128221;</span>
                        <span class="notes-label">Notes</span>
                    </div>
                    <div class="notes-content">{notes_preview_escaped}</div>
                </div>'''

        # Escape for JavaScript
        path_js = root_path.replace("\\", "\\\\").replace("'", "\\'")

        return f"""
            <div class="project-card" data-name="{name}" data-path="{root_path_escaped}" data-description="{description}" data-tags="{tags_data}" data-notes="{notes_escaped}">
                <div class="project-header">
                    <h3 class="project-name">{name}</h3>
                    {favorite_badge}
                </div>
                {description_html}
                {notes_html}
                <div class="project-path-container">
                    <div class="project-path" onclick="copyToClipboard('{path_js}')" title="Click to copy path">
                        <span class="path-icon">&#128193;</span>
                        <span class="path-text">{root_path_escaped}</span>
                        <span class="copy-hint">copy</span>
                    </div>
                    <button class="open-folder-btn" onclick="openInExplorer('{path_js}')" title="Copy explorer command">
                        <span>&#128194;</span> Open
                    </button>
                </div>
                <div class="project-tags">
                    {tags_html}
                </div>
                <div class="project-stats">
                    <span class="project-stat">
                        <span class="project-stat-icon">&#128197;</span>
                        {last_opened_str}
                    </span>
                    <span class="project-stat">
                        <span class="project-stat-icon">&#128275;</span>
                        {open_count} opens
                    </span>
                </div>
            </div>
        """

    def _calculate_stats(self, projects: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate statistics from projects."""
        total = len(projects)
        favorites = sum(1 for p in projects if p.get("favorite"))
        total_opens = sum(p.get("open_count", 0) for p in projects)
        
        return {
            "total": total,
            "favorites": favorites,
            "total_opens": total_opens,
        }
