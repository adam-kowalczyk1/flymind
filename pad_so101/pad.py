"""pad_so101/pad.py — odczyt pada Xbox przez SDL GameController (pygame-ce). Standardowe nazwy przycisków,
więc nie zgadujemy indeksów zależnych od systemu. Wymaga pygame.init() i pompowania zdarzeń w pętli (run.py)."""
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame
from pygame._sdl2 import controller as sdlc

from control import PadState
from settings import DEFAULTS

BUTTONS = {n: getattr(pygame, f"CONTROLLER_BUTTON_{n}") for n in (
    "A", "B", "X", "Y", "BACK", "START", "LEFTSTICK", "RIGHTSTICK",
    "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT")}
BUTTONS |= {"LB": pygame.CONTROLLER_BUTTON_LEFTSHOULDER, "RB": pygame.CONTROLLER_BUTTON_RIGHTSHOULDER}


class Pad:
    def __init__(self):
        sdlc.init()
        self.c = None
        self.name = None
        self.configure(DEFAULTS)

    def configure(self, s):
        """Mapa z ustawień: przycisk fizyczny → nazwa, której oczekuje control.py (domyślny przycisk tej akcji)."""
        self.remap = {s["buttons"][a]: DEFAULTS["buttons"][a] for a in DEFAULTS["buttons"]}
        self.inv = {k: -1.0 if v else 1.0 for k, v in s["invert"].items()}
        self.swap = s["swap_triggers"]
        self.rumble_on = s["rumble"]

    def poll(self):
        """PadState albo None, gdy pad niepodłączony (wtedy run.py robi STOP)."""
        if self.c is not None and not self.c.attached():
            self.c = self.name = None
        if self.c is None:
            for i in range(sdlc.get_count()):
                if sdlc.is_controller(i):
                    self.c = sdlc.Controller(i)
                    self.name = self.c.name
                    break
            else:
                return None
        ax = lambda a: max(-1.0, self.c.get_axis(a) / 32767)
        i = self.inv
        lt, rt = ax(pygame.CONTROLLER_AXIS_TRIGGERLEFT), ax(pygame.CONTROLLER_AXIS_TRIGGERRIGHT)
        if self.swap:
            lt, rt = rt, lt
        return PadState(
            lx=i["lx"] * ax(pygame.CONTROLLER_AXIS_LEFTX), ly=-i["ly"] * ax(pygame.CONTROLLER_AXIS_LEFTY),  # SDL: y w dół = +
            rx=i["rx"] * ax(pygame.CONTROLLER_AXIS_RIGHTX), ry=-i["ry"] * ax(pygame.CONTROLLER_AXIS_RIGHTY),
            lt=lt, rt=rt,
            buttons=frozenset(self.remap[n] for n, b in BUTTONS.items() if n in self.remap and self.c.get_button(b)))

    def rumble(self, strength, ms):
        try:
            if self.c is not None and self.rumble_on:
                self.c.rumble(strength, strength, ms)
        except pygame.error:       # nie każdy pad / sterownik wspiera wibracje — to tylko informacja zwrotna
            pass
