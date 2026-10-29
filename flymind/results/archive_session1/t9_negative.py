# Kontrola negatywna T9: zachowanie sprzed poprawki (close bez ustawienia własnego kontekstu) → T9 powinien paść.
import sys
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import so101, test_so101
def old_close(self):
    r = getattr(self, "renderer", None)
    if r is not None:
        r.close()
        self.renderer = None
so101.SO101Sim.close = old_close
try:
    test_so101.t9()
    print("T9 PRZESZEDŁ przy starym zachowaniu — test nie wykrywa błędu")
except AssertionError:
    print("T9 padł przy starym zachowaniu — test wykrywa błąd (oczekiwane)")
