<div align="center">
  <h1>Michigan Lottery Stats Dashboard</h1>
  <p><strong>A zero-maintenance, automated data pipeline & visualization dashboard for the Michigan Lottery.</strong></p>
  
  [![Automated Updates](https://github.com/lussierd16/lotto-tinker/actions/workflows/update-lottery.yml/badge.svg)](https://github.com/lussierd16/lotto-tinker/actions)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
</div>

<hr />

## 🎯 The "Lotto Tinker" Philosophy

Most people play the lottery based on dates, dreams, or "lucky" numbers. This project treats the lottery strictly as a mathematical variable-reward system.

The dashboard uses **Expected Value (EV)** to determine the exact moment a jackpot becomes large enough to offset the astronomical odds, moving the game from a "tax on hope" to a statistically valid (though highly volatile) proposition.

### Core Strategies Modeled:
1. **The Invisible Haircut:** All EV calculations account for the ~35% true net payout (adjusting for cash-option rates, federal taxes, and state taxes).
2. **Break-Even Focus:** Games are flagged as **+EV (Worth It)** *only* when the net jackpot payout exceeds the mathematical probability of winning.
3. **The Unpopular Zone:** The dashboard highlights the "32+ Zone." Playing numbers above 31 does not increase your odds of winning, but it drastically reduces your odds of *splitting* the jackpot with players who use calendar dates.

---

## 🚀 Features

*   **Automated Data Ingestion:** Fetches historical data directly from the official Michigan Lottery GraphQL API.
*   **Mathematical Modeling:** Calculates EV, Break-Even thresholds, sum distributions, gap analysis, and frequency mapping.
*   **Smart Number Generator:** An interactive, constrained random generator that allows users to lock specific balls, target a specific sum, and weight picks toward the "Unpopular Zone."
*   **"Zero-Maintenance" Infrastructure:** Powered by a daily GitHub Action that pulls data, recalculates stats, rebuilds the HTML, and triggers a Cloudflare Pages deployment.

---

## 🛠️ Architecture & Tech Stack

This project is designed to be as lightweight and portable as possible.

*   **Data Layer:** Python 3 (Standard Library only — no `pip` dependencies required).
*   **API:** Michigan Lottery Public GraphQL (`https://www.michiganlottery.com/api`).
*   **Frontend:** A single, self-contained `index.html` file using Vanilla JavaScript and [Chart.js](https://www.chartjs.org/) (via CDN).
*   **Automation:** GitHub Actions (`.github/workflows/update-lottery.yml`).
*   **Hosting:** Cloudflare Pages (Static Site).

---

## 📊 Tracked Games

| Game | Ticket Cost | Odds (1 in...) | EV Status |
| :--- | :--- | :--- | :--- |
| **Club Keno** | $1.00+ | N/A (parimutuel) | N/A — EV depends on spots played |
| **Classic Lotto 47** | $1.00 | 10,737,573 | Dynamic (+EV only at ~$30M+) |
| **Mega Millions** | $5.00 | 302,575,350 | Dynamic (+EV only at ~$4.1B+) |
| **Powerball** | $2.00 | 292,201,338 | Dynamic (+EV only at ~$1.6B+) |
| **Millionaire for Life**| $5.00 | 22,910,580 | **Permanent -EV** (Capped Prize) |

*(Note: Mega Millions pricing reflects the 2025/2026 $5.00 ticket structure. Club Keno draws 20 numbers from 1–80 every ~3.5 minutes; one draw per day is sampled for stats.)*

---

## ⚙️ How to Deploy Your Own

You can fork this repository to run your own automated dashboard for free.

1. **Fork the Repo:** Click the "Fork" button at the top right of this repository.
2. **Enable Actions:** Go to the "Actions" tab in your fork and enable workflows. The `Daily Lottery Update` action will now run automatically every day at 6:00 AM EST.
3. **Connect to Cloudflare Pages:**
   * Log into Cloudflare Pages.
   * Click **Create a project** > **Connect to Git**.
   * Select your forked repository.
   * Set **Framework preset** to `None`.
   * Set **Build output directory** to `.` (the root directory).
   * Save and deploy! 

Your site will now automatically update itself every day.

---

## ⚠️ Disclaimer

This project is for educational and statistical purposes only. The Michigan Lottery is a game of chance. This dashboard does not guarantee winnings, nor does it provide financial advice. Please play responsibly.

---

## 🤖 A Note on How This Was Built

The overwhelming majority of this project — was written by [Claude](https://claude.ai) (Anthropic's AI), operating through a personal AI infrastructure layer called [PAI](https://github.com/danielmiessler/Personal_AI_Infrastructure).

My role was mostly directing: identifying interesting public APIs worth exploring, deciding how the data should be presented, and making the key architecture calls around automation, hosting, and tooling.

I'm a Senior Cloud Consultant with 20+ years in IT — cloud infrastructure, Terraform, DevOps, CI/CD pipelines. That background turns out to be useful in steering Claude toward the right architecture rather than just accepting whatever it produces. The interesting challenge isn't whether AI can write the code — it clearly can — it's learning how to collaborate with it effectively enough that the output reflects real judgment, not just plausible-looking output. That's what I'm actually practicing.