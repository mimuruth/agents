### **Using `trace()` with OpenAI**

The OpenAI Agents SDK provides a built-in `trace()` function for monitoring and debugging your AI agent workflows.

---

### **What tracing does**

Tracing captures a detailed record of events occurring within your agent's execution, including LLM generations, tool calls, handoffs, and guardrails. This information can be visualized in the OpenAI Traces dashboard to help you identify performance bottlenecks, diagnose issues like inaccurate tool calls, or understand the agent's decision-making process.

---

### **How to use `trace()`**

The `trace()` function can be used in two main ways:

---

#### 1. **Context Manager (Recommended)**  
Wrap the agent's execution within a `with trace(...)` block. This automatically handles starting and ending the trace.

```python
from agents import Agent, Runner, trace

async def main():
    agent = Agent(name="Joke generator", instructions="Tell funny jokes.")
    with trace("Joke workflow"): 
        first_result = await Runner.run(agent, "Tell me a joke")
        second_result = await Runner.run(agent, f"Rate this joke: {first_result.final_output}")
        print(f"Joke: {first_result.final_output}")
        print(f"Rating: {second_result.final_output}")
```

---

#### 2. **Manual Start/Stop**  
You can manually call `trace.start()` and `trace.finish()` to define the trace boundaries. Note that if you manually manage the trace, you'll need to pass `mark_as_current=True` and `reset_current=True` to `start()` and `finish()` respectively to update the current trace.

```python
from agents import Agent, Runner, trace

async def main():
    agent = Agent(name="Joke generator", instructions="Tell funny jokes.")
    t = trace.start("Joke workflow", mark_as_current=True)
    try:
        first_result = await Runner.run(agent, "Tell me a joke")
        second_result = await Runner.run(agent, f"Rate this joke: {first_result.final_output}")
        print(f"Joke: {first_result.final_output}")
        print(f"Rating: {second_result.final_output}")
    finally:
        trace.finish(reset_current=True)
```

---

### ✅ Tips

- Always prefer the context manager approach for simpler, safer tracing.
- Use descriptive trace names for easier debugging in the OpenAI dashboard.
