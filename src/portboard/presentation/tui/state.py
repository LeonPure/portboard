"""Presentation-only state for filtering and sorting a service snapshot."""

from __future__ import annotations

from dataclasses import dataclass

from portboard.domain.models import Service, ServiceSnapshot
from portboard.presentation.tui.formatters import searchable_text, sort_key


@dataclass(slots=True)
class DashboardState:
    """Keep mutable dashboard concerns out of the domain snapshot."""

    snapshot: ServiceSnapshot | None = None
    filter_text: str = ""
    sort_field: str = "port"
    sort_reverse: bool = False

    def set_filter(self, value: str) -> None:
        self.filter_text = value.casefold().strip()

    def toggle_sort(self, field: str) -> None:
        if self.sort_field == field:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_field = field
            self.sort_reverse = False

    def visible_services(self) -> tuple[Service, ...]:
        if self.snapshot is None:
            return ()
        services = self.snapshot.services
        if self.filter_text:
            services = tuple(
                service
                for service in services
                if self.filter_text in searchable_text(service).casefold()
            )
        return tuple(
            sorted(
                services,
                key=lambda service: sort_key(service, self.sort_field),
                reverse=self.sort_reverse,
            )
        )
