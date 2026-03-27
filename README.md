# Crawl4AI Tool Suite

A locally hosted web scraping and analysis suite built on **crawl4ai**. The tool suite includes a crawler, analysis pipeline, and Streamlit interface for orchestrating runs and visualizing results.

## Prerequisites
- **Python**: 3.9 or newer.
- **pip/venv**: Ensure `python -m venv` is available for creating virtual environments.
- **Playwright browsers**: Required by `crawl4ai` for page rendering.
- **System build tools**: Typical C/C++ build essentials for installing Python packages.

## Installation
1. **Clone the repository** (if you haven't already) and change into the project directory:
   ```bash
   git clone <repo-url>
   cd crawl4ai
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers** (required for crawl4ai):
   ```bash
   playwright install
   ```

## Usage
From the project root, launch the Streamlit interface:
```bash
streamlit run app.py
```

If you prefer one-click launchers, use the provided scripts which also set `PYTHONPATH` to the project root to avoid import errors:
- macOS/Linux: `./run_app.sh`
- Windows: `run_app.bat`

The app opens in your browser. Use the sidebar to start crawls, run analyses, and review results across the tabs.

## File Structure Overview
- `app.py`: Streamlit UI wiring crawl and analysis modules.
- `toolsuite/`: Package containing configuration, storage, crawl, and analysis logic.
- `data/raw/`: Directory where raw crawl payloads are stored (created automatically on first run).

## Sanity Check
`app.py` imports from the `toolsuite` package while staying in the repository root. Running `streamlit run app.py` from the root works as long as the root is on `PYTHONPATH`. The launcher scripts export this automatically. If running manually and you see `ModuleNotFoundError: toolsuite`, set `export PYTHONPATH="$(pwd)"` (macOS/Linux) or `set PYTHONPATH=%cd%` (Windows) before launching.
