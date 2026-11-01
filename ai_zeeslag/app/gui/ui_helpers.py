"""Drawing helpers, fonts, colours and layout maths shared by both windows."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pygame

from app.game_logic.open_functions import BOARD_SIZE, Coordinate

Color = tuple[int, int, int]
Point = tuple[int, int]

# ---------------------------------------------------------------------- #
# Assets
# ---------------------------------------------------------------------- #
ASSETS_DIR: Path = Path(__file__).resolve().parent.parent / "assets"
FONT_PATH: Path = ASSETS_DIR / "fonts" / "secret.ttf"
BACKGROUND_PATH: Path = ASSETS_DIR / "images" / "bg.jpg"

# ---------------------------------------------------------------------- #
# Window sizes (both fit next to each other on a 1920 px wide screen)
# ---------------------------------------------------------------------- #
PLAYER_WINDOW_SIZE: Point = (1020, 700)
DEBUG_WINDOW_SIZE: Point = (820, 760)
WINDOW_MARGIN: int = 20

# ---------------------------------------------------------------------- #
# Colours
# ---------------------------------------------------------------------- #
COLOR_BACKGROUND: Color = (12, 24, 40)
COLOR_PANEL: Color = (8, 16, 28)
COLOR_TEXT: Color = (232, 238, 245)
COLOR_TEXT_DIM: Color = (150, 165, 182)
COLOR_ACCENT: Color = (240, 190, 70)
COLOR_WATER: Color = (28, 70, 116)
COLOR_WATER_HOVER: Color = (52, 110, 168)
COLOR_SHIP: Color = (128, 140, 152)
COLOR_MISS: Color = (206, 216, 230)
COLOR_HIT: Color = (214, 62, 52)
COLOR_SUNK: Color = (110, 22, 26)
COLOR_VALID: Color = (64, 176, 96)
COLOR_INVALID: Color = (204, 66, 66)
COLOR_BUTTON: Color = (40, 84, 132)
COLOR_BUTTON_HOVER: Color = (58, 112, 168)
COLOR_BUTTON_DISABLED: Color = (50, 58, 70)


# ---------------------------------------------------------------------- #
# Fonts and images
# ---------------------------------------------------------------------- #
@lru_cache(maxsize=None)
def title_font(size: int) -> pygame.font.Font:
    """The decorative game font (assets/fonts/secret.ttf), with a fallback."""
    if FONT_PATH.exists():
        try:
            return pygame.font.Font(str(FONT_PATH), size)
        except (pygame.error, OSError):
            pass
    return pygame.font.Font(None, int(size * 1.25))


@lru_cache(maxsize=None)
def body_font(size: int) -> pygame.font.Font:
    """A plain, readable font for small text."""
    return pygame.font.SysFont("segoeui,helvetica,arial,dejavusans", size)


@lru_cache(maxsize=None)
def mono_font(size: int) -> pygame.font.Font:
    """Monospace font for numbers in the debug window."""
    return pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", size)


def load_background(size: Point) -> pygame.Surface | None:
    """Load assets/images/bg.jpg scaled to ``size``; None if it is missing."""
    if not BACKGROUND_PATH.exists():
        return None
    try:
        image = pygame.image.load(str(BACKGROUND_PATH)).convert()
    except (pygame.error, OSError):
        return None
    return pygame.transform.smoothscale(image, size)


# ---------------------------------------------------------------------- #
# Drawing
# ---------------------------------------------------------------------- #
def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: Color,
    position: Point,
    anchor: str = "center",
) -> pygame.Rect:
    """Render ``text`` with its ``anchor`` point (a pygame.Rect attribute) at ``position``."""
    image = font.render(text, True, color)
    rect = image.get_rect(**{anchor: position})
    surface.blit(image, rect)
    return rect


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Split ``text`` into lines that fit in ``max_width`` pixels."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, alpha: int = 185) -> None:
    """Draw a semi-transparent dark rounded panel."""
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*COLOR_PANEL, alpha), panel.get_rect(), border_radius=10)
    surface.blit(panel, rect.topleft)


@dataclass
class Button:
    """A simple clickable rectangle."""

    rect: pygame.Rect
    label: str
    enabled: bool = True

    def contains(self, position: Point) -> bool:
        return self.enabled and self.rect.collidepoint(position)

    def draw(self, surface: pygame.Surface, mouse_position: Point) -> None:
        if not self.enabled:
            color, text_color = COLOR_BUTTON_DISABLED, COLOR_TEXT_DIM
        elif self.rect.collidepoint(mouse_position):
            color, text_color = COLOR_BUTTON_HOVER, COLOR_TEXT
        else:
            color, text_color = COLOR_BUTTON, COLOR_TEXT
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        draw_text(surface, self.label, title_font(22), text_color, self.rect.center)


@dataclass(frozen=True)
class BoardLayout:
    """Where a board is drawn on screen and how to map pixels to cells."""

    origin: Point  # top-left pixel of cell (0, 0)
    cell_size: int
    gap: int = 2
    size: int = BOARD_SIZE

    @property
    def pitch(self) -> int:
        return self.cell_size + self.gap

    @property
    def pixel_size(self) -> int:
        return self.size * self.pitch - self.gap

    def cell_rect(self, coordinate: Coordinate) -> pygame.Rect:
        row, column = coordinate
        return pygame.Rect(
            self.origin[0] + column * self.pitch,
            self.origin[1] + row * self.pitch,
            self.cell_size,
            self.cell_size,
        )

    def coordinate_at(self, position: Point) -> Coordinate | None:
        """The cell under ``position`` (gaps count to the cell on their right/below)."""
        x = position[0] - self.origin[0]
        y = position[1] - self.origin[1]
        if x < 0 or y < 0:
            return None
        column, row = x // self.pitch, y // self.pitch
        if row >= self.size or column >= self.size:
            return None
        return int(row), int(column)


def draw_board_labels(surface: pygame.Surface, layout: BoardLayout, font: pygame.font.Font) -> None:
    """Letters above the columns and numbers left of the rows."""
    for index in range(layout.size):
        rect = layout.cell_rect((0, index))
        draw_text(surface, chr(ord("A") + index), font, COLOR_TEXT_DIM, (rect.centerx, rect.top - 12))
        rect = layout.cell_rect((index, 0))
        draw_text(surface, str(index + 1), font, COLOR_TEXT_DIM, (rect.left - 14, rect.centery))


def draw_cross(surface: pygame.Surface, rect: pygame.Rect, color: Color, width: int = 3) -> None:
    """Draw an X inside ``rect``."""
    inset = max(4, rect.width // 5)
    inner = rect.inflate(-2 * inset, -2 * inset)
    pygame.draw.line(surface, color, inner.topleft, inner.bottomright, width)
    pygame.draw.line(surface, color, inner.topright, inner.bottomleft, width)
