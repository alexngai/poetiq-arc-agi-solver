# Poetiq: SOTA Reasoning on ARC-AGI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![ARC-AGI](https://img.shields.io/badge/Task-ARC--AGI-red)](https://arcprize.org/)

This repository allows reproduction of **Poetiq's** record-breaking submission to the ARC-AGI-1 and ARC-AGI-2 benchmarks.

Full analysis is available in our launch post, **[Traversing the Frontier of Superintelligence](https://poetiq.ai/posts/arcagi_announcement/)**.

---

## 📊 Results

<p align="center">
  <img src="arcagi1.png" width="45%" />
  <img src="arcagi2.png" width="45%" />
</p>

## 🛠️ Usage

### Prerequisites
- Python 3.11+
- API Keys for the models you wish to test (Gemini, OpenAI, etc.)
- 8GB+ RAM recommended

### Quick Start

**Option 1: Automated Setup (Recommended)**

```bash
./setup.sh
```

Then edit `.env` with your API keys and run:

```bash
source .venv/bin/activate
python main.py
```

**Option 2: Manual Setup**

1. Setup the environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Create a .env file in the root directory:
    ```bash
    cp .env.example .env
    # Edit .env and add your API keys
    ```

3. Create output directory:
    ```bash
    mkdir -p output
    ```

4. Run the solver:
    ```bash
    python main.py
    ```

### Configuration

By default, the code runs **Poetiq(Gemini-3-a)** with 1 expert. To use other configurations, edit `arc_agi/config.py`:

- **Poetiq(Gemini-3-a)**: `NUM_EXPERTS = 1` (default, fastest)
- **Poetiq(Gemini-3-b)**: `NUM_EXPERTS = 2` (better accuracy)
- **Poetiq(Gemini-3-c)**: `NUM_EXPERTS = 8` (best accuracy, slowest)

To customize which problems to solve, edit `main.py`:
- `NUM_PROBLEMS`: Number of problems to solve (None = all)
- `SELECTED_PROBLEMS`: List of specific problem IDs to solve
- `DATA_CHALLENGES`: Path to challenge dataset (ARC-AGI-1 or ARC-AGI-2)

For detailed setup instructions, troubleshooting, and advanced usage, see **[SETUP_GUIDE.md](SETUP_GUIDE.md)**.

## 📄 Contact
If you use this code or these results in your research, please cite our blog post:

Poetiq Team. (2025). *Traversing the Frontier of Superintelligence*. Poetiq AI. [https://poetiq.ai/posts/arcagi_announcement/](https://poetiq.ai/posts/arcagi_announcement/)

For questions or to discuss the future of reasoning, reach out to us at poetiq@poetiq.ai.

[![X (formerly Twitter)](https://img.shields.io/badge/X-000000?style=for-the-badge&logo=x&logoColor=white)](https://x.com/poetiq_ai)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/company/poetiq/)
[![Bluesky](https://img.shields.io/badge/Bluesky-0285FF?style=for-the-badge&logo=Bluesky&logoColor=white)](https://bsky.app/profile/poetiq-ai.bsky.social)
