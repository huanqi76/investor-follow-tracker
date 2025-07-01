# investor follow tracker

usage: tracks the new fellows of specified connections on linkedin and highlights changes to your google sheet of choice.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)]
(https://colab.research.google.com/github/huanqi76/investor-follow-tracker/blob/main/colab_launcher.ipynb)

## ✨ Features
* **Headless scraping** – handles infinite scroll and dynamic selectors.
* **Snapshot diffing** – stores historical JSON & flags new follows.
* **1-click export** – updates a chosen Google Sheet tab.

## 🚀 Quick start (local)

```bash
git clone https://github.com/huanqi76/investor-follow-tracker.git
cd investor-follow-tracker
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m investor_follow_tracker.cli