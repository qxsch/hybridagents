"""
Custom tools for the 05_custom_tools example.

Shows how to write tools using the @tool decorator from the SDK.
"""

import datetime
import json
import random

from agents import tool


@tool(
    name="current_time",
    description="Return the current date and time in ISO format.",
    parameters={},
)
def current_time() -> str:
    return datetime.datetime.now().isoformat()


@tool(
    name="dice_roll",
    description="Roll one or more dice. Returns the individual results and the total.",
    parameters={
        "sides": {"type": "integer", "description": "Number of sides per die (default 6)"},
        "count": {"type": "integer", "description": "Number of dice to roll (default 1)"},
    },
)
def dice_roll(sides: int = 6, count: int = 1) -> str:
    sides = int(sides)
    count = int(count)
    rolls = [random.randint(1, sides) for _ in range(count)]
    return json.dumps({"rolls": rolls, "total": sum(rolls)})


@tool(
    name="word_count",
    description="Count words, characters, and lines in the given text.",
    parameters={
        "text": {"type": "string", "description": "The text to analyse"},
    },
)
def word_count(text: str) -> str:
    lines = text.splitlines()
    words = text.split()
    return json.dumps({
        "lines": len(lines),
        "words": len(words),
        "characters": len(text),
    })
