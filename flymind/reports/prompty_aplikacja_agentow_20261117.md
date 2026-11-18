# Dwa prompty: aplikacja „Centrum Agentów” (17 XI 2026)

Wklejasz w nową sesję Claude Code (Opus) **najpierw PROMPT 1**. Dopiero gdy interfejs Ci się spodoba, w tej samej sesji wklejasz **PROMPT 2**.

Co sprawdziłem na Twoim Macu (17 XI):

| Program | Stan |
|---|---|
| `claude` | zainstalowany |
| `codex` | zainstalowany |
| `opencode` | zainstalowany |
| `gemini` | zainstalowany |
| `agy` | zainstalowany (komenda Antigravity) |
| Antigravity.app, Cursor.app | zainstalowane |
| `cursor-agent` (Cursor w trybie terminala) | **brak** |

---

## PROMPT 1 — INTERFEJS (klikalna makieta, bez prawdziwych agentów)

```
Zbuduj interfejs aplikacji „Centrum Agentów” — klikalną makietę na FAŁSZYWYCH danych, bez łączenia z prawdziwymi agentami.

DLA KOGO: Adam — właściciel projektu, NIETECHNICZNY. Wszystko po polsku, prostymi słowami, duże przyciski, zero żargonu
(zamiast „worktree” → „osobna kopia robocza”, zamiast „stdout” → „co agent pisze”). Każdy ekran ma jedno zdanie „co tu robisz”.

PO CO APLIKACJA: jedno miejsce, z którego Adam zleca pracę kilku agentom AI do kodowania i widzi, co robią:
Claude Code (główny — planuje i SPRAWDZA pracę innych), Codex, Antigravity (lub Gemini CLI), OpenCode, a w przyszłości Cursor.
Lżejsze agenty robią prostsze roboty, żeby oszczędzać tokeny Claude'a. Agenci nie rozmawiają ze sobą bezpośrednio:
wymieniają się ZADANIAMI (zlecenie → wynik → sprawdzenie przez Claude'a).

EKRANY (nawigacja z lewej, na telefonie menu ☰):
1. Start — „Co się teraz dzieje”: ilu agentów pracuje, co czeka na Adama (zatwierdzenia, gotowe wyniki), ostatnie zdarzenia.
2. Zadania — tablica 4 kolumn: Do zrobienia / W toku / Oddane (czeka na sprawdzenie) / Sprawdzone. Karta: tytuł, kolorowa etykieta agenta,
   czas, pasek postępu, przyciski „Pokaż”, „Zatrzymaj”.
3. Nowe zadanie — prosty formularz: Co ma powstać? Komu dać (lista agentów + „niech Claude zdecyduje”)? Które pliki wolno zmieniać?
   Jak sprawdzimy, że gotowe? Przycisk „Zleć”. Opcja „powtarzaj (pętla) N razy”.
4. Szczegóły zadania — na żywo co agent pisze (przewijany dziennik), lista zmienionych plików, wynik, werdykt Claude'a
   (✅ przeszło / ❌ poprawka z opisem), przyciski „Przyjmij”, „Odrzuć i popraw”, „Zatrzymaj agenta”.
5. Agenci — karta na każdego: połączony / niepołączony / tryb ręczny, czym się zajmuje, ile zadań zrobił, zużycie (tokeny lub koszt, jeśli znane),
   przycisk „Sprawdź połączenie”. Dla agenta w trybie ręcznym: przycisk „Kopiuj polecenie”, które Adam wkleja sam.
6. Do zatwierdzenia — wszystkie prośby agentów o zgodę w jednym miejscu (np. „agent chce uruchomić komendę X”, „chce zapisać zmiany w git”),
   każda z przyciskami Zgoda / Odmowa i opisem prostymi słowami, co się stanie.
7. Ustawienia — folder projektu, ilu agentów naraz (domyślnie 3), które agenty włączone, limity zużycia, jasny/ciemny motyw.

ZASADY BUDOWY:
- Folder: ~/CentrumAgentow/ (nowe repo git; NIE w innych projektach). Na razie zwykłe HTML + CSS + JavaScript bez bibliotek do instalowania,
  otwierane przez dwuklik w plik albo prosty serwer — tak, żeby Adam nie musiał niczego instalować.
- Fałszywe dane w jednym pliku (np. demo-data.js), żeby dało się przeklikać CAŁE życie zadania: zlecenie → w toku → oddane → Claude sprawdza →
  odrzucone z poprawką → ponownie → przyjęte. Agenci w różnych stanach (np. Cursor „wkrótce”).
- Czytelność i wygoda ważniejsze niż efekty. Działa na ekranie laptopa i telefonu.
- Na koniec: otwórz makietę w przeglądarce, zrób zrzuty ekranów każdego ekranu, sprawdź sam, czy wszystko się klika,
  i napisz Adamowi 3–5 zdań: co jest, jak to obejrzeć, o co go pytasz (max 3 pytania z Twoimi rekomendacjami).
- NIE łącz się jeszcze z żadnym agentem, NIE uruchamiaj ich. Nie rób git push. Commit lokalny tylko po zgodzie Adama.
```

---

## PROMPT 2 — DZIAŁAJĄCY PROGRAM (wklej po akceptacji interfejsu)

```
Interfejs „Centrum Agentów” jest zaakceptowany. Teraz podłącz go do PRAWDZIWYCH agentów — małymi krokami, każdy krok działający i sprawdzony.

ARCHITEKTURA (najprościej, lokalnie, bez chmury):
- Lokalny serwer na 127.0.0.1 (najlepiej Python 3 z samą biblioteką standardową; jeśli naprawdę potrzebujesz czegoś więcej — zapytaj Adama,
  podając powód i alternatywę). Strona z PROMPTU 1 rozmawia z serwerem; zdarzenia na żywo przez Server-Sent Events.
- Wspólna „szyna” = zwykłe pliki: ~/CentrumAgentow/zadania/{do_zrobienia,w_toku,oddane,sprawdzone}/ z plikami ZL-<data>-<nr>-<AGENT>.md
  i WYNIK-….md (format jak w /Users/admin/FlyMind_Hub/zlecenia/JAK_TO_DZIALA.md — przeczytaj i zachowaj zgodność).
  Dzięki temu zadania może pisać zarówno Adam (formularz), jak i Claude Code jako główny agent.
- Adapter na każdego agenta, jedna wspólna umowa: start(zadanie) → strumień tekstu → koniec (kod wyjścia, zmienione pliki, zużycie) + stop().
  Dwa tryby: „automatyczny” (aplikacja uruchamia program w terminalu bez okna) i „ręczny” (przycisk Kopiuj polecenie + aplikacja czeka na plik WYNIK).

AGENCI NA TYM MACU (sprawdzone 17 XI; flagi SPRAWDŹ SAM przez `<komenda> --help` i dokumentację — nie zgaduj):
- Claude Code: `claude` (tryb bez okna, wyjście JSON/strumień) — GŁÓWNY: dzieli duże zadania, pisze zlecenia dla innych, SPRAWDZA ich wyniki.
- Codex: `codex` (tryb nieinteraktywny, np. `codex exec`).
- OpenCode: `opencode` (np. `opencode run`, ewentualnie jego serwer HTTP).
- Antigravity: aplikacja + komenda `agy` — ustal, czy da się nią zlecić zadanie bez okna; jeśli nie, tryb ręczny albo `gemini` (Gemini CLI) jako zastępstwo.
- Cursor: Cursor.app jest, ale `cursor-agent` NIE jest zainstalowany → na razie tryb ręczny; instalacja tylko za zgodą Adama.

BEZPIECZEŃSTWO (obowiązkowe):
- Każde zadanie z kodem w OSOBNEJ kopii roboczej (git worktree, osobna gałąź) — agenci nigdy nie piszą jednocześnie w tych samych plikach.
- Żadnego git commit/push, usuwania plików, instalowania programów bez kliknięcia „Zgoda” przez Adama w ekranie „Do zatwierdzenia”.
- Uprawnienia agentów najwęższe, jakie pozwalają zrobić zadanie (tryby bez „pełnej swobody”); przycisk „Zatrzymaj” zabija proces natychmiast.
- Najwyżej N agentów naraz (domyślnie 3). Limity czasu i zużycia na zadanie. Klucze i hasła nigdy w plikach zadań ani w dziennikach.
- Prywatne dane Adama (e-mail, nazwiska) nie trafiają do zewnętrznych usług poza samymi agentami, które Adam włączył.

KOLEJNOŚĆ (po każdym kroku: test, zrzut ekranu, 3 zdania dla Adama, commit lokalny dopiero po jego zgodzie):
K1. Serwer + zadania z plików (bez agentów): formularz tworzy plik, tablica pokazuje prawdziwe pliki.
K2. Claude Code automatycznie: jedno zadanie od początku do końca, dziennik na żywo, Stop działa.
K3. Codex. K4. OpenCode. K5. Antigravity/Gemini (lub tryb ręczny). K6. Cursor ręcznie.
K7. Claude jako kierownik: zadanie „duże” → Claude rozpisuje zlecenia dla innych agentów → oni robią → Claude sprawdza (uruchamia komendę
    sprawdzającą, czyta zmiany, porównuje liczby) → przyjmuje albo pisze poprawkę. Pętla „powtarzaj N razy” dla prostych powtarzalnych zadań.
K8. Licznik zużycia na agenta (jeśli program go podaje; jeśli nie — napisz uczciwie „nieznane”).

TESTY: każdy adapter ma mały test (atrapa agenta = skrypt, który pisze kilka linii i kończy się kodem 0 albo 1). Testy uruchamiaj sam.
Mów Adamowi uczciwie, co działa, a co nie — bez upiększania.
```
