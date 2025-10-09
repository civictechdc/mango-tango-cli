# CIBMangoTree Time Coordination Analyzer

Time coordination analysis for identifying synchronized posting patterns.

## Description

This analysis measures time coordination between users by examining correlated user pairings. It calculates how often two users post within the same 15-minute time window, with windows sliding every 5 minutes. A high frequency of co-occurrence suggests potential coordination between the users.

## Installation

```bash
pip install cibmangotree-analyzer-time-coordination
```

## Features

- Sliding time window analysis (15-minute windows, 5-minute slides)
- User pair co-occurrence counting
- Coordination pattern detection

## Usage

This analyzer is automatically discovered by CIBMangoTree when installed.
