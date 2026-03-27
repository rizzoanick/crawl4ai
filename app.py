import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st

from toolsuite.analyze import analyze_crawl
from toolsuite.crawl import run_crawl
from toolsuite.storage import (
    fetch_analysis_for_crawl,
    fetch_crawl,
    fetch_latest_analysis,
    fetch_recent_crawls,
    init_db,
)


executor = ThreadPoolExecutor(max_workers=2)


def _init_session():
    if "task_log" not in st.session_state:
        st.session_state["task_log"] = []


def _observe_tasks():
    for task in st.session_state["task_log"]:
        if "result" not in task and task["future"].done():
            task["result"] = task["future"].result()


def _enqueue_task(kind: str, future) -> None:
    st.session_state["task_log"].append({"kind": kind, "future": future})


def _display_tasks():
    if not st.session_state["task_log"]:
        st.caption("No background tasks running.")
        return
    for idx, task in enumerate(st.session_state["task_log"], 1):
        future = task["future"]
        status = "running" if not future.done() else "done"
        with st.status(label=f"Task {idx}: {task['kind']}", state="running" if status == "running" else "complete"):
            if status == "running":
                st.write("Processing...")
            else:
                result = task.get("result") or future.result()
                if result.get("success", True):
                    st.success(f"Finished {task['kind']} (ID: {result.get('crawl_id') or result.get('analysis_id')})")
                else:
                    st.error(result.get("error", "Unknown error"))


def _render_overview_tab(crawls: List[Dict]):
    st.subheader("Recent Crawls")
    if not crawls:
        st.info("No crawls recorded yet. Start one from the sidebar.")
        return
    df = pd.DataFrame(crawls)
    st.dataframe(df)


def _render_raw_tab(crawls: List[Dict]):
    st.subheader("Raw Data Viewer")
    if not crawls:
        st.info("No crawls to display yet.")
        return
    crawl_options = {f"Crawl #{row['id']} - {row['url']}": row["id"] for row in crawls if row.get("raw_path")}
    if not crawl_options:
        st.warning("Crawls are recorded but no raw payloads are available yet.")
        return
    selected_label = st.selectbox("Select a crawl", list(crawl_options.keys()))
    selected_id = crawl_options[selected_label]
    record = fetch_crawl(selected_id)
    if not record or not record.get("raw_path"):
        st.error("Unable to load the selected crawl.")
        return
    raw_path = Path(record["raw_path"])
    if not raw_path.exists():
        st.error("Raw payload file is missing on disk.")
        return
    with open(raw_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    st.write(f"URL: {payload.get('url')}")
    st.write(f"Status: {'Success' if payload.get('success') else 'Failed'}")
    st.text_area("HTML snippet", value=(payload.get("html") or "")[:2000], height=300)
    if payload.get("markdown"):
        st.text_area("Markdown snippet", value=str(payload.get("markdown"))[:2000], height=300)


def _render_analysis_tab(crawls: List[Dict]):
    st.subheader("Analysis Results")
    if not crawls:
        st.info("No crawls yet to analyze.")
        return
    crawl_options = {f"Crawl #{row['id']} - {row['url']}": row["id"] for row in crawls}
    selected_label = st.selectbox("Select crawl for analysis results", list(crawl_options.keys()))
    selected_id = crawl_options[selected_label]
    analyses = fetch_analysis_for_crawl(selected_id)
    latest_analysis = analyses[0] if analyses else None
    if not latest_analysis:
        st.warning("No analyses for this crawl yet.")
        return
    metrics = json.loads(latest_analysis.get("metrics_json") or "{}")
    st.metric("Word Count", metrics.get("word_count", 0))
    st.metric("Link Count", metrics.get("link_count", 0))
    keywords = metrics.get("top_keywords") or []
    if keywords:
        keyword_df = pd.DataFrame(keywords)
        st.bar_chart(keyword_df, x="keyword", y="count")
    st.json(metrics)


def main():
    st.set_page_config(page_title="Crawl4AI Tool Suite", layout="wide")
    init_db()
    _init_session()
    _observe_tasks()

    st.sidebar.header("Crawl Controls")
    url = st.sidebar.text_input("Target URL")
    note = st.sidebar.text_area("Notes", height=80)
    if st.sidebar.button("Run Crawl", type="primary"):
        if not url:
            st.sidebar.error("Please provide a URL before starting a crawl.")
        else:
            future = executor.submit(run_crawl, url, note)
            _enqueue_task("crawl", future)
            st.sidebar.success("Crawl dispatched. Check task status below.")

    st.sidebar.header("Process Controls")
    recent_crawls = fetch_recent_crawls(limit=25)
    crawl_options = {f"Crawl #{row['id']} - {row['url']}": row["id"] for row in recent_crawls}
    selected_crawl = (
        st.sidebar.selectbox("Select crawl to analyze", list(crawl_options.keys())) if crawl_options else None
    )
    if st.sidebar.button("Run Analysis"):
        target_id = crawl_options.get(selected_crawl) if selected_crawl else None
        future = executor.submit(analyze_crawl, target_id)
        _enqueue_task("analysis", future)
        st.sidebar.success("Analysis dispatched.")

    st.sidebar.divider()
    st.sidebar.subheader("Background Tasks")
    _display_tasks()

    tabs = st.tabs(["Overview", "Raw Data Viewer", "Analysis Results"])
    with tabs[0]:
        _render_overview_tab(recent_crawls)
    with tabs[1]:
        _render_raw_tab(recent_crawls)
    with tabs[2]:
        _render_analysis_tab(recent_crawls)

    st.sidebar.divider()
    latest_analysis = fetch_latest_analysis()
    if latest_analysis:
        st.sidebar.caption(
            f"Latest analysis ID: {latest_analysis['id']} for crawl #{latest_analysis['crawl_id']}"
        )


if __name__ == "__main__":
    main()
