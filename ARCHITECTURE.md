# Poetiq ARC-AGI Solver - Architecture Documentation

This document explains how the Poetiq ARC-AGI solver works internally.

## Overview

The Poetiq solver uses an **iterative code generation and refinement** approach with **multi-expert ensemble voting** to solve ARC-AGI tasks. The key innovation is using LLMs to generate Python code that transforms input grids to output grids, with feedback loops to improve solutions.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                             │
│  - Loads challenges and solutions                           │
│  - Orchestrates parallel problem solving                    │
│  - Scores results and generates submission                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                       solve.py                              │
│  - Entry point for solving a single problem                 │
│  - Delegates to solve_parallel_coding                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 solve_parallel_coding.py                    │
│  - Runs N expert solvers in parallel                        │
│  - Collects all expert solutions                            │
│  - Groups solutions by identical outputs                    │
│  - Ranks solutions using ensemble voting                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼ (for each expert)
┌─────────────────────────────────────────────────────────────┐
│                    solve_coding.py                          │
│  - Single expert solver with iterative refinement           │
│  - Generates code using LLM                                 │
│  - Tests code in sandbox                                    │
│  - Builds feedback from failures                            │
│  - Refines solution in next iteration                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌──────────────┐              ┌──────────────┐
│    llm.py    │              │  sandbox.py  │
│ - API calls  │              │ - Executes   │
│ - Rate       │              │   code in    │
│   limiting   │              │   subprocess │
│ - Retries    │              │ - Timeout    │
└──────────────┘              └──────────────┘
```

## Core Components

### 1. Main Orchestrator (`main.py`)

**Purpose:** Top-level script that runs the entire evaluation.

**Key responsibilities:**
- Load challenge and solution datasets
- Run problems in parallel using `asyncio`
- Collect and score results
- Write outputs incrementally
- Generate final submission file

**Key features:**
- Problems run concurrently for efficiency
- Results are written after each problem (crash-resilient)
- Optional scoring if ground truth is available
- Configurable problem selection

### 2. Parallel Expert Solver (`solve_parallel_coding.py`)

**Purpose:** Run multiple expert solvers in parallel and combine their outputs using ensemble voting.

**Algorithm:**
1. Launch N expert solvers concurrently (N = NUM_EXPERTS)
2. Wait for all experts to complete
3. Group solutions by identical test outputs (canonical key)
4. Separate passing solutions (all training examples correct) from failing ones
5. Rank solutions using voting strategy:
   - **Diversity-first:** One solution from each unique output
   - **Vote-weighted:** More experts agreeing = higher rank
   - **Iteration-aware:** Optional tiebreaking by iteration count
   - **Soft-score fallback:** For failing solutions, use pixel-wise accuracy

**Output:** Ordered list of solutions, best first

### 3. Single Expert Solver (`solve_coding.py`)

**Purpose:** Iteratively generate and refine code solutions for a single problem.

**Algorithm:**
```
Initialize: empty solution list, iteration = 0

For iteration in range(max_iterations):
    1. Format problem as text with examples
    2. Build prompt with solver instructions
    3. If previous solutions exist:
       - Sample solutions with selection_probability
       - Add feedback about their failures to prompt
    4. Call LLM to generate code
    5. Parse code from LLM response
    6. Run code on training examples in sandbox
    7. If all training examples pass:
       - Return solution immediately (SUCCESS)
    8. Otherwise:
       - Generate detailed feedback about failures
       - Add solution to solution list with feedback and score
       - Continue to next iteration

If no solution found after max_iterations:
    - Return best solution (if return_best_result=True)
    - Or return last attempted solution
```

**Key features:**
- **Iterative refinement:** Each iteration learns from previous failures
- **Feedback generation:** Detailed error messages and pixel-wise diffs
- **Solution selection:** Randomly samples past solutions to show LLM
- **Early stopping:** Returns immediately on success
- **Best result tracking:** Can return best partial solution if no perfect solution found

### 4. LLM Interface (`llm.py`)

**Purpose:** Handle API calls to various LLM providers.

**Key features:**
- **Multi-provider support:** Uses litellm to support Gemini, OpenAI, Anthropic, xAI, Groq
- **Rate limiting:** Per-model rate limiters prevent API throttling
- **Retry logic:** Automatic retries with exponential backoff
- **Timeout management:** Configurable request timeouts
- **Budget tracking:** Tracks total time and timeout counts per problem
- **Extended thinking:** Enables extended thinking modes for supported models (Claude, Gemini)

### 5. Sandbox Executor (`sandbox.py`)

**Purpose:** Safely execute untrusted LLM-generated code.

**Key features:**
- **Subprocess isolation:** Code runs in separate Python subprocess
- **Timeout protection:** Kills process if execution exceeds timeout
- **JSON I/O:** Input/output via JSON for clean serialization
- **Error capture:** Returns both stdout and stderr
- **Environment control:** Sets PYTHONHASHSEED for reproducibility

**Security:**
- Code runs in temporary directory
- Limited to Python standard library + numpy + scipy
- Process-level isolation
- Timeout enforcement

### 6. Prompts (`prompts.py`)

**Three prompt strategies:**

**SOLVER_PROMPT_1:** Basic prompt
- Concise instructions
- Simple examples
- Focus on analysis and implementation

**SOLVER_PROMPT_2:** Detailed expert prompt
- "World-class expert" framing
- Iterative process guidance
- Mentions cv2/OpenCV availability
- Emphasis on not giving up

**SOLVER_PROMPT_3:** Example-rich prompt
- Multiple worked examples
- More concrete guidance
- Shows diversity of transformation types

**FEEDBACK_PROMPT:** Provides context for previous solutions
- Shows code, evaluation, and score for each past solution
- Encourages learning from mistakes

### 7. Voting and Ranking (`solve_parallel_coding.py`)

**Ensemble voting algorithm:**

1. **Grouping by output:**
   - Solutions with identical test outputs are grouped together
   - Groups act as "votes" for that output

2. **Passing vs. Failing:**
   - Passing: All training examples solved correctly
   - Failing: At least one training example incorrect

3. **Ranking strategy (use_new_voting=True):**
   ```
   Passers (ranked by votes, diversity-first):
   - Group 1 (10 votes): solution_1a, solution_1b, ...
   - Group 2 (3 votes):  solution_2a, solution_2b, ...
   - Group 3 (1 vote):   solution_3a

   Failers (ranked by votes & soft-score):
   - Group A (5 votes):  solution_Aa (best soft), solution_Ab, ...
   - Group B (2 votes):  solution_Ba (best soft), solution_Bb, ...

   Final ranking:
   [1a, 2a, 3a,           # One from each passer group (diversity)
    Aa, Ba,               # One from each failer group (diversity)
    1b, 1c, ...,          # Remaining from passer groups
    Ab, Ac, ...]          # Remaining from failer groups
   ```

4. **Tiebreaking (optional):**
   - `iters_tiebreak=True`: Break ties by iteration count
   - `low_to_high_iters=True`: Prefer lower iterations (simpler solutions)

## Data Flow

### For a Single Problem:

```
Input: train_in, train_out, test_in
  │
  ├─> Expert 1 (async)
  │     └─> Iteration 1: LLM → code → sandbox → feedback
  │     └─> Iteration 2: LLM + feedback → code → sandbox → feedback
  │     └─> ...
  │     └─> Result: {train_results, test_results, iteration}
  │
  ├─> Expert 2 (async)
  │     └─> Iteration 1: ...
  │     └─> ...
  │
  └─> Expert N (async)
        └─> ...

All experts complete
  │
  ▼
Voting & Ranking
  │
  ▼
Ordered list of solutions
  │
  ▼
Top 2 test outputs → Kaggle submission format
```

## Configuration System

### Config Structure (`arc_agi/config.py`)

```python
CONFIG_LIST = [
  {
    # Prompts
    'solver_prompt': SOLVER_PROMPT_1,
    'feedback_prompt': FEEDBACK_PROMPT,

    # LLM parameters
    'llm_id': 'gemini/gemini-3-pro-preview',
    'solver_temperature': 1.0,
    'request_timeout': 3600,
    'max_total_timeouts': 15,
    'max_total_time': None,
    'per_iteration_retries': 2,

    # Solver parameters
    'num_experts': 1,
    'max_iterations': 10,
    'max_solutions': 5,
    'selection_probability': 1.0,
    'seed': 0,
    'shuffle_examples': True,
    'improving_order': True,
    'return_best_result': True,
    'timeout_s': 5.0,

    # Voting parameters
    'use_new_voting': True,
    'count_failed_matches': True,
    'iters_tiebreak': False,
    'low_to_high_iters': False,
  },
] * NUM_EXPERTS
```

### Key Parameters:

- **max_iterations:** How many attempts per expert (default: 10)
- **max_solutions:** How many past solutions to show as feedback (default: 5)
- **selection_probability:** Probability of including each past solution (default: 1.0)
- **shuffle_examples:** Randomize order of training examples (default: True)
- **improving_order:** Show feedback in worst→best order (default: True)
- **return_best_result:** Return best partial solution if no perfect solution found
- **use_new_voting:** Use diversity-first ensemble voting (default: True)
- **count_failed_matches:** Include failers in voting if outputs match passers

## Performance Optimizations

1. **Parallel execution:**
   - Problems run concurrently
   - Experts run concurrently
   - Limited only by rate limits

2. **Rate limiting:**
   - Per-model rate limiters prevent API throttling
   - Configured for each provider's limits

3. **Early termination:**
   - Expert stops immediately when perfect solution found
   - Experts can stop early if budget exhausted

4. **Incremental output:**
   - Results written after each problem
   - Crash-resilient

5. **Resource management:**
   - File handle limits raised
   - Temporary directories cleaned up
   - Processes properly killed on timeout

## Scoring System

### Per-Task Scoring:

- A task has multiple test inputs (usually 1-3)
- For each test input, we have 2 attempts
- Task is correct if ANY attempt matches ground truth for EVERY test input
- Score = (# test inputs correct) / (# total test inputs)
- Perfect score: 1.0 (all test inputs correct)

### Soft Scoring (for training feedback):

- Used to rank imperfect solutions
- Pixel-wise accuracy: (# correct pixels) / (# total pixels)
- Only counts if output shape matches expected shape
- Used for generating feedback and ranking failing solutions

## Example: Solving One Problem with 3 Experts

```
Problem: "b7999b51"
  train_in: [3 examples]
  train_out: [3 examples]
  test_in: [2 challenges]

┌─────────────────────────────────────────────────┐
│               Expert 1 (seed=0)                 │
├─────────────────────────────────────────────────┤
│ Iteration 1: Generate code → Test → Fail (0.6) │
│ Iteration 2: Refine → Test → Fail (0.8)        │
│ Iteration 3: Refine → Test → SUCCESS ✓         │
│ Result: Passing, iteration=3                    │
│ Test outputs: [[[1,2]], [[3,4]]]               │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│               Expert 2 (seed=10)                │
├─────────────────────────────────────────────────┤
│ Iteration 1: Generate code → Test → Fail (0.7) │
│ Iteration 2: Refine → Test → SUCCESS ✓         │
│ Result: Passing, iteration=2                    │
│ Test outputs: [[[1,2]], [[3,4]]]               │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│               Expert 3 (seed=20)                │
├─────────────────────────────────────────────────┤
│ Iteration 1: Generate code → Test → Fail (0.5) │
│ Iteration 2: Refine → Test → Fail (0.7)        │
│ ...                                             │
│ Iteration 10: Refine → Test → Fail (0.9)       │
│ Result: Failing, best_score=0.9, iteration=10  │
│ Test outputs: [[[5,6]], [[7,8]]]               │
└─────────────────────────────────────────────────┘

Voting:
  Group A: [[[1,2]], [[3,4]]] - 2 votes (Experts 1, 2) ← WINNER
  Group B: [[[5,6]], [[7,8]]] - 1 vote (Expert 3, failing)

Ranked results:
  1. Expert 1 (Group A representative)
  2. Expert 2 (Group A member)
  3. Expert 3 (Group B representative)

Final submission for this problem:
  attempt_1: [[1,2]]  (test input 1, from Expert 1)
  attempt_2: [[1,2]]  (test input 1, from Expert 2)

  attempt_1: [[3,4]]  (test input 2, from Expert 1)
  attempt_2: [[3,4]]  (test input 2, from Expert 2)
```

## Reproducibility

The solver includes several mechanisms for reproducibility:

1. **Seed management:**
   - Each expert gets a unique seed offset
   - Each iteration adds to the seed
   - Ensures different random choices across experts and iterations

2. **Example shuffling:**
   - Training examples shuffled per iteration (if enabled)
   - Uses seeded random generator

3. **Temperature:**
   - Default: 1.0 (creative)
   - Can be adjusted for more deterministic output

4. **Environment:**
   - PYTHONHASHSEED set to 0 in sandbox

Note: LLM outputs are inherently non-deterministic, so exact reproduction requires the same model version and may still vary.

## Extending the Solver

### Adding a New Model:

1. Add model to `types.py`:
   ```python
   Models = Literal[
       ...,
       "provider/model-name",
   ]
   ```

2. Add rate limiter in `llm.py`:
   ```python
   limiters: dict[Models, Limiter] = {
       ...,
       "provider/model-name": Limiter(1.0),
   }
   ```

3. Add model props (if needed):
   ```python
   props: dict[Models, dict] = {
       ...,
       "provider/model-name": {"custom_param": value},
   }
   ```

4. Update config to use new model:
   ```python
   'llm_id': 'provider/model-name',
   ```

### Adding a New Prompt Strategy:

1. Add prompt to `prompts.py`:
   ```python
   MY_CUSTOM_PROMPT = '''
   [Your prompt here with $$problem$$ placeholder]
   '''
   ```

2. Update config:
   ```python
   'solver_prompt': MY_CUSTOM_PROMPT,
   ```

### Modifying Voting Strategy:

Edit `solve_parallel_coding.py`, particularly the ranking logic in the `solve_parallel_coding` function after line 82.

## Debugging Tips

1. **Enable verbose logging:**
   - Add print statements in `solve_coding.py`
   - Log LLM responses, code, and errors

2. **Test with single problem:**
   ```python
   NUM_PROBLEMS = 1
   SELECTED_PROBLEMS = ['problem_id_here']
   ```

3. **Reduce complexity:**
   ```python
   NUM_EXPERTS = 1
   'max_iterations': 3
   ```

4. **Check intermediate outputs:**
   - Inspect `output/config_*.json` for actual config used
   - Check `output/submission_*.json` for intermediate results

5. **Sandbox debugging:**
   - Modify `sandbox.py` to keep temp files
   - Add print statements to generated scripts

## Performance Characteristics

**Typical timings (per problem):**
- Simple problem: 30-60 seconds (1 expert, 1-2 iterations)
- Medium problem: 1-3 minutes (1 expert, 3-5 iterations)
- Hard problem: 5-10 minutes (1 expert, max iterations)
- With 8 experts: 8x parallel, same wall time (if API allows)

**API costs (approximate):**
- Gemini: Most cost-effective for large-scale runs
- OpenAI: Higher cost but sometimes better quality
- Varies significantly by problem complexity and iteration count

**Memory usage:**
- ~100-500 MB per expert
- Scales with number of concurrent problems
- Most memory used by LLM response caching

## References

- **Blog post:** https://poetiq.ai/posts/arcagi_announcement/
- **ARC-AGI:** https://arcprize.org/
- **LiteLLM:** https://github.com/BerriAI/litellm
