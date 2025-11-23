# Persona Simulation Framework

A sophisticated multi-agent simulation system for optimizing customer communication strategies through AI-powered conversational simulations.

## Overview

This framework allows you to:

1. **Simulate realistic customer conversations** with different personas
2. **Evaluate communication effectiveness** using LLM-as-a-judge
3. **Optimize communication strategies** iteratively using DSPy
4. **Scale UX research** by testing strategies across many personas automatically

## Architecture

The framework consists of several interconnected components:

```
┌─────────────────────────────────────────────────────────────┐
│                    Persona Simulation                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │ Interviewer  │◄───────►│ Interviewee  │                 │
│  │    Agent     │         │    Agent     │                 │
│  └──────┬───────┘         └──────┬───────┘                 │
│         │                        │                          │
│         │  ┌──────────────────┐  │                          │
│         └─►│  Conversation    │◄─┘                          │
│            │     Engine       │                             │
│            └────────┬─────────┘                             │
│                     │                                        │
│         ┌───────────▼──────────────┐                        │
│         │  Knowledge Base (RAG)    │                        │
│         └──────────────────────────┘                        │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                     Evaluation System                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐      ┌─────────────────────┐         │
│  │  Questionnaire   │      │  LLM-as-a-Judge     │         │
│  │    Generator     │      │    Evaluator        │         │
│  └──────────────────┘      └─────────────────────┘         │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                  Optimization Framework                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────┐           │
│  │         DSPy Strategy Optimizer              │           │
│  │  (Iterative improvement based on feedback)   │           │
│  └──────────────────────────────────────────────┘           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Models (`models/`)
- **Data schemas** using Pydantic for type safety
- Personas, strategies, conversations, evaluations
- All models are serializable for storage and analysis

### 2. Agents (`agents/`)
- **InterviewerAgent** (Simple): Explains the product and follows a communication strategy
- **ComputerUseInterviewerAgent**: Enhanced agent with tool access for browsing docs, searching code, etc.
- **IntervieweeAgent**: Maintains a persona and responds authentically
- **AgentFactory**: Factory pattern for creating different agent types
- All agents use Claude via the Anthropic API

#### Agent Types

The framework supports multiple interviewer agent types:

1. **Simple Agent** (`agent_type="simple"`):
   - Basic agent with knowledge base (RAG) access
   - Good for general conversations
   - Lower latency, fewer API calls

2. **Computer Use Agent** (`agent_type="computer_use"`):
   - Enhanced agent with tool capabilities
   - Can browse files, search code, run safe commands
   - Perfect for technical conversations requiring specific details
   - Tools available:
     - `read_file`: Read documentation or code files
     - `list_directory`: Explore directory structure
     - `search_files`: Find files by name pattern
     - `search_code`: Search for code patterns using grep
     - `run_command`: Run safe read-only commands

3. **Custom Agents**:
   - Register your own agent implementations via `AgentFactory.register_agent_type()`

### 3. Knowledge Base (`knowledge/`)
- **RAG system** using LangChain + ChromaDB
- Index documentation, code, and past conversations
- Provides context to interviewer agent dynamically

### 4. Conversation Engine (`conversation/`)
- **Turn-based dialogue management**
- Coordinates agent interactions
- Tracks conversation state and history

### 5. Evaluation (`evaluation/`)
- **Questionnaire generator**: Creates assessment questions
- **Questionnaire administrator**: Collects responses from agents
- **LLM-as-a-judge**: Scores interviewer strategy adherence and interviewee understanding

### 6. Optimization (`optimization/`)
- **DSPy-based optimizer**: Iteratively improves strategies
- **Feedback loop**: Uses evaluation scores to refine approach
- **Metrics tracking**: Monitor improvement over iterations

### 7. Orchestrator (`orchestrator/`)
- **PersonaSimulator**: Main simulation runner
- **CLI**: Command-line interface for easy usage

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Quick Start

### 1. Running Simulations

```bash
# Basic simulation
python -m persona_sim.orchestrator.cli simulate \
  --personas persona_sim/examples/personas.yaml \
  --strategy persona_sim/examples/strategy.yaml \
  --product-name "DevTool X" \
  --product-description "An AI-powered development tool that automates code reviews" \
  --max-turns 20 \
  --output-dir ./results

# With knowledge base
python -m persona_sim.orchestrator.cli simulate \
  --personas persona_sim/examples/personas.yaml \
  --strategy persona_sim/examples/strategy.yaml \
  --product-name "DevTool X" \
  --product-description "An AI-powered development tool" \
  --knowledge-dir ./docs \
  --max-turns 20

# With computer use agent (for technical conversations)
python -m persona_sim.orchestrator.cli simulate \
  --personas persona_sim/examples/personas.yaml \
  --strategy persona_sim/examples/strategy.yaml \
  --product-name "DevTool X" \
  --product-description "An AI-powered development tool" \
  --agent-type computer_use \
  --allowed-paths ./docs ./src \
  --max-turns 20
```

### 2. Optimizing Strategies

```bash
python -m persona_sim.orchestrator.cli optimize \
  --personas persona_sim/examples/personas.yaml \
  --strategy persona_sim/examples/strategy.yaml \
  --product-name "DevTool X" \
  --product-description "An AI-powered development tool" \
  --iterations 5 \
  --sims-per-iteration 3 \
  --output-strategy ./optimized_strategy.yaml
```

### 3. Programmatic Usage

```python
from persona_sim import (
    PersonaSimulator,
    Persona,
    CommunicationStrategy,
    build_knowledge_base,
)

# Load your personas and strategy
personas = [...]  # Load from YAML/JSON
strategy = ...     # Load from YAML/JSON

# Build knowledge base
kb = build_knowledge_base(
    source_paths=["./docs", "./transcripts"],
    persist_directory="./chroma_db",
)

# Create simulator
simulator = PersonaSimulator(
    product_name="Your Product",
    product_description="Product description",
    knowledge_base=kb,
)

# Run simulation with simple agent
result = simulator.run_simulation(
    strategy=strategy,
    persona=personas[0],
    max_turns=20,
)

# Run simulation with computer use agent
result = simulator.run_simulation(
    strategy=strategy,
    persona=personas[0],
    max_turns=20,
    interviewer_agent_type="computer_use",
    allowed_paths=["./docs", "./src"],
)

# Access results
print(f"Interviewer score: {result.interviewer_eval.overall_score}")
print(f"Understanding score: {result.interviewee_eval.questionnaire_score}")

# Save results
simulator.save_results([result], output_dir="./results")
```

## Configuration Files

### Persona Configuration (YAML/JSON)

```yaml
personas:
  - name: "Sarah Chen"
    description: "Early-stage startup founder"
    background: "Technical founder building B2B SaaS..."
    goals:
      - "Ship features faster"
      - "Reduce operational overhead"
    pain_points:
      - "Limited budget"
      - "Too many competing priorities"
    communication_style: "Direct and pragmatic"
    technical_level: "intermediate"
    key_characteristics:
      - "Time-conscious"
      - "ROI-focused"
    objections:
      - "Budget constraints"
      - "Learning curve"
    priorities:
      - "Speed to market"
      - "Cost effectiveness"
```

### Strategy Configuration (YAML/JSON)

```yaml
name: "Value-First Approach"
description: "Focus on value proposition with progressive disclosure"
approach: "Start with benefits, adapt to technical level"
key_points:
  - "Core value proposition"
  - "Concrete examples"
  - "Integration story"
dos:
  - "Listen and adapt"
  - "Use concrete examples"
  - "Address objections directly"
donts:
  - "Don't use excessive jargon"
  - "Don't oversell"
  - "Don't dismiss concerns"
target_outcomes:
  - "Clear understanding of value"
  - "Addressed main objections"
  - "Can articulate use cases"
```

## Evaluation Metrics

The framework provides comprehensive evaluation:

### Interviewer Evaluation
- **Strategy Adherence** (0-100): How well they followed the strategy
- **Clarity** (0-100): How clearly they explained concepts
- **Responsiveness** (0-100): How well they addressed questions
- **Persuasiveness** (0-100): How convincing they were
- **Engagement** (0-100): How well they maintained interest

### Interviewee Evaluation
- **Persona Adherence** (0-100): How consistently they maintained character
- **Questionnaire Score** (0-100): Quality and consistency of understanding

### Optimization Metrics
- Track improvement across iterations
- Identify best-performing strategies
- Analyze common strengths and weaknesses

## Advanced Features

### Knowledge Base Integration

The interviewer agent can access a knowledge base (RAG) containing:
- Product documentation
- Code repositories
- Past conversation transcripts
- Training materials

This enables dynamic, context-aware responses.

### DSPy Optimization

The framework uses DSPy for:
- Structured prompt optimization
- Feedback-driven strategy improvement
- Automatic refinement based on evaluation scores

### Batch Processing

Run simulations across multiple personas in parallel:

```python
results = simulator.run_batch_simulations(
    strategy=strategy,
    personas=personas,
    max_turns=20,
)
```

## Output and Results

Results are saved as JSON files containing:
- Full conversation transcripts
- Questionnaire responses
- Evaluation scores and reasoning
- Detailed feedback and suggestions

Summary statistics are also generated:
- Average scores across all simulations
- Common strengths and weaknesses
- Persona-specific insights

## Use Cases

1. **UX Research Scaling**: Test communication strategies across many personas without manual interviews

2. **Sales Training**: Optimize sales pitches for different customer segments

3. **Product Messaging**: Refine how you explain your product to different audiences

4. **Documentation Testing**: Verify that your docs effectively communicate to target personas

5. **Customer Success**: Develop better onboarding strategies for different user types

6. **Market Research**: Understand how different personas perceive your product

## Customization

### Custom Evaluation Criteria

Add your own evaluation criteria in the judge prompts.

### Custom Questionnaires

Pre-define questionnaires for consistent evaluation:

```python
from persona_sim.models import Questionnaire, QuestionnaireQuestion

custom_q = Questionnaire(
    questions=[
        QuestionnaireQuestion(
            id="q1",
            question="What are the top 3 benefits you understand?",
            category="understanding",
        ),
        # ... more questions
    ],
    product_name="Your Product",
)
```

### Computer Use Agents

The computer use agent provides enhanced capabilities for technical conversations:

**When to use:**
- Technical personas asking detailed questions
- Need to reference specific code or documentation
- Want to demonstrate actual implementation details
- Explaining complex architectural concepts

**How it works:**
The agent uses tools to:
- Browse and read files from allowed directories
- Search code repositories for specific patterns
- List directory structures
- Run safe read-only commands

**Security:**
- Restricted to allowed paths only
- Only safe read-only commands permitted
- No write operations or destructive commands
- Configurable path restrictions per simulation

**Example:**
```python
# Create simulation with computer use agent
result = simulator.run_simulation(
    strategy=technical_strategy,
    persona=engineer_persona,
    interviewer_agent_type="computer_use",
    allowed_paths=[
        "./docs",  # Documentation directory
        "./src",   # Source code directory
    ],
)
```

See `examples/computer_use_example.py` for a complete working example.

### Custom Agent Types

Register your own agent implementations:

```python
from persona_sim.agents import BaseAgent, AgentFactory

class MyCustomAgent(BaseAgent):
    def __call__(self, conversation_history, conversation, **kwargs):
        # Your custom logic
        response = "Your custom implementation"
        return response

# Register the agent type
AgentFactory.register_agent_type("my_custom", MyCustomAgent)

# Use it in simulations
result = simulator.run_simulation(
    strategy=strategy,
    persona=persona,
    interviewer_agent_type="my_custom",
)
```

## Limitations

- Requires Anthropic API access (costs scale with usage)
- Simulations are approximations, not real human behavior
- Quality depends on persona and strategy definitions
- ChromaDB requires local storage for vector database

## Best Practices

1. **Start with diverse personas** representing your actual customer segments
2. **Define clear strategies** with specific dos and don'ts
3. **Iterate based on results** - use optimization to improve
4. **Include knowledge base** for more realistic, informed conversations
5. **Run multiple simulations** per persona for consistency
6. **Review conversation transcripts** not just scores
7. **Update personas** based on real customer feedback

## Troubleshooting

### API Rate Limits
- Reduce `sims_per_iteration` or add delays
- Use lower-cost models for experimentation

### Memory Issues
- Limit `max_turns` for conversations
- Clear ChromaDB cache periodically

### Poor Evaluation Scores
- Review and refine persona definitions
- Ensure strategy has clear, actionable guidelines
- Check that knowledge base is properly indexed

## Future Enhancements

- Support for multiple LLM providers
- Real-time streaming conversations
- Web UI for easier configuration
- Integration with analytics platforms
- A/B testing framework
- Multi-turn conversation branching

## Contributing

This is a research framework. Feel free to extend and customize for your needs.

## License

MIT License (inherited from parent project)

## Support

For questions or issues, please refer to the main repository documentation.
