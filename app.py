import html
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# Constants
FEED_URL = "https://docs.cloud.google.com/feeds/bigquery-release-notes.xml"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

def strip_html(html_str):
    """Helper to convert HTML content to plain text for tweeting."""
    # Replace common HTML breaks/paragraphs with newlines
    text = re.sub(r'</?(p|br|div|li)[^>]*>', '\n', html_str)
    # Remove all other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Normalize whitespaces
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)

def parse_feed():
    """Fetches and parses the BigQuery release notes Atom feed."""
    try:
        req = urllib.request.Request(
            FEED_URL, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
    except urllib.error.URLError as e:
        raise Exception(f"Failed to fetch release notes feed: {str(e)}")
    except Exception as e:
        raise Exception(f"Error fetching feed: {str(e)}")

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        raise Exception(f"Failed to parse XML feed: {str(e)}")

    releases = []
    # Atom feeds contain entry elements
    for entry in root.findall("atom:entry", ATOM_NS):
        # Date of the entry
        date_title = entry.find("atom:title", ATOM_NS)
        date_str = date_title.text if date_title is not None else "Unknown Date"
        
        # Entry link
        link_elem = entry.find("atom:link[@rel='alternate']", ATOM_NS)
        if link_elem is None:
            link_elem = entry.find("atom:link", ATOM_NS)
        link_url = link_elem.get("href") if link_elem is not None else ""
        
        # Content HTML
        content_elem = entry.find("atom:content", ATOM_NS)
        if content_elem is None or content_elem.text is None:
            continue
            
        content_html = content_elem.text.strip()
        
        # Parse individual updates within a single entry by splitting on <h3>
        # Each entry content is typically structured as <h3>[Type]</h3> <p>[Description]</p>
        pattern = re.compile(r'<h3>(.*?)</h3>(.*?)(?=<h3>|$)', re.DOTALL)
        matches = pattern.findall(content_html)
        
        if matches:
            for idx, (update_type, desc_html) in enumerate(matches):
                desc_html = desc_html.strip()
                update_type = update_type.strip()
                releases.append({
                    "id": f"{date_str.replace(' ', '_')}_{idx}",
                    "date": date_str,
                    "type": update_type,
                    "content_html": desc_html,
                    "content_text": strip_html(desc_html),
                    "link": link_url
                })
        else:
            # Fallback if there are no <h3> tags
            releases.append({
                "id": f"{date_str.replace(' ', '_')}_0",
                "date": date_str,
                "type": "Update",
                "content_html": content_html,
                "content_text": strip_html(content_html),
                "link": link_url
            })
            
    return releases

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/releases")
def get_releases():
    try:
        releases = parse_feed()
        return jsonify({"success": True, "releases": releases})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Embedded HTML Template for a single-file template to keep tokens minimal yet rich.
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BigQuery Release Notes Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #0B0F19;
            --bg-surface: #151B2C;
            --bg-card: #1E2640;
            --border-color: #2D3758;
            --text-primary: #F3F4F6;
            --text-secondary: #9CA3AF;
            --text-muted: #6B7280;
            --accent-primary: #3B82F6;
            --accent-hover: #2563EB;
            --accent-success: #10B981;
            --accent-warning: #F59E0B;
            --accent-danger: #EF4444;
            --accent-info: #06B6D4;
            --twitter-blue: #1DA1F2;
            --twitter-hover: #1A91DA;
            --font-display: 'Outfit', sans-serif;
            --font-body: 'Plus Jakarta Sans', sans-serif;
            --shadow-premium: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
            --transition-smooth: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        body.light-theme {
            --bg-base: #F8FAFC;
            --bg-surface: #FFFFFF;
            --bg-card: #F1F5F9;
            --border-color: #E2E8F0;
            --text-primary: #0F172A;
            --text-secondary: #475569;
            --text-muted: #94A3B8;
            --shadow-premium: 0 10px 30px -10px rgba(15, 23, 42, 0.05);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-base);
            color: var(--text-primary);
            font-family: var(--font-body);
            min-height: 100vh;
            line-height: 1.6;
            overflow-x: hidden;
            display: flex;
            flex-direction: column;
            transition: background-color 0.3s ease, color 0.3s ease;
        }

        /* Ambient background glow */
        body::before {
            content: '';
            position: fixed;
            top: -10%;
            left: -10%;
            width: 50vw;
            height: 50vw;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.08) 0%, rgba(0,0,0,0) 70%);
            z-index: -1;
            pointer-events: none;
        }

        body::after {
            content: '';
            position: fixed;
            bottom: -10%;
            right: -10%;
            width: 50vw;
            height: 50vw;
            background: radial-gradient(circle, rgba(6, 182, 212, 0.06) 0%, rgba(0,0,0,0) 70%);
            z-index: -1;
            pointer-events: none;
        }

        body.light-theme::before {
            background: radial-gradient(circle, rgba(59, 130, 246, 0.04) 0%, rgba(0,0,0,0) 70%);
        }

        body.light-theme::after {
            background: radial-gradient(circle, rgba(6, 182, 212, 0.03) 0%, rgba(0,0,0,0) 70%);
        }

        header {
            background-color: rgba(21, 27, 44, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
            padding: 1.25rem 2rem;
            position: sticky;
            top: 0;
            z-index: 10;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background-color 0.3s ease, border-color 0.3s ease;
        }

        body.light-theme header {
            background-color: rgba(255, 255, 255, 0.8);
        }

        .logo-container {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-icon {
            width: 2.25rem;
            height: 2.25rem;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-info));
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            color: white;
            font-family: var(--font-display);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }

        h1 {
            font-family: var(--font-display);
            font-size: 1.5rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            background: linear-gradient(to right, var(--text-primary), var(--text-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .controls {
            display: flex;
            align-items: center;
            gap: 1.25rem;
        }

        .status-badge {
            font-size: 0.8rem;
            color: var(--text-secondary);
            background-color: rgba(45, 55, 88, 0.4);
            padding: 0.4rem 0.8rem;
            border-radius: 9999px;
            border: 1px solid rgba(45, 55, 88, 0.6);
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: var(--transition-smooth);
        }

        body.light-theme .status-badge {
            background-color: rgba(226, 232, 240, 0.8);
            border-color: var(--border-color);
        }

        .status-dot {
            width: 6px;
            height: 6px;
            background-color: var(--accent-success);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--accent-success);
        }

        button.btn {
            background-color: var(--accent-primary);
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            font-family: var(--font-body);
            font-weight: 500;
            font-size: 0.9rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: var(--transition-smooth);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
        }

        button.btn:hover {
            background-color: var(--accent-hover);
            transform: translateY(-1px);
        }

        button.btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
            transform: none;
        }

        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top: 2px solid white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            display: none;
        }

        button.btn.loading .spinner {
            display: inline-block;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Theme Toggle Slider */
        .theme-switch-wrapper {
            display: flex;
            align-items: center;
        }

        .theme-switch {
            display: inline-block;
            height: 28px;
            position: relative;
            width: 50px;
        }

        .theme-switch input {
            display: none;
        }

        .slider {
            background-color: rgba(45, 55, 88, 0.6);
            bottom: 0;
            cursor: pointer;
            left: 0;
            position: absolute;
            right: 0;
            top: 0;
            transition: var(--transition-smooth);
            border-radius: 34px;
            border: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 6px;
        }

        body.light-theme .slider {
            background-color: #E2E8F0;
        }

        .slider::before {
            background-color: white;
            bottom: 3px;
            content: "";
            height: 20px;
            left: 4px;
            position: absolute;
            transition: var(--transition-smooth);
            width: 20px;
            border-radius: 50%;
            z-index: 2;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        input:checked + .slider {
            background-color: var(--accent-primary);
        }

        input:checked + .slider::before {
            transform: translateX(20px);
        }

        .slider svg {
            width: 12px;
            height: 12px;
            z-index: 1;
            transition: var(--transition-smooth);
        }

        .slider .sun {
            color: var(--accent-warning);
            opacity: 0;
        }

        .slider .moon {
            color: #93C5FD;
            opacity: 1;
        }

        input:checked + .slider .sun {
            opacity: 1;
        }

        input:checked + .slider .moon {
            opacity: 0;
        }

        main {
            flex: 1;
            max-width: 1200px;
            width: 100%;
            margin: 0 auto;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }

        /* Filter Panel */
        .filter-section {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
            background-color: var(--bg-surface);
            padding: 1rem 1.5rem;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            transition: background-color 0.3s ease, border-color 0.3s ease;
        }

        .filter-group {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        .filter-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .chip {
            background-color: var(--bg-card);
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
            padding: 0.4rem 0.9rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition-smooth);
        }

        .chip:hover {
            color: var(--text-primary);
            border-color: var(--text-secondary);
        }

        .chip.active {
            background-color: rgba(59, 130, 246, 0.15);
            color: var(--accent-primary);
            border-color: var(--accent-primary);
        }

        body.light-theme .chip.active {
            background-color: rgba(59, 130, 246, 0.1);
        }

        .filter-actions {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .stats-info {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .btn-export {
            background-color: transparent;
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
            padding: 0.4rem 0.9rem;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.25rem;
            transition: var(--transition-smooth);
        }

        .btn-export:hover {
            background-color: rgba(59, 130, 246, 0.1);
            color: var(--accent-primary);
            border-color: var(--accent-primary);
        }

        /* Error Banner */
        .error-banner {
            background-color: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.25);
            color: #FCA5A5;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            display: none;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.95rem;
        }

        body.light-theme .error-banner {
            background-color: rgba(239, 68, 68, 0.05);
            color: var(--accent-danger);
        }

        /* Release Cards Grid */
        .grid-container {
            display: grid;
            grid-template-columns: 1fr;
            gap: 1.5rem;
        }

        .release-card {
            background-color: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.75rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            transition: var(--transition-smooth);
            position: relative;
            overflow: hidden;
        }

        .release-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background-color: var(--accent-primary);
            opacity: 0;
            transition: var(--transition-smooth);
        }

        .release-card:hover {
            transform: translateY(-2px);
            border-color: rgba(59, 130, 246, 0.4);
            box-shadow: var(--shadow-premium);
        }

        .release-card:hover::before {
            opacity: 1;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-meta {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .card-date {
            font-size: 0.85rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .card-badge {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            padding: 0.25rem 0.6rem;
            border-radius: 6px;
            letter-spacing: 0.05em;
        }

        /* Badge themes */
        .badge-feature { background-color: rgba(59, 130, 246, 0.15); color: #93C5FD; border: 1px solid rgba(59, 130, 246, 0.25); }
        .badge-announcement { background-color: rgba(167, 139, 250, 0.15); color: #C4B5FD; border: 1px solid rgba(167, 139, 250, 0.25); }
        .badge-issue { background-color: rgba(239, 68, 68, 0.15); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.25); }
        .badge-deprecation { background-color: rgba(245, 158, 11, 0.15); color: #FDE047; border: 1px solid rgba(245, 158, 11, 0.25); }
        .badge-other { background-color: rgba(107, 114, 128, 0.15); color: #D1D5DB; border: 1px solid rgba(107, 114, 128, 0.25); }

        body.light-theme .badge-feature { background-color: rgba(59, 130, 246, 0.1); color: var(--accent-primary); border-color: rgba(59, 130, 246, 0.2); }
        body.light-theme .badge-announcement { background-color: rgba(167, 139, 250, 0.1); color: #7C3AED; border-color: rgba(167, 139, 250, 0.2); }
        body.light-theme .badge-issue { background-color: rgba(239, 68, 68, 0.1); color: var(--accent-danger); border-color: rgba(239, 68, 68, 0.2); }
        body.light-theme .badge-deprecation { background-color: rgba(245, 158, 11, 0.1); color: #D97706; border-color: rgba(245, 158, 11, 0.2); }

        .card-link {
            color: var(--text-muted);
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 0.25rem;
            font-size: 0.8rem;
            transition: var(--transition-smooth);
        }

        .card-link:hover {
            color: var(--accent-primary);
        }

        .card-body {
            font-size: 0.95rem;
            color: var(--text-primary);
            word-wrap: break-word;
        }

        .card-body p {
            margin-bottom: 0.75rem;
        }

        .card-body p:last-child {
            margin-bottom: 0;
        }

        .card-body a {
            color: var(--accent-primary);
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: var(--transition-smooth);
        }

        .card-body a:hover {
            border-bottom-color: var(--accent-primary);
        }

        .card-body code {
            font-family: monospace;
            background-color: rgba(45, 55, 88, 0.4);
            padding: 0.1rem 0.3rem;
            border-radius: 4px;
            font-size: 0.85em;
            color: #F472B6;
            border: 1px solid rgba(45, 55, 88, 0.6);
        }

        body.light-theme .card-body code {
            background-color: #F1F5F9;
            border-color: #E2E8F0;
            color: #DB2777;
        }

        .card-actions {
            border-top: 1px solid var(--border-color);
            padding-top: 1rem;
            margin-top: auto;
            display: flex;
            justify-content: flex-end;
            gap: 0.75rem;
        }

        .btn-card-action {
            background-color: transparent;
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.85rem;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: var(--transition-smooth);
        }

        .btn-card-action:hover {
            background-color: rgba(16, 185, 129, 0.1);
            color: var(--accent-success);
            border-color: var(--accent-success);
        }

        .btn-tweet {
            background-color: transparent;
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.85rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: var(--transition-smooth);
        }

        .btn-tweet:hover {
            background-color: rgba(29, 161, 242, 0.1);
            color: var(--twitter-blue);
            border-color: var(--twitter-blue);
        }

        .btn-tweet svg {
            width: 14px;
            height: 14px;
            fill: currentColor;
        }

        /* Modal styling */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(11, 15, 25, 0.85);
            backdrop-filter: blur(8px);
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: var(--transition-smooth);
        }

        body.light-theme .modal-overlay {
            background-color: rgba(248, 250, 252, 0.85);
        }

        .modal {
            background-color: var(--bg-surface);
            border: 1px solid var(--border-color);
            width: 90%;
            max-width: 520px;
            border-radius: 16px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
            overflow: hidden;
            transform: scale(0.95);
            transition: var(--transition-smooth);
        }

        body.light-theme .modal {
            box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.15);
        }

        .modal-overlay.active .modal {
            transform: scale(1);
        }

        .modal-header {
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-title {
            font-family: var(--font-display);
            font-size: 1.2rem;
            font-weight: 600;
        }

        .modal-close {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.5rem;
            cursor: pointer;
            line-height: 1;
            transition: var(--transition-smooth);
        }

        .modal-close:hover {
            color: var(--text-primary);
        }

        .modal-body {
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .tweet-textarea {
            width: 100%;
            height: 130px;
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.75rem;
            color: var(--text-primary);
            font-family: var(--font-body);
            font-size: 0.95rem;
            resize: none;
            outline: none;
            transition: var(--transition-smooth);
        }

        .tweet-textarea:focus {
            border-color: var(--twitter-blue);
            box-shadow: 0 0 0 2px rgba(29, 161, 242, 0.2);
        }

        .modal-footer {
            padding: 1rem 1.5rem;
            background-color: rgba(11, 15, 25, 0.4);
            border-top: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        body.light-theme .modal-footer {
            background-color: rgba(241, 245, 249, 0.5);
        }

        .char-counter {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .char-counter.error {
            color: var(--accent-danger);
            font-weight: bold;
        }

        .btn-post-tweet {
            background-color: var(--twitter-blue);
            color: white;
            border: none;
            padding: 0.6rem 1.25rem;
            border-radius: 8px;
            font-family: var(--font-body);
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: var(--transition-smooth);
        }

        .btn-post-tweet:hover {
            background-color: var(--twitter-hover);
        }

        .btn-post-tweet:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Loading Skeleton */
        .skeleton {
            background: linear-gradient(90deg, var(--bg-surface) 25%, var(--bg-card) 50%, var(--bg-surface) 75%);
            background-size: 200% 100%;
            animation: loading-shimmer 1.5s infinite;
            border-radius: 12px;
        }

        @keyframes loading-shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        .skeleton-card {
            height: 180px;
            border: 1px solid var(--border-color);
        }

        footer {
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.8rem;
            border-top: 1px solid rgba(45, 55, 88, 0.4);
            margin-top: auto;
        }

        body.light-theme footer {
            border-top-color: var(--border-color);
        }

        @media (max-width: 768px) {
            header {
                padding: 1rem;
                flex-direction: column;
                gap: 1rem;
                align-items: stretch;
            }
            .controls {
                justify-content: space-between;
            }
            main {
                padding: 1rem;
            }
            .filter-section {
                flex-direction: column;
                align-items: stretch;
                gap: 1.5rem;
            }
            .filter-actions {
                justify-content: space-between;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-container">
            <div class="logo-icon">BQ</div>
            <h1>BigQuery Releases</h1>
        </div>
        <div class="controls">
            <div class="status-badge">
                <span class="status-dot"></span>
                <span id="last-updated">Updating...</span>
            </div>
            <button id="btn-refresh" class="btn">
                <div class="spinner"></div>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                Refresh
            </button>
            <div class="theme-switch-wrapper">
                <label class="theme-switch" for="theme-checkbox">
                    <input type="checkbox" id="theme-checkbox" />
                    <div class="slider round">
                        <svg class="sun" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
                        <svg class="moon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
                    </div>
                </label>
            </div>
        </div>
    </header>

    <main>
        <div id="error-banner" class="error-banner">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <span id="error-message"></span>
        </div>

        <section class="filter-section">
            <div class="filter-group">
                <span class="filter-label">Filter:</span>
                <span class="chip active" data-filter="all">All</span>
                <span class="chip" data-filter="Feature">Features</span>
                <span class="chip" data-filter="Announcement">Announcements</span>
                <span class="chip" data-filter="Issue">Issues</span>
                <span class="chip" data-filter="Deprecation">Deprecations</span>
            </div>
            <div class="filter-actions">
                <button id="btn-export" class="btn-export">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Export CSV
                </button>
                <div id="stats-info" class="stats-info">Showing 0 updates</div>
            </div>
        </section>

        <section id="releases-grid" class="grid-container">
            <!-- Loading skeletons initially -->
            <div class="skeleton skeleton-card"></div>
            <div class="skeleton skeleton-card"></div>
            <div class="skeleton skeleton-card"></div>
        </section>
    </main>

    <!-- Twitter Preview Modal -->
    <div id="tweet-modal" class="modal-overlay">
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title">Share to Twitter / X</h3>
                <button id="modal-close" class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <textarea id="tweet-text" class="tweet-textarea" placeholder="What's happening?"></textarea>
            </div>
            <div class="modal-footer">
                <div id="char-counter" class="char-counter">0 / 280</div>
                <button id="btn-submit-tweet" class="btn-post-tweet">
                    <svg width="14" height="14" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                    Post Tweet
                </button>
            </div>
        </div>
    </div>

    <footer>
        BigQuery Release Notes Dashboard &bull; Google Cloud Feeds
    </footer>

    <script>
        let allReleases = [];
        let activeFilter = 'all';

        const btnRefresh = document.getElementById('btn-refresh');
        const grid = document.getElementById('releases-grid');
        const errorBanner = document.getElementById('error-banner');
        const errorMessage = document.getElementById('error-message');
        const lastUpdatedText = document.getElementById('last-updated');
        const statsInfo = document.getElementById('stats-info');
        const chips = document.querySelectorAll('.chip');
        const themeCheckbox = document.getElementById('theme-checkbox');
        const btnExport = document.getElementById('btn-export');

        // Modal Elements
        const tweetModal = document.getElementById('tweet-modal');
        const modalClose = document.getElementById('modal-close');
        const tweetText = document.getElementById('tweet-text');
        const charCounter = document.getElementById('char-counter');
        const btnSubmitTweet = document.getElementById('btn-submit-tweet');

        // Theme Toggle Switch Listener
        themeCheckbox.addEventListener('change', () => {
            if (themeCheckbox.checked) {
                document.body.classList.add('light-theme');
            } else {
                document.body.classList.remove('light-theme');
            }
        });

        // Local Clipboard copy action
        window.copyToClipboard = function(id, btnElement) {
            const release = allReleases.find(r => r.id === id);
            if (!release) return;
            
            const textToCopy = `📢 #BigQuery Release [${release.date}] (${release.type}):\n\n${release.content_text}${release.link ? `\n\nRead more: ${release.link}` : ''}`;
            
            navigator.clipboard.writeText(textToCopy).then(() => {
                const origHtml = btnElement.innerHTML;
                btnElement.innerHTML = `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-success)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                    Copied!
                `;
                btnElement.style.color = 'var(--accent-success)';
                btnElement.style.borderColor = 'var(--accent-success)';
                setTimeout(() => {
                    btnElement.innerHTML = origHtml;
                    btnElement.style.color = '';
                    btnElement.style.borderColor = '';
                }, 2000);
            }).catch(err => {
                console.error('Could not copy text: ', err);
            });
        };

        // Export active filtered releases to CSV file
        btnExport.addEventListener('click', () => {
            const filtered = activeFilter === 'all' 
                ? allReleases 
                : allReleases.filter(r => r.type.toLowerCase().includes(activeFilter.toLowerCase()));

            if (filtered.length === 0) {
                alert("No release notes to export.");
                return;
            }

            const headers = ["Date", "Type", "Link", "Content"];
            const rows = filtered.map(r => [
                r.date,
                r.type,
                r.link,
                r.content_text
            ]);

            const csvContent = [
                headers.join(','),
                ...rows.map(row => row.map(val => {
                    const escaped = (val || '').replace(/"/g, '""');
                    return `"${escaped}"`;
                }).join(','))
            ].join('\n');

            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.setAttribute("href", url);
            link.setAttribute("download", `bigquery_releases_${activeFilter}_${new Date().toISOString().slice(0, 10)}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });

        async function fetchReleases() {
            btnRefresh.classList.add('loading');
            btnRefresh.disabled = true;
            errorBanner.style.display = 'none';

            // Show skeleton loading
            grid.innerHTML = `
                <div class="skeleton skeleton-card"></div>
                <div class="skeleton skeleton-card"></div>
                <div class="skeleton skeleton-card"></div>
            `;

            try {
                const response = await fetch('/api/releases');
                const data = await response.json();

                if (data.success) {
                    allReleases = data.releases;
                    renderReleases();
                    const now = new Date();
                    lastUpdatedText.textContent = `Refreshed ${now.toLocaleTimeString()}`;
                } else {
                    showError(data.error || 'Failed to load updates.');
                }
            } catch (err) {
                showError('Could not connect to the backend server.');
            } finally {
                btnRefresh.classList.remove('loading');
                btnRefresh.disabled = false;
            }
        }

        function showError(message) {
            errorMessage.textContent = message;
            errorBanner.style.display = 'flex';
            grid.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 2rem;">No data available. Click Refresh to retry.</div>';
            statsInfo.textContent = 'Showing 0 updates';
        }

        function getBadgeClass(type) {
            const t = type.toLowerCase();
            if (t.includes('feature')) return 'badge-feature';
            if (t.includes('announcement')) return 'badge-announcement';
            if (t.includes('issue')) return 'badge-issue';
            if (t.includes('deprecation')) return 'badge-deprecation';
            return 'badge-other';
        }

        function renderReleases() {
            const filtered = activeFilter === 'all' 
                ? allReleases 
                : allReleases.filter(r => r.type.toLowerCase().includes(activeFilter.toLowerCase()));

            statsInfo.textContent = `Showing ${filtered.length} of ${allReleases.length} updates`;

            if (filtered.length === 0) {
                grid.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 3rem;">No release notes match the active filter.</div>';
                return;
            }

            grid.innerHTML = filtered.map(release => `
                <article class="release-card">
                    <div class="card-header">
                        <div class="card-meta">
                            <span class="card-badge ${getBadgeClass(release.type)}">${release.type}</span>
                            <span class="card-date">${release.date}</span>
                        </div>
                        ${release.link ? `
                            <a href="${release.link}" target="_blank" rel="noopener noreferrer" class="card-link">
                                Source
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14L21 3"/></svg>
                            </a>
                        ` : ''}
                    </div>
                    <div class="card-body">
                        ${release.content_html}
                    </div>
                    <div class="card-actions">
                        <button class="btn-card-action" onclick="copyToClipboard('${release.id}', this)">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                            Copy
                        </button>
                        <button class="btn-tweet" onclick="openTweetModal('${release.id}')">
                            <svg viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                            Tweet
                        </button>
                    </div>
                </article>
            `).join('');
        }

        // Filters
        chips.forEach(chip => {
            chip.addEventListener('click', () => {
                chips.forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                activeFilter = chip.getAttribute('data-filter');
                renderReleases();
            });
        });

        // Tweet Modal functionality
        window.openTweetModal = function(id) {
            const release = allReleases.find(r => r.id === id);
            if (!release) return;

            // Build pre-composed tweet
            const header = `📢 #BigQuery Update [${release.date}]\\nType: ${release.type}\\n\\n`;
            const footer = release.link ? `\\n\\nRead more: ${release.link}` : '';
            
            // Limit desc so total is within 280 chars
            const allowedDescLen = 280 - header.length - footer.length;
            let desc = release.content_text;
            if (desc.length > allowedDescLen) {
                desc = desc.substring(0, allowedDescLen - 3) + '...';
            }
            
            tweetText.value = `${header}${desc}${footer}`.replace(/\\\\n/g, '\\n');
            updateCharCount();
            
            tweetModal.classList.add('active');
            tweetText.focus();
        };

        function updateCharCount() {
            const len = tweetText.value.length;
            charCounter.textContent = `${len} / 280`;
            if (len > 280) {
                charCounter.classList.add('error');
                btnSubmitTweet.disabled = true;
            } else {
                charCounter.classList.remove('error');
                btnSubmitTweet.disabled = len === 0;
            }
        }

        tweetText.addEventListener('input', updateCharCount);

        modalClose.addEventListener('click', () => {
            tweetModal.classList.remove('active');
        });

        tweetModal.addEventListener('click', (e) => {
            if (e.target === tweetModal) {
                tweetModal.classList.remove('active');
            }
        });

        btnSubmitTweet.addEventListener('click', () => {
            const text = encodeURIComponent(tweetText.value);
            window.open(`https://twitter.com/intent/tweet?text=${text}`, '_blank');
            tweetModal.classList.remove('active');
        });

        btnRefresh.addEventListener('click', fetchReleases);

        // Initial load
        fetchReleases();
    </script>
</body>
</html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
