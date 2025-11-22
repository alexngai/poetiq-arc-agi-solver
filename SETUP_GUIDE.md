# Poetiq ARC-AGI Solver - Complete Setup Guide

This guide will help you set up and run the Poetiq ARC-AGI solver to reproduce the state-of-the-art results on the ARC-AGI-1 and ARC-AGI-2 benchmarks.

## Prerequisites

- **Python 3.11 or higher** (Python 3.11, 3.12, or 3.13 recommended)
- **API Keys** for at least one LLM provider (see below)
- **8GB+ RAM** recommended
- **Stable internet connection** for API calls

## Quick Setup

### Option 1: Automated Setup (Recommended)

Run the provided setup script:

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Create a `.env` file from the template
- Set up the output directory

After running the script:
1. Edit `.env` and add your API keys (see API Keys section below)
2. Activate the virtual environment: `source .venv/bin/activate`
3. Run the solver: `python main.py`

### Option 2: Manual Setup

1. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

4. **Create output directory:**
   ```bash
   mkdir -p output
   ```

## API Keys

The solver supports multiple LLM providers. You need at least one API key for the model you want to use.

### Gemini (Google) - Recommended for SOTA Results

The Poetiq team achieved their best results using Gemini models.

1. Get your API key at: https://aistudio.google.com/apikey
2. Add to `.env`:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

### Other Supported Providers

**OpenAI (GPT-5, GPT-5.1):**
- Get key at: https://platform.openai.com/api-keys
- Add to `.env`: `OPENAI_API_KEY=your_key_here`

**Anthropic (Claude Sonnet 4.5, Claude Haiku 4.5):**
- Get key at: https://console.anthropic.com/
- Add to `.env`: `ANTHROPIC_API_KEY=your_key_here`

**xAI (Grok-4, Grok-4-Fast):**
- Get key at: https://console.x.ai/
- Add to `.env`: `XAI_API_KEY=your_key_here`

**Groq:**
- Get key at: https://console.groq.com/
- Add to `.env`: `GROQ_API_KEY=your_key_here`

## Configuration

The solver is configured in `arc_agi/config.py`. By default, it runs the **Poetiq(Gemini-3-a)** configuration with 1 expert.

### Available Configurations

Edit `arc_agi/config.py` to switch between configurations:

```python
# Poetiq(Gemini-3-a) - Default, fastest
NUM_EXPERTS = 1

# Poetiq(Gemini-3-b) - Better accuracy
# NUM_EXPERTS = 2

# Poetiq(Gemini-3-c) - Best accuracy, slowest
# NUM_EXPERTS = 8
```

### Main Configuration Parameters

In the `CONFIG_LIST` in `config.py`:

- **`llm_id`**: Which model to use (default: `'gemini/gemini-3-pro-preview'`)
- **`max_iterations`**: Number of solution attempts per problem (default: 10)
- **`solver_temperature`**: LLM temperature for creativity (default: 1.0)
- **`max_solutions`**: Number of previous solutions to show as feedback (default: 5)
- **`timeout_s`**: Timeout for code execution in seconds (default: 5.0)
- **`request_timeout`**: Timeout for LLM API calls (default: 3600 seconds)

### Customizing the Run

Edit `main.py` to customize what gets evaluated:

```python
# Choose dataset
DATA_CHALLENGES = os.path.join(os.path.dirname(__file__), "data", "arc-prize-2024", "arc-agi_evaluation_challenges.json")
# Or use ARC-AGI-2:
# DATA_CHALLENGES = os.path.join(os.path.dirname(__file__), "data", "arc-prize-2025", "arc-agi_evaluation_challenges.json")

# Number of problems to solve (None = all)
NUM_PROBLEMS = None

# Select specific problems by ID
SELECTED_PROBLEMS = []  # e.g. ['b7999b51', 'a1b2c3d4']
```

## Running the Solver

1. **Activate the virtual environment** (if not already active):
   ```bash
   source .venv/bin/activate
   ```

2. **Run the solver:**
   ```bash
   python main.py
   ```

3. **Monitor progress:**
   - The solver will print progress for each problem
   - ✓ indicates a correctly solved problem
   - ✗ indicates an incorrect solution
   - The solver runs problems in parallel for efficiency

4. **View results:**
   - Results are saved to `output/submission_<timestamp>.json`
   - Configuration is saved to `output/config_<timestamp>.json`
   - Final accuracy is printed at the end

## Understanding the Output

### Console Output

```
✓ b7999b51 (45s) [1/1]    # Solved correctly in 45 seconds
✗ a1b2c3d4 (120s) [1/2]   # Failed, 1 correct out of 2 total
```

### Output Files

**`output/submission_<timestamp>.json`:**
- Kaggle-format submission file
- Contains 2 attempts per test input
- Can be submitted to the ARC Prize competition

**`output/config_<timestamp>.json`:**
- Complete configuration used for this run
- Useful for reproducing results

## Testing the Setup

To verify everything is working, run a small test:

1. Edit `main.py` and set:
   ```python
   NUM_PROBLEMS = 1
   ```

2. Run:
   ```bash
   python main.py
   ```

3. You should see the solver attempt one problem and generate output.

## Troubleshooting

### "Module not found" errors

Make sure you've activated the virtual environment:
```bash
source .venv/bin/activate
```

### API Key errors

- Verify your API keys are correctly set in `.env`
- Check that the key is for the correct provider
- Ensure there are no extra spaces or quotes around the key

### Rate limiting

If you get rate limit errors:
- The solver has built-in rate limiters, but provider limits may still apply
- Consider reducing `NUM_PROBLEMS` or `NUM_EXPERTS`
- Wait a few minutes and try again

### Timeout errors

If problems timeout frequently:
- Increase `timeout_s` in `config.py` for longer-running code
- Increase `request_timeout` for slower LLM responses
- Increase `max_total_timeouts` to allow more timeouts per problem

### Memory issues

If you run out of memory:
- Reduce `NUM_EXPERTS` in `config.py`
- Reduce the number of parallel problems by setting `NUM_PROBLEMS` to a smaller value
- Close other applications

## Performance Tips

1. **Start small:** Test with `NUM_PROBLEMS = 5` before running on full dataset
2. **Use caching:** Results are written incrementally, so you can resume if interrupted
3. **Monitor costs:** Track API usage, especially with multiple experts
4. **Optimize for your goal:**
   - For speed: Use `NUM_EXPERTS = 1`
   - For accuracy: Use `NUM_EXPERTS = 8`
   - For balance: Use `NUM_EXPERTS = 2`

## Advanced Usage

### Using Different Prompts

The solver includes three different prompt strategies in `arc_agi/prompts.py`:
- `SOLVER_PROMPT_1`: Basic prompt
- `SOLVER_PROMPT_2`: More detailed, world-class expert prompt
- `SOLVER_PROMPT_3`: Includes multiple examples

Change in `config.py`:
```python
'solver_prompt': SOLVER_PROMPT_2,  # or SOLVER_PROMPT_3
```

### Switching Models

To use a different model, edit `config.py`:

```python
# For OpenAI GPT-5
'llm_id': 'openai/gpt-5',

# For Claude Sonnet
'llm_id': 'anthropic/claude-sonnet-4-5',

# For Grok-4
'llm_id': 'xai/grok-4',
```

### Running on Different Datasets

The repository includes both ARC-AGI-1 (2024) and ARC-AGI-2 (2025) datasets:

```python
# ARC-AGI-1 (2024)
DATA_CHALLENGES = os.path.join(os.path.dirname(__file__), "data", "arc-prize-2024", "arc-agi_evaluation_challenges.json")
DATA_SOLUTIONS = os.path.join(os.path.dirname(__file__), "data", "arc-prize-2024", "arc-agi_evaluation_solutions.json")

# ARC-AGI-2 (2025)
DATA_CHALLENGES = os.path.join(os.path.dirname(__file__), "data", "arc-prize-2025", "arc-agi_evaluation_challenges.json")
DATA_SOLUTIONS = os.path.join(os.path.dirname(__file__), "data", "arc-prize-2025", "arc-agi_evaluation_solutions.json")

# Training set (for development)
DATA_CHALLENGES = os.path.join(os.path.dirname(__file__), "data", "arc-prize-2024", "arc-agi_training_challenges.json")
DATA_SOLUTIONS = os.path.join(os.path.dirname(__file__), "data", "arc-prize-2024", "arc-agi_training_solutions.json")
```

## Contributing

If you find issues or have improvements:
1. Check existing issues on GitHub
2. Test your changes thoroughly
3. Submit a pull request with a clear description

## Citation

If you use this code in your research, please cite the Poetiq blog post:

```
Poetiq Team. (2025). Traversing the Frontier of Superintelligence.
Poetiq AI. https://poetiq.ai/posts/arcagi_announcement/
```

## Support

- **Questions:** poetiq@poetiq.ai
- **Blog post:** https://poetiq.ai/posts/arcagi_announcement/
- **Twitter/X:** https://x.com/poetiq_ai
- **LinkedIn:** https://www.linkedin.com/company/poetiq/
- **Bluesky:** https://bsky.app/profile/poetiq-ai.bsky.social

## License

MIT License - see LICENSE file for details
