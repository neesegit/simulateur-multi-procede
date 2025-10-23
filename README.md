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
. <br>
├── config/ # Configuration files <br>
├── core/ # Main logic <br>
├── data_layer/ # Data management <br>
├── interfaces/ # CLI interfaces, config loader and more <br>
├── models/ # Process models <br>
├── processes/ # Water treatment process implementations <br>
├── main.py # Simulation entry point <br> 
├── requirements.txt # Dependencies <br>
└── README.md <br>

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
