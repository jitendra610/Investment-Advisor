from pathlib import Path
from typing import Any

import yaml


class PromptManager:

    def __init__(self):
        self.base_path = Path(__file__).resolve().parent
        self.versions_path = self.base_path / "versions"
        self.active_versions_path = self.base_path / "active_versions.yaml"

        self.active_versions = self._load_active_versions()

    def _load_yaml(self, file_path: Path) -> dict[str, Any]:
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")

        with file_path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid YAML prompt file: {file_path}")

        return data

    def _load_active_versions(self) -> dict[str, str]:
        return self._load_yaml(self.active_versions_path)

    def get_prompt(
        self,
        agent_name: str,
        version: str | None = None
    ) -> dict[str, Any]:

        selected_version = version or self.active_versions.get(agent_name)

        if not selected_version:
            raise ValueError(
                f"No active prompt version configured for {agent_name}"
            )

        prompt_file = (
            self.versions_path
            / agent_name
            / f"{selected_version}.yaml"
        )

        prompt_data = self._load_yaml(prompt_file)

        if prompt_data.get("name") != agent_name:
            raise ValueError("Agent name does not match prompt metadata.")

        if prompt_data.get("version") != selected_version:
            raise ValueError("Prompt version does not match file selection.")

        return prompt_data

    def render_prompt(
        self,
        agent_name: str,
        prompt_type: str,
        version: str | None = None,
        **variables
    ) -> str:

        prompt_data = self.get_prompt(agent_name, version)

        if prompt_type not in ("system_prompt", "human_prompt"):
            raise ValueError(f"Unsupported prompt type: {prompt_type}")

        template = prompt_data.get(prompt_type)

        if not isinstance(template, str):
            raise ValueError(f"Missing or invalid {prompt_type}")

        try:
            return template.format(**variables)
        except KeyError as exc:
            raise ValueError(
                f"Missing prompt variable: {exc.args[0]}"
            ) from exc


prompt_manager = PromptManager()