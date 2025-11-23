# Poetiq: SOTA Reasoning on ARC-AGI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![ARC-AGI](https://img.shields.io/badge/Task-ARC--AGI-red)](https://arcprize.org/)

This repository contains:

1. **ARC-AGI Solver**: Reproduction of **Poetiq's** record-breaking submission to the ARC-AGI-1 and ARC-AGI-2 benchmarks
2. **Persona Simulation Framework**: Multi-agent AI system for optimizing customer communication strategies through conversational simulations

Full analysis of ARC-AGI results is available in our launch post, **[Traversing the Frontier of Superintelligence](https://poetiq.ai/posts/arcagi_announcement/)**.

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

### Quick Start

1. Setup the environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Create a .env file in the root directory. You must include keys for the models you intend to run.

    ```bash
    GEMINI_API_KEY=...
    OPENAI_API_KEY=...
    ```

3. Modify the constants in main.py to set the problem set, number of problems, etc. Then run the script:

    ```bash
    python main.py
    ```

4. By default, the code runs the Poetiq 3 config described in the blog post. You can uncomment other ones or modify the config in config.py

---

## 🎭 Persona Simulation Framework

A sophisticated multi-agent simulation system for optimizing customer communication strategies through AI-powered conversational simulations.

### Features

- **Multi-Agent Simulations**: Interviewer and interviewee agents engage in realistic conversations
- **Multiple Agent Types**: Simple agents with RAG, or Computer Use agents with tool access
- **Computer Use Capabilities**: Agents can browse files, search code, and gather real-time information
- **Persona System**: Define detailed customer personas with backgrounds, goals, pain points, and communication styles
- **Communication Strategies**: Define and optimize how to explain your product to different audiences
- **Knowledge Base Integration**: RAG system for providing context-aware responses
- **LLM-as-a-Judge Evaluation**: Comprehensive scoring of conversation quality and effectiveness
- **DSPy Optimization**: Iteratively improve strategies based on evaluation feedback
- **Batch Processing**: Run simulations across multiple personas efficiently
- **Extensible Architecture**: Factory pattern for custom agent implementations

### Quick Start (Persona Simulation)

```bash
# Navigate to the persona_sim directory
cd persona_sim

# Run a basic simulation
python -m persona_sim.orchestrator.cli simulate \
  --personas examples/personas.yaml \
  --strategy examples/strategy.yaml \
  --product-name "Your Product" \
  --product-description "What your product does" \
  --max-turns 20

# Optimize a strategy
python -m persona_sim.orchestrator.cli optimize \
  --personas examples/personas.yaml \
  --strategy examples/strategy.yaml \
  --product-name "Your Product" \
  --product-description "What your product does" \
  --iterations 5 \
  --output-strategy ./optimized_strategy.yaml
```

### Programmatic Usage

```python
from persona_sim import PersonaSimulator, Persona, CommunicationStrategy

# Create simulator
simulator = PersonaSimulator(
    product_name="Your Product",
    product_description="What it does",
)

# Run simulation
result = simulator.run_simulation(
    strategy=your_strategy,
    persona=your_persona,
    max_turns=20,
)

# Access results
print(f"Interviewer score: {result.interviewer_eval.overall_score}")
print(f"Understanding score: {result.interviewee_eval.questionnaire_score}")
```

### Documentation

For comprehensive documentation, see [persona_sim/README.md](persona_sim/README.md).

Example configurations are available in [persona_sim/examples/](persona_sim/examples/).

### Use Cases

- **UX Research**: Scale user research by simulating conversations with diverse personas
- **Sales Optimization**: Refine sales pitches for different customer segments
- **Product Messaging**: Test how different audiences understand your product
- **Training**: Develop better onboarding and training materials
- **Market Research**: Understand perception across different user types

---

## 📄 Contact
If you use this code or these results in your research, please cite our blog post:

Poetiq Team. (2025). *Traversing the Frontier of Superintelligence*. Poetiq AI. [https://poetiq.ai/posts/arcagi_announcement/](https://poetiq.ai/posts/arcagi_announcement/)

For questions or to discuss the future of reasoning, reach out to us at poetiq@poetiq.ai.

[![X (formerly Twitter)](https://img.shields.io/badge/X-000000?style=for-the-badge&logo=x&logoColor=white)](https://x.com/poetiq_ai)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/company/poetiq/)
[![Bluesky](https://img.shields.io/badge/Bluesky-0285FF?style=for-the-badge&logo=Bluesky&logoColor=white)](https://bsky.app/profile/poetiq-ai.bsky.social)
