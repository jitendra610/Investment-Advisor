from app.prompts.prompt_manager import prompt_manager

print("Testing Prompt Manager...")

system_prompt = prompt_manager.render_prompt(
    agent_name="query_analyzer",
    prompt_type="system_prompt"
)

human_prompt = prompt_manager.render_prompt(
    agent_name="query_analyzer",
    prompt_type="human_prompt",
    query="Explain my workplace pension.",
    customer_id="C1001",
    market="UK"
)

print("\nSYSTEM PROMPT:")
print(system_prompt)

print("\nHUMAN PROMPT:")
print(human_prompt)

print("\nACTIVE VERSION:")
print(prompt_manager.active_versions["query_analyzer"])

print("\nPrompt Manager test completed successfully!")