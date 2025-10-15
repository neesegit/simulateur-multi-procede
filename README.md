# Water treatment simulation

## Overview

This project aims to simulate several water treatment processes and evaluate their performance in terms of:
- water purification efficiency,
- energy consumption and production

---

## Features
- Modular simulator architecture (`core`, `models`, `processes`, etc.)
- Evaluation of efficiency and energy use

---

## Project structure
.
├── config/ # Configuration files
├── core/ # Main logic
├── data_layer/ # Data management
├── interfaces/ # CLI interfaces, config loader and more
├── models/ # Process models
├── processes/ # Water treatment process implementations
├── main.py # Simulation entry point
├── requirements.txt # Dependencies
└── README.md

---

## Installation

```bash
git clone https://github.com/neesegit/simulation.git
cd simulation
python3 -m venv venv
source venv/bin/activate # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

---

## Usage

You can find everything by doing the command:
```bash
python main.py --help
```
