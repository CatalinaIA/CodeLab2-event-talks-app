# BigQuery Release Notes Web App

A premium, lightweight, single-page dashboard built with Python Flask and vanilla HTML/CSS/JavaScript. It fetches Google Cloud's official BigQuery Atom release feed, parses it dynamically into granular update entries, and provides instant local filtering and custom Twitter/X sharing features.

---

## Features

- **Live Feeds Aggregation**: Instantly pulls and parses the official Google Cloud BigQuery release feed.
- **Granular Segmenting**: Automatically parses entries and groups updates by type (*Features*, *Announcements*, *Issues*, *Deprecations*).
- **Responsive Dashboard**: Beautiful custom dark mode styling with ambient glow effects, responsive CSS grid, and smooth interactive card transitions.
- **Dynamic Category Filtering**: Fast local filtering of updates using filter chips.
- **Twitter/X Integration**: A custom tweet compose modal that pre-formats release information, automatically limits characters (under 280), and links directly to Twitter web intents.
- **Robust Error Handling**: Integrated skeleton loading state indicator and API error banners.

---

## Technical Stack

- **Backend**: Python 3.x, Flask (minimal footprint, XML parser using standard library `xml.etree.ElementTree` and regular expressions).
- **Frontend**: Standard Vanilla HTML5, CSS3, and JavaScript (ES6+).
- **Fonts**: Google Fonts (*Outfit*, *Plus Jakarta Sans*).

---

## Quick Start

### 1. Prerequisites

Ensure you have Python 3.9+ installed.

### 2. Installation

Navigate to the project directory and install the necessary dependencies:

```powershell
pip install -r requirements.txt
```

### 3. Run the Application

Start the Flask development server:

```powershell
python app.py
```

### 4. Visit the App

Open your browser and navigate to:
[http://localhost:5000](http://localhost:5000)

---

## Git & GitHub Deployment Reference

If you need to push updates or deploy this project to GitHub, follow these quick commands:

### 1. Authenticate with GitHub (first-time setup)
```powershell
gh auth login
```

### 2. Initialize and Push to your Repository
```powershell
git init
git add .
git commit -m "Initial commit: BigQuery Release Notes Web App"
git branch -M main
gh repo create CodeLab2-event-talks-app --public --source=. --push
```
