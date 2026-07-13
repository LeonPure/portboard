"""Reusable widgets for PortBoard's terminal presentation."""

from __future__ import annotations

from rich.text import Text
from textual import events
from textual.widgets import DataTable, Static

SHORTCUT_ROWS = (
    (
        "VIEW",
        (
            ("r", "Refresh"),
            ("f", "Filter"),
            ("Esc", "Clear filter"),
            ("d / Enter", "Details"),
            ("w", "Warnings"),
            ("q", "Quit"),
        ),
    ),
    ("SORT", (("p", "Project"), ("o", "Port"), ("n", "Process"))),
    (
        "SERVICE",
        (
            ("c", "Copy URL"),
            ("b", "Open URL"),
            ("x", "Stop process"),
            ("l", "LAN QR"),
        ),
    ),
)


def shortcut_footer_text() -> str:
    """Return the plain text equivalent of the themed shortcut footer."""
    return "\n".join(
        f"{category:<8}"
        + "".join(f" {key} {description}  " for key, description in shortcuts)
        for category, shortcuts in SHORTCUT_ROWS
    )


class ShortcutFooter(Static):
    """A three-row, nano-style shortcut reference using the active theme."""

    COMPONENT_CLASSES = {
        "shortcut-footer--category",
        "shortcut-footer--key",
        "shortcut-footer--description",
    }

    def render(self) -> Text:
        category_style = self.get_component_rich_style("shortcut-footer--category")
        key_style = self.get_component_rich_style("shortcut-footer--key")
        description_style = self.get_component_rich_style(
            "shortcut-footer--description"
        )
        footer = Text()
        for row_number, (category, shortcuts) in enumerate(SHORTCUT_ROWS):
            footer.append(f"{category:<8}", style=category_style)
            for key, description in shortcuts:
                footer.append(f" {key} ", style=key_style)
                footer.append(f" {description}  ", style=description_style)
            if row_number < len(SHORTCUT_ROWS) - 1:
                footer.append("\n")
        return footer


class KeyboardServiceTable(DataTable):
    """A service table whose selection is controlled exclusively by the keyboard."""

    def _on_mouse_move(self, event: events.MouseMove) -> None:
        event.prevent_default()
        self._set_hover_cursor(False)

    async def _on_click(self, event: events.Click) -> None:
        event.prevent_default()
        event.stop()
