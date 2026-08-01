"""Resolve the complete system instruction from user-visible Chinese prompt parts."""

from mv_platform.application.prompt_catalog import (
    DEFAULT_PROMPTS, DEFAULT_SYSTEM_PROMPTS, SYSTEM_PREFIX,
)


def resolved_prompt(step_id, overrides=None):
    overrides = overrides or {}
    system_prompt = overrides.get(
        SYSTEM_PREFIX + step_id, DEFAULT_SYSTEM_PROMPTS[step_id]
    )
    task_prompt = overrides.get(step_id, DEFAULT_PROMPTS[step_id])
    return system_prompt.strip() + "\n\n本步骤任务要求：\n" + task_prompt.strip()


def resolved_prompt_parts(step_id, overrides=None):
    overrides = overrides or {}
    return {
        "system_prompt": overrides.get(
            SYSTEM_PREFIX + step_id, DEFAULT_SYSTEM_PROMPTS[step_id]
        ).strip(),
        "task_prompt": overrides.get(step_id, DEFAULT_PROMPTS[step_id]).strip(),
    }
