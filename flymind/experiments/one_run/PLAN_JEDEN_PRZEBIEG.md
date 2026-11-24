# Jedna ciągła próba: kamera + dwa dotyki + trzy stawy (24 XI 2026, zapisane PRZED przebiegiem)

To POKAZ obecnego modelu (jeden przebieg, jedno ziarno), nie test hipotezy. Tylko MuJoCo. Bez strojenia, bez resetu, bez sekwencji gestów, bez trybów.

## Model (bez zmian)
`head.HeadLife(−1, "N", eyes=True)` (15 571 neuronów), szum 2 mV, wzmocnienie 0,005; oko `FlyEye` v2 z obrazu kamery nadgarstka na żywo (render 640×400 → 160×100,
100 kl./s); dotyk hw2: A0 szczęka stała → grupa „udo” (230), A1 szczęka ruchoma → „goleń+stopa” (92), czujnik `Feel(ideal)`; czucie łokcia z rzeczywistego kąta.
Ramię: `ArmGrip.tick` + `SafetyLayer` + fizyka; stawy 1–3 z sieci w KAŻDYM takcie; podstawa, obrót i szczęka trzymane klasycznie. Przed startem 1 s osiadania ramienia.
W każdym takcie ta sama operacja: klatka → oko; siły A0/A1 → czujniki; kąty → czucie; suma wejść → sieć → trzy przyrosty kąta. Kod nie wie, jaki jest bodziec.

## Bodźce (środowisko, nie gesty; 45 s)
0–6 spokój, nic w kadrze · 6,0–8,5 kula przejeżdża w poprzek kadru (22 cm od kamery, 0,3 m/s) · 10,0–11,25 wraca na środek · 12,0–12,53 zbliżenie 22 → 6 cm ·
13,2–13,73 oddalenie · 14,5–15,75 wyjazd · 16–20 spokój · 20–22 nacisk A0 3 N · 22–27 spokój · 27–29 nacisk A1 3 N · 29–34 spokój · 34,0–35,25 kula na środek ·
36,0–36,53 zbliżenie I JEDNOCZEŚNIE 36–38 nacisk A1 · 38,5–39,03 oddalenie · 40–41,25 wyjazd · 41,25–45 spokój.
Nacisk = sygnał czujnika (bez pchnięcia palca). Kula tylko rysowana. Tor kuli w świecie, względem kamery w pozie startowej.

## Skąd wiadomo, co zrobiła sieć
Kontrole z tym samym ziarnem (nie do pokazu, tylko do przypisania przyczyn): (a) sieć odcięta od stawów, (b) bez wzroku, (c) bez dotyku, (d) bez obu.
Ruch „z sieci” = rzeczywisty kąt zmienia się zgodnie z sumą komend sieci (różnica ≤ 0,002 rad) i znika w (a). Zdarzenie przypisane do bodźca, jeśli znika bez niego.
Zdarzenie = odcinek z niezerową komendą stawu (przerwa ≥ 0,3 s dzieli). Bezruch = takty bez komend trzech stawów.
Ziarno 27 601 001 (szum sieci; czujnik). Wynik pokazuję niezależnie od tego, jaki będzie.
