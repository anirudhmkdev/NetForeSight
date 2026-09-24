# NetForeSight — AI-Based Network Attack Forecasting (World Models)

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Environment](https://img.shields.io/badge/Environment-100%25%20Offline-success)](#)
[![MITRE ATT&CK](https://img.shields.io/badge/Framework-MITRE%20ATT%26CK-orange)](#)

> **“Anticipate attacker progression before compromise is completed.”**

NetForeSight is an AI-powered network attack forecasting prototype designed for Critical Information Infrastructure and Enterprise SOC environments. Rather than relying solely on reactive, post-facto intrusion detection, NetForeSight leverages **temporal network state sequences and World Models** to forecast future attack trajectories, anticipate MITRE ATT&CK stage transitions, and provide interpretable decision support for security defenders.

---

## Key Features

- **Temporal Network State Representation**: Aggregates continuous network telemetry (PCAP / PCAPNG / CSV) into chronological time windows parameterized as 10-dimensional network state vectors.
- **World Model Forecasting Engine**: Evaluates state-transition dynamics across sequential horizons ($T+1$ through $T+5$) to anticipate attack progression before compromise completion.
- **MITRE ATT&CK Stage Mapping**: Automatically projects network trajectories into tactical phases (*Reconnaissance*, *Initial Access*, *Lateral Movement*, *Command & Control*, *Exfiltration*).
- **Interpretable Decision Support (XAI)**: Attention-style and SHAP-style feature attribution highlighting critical signals (TCP SYN surge, service port probing, IAT variance, TCP window anomalies).
- **Interactive SOC Analyst Console**:
  - **Traffic Monitor**: Drill-down inspection drawer with packet-level and flow-level anomaly metrics.
  - **Attack Forecast & Timeline**: Visual trajectory forecasting with threshold crossing warnings.
  - **Model Benchmark Evaluation**: Comparative evaluation against reactive baselines (Logistic Regression, Random Forest) illustrating lead-time advantages.
  - **Security Reports**: Automated incident briefing generation with one-click export.
- **100% Offline & Private**: Executes entirely on local compute with zero external cloud dependencies or telemetry leakage.

---

## Architecture Flow

```text
Raw Network Telemetry (PCAP / PCAPNG / CSV)
                    │
                    ▼
     [Flow & Packet Feature Extraction]
  (Port Entropy, IAT Variance, Window Size, TTL)
                    │
                    ▼
       [Min-Max Feature Normalization]
                    │
                    ▼
   [Ordered Time-Window State Representation]
           (10-Dim State Vectors)
                    │
                    ▼
          [World Model Forecaster]
      (State Dynamics & Transition Logic)
                    │
       ┌────────────┴────────────┐
       ▼                         ▼
 [K-Step Risk Forecast]   [Explainability (XAI)]
  (Confidence Bands &      (SHAP-style Signal
   MITRE Stage Trajectory)   Contributions)
       │                         │
       └────────────┬────────────┘
                    ▼
      [Interactive SOC Dashboard]
```

---

## Getting Started

### Prerequisites
- Python 3.10 or higher
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/NetForeSight.git
   cd NetForeSight
   ```

2. **(Optional) Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

Launch the Streamlit web console:
```bash
python -m streamlit run app.py
```
*Or, if Streamlit is in your system PATH:*
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## Supported Datasets

- **Real Traffic CSVs**: CIC-IDS-2017 / CIC-IDS-2018 benchmark flows, Zeek/Bro connection logs, Suricata EVE logs, or NetForeSight standard flow schema.
- **Raw Packet Captures**: Standard `.pcap` and `.pcapng` traces (requires `scapy`).
- **Included Sample Data**: Pre-packaged synthetic network traces in `data/` for rapid evaluation.

---

## Project Structure

```text
NetForeSight/
├── app.py                    # Main Streamlit application and page controller
├── requirements.txt          # Python package dependencies
├── README.md                 # Project documentation
├── LICENSE                   # MIT License
├── .gitignore                # Git ignore rules
│
├── modules/                  # Modular backend & UI components
│   ├── __init__.py           # Constants, ATT&CK stages, and severities
│   ├── data_loader.py        # PCAP reader (Scapy) and CSV ingestors
│   ├── feature_extractor.py  # Port entropy, IAT stats, and flow metrics
│   ├── windowing.py          # 10-D network state vector builder
│   ├── forecast_engine.py    # WorldModel ABC & inference backends
│   ├── explainability.py     # Attribution layer & SHAP-style weights
│   ├── visualizations.py     # Plotly interactive graphs and styling
│   └── demo_ui.py            # Dashboard scenario components
│
└── data/                     # Sample datasets and benchmark traces
    └── demo_network.csv      # Reference traffic trace
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
