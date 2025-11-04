# The Last Application

> ⚠️ **Work in Progress** - This project is currently under active development.

## Overview

*One bot to rule all applications, one bot to find them,*  
*One bot to bring all offers and in employment bind them.*

In the vast realm of digital employment, where countless job seekers wander through endless applications, emerges a legendary tool forged to end the tedious quest. **The Last Application** is your automated champion, wielding the power to conquer LinkedIn Easy Apply at scale—so this may truly be the last time you manually submit an application.

Born from ancient automation magic and modern AI sorcery, this bot traverses the job boards, answers the gatekeepers' questions with wisdom, and records every conquest in its hall of records. No antibot sentinel shall stand in its way.

## Features

- **Antibot Bypass**: Utilizes nodriver to circumvent antibot detection systems and breach the walls of digital fortresses
- **Smart Question Answering**: 
  - Primary: Uses predefined answer list for known questions
  - Fallback: Leverages LangChain with Ollama/GPT-3.5 for unknown queries
- **Data Persistence**: All interactions stored in DuckDB including:
  - Question-answer pairs
  - Hiring information
  - Status tracking
  - Metadata and analytics
- **Visualization Dashboard**: Upcoming super cool dashboard for data visualization and analytics insights
- **Future Expansion**: Planned extension to support external websites beyond LinkedIn

## Status

Currently implementing core features. Usage documentation and detailed setup instructions coming soon.

## Roadmap

- [ ] Complete core Q&A functionality
- [ ] Build visualization dashboard
- [ ] Add external website support
- [ ] Documentation and usage examples

## Tech Stack

- nodriver
- LangChain
- Ollama/GPT-3.5
- DuckDB

---

_More details and usage instructions will be added as development progresses._

*(Project name subject to change, but the legend remains)*
