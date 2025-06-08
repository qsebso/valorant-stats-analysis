# Phase Tagging Rules

This document defines how to assign each match’s `phase` based on its date.

## 1. Purpose

When scraping match data, we record `match_date`. This file tells our scraper which dates belong to the regular season and which belong to playoffs, so every row in `map_stats` gets the correct `phase`.

## 2. Source of Truth

Refer to the official event calendar or bracket pages for exact dates. For example:
- Riot’s VCT Calendar: https://playvalorant.com/…
- VLR.gg bracket pages for “Upper Bracket,” “Lower Bracket,” etc.

## 3. Date-Range Rules

Use these rules in your `scheduler.py`:

```yaml
rules:
  # Regular Season runs from kickoff through the day before playoffs start
  - from: "2025-01-10"   # first day of regular season
    to:   "2025-01-20"   # last day before playoffs begin
    phase: "Regular Season"

  # Playoffs run from the first playoff date through the final
  - from: "2025-01-21"   # first playoff match
    to:   "2025-01-25"   # final playoff match
    phase: "Playoffs"
