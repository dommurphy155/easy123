# Easy123 Job Scraper & Telegram Notifier Bot

## Overview

Easy123 is a lightweight, fully automated job scraping bot designed to run on Ubuntu 20.04 Micro Flex E2 VPS. It scrapes part-time jobs from Indeed, filters and ranks them based on your CV compatibility, location, salary, and company rating, then sends curated job alerts directly to your Telegram with accept/decline functionality.

---

## Features

- Scrapes up to 33 jobs per run, batching 8 jobs per Telegram message  
- Strict filters: part-time only, within 5 miles of Leigh (WN7 1NX), salary thresholds  
- Hugging Face semantic ranking for CV-job compatibility  
- Company ratings from Indeed reviews with fallback logic  
- Inline Telegram buttons for Accept (auto-apply) and Decline (blacklist)  
- Automatic job deduplication and cleanup  
- Scheduled scrapes and sends at fixed UK local times  
- CPU and memory monitoring with critical Telegram alerts  
- Fully asynchronous for low resource consumption  
- Easy deployment with systemd service and environment config  

---

## Installation

1. Clone the repo via SSH:

   ```bash
   git clone git@github.com:dommurphy155/easy123.git
   cd easy123
