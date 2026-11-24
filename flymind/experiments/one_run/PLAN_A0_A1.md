# A0 czy A1 jako pierwszy dotyk (24 XI 2026, zapisane PRZED przebiegami)

Zamrożenie bez zmian (`results/seeds10_20261124/zamrozenie.json`, sprawdzane przez skrypt). Ziarna 27 602 001–010 (te same). Tylko MuJoCo, bez strojenia, bez sprzętu.
A0: istniejące zapisy `results/seeds10_20261124/raw`. A1: ta sama scena, jedyna różnica — kanał pierwszego nacisku 20–22 s to A1 zamiast A0 (ta sama siła 3 N, ten sam czas i narastanie 0,1 s). Przebieg kończy się w 22,00 s (2200 taktów), reszta sceny nie jest liczona.
**Zgodność:** wszystkie zapisane pola taktów 0–1999 (stan do 20,00 s) i poza startowa mają być równe co do bitu; podaję też pierwszy takt różnicy każdego pola. Siła odczuta: A0 w kanale 0 i A1 w kanale 1 mają być takie same takt po takcie. Para z niezgodnością przed dotykiem nie wchodzi do wyniku i jest zgłoszona.
**Miara:** kąt w 22,00 s − kąt w 20,00 s (MuJoCo) dla barku, podstawy i łokcia; różnica sparowana = A1 − A0 dla każdego ziarna; mediana, zakres i liczba par po każdej stronie zera (|różnica| < 0,05° osobno). Opis, bez progu zaliczenia.
Zastrzeżenie zapisane z góry: A0 trafia do 230 receptorów („udo”), A1 do 92 („goleń + stopa”). Różnica ruchu miesza więc rodzaj receptorów z ich liczbą; ta próba ich nie rozdziela.
