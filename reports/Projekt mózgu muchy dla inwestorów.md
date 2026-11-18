# Wyróżnij się uczciwością, nie rekordem: SO-101 z mózgiem muchy

**Stan na 3 listopada 2026. Raport powstał wyłącznie na podstawie czterech notatek badawczych (ścieżki na końcu) i jest pisany dla ucznia liceum, bez żargonu.**

Twój projekt nie wyróżni się tym, że „mózg muchy steruje robotem”. Takich symulacji jest już sporo, w tym jedna od firmy z finansowaniem ([konkurencja_stan_wiedzy.md §2][kw]). Wyróżnić Cię mogą dwie rzeczy. Pierwsza to wąskie, sprawdzalne twierdzenie: według notatek nie znaleziono w publicznych źródłach ramienia-manipulatora (SO-101 ani żadnego innego) sterowanego siecią z konektomu muchy ([konkurencja_stan_wiedzy.md §3][kw]). To zdanie będzie prawdziwe dopiero wtedy, gdy sieć zadziała na prawdziwym ramieniu, bo dziś wszystko, co zmierzyłeś, działo się w symulacji (MuJoCo) i żaden wynik nie pochodzi ze sprzętu ([nasze_wyniki.md, nagłówek i §2A][nw]). Druga rzecz to metoda: kontrole z przetasowanymi połączeniami, zamrożone protokoły, rejestry ziaren losowości i opisane porażki. Konkurs sam o to prosi: Fundacja pisze, że projekt z porażkami często wypada lepiej niż „idealny” ([5 Zasad Projektowych][zasady]). Dla inwestora uczciwa odpowiedź na „kto za to zapłaci?” brzmi: dziś nikt, a realna szansa to małe granty i konkursy. Najmocniejszy pomost do ORLEN-u to inspekcje przemysłowe, ale jako kierunek na przyszłość, nie coś udowodnionego. Najważniejsze zadanie przed 1 grudnia to uruchomić sieć na prawdziwym ramieniu, choćby tylko w obrocie podstawy w stronę piłeczki, i porównać ją z przetasowaną siecią.

## Co jest naprawdę nowe: wąskie twierdzenie i metoda, a nie „mózg muchy w robocie”

Zacznijmy od tego, co **nowe nie jest**. Dane są publiczne: konektom (czyli „mapa połączeń” między neuronami) FlyWire opisano w Nature w 2024 roku, a Twoja baza MaleCNS od Janelii (samiec muszki, razem z rdzeniem nerwowym) ukazała się w Cell 3 września 2026 ([Live Science][ls]). Standardowy model „mózg jako sieć impulsowa” (neurony wysyłają impulsy, jak w prawdziwym mózgu) opublikowali Shiu i in. w 2024 roku ([Princeton Pure][shiu]). Firma Eon Systems pokazała w marcu 2026 symulowaną muchę z takim mózgiem w ciele z NeuroMechFly v2 ([Eon][eon]). Co ważne, sam Eon przyznaje w swoim tekście, że wiele połączeń między mózgiem a ciałem „wybrano ręcznie”, a wejście z wzroku jest „dekoracyjne” ([Eon][eon]). Czyli także tam sama sieć nie tłumaczy zachowania, tylko sieć plus zaprojektowany interfejs. Ty masz dokładnie ten sam typ interfejsu (kamera → sygnał, impulsy → komenda), więc nie udawaj, że go nie ma.

Fizyczne roboty też już istnieją, choć w zalążku. „Fly Brain Bridge” (czworonóg Sesame, mózg z MaleCNS) i „FlyDrones” (drony) to projekty hobbystyczne, których autorzy sami piszą, że test na prawdziwym sprzęcie jest jeszcze przed nimi ([Fly Brain Bridge][fbb], [FlyDrones README][fd]). Strony nie mają dat, więc od tamtej pory mogło się to zmienić. Pierwszy robot z konektomem w ogóle to LEGO z robakiem C. elegans z 2014 roku ([Elektor][elektor]). Dlatego **zdania „pierwszy robot sterowany konektomem” i „pierwsza cyfrowa mucha” są nieprawdziwe**, a Fundacja ostrzega, że „nikt tego wcześniej nie zrobił” to jedno z najniebezpieczniejszych zdań w rozmowie z jury ([5 Zasad Projektowych][zasady]).

| Kto | Co zrobił | Sprzęt? | Czym Ty się różnisz |
|---|---|---|---|
| Eon Systems | Mózg Shiu + symulowane ciało muchy; seed 3,5 mln USD ([Untapped Ventures][eonfund]) | Nie, tylko symulacja | Ty celujesz w manipulator i w kontrole |
| NeuroMechFly, flybody | Symulowane ciała muchy; flybody sterowane siecią wyuczoną z nagrań, nie konektomem ([Janelia][flybody]) | Nie | Ty masz własny sterownik z konektomu |
| Fly Brain Bridge, FlyDrones | MaleCNS → czworonóg / drony | Autorzy: test sprzętowy jeszcze nie zrobiony | Ty: ramię, tani zestaw |
| OpenWorm / Busbice | Robak C. elegans w LEGO (2014) | Tak | Inny organizm, ale precedens „konektom w sprzęcie” |
| Cortical Labs, Opteran | Żywe neurony w układzie (CL1 za 35 000 USD); algorytmy z mózgu pszczoły ([Wikipedia][cl], [Tech.eu][opt]) | Tak, to firmy | Inna technologia; to kontekst, nie rywale |
| Układy neuromorficzne | Cała sieć FlyWire na 12 chipach Loihi 2, bez robota ([arXiv][sandia]) | Chipy tak, robot nie | Ty działasz na zwykłym laptopie |

**Co zatem może być Twoje.** Notatki wskazują cztery elementy: manipulator (ramię), konkretnie SO-101, pomiar zamkniętej pętli ze sprzężeniem zwrotnym ze sprzętu oraz kontrole typu „przetasowany konektom” na sprzęcie, a do tego tani, otwarty zestaw ([konkurencja_stan_wiedzy.md §7][kw]). Bezpieczne sformułowanie to: *„Według moich poszukiwań w publicznych źródłach do listopada 2026 nie znalazłem ramienia-manipulatora sterowanego konektomem muchy; sprawdzam to na sprzęcie z kontrolami.”* Zanim powiesz „pierwszy”, sprawdź ręcznie YouTube, Hackaday, Reddit i Discorda LeRobot, bo narzędzie, którym przeszukiwano sieć, tego nie obejmowało, a repozytorium `hwihwalab/malecns-connectome-robotics-2026` zwróciło błąd 401 i nie zostało przeczytane ([konkurencja_stan_wiedzy.md, Gaps][kw]).

**Prawdziwa przewaga to metoda.** Autorzy hobbystycznych repozytoriów często pokazują wyniki z 3 ziaren i ich własne definicje sukcesu ([Froststar16][froststar]). Ty masz zamrożone protokoły z sumami kontrolnymi (sha256), rejestry ziaren, trzy rundy krytyki (przez osobne instancje modelu AI, nie ludzi) i niezależne przeliczenie analizy ([nasze_wyniki.md §3][nw]). Konkretny wynik: w symulacji sieć z danych nakierowała kamerę na piłeczkę w **38 z 40** prób, przetasowana sieć w 3 z 40, z zamienionymi stronami w 0 z 40 ([nasze_wyniki.md §2B][nw]). To najlepsze, co masz, ale trzeba je podać razem z jego cieniem. Prosty klasyczny regulator P zrobił to 40/40 i dokładniej (błąd mediany 0,16° wobec 1,41°). Kontrola, w której przetasowanie zachowało siłę sygnału, dała we wstępnej wersji 10/10, czyli liczy się głównie to, która strona pobudza którą, a nie dokładny wzór połączeń. W większym teście (V5 v4, 2700 prób) przewaga wzorca z danych nad losowym zmieniała znak zależnie od odległości celu i mieściła się w granicy ±0,5° ([nasze_wyniki.md §2B pkt 1, 3][nw]). Dwie rzeczy, które lepiej wiedzieć, zanim zapyta jurora: obwód odruchu chwytu zawiera 20 neuronów Twojego autorstwa, a kluczowe są właśnie one, nie dane ([nasze_wyniki.md §2B pkt 6][nw]); eksperyment z szczęką (FJ1) dał 12/12, ale prosty odruch w jednej linijce też 12/12, więc nie wykazano roli konkretnych połączeń ([nasze_wyniki.md §2B pkt 9][nw]). Nowością i siłą jest więc zadanie pytania „czy prawdziwe połączenia coś wnoszą?” i uczciwa odpowiedź „mało i zależnie od warunków”, a nie „jesteśmy lepsi od algorytmu”.

## Co wolno mówić, a czego nie

Notatki wprost wymieniają zdania bezpieczne i zakazane ([nasze_wyniki.md §7][nw]). Dodałem trzy własne dopiski (oznaczone), wynikające z wymogów konkursu i z notatek o konkurencji.

| Wolno (poparte plikami) | Nie wolno |
|---|---|
| „Zbudowałem **w symulacji** model sterownika ramienia SO-101 opartego na prawdziwych połączeniach konektomu samca muchy (MaleCNS v1.0).” | „Prawdziwe ramię jest sterowane mózgiem muchy” (dopóki tego nie zrobisz i nie zmierzysz). |
| „W symulacji sieć z danych nakierowała kamerę na piłeczkę w 38/40 prób, przetasowana w 3/40, z odwróconymi stronami 0/40.” | „Cyfrowa mucha”, „skopiowałem mózg muchy”, „zachowuje się jak mucha”. |
| „Prosty regulator klasyczny robi to dokładniej; mój wynik dotyczy zachowania sieci, nie przewagi nad algorytmem.” | „Konektom jest lepszy niż klasyczny algorytm.” |
| „Wiele hipotez obaliłem lub wycofałem kontrolami.” | „Wykazałem, że liczą się konkretne połączenia” (FJ1: nierozstrzygnięte/odrzucone). |
| „W symulacji odruch nogi (z moim modułem odruchu) chwytał piłeczkę w 87 % prób bez zgnieceń (26/30).” | „Mózg łapie rzuconą piłeczkę” (to inżynieria 94–98 %, wersja biologiczna 7/20). |
| „Pilotaż: sieć wzrok→nogi w symulacji przybliżyła chwytak do piłeczki z 71 do 17 mm; wynik wstępny.” | „Znalazłem odruch uniesienia” (hipoteza; jeden przetasowany obwód dał podobny wynik). |
| *(dopisek)* „Używam MaleCNS z Janelii, nie FlyWire.” | „Używam FlyWire.” |
| *(dopisek)* „Według moich poszukiwań nie znalazłem ramienia sterowanego konektomem muchy.” | *(dopisek)* „Nikt tego wcześniej nie zrobił.” Ani „pierwszy robot z konektomem”. |
| *(dopisek)* „Oszczędność energii to hipoteza układów neuromorficznych, której mój projekt nie mierzy.” | Jakiekolwiek liczby o koszcie, mocy czy czasie reakcji **na robocie**; „oszczędzamy energię”; „leczymy”. |

Do tego dopisek formalny: formularz Explory zawiera obowiązkowe pytanie, czy zespół korzystał z pomocy AI i w jakim zakresie ([formularz 2027][form]). Opisz to prawdziwie, bo jury zada pytania sprawdzające, czy rozumiesz własny projekt, a Fundacja zastrzega, że projekt ma być prowadzony samodzielnie ([konkurs_explory.md §1][ke]). Pamiętaj też o jednej z trzech wprost wymienionych zasad etyki: nie wolno zgłaszać projektów o tematyce militarnej, więc mów o ramieniu i inspekcjach, nie o dronach bojowych ([Regulamin §4][reg]).

## Inwestor zapyta „kto za to zapłaci”, a uczciwa odpowiedź to granty i otwarty zestaw

Rynek wygląda tak. Prognozy rynku obliczeń neuromorficznych na 2030 rok różnią się o ponad rząd wielkości: od około 0,3 mld USD (Report Prime) do 20 mld USD (Grand View Research), przy czym to komercyjne szacunki z różnymi definicjami ([MarketsandMarkets][mm], [Grand View][gv], [Report Prime][rp]). Prawdziwe przychody są małe: BrainChip miał w 2025 roku **1,89 mln USD** przy stracie około 20,5 mln USD ([Business Wire][bc], [Motley Fool AU][mf]). Argument energetyczny (deklaracje Intela „do 100x mniej energii” czy Innatery „500x”) pochodzi od producentów i dotyczy wybranych testów ([SiliconANGLE][hala], [Unite.ai][innatera]). IEA szacuje, że centra danych zużyły w 2024 roku około 415 TWh, a w 2030 roku zużyją około 945 TWh, ale też zaznacza, że to około jedna dziesiąta wzrostu światowego popytu na prąd ([IEA][iea]). Twój projekt nie mierzy zużycia energii. Dodatkowo działa na zwykłym komputerze, nie na układzie neuromorficznym, więc żadnej oszczędności nie dowodzi.

Najbliższy sensowny wzór biznesowy to Opteran: spółka ze Sheffield, której owadzie algorytmy unikania kolizji zebrały 12 mln USD w 2022 roku i mają pilotaże u klientów ([Tech.eu][opt], [Dealroom][dealroom]). Późniejsze kwoty są niespójne między agregatorami. Z kolei fundusze w „dużej” robotyce (Figure ok. 39 mld USD wyceny, Physical Intelligence ok. 11 mld) to inna skala, tylko kontekst: wyceny nie są dowodem na model biznesowy, a PI według doniesień nie miało jeszcze przychodów ([The Robot Report][figure], [Dealroom][pi]). Dla Ciebie lepszym otwarciem jest: *„Pieniądze płyną do dużych modeli robotów; ja badam przeciwny biegun, mały, przejrzysty sterownik z prawdziwych połączeń, na sprzęcie za około 100–130 USD.”* Cena SO-101 to według Hugging Face około 100 USD baza i około 130 USD z drukiem i silnikami, w praktyce 100–500 USD zależnie od dostawcy i ceł, a kamera jest osobno ([TechCrunch][techcrunch]). Kosztów Twojego własnego zestawu (ramię, kamera) projekt nigdzie nie dokumentuje, więc sprawdź je przed podaniem liczby.

**Które programy ORLEN pasują.** Realny cel to **Fundacja ORLEN**, nie fundusz. Program „Inżynierowie Przyszłości” daje uczniom szkół ponadpodstawowych 100 grantów po 2 000 zł na materiały i sprzęt, ale edycja 2026/27 miała nabór do 9 października 2026 i jest zamknięta; finał jest w czerwcu 2027 ([Warto Wiedzieć][iprz]). To źródło wtórne, a limit wieku i to, czy symulacja się kwalifikuje, nie są sprawdzone. Dwa tysiące złotych to mniej więcej koszt sprzętu klasy SO-101 (moje przeliczenie, nie z notatek). Stypendium „Mogę więcej” miało nabór do 4 października 2026, a wyniki do 10 listopada 2026 ([Warto Wiedzieć][mw]). **ORLEN Skylight Accelerator** jest dla startupów, ma wyzwania typu Industry 4.0, inteligentna infrastruktura, a ORLEN pokrywa koszty pilotażu w swoich zakładach ([ORLEN][skylight]), więc to etap „może kiedyś, z zespołem”. **ORLEN VC** (około 100 mln EUR) inwestuje w dojrzałe startupy deep-tech i cleantech, nie w projekty szkolne ([ORLEN VC][vc]). ORLEN sponsoruje też Nagrodę Główną Explory (15 000 zł) ([konkurs_explory.md §2][ke]). Najpraktyczniejsze więc: wygrać nagrodę w konkursie, a po festiwalu złożyć wniosek do Fundacji w następnej edycji.

**Najmocniejszy związek z ORLEN-em i jego twarda granica.** ORLEN już stosuje drony do ochrony zakładu w Płocku i do monitoringu rurociągu, a w 2022 ogłosił analizy opłacalności inspekcji dronowych ([ORLEN 2019][orlen19], [Bankier][bankier]). Rynek robotów inspekcyjnych w ropie, gazie i chemii istnieje: ANYbotics (czworonożne roboty) zebrało 50 mln USD i ma zamówienia i rezerwacje ponad 150 mln USD, a jego klientami są m.in. Shell i PETRONAS, nie ORLEN ([Business Wire][anybotics]). Możesz więc powiedzieć: *„Kierunek na przyszłość: mały, przejrzysty sterownik do robotów inspekcyjnych w zakładach przemysłowych. Tego nie sprawdzałem.”* Nie wynika z żadnych źródeł, że ORLEN inwestuje w neuromorficzne sterowanie czy roboty-owady, więc nie sugeruj, że się tym interesuje ([rynek_inwestorzy.md §6][ri]). Uczciwa komercyjna ścieżka to otwarty zestaw edukacyjny na wzór Backyard Brains, które sprzedało 10 000 SpikerBoxów do 2016 roku i miało około 500 tys. USD przychodu po pięciu latach (starsze, regionalne doniesienie) ([Backyard Brains][byb]). To mała skala, ale realna.

**Dlaczego ktoś miałby zainwestować właśnie w Ciebie?** Nie w produkt, bo go nie ma, tylko w osobę i sposób pracy: ktoś, kto w kilka tygodni zbudował sieć z prawdziwych danych, sam obalił swoje mocniejsze hipotezy i potrafi powiedzieć „to nie wyszło”. Mała kwota (rzędu grantu 2 000 zł) kupuje sprzęt i pierwszy pomiar na prawdziwym ramieniu. Taki pitch broni się lepiej niż „rynek wart 20 mld”.

## Cel zrównoważonego rozwoju: SDG 9 jako główny, SDG 4 jako dodatek

Wybierz **SDG 9** („innowacje i infrastruktura”), konkretnie cel 9.5 (wzmacnianie badań naukowych i zdolności technologicznych) ([ONZ SDG 9][sdg9]). Uzasadnienie, którego jury może zażądać (kryterium „Społeczne oddziaływanie” w finale wymaga wykazania związku z celem, zidentyfikowanego problemu i uzasadnienia pozytywnej zmiany ([Regulamin §7][reg])): problemem jest brak otwartych, powtarzalnych sposobów sprawdzania, czy połączenia z prawdziwego mózgu cokolwiek wnoszą w sterowaniu robotem; Ty dajesz otwarte dane, kod i kontrole. **SDG 4** (edukacja) dodaj tylko wtedy, gdy rzeczywiście powstanie materiał dydaktyczny, np. demo i krótki opis dla uczniów. SDG 7 i 13 (energia, klimat) traktuj co najwyżej jako odległą hipotezę, nie jako efekt projektu. Zdrowie (SDG 3) też odpada jako uzasadnienie, bo projekt niczego medycznego nie mierzy ([rynek_inwestorzy.md §5][ri]). Dobrze też trafia w kategorię nagród zrównoważonego rozwoju „Gospodarka i Bezpieczeństwo” ([Regulamin §8][reg]).

## Opis szkoły a oficjalne zasady Explory: zapytaj koordynatora

Według oficjalnego regulaminu Szkolnych Festiwali Explory ocenia 3 jurorów trzema kryteriami po 0–10: wiedza o temacie, dodatkowa wartość naukowa, społeczna lub gospodarcza oraz **praktyczne zastosowanie wyników** ([Regulamin Szkolnych Explory §5][sfe]). Jeśli szkoła opisuje trzecie kryterium jako „prezentację”, to jest rozbieżność, bo prezentacja to kryterium półfinału, a nie szkolnego festiwalu. Czas: dokumenty dla jurorów sugerują rozmowę „nieprzekraczającą 15 minut” ([Niezbędnik Jurora][jurorzy]), więc 10 minut to prawdopodobnie ustalenie szkoły, ale przygotuj się na obie wersje. Terminy: regulamin podaje, że wyniki kwalifikacji przychodzą mailem do 30 kwietnia ([Regulamin §6][reg]); jeśli w materiałach szkoły widzisz inny termin, np. koniec lutego, to nie znaleziono dokumentu, który by to potwierdzał, tak samo jak „regionalnego przeglądu mazowieckiego” ([konkurs_explory.md, Gaps][ke]). Nazwa „explore.penta” nie występuje w żadnym źródle; to prawdopodobnie strona szkoły. Z tego powodu **zapytaj koordynatora o cztery rzeczy**: (1) jakie dokładnie są kryteria i czy to te trzy oficjalne, (2) ile trwa rozmowa, (3) kiedy i jak następuje awans (jeden projekt na pięć, a pozostałe i tak ocenia Jury Fundacji, [Regulamin Szkolnych §5][sfe]), (4) czy plakat szkolny wymaga SDG i gdzie jest wzór. Drobny, ale ważny termin: projekt musi być zarejestrowany w systemie konkursowym co najmniej 14 dni przed festiwalem, czyli w Twoim przypadku około **17 listopada** (inne źródło mówi o dniu przed festiwalem, więc zweryfikuj) ([konkurs_explory.md §1][ke]).

## Plan do 16 listopada i do 1 grudnia: najpierw prawdziwe ramię

Dziś to 13 dni do plakatu i 28 dni do festiwalu. **Priorytet nr 1 to uruchomić sieć na prawdziwym SO-101**, nawet w najprostszej wersji: obrót podstawy w stronę piłeczki, jak w symulacji V5. W repozytorium nie ma sterownika sprzętowego ([nasze_wyniki.md §2A][nw]). LeRobot obsługuje SO-101 jako sprzęt, więc to nie jest droga bez wsparcia ([LeRobot][lerobot]). Według Twojego planu walidacji sprzęt fizyczny wymaga osobnej zgody właściciela projektu, więc to decyzja do podjęcia już teraz ([nasze_wyniki.md §1][nw]). Główny cel to nie wynik, ale uczciwy pomiar. Trzy warianty w tej samej pętli: sieć z danych, sieć przetasowana i regulator klasyczny jako punkt odniesienia. Kilkanaście prób każdy, protokół zapisany z góry i raport niezależnie od wyniku. Realne ryzyko: w symulacji sieć jest dużo bardziej wrażliwa na opóźnienia klatek niż regulator P (50 ms: 9/20 wobec 20/20), a prawdziwa kamera USB je doda ([nasze_wyniki.md §2D][nw]). Jeśli się nie uda, pokaż dokładnie to: „próbowałem, oto co poszło nie tak”. To pasuje do zasad Fundacji i nie zmienia zasady projektu, że klasyka może być tylko warstwą bezpieczeństwa i punktem odniesienia.

| Kiedy | Zadanie |
|---|---|
| Teraz | Decyzja o sprzęcie. Zapytać koordynatora (cztery pytania wyżej). Przeszukać ręcznie YouTube, Hackaday, Reddit, Discord LeRobot pod kątem „SO-101 + fly brain”. |
| Do 8 listopada | Sterownik sprzętowy + warstwa bezpieczeństwa (limity ruchu, prędkości). Podstawa obraca się „na sucho”, bez sieci. |
| Do 14 listopada | Prawdziwa kamera + pierwszy bieg sieci z danych. Zamrożony prosty protokół. |
| Do 16 listopada | **Plakat** wg szablonu Canva: tytuł, problem, metoda, wyniki z porażkami, zastosowanie; SDG 9; opis użycia AI. Rejestracja w systemie. Zamiana wszystkich „FlyWire” na „MaleCNS”. |
| Do 23 listopada | Serie pomiarowe: sieć z danych vs przetasowana vs regulator P na ramieniu, nagranie wideo. |
| Do 27 listopada | Pitch 2–3 minuty na pamięć „w zarysie”, nie dosłownie, plus próby pytań. Demo symulacyjne (okno SNN vs P z `flymind/demo/`) sprawdzone i nagrane jako plan B. |
| 1 grudnia | Pokaz: wideo z ramienia + symulacja + plakat. |
| Po festiwalu | Wniosek do Fundacji ORLEN w następnej edycji, zgłoszenie na Explory 2027, ewentualny kontakt z kołem naukowym lub uczelnią. |

Pitch 2–3 minuty (struktura zgodna z zaleceniami Fundacji: problem, metoda, wyniki z porażkami, sens ([Niezbędnik Uczestnika][uczestnik])):

> *„Czy prawdziwe połączenia z mózgu muszki coś wnoszą w sterowaniu robotem, czy to tylko ładna opowieść? Wziąłem publiczny konektom samca muszki (MaleCNS, Janelia) i zbudowałem z jego wycinka sieć impulsową, która w symulacji kieruje ramieniem SO-101 na piłeczkę. W symulacji działa w 38 z 40 prób. Gdy przetasuję połączenia, tylko w 3 z 40. Ale prosty regulator klasyczny robi to dokładniej, a po wyrównaniu siły sygnału przewaga prawdziwych połączeń jest mała i zależy od warunków. Wiele moich hipotez obaliłem kontrolami i opisałem to. Teraz sprawdzam to na prawdziwym ramieniu: [wynik]. Według moich poszukiwań nie znalazłem takiego ramienia w publicznych źródłach. Cel: SDG 9, otwarty zestaw do uczciwego testowania modeli mózgu w robotach. Kierunek na przyszłość, którego nie sprawdzałem: sterowniki do robotów inspekcyjnych.”*

Na rozmowę przygotuj odpowiedzi na pięć pytań: „Czy ktoś już to zrobił?” (Eon, Fly Brain Bridge, FlyDrones; czym się różnię), „Czemu regulator P jest lepszy i po co to?”, „Co jest z danych, a co Twoje?” (20 neuronów odruchu, dynamika neuronów, kamera i dekodery to model lub inżynieria, [nasze_wyniki.md §1][nw]), „Co zrobiła AI, a co Ty?” oraz „Kto za to zapłaci?”.

## Wnioski

Wartość tego projektu leży w metodzie i w odwadze zadania pytania, na które odpowiedź może być „prawie nic”. Liczby z kontroli (38/40 wobec 3/40 i 0/40) są mocne, a to, że prosty regulator wygrywa i swoistość połączeń jest niepewna, nie osłabia pitchu, tylko go uwiarygodnia, bo dokładnie tego Fundacja i sędziowie ISEF szukają (jasne kontrole, ograniczenia, nieukrywanie błędów) ([Society for Science][isef], [5 Zasad][zasady]). Konkurencja pokazuje, że „mózg muchy w symulowanym ciele” jest już powszechne, a najsłabszym punktem wszystkich (także hobbystów z dronami i czworonogiem) jest brak potwierdzonego testu na sprzęcie. Dlatego jeden przetestowany obrót podstawy z kontrolą przetasowaną będzie wart więcej niż kolejna symulacja.

Dla inwestora kluczowa jest zmiana pytania. Nie „czy to się opłaca?”, tylko „czy ten człowiek zrobi uczciwy pomiar z małym budżetem?”. To pytanie możesz udowodnić dużo szybciej niż model biznesowy. Nie masz dziś dowodu na oszczędność energii, na przewagę nad klasycznym sterowaniem ani na zastosowanie w ORLEN-ie. Wolno Ci to nazwać kierunkiem, nie wynikiem.

## Ograniczenia tego raportu

Raport opiera się na czterech notatkach i nie sprawdziłem niczego poza nimi. Liczby z `nasze_wyniki.md` cytują raporty projektu, których nie przeliczałem od nowa. Kwoty finansowania firm (Opteran, Cortical Labs, Figure, PI) pochodzą z agregatorów i prasy i bywają niespójne. Regulamin Fundacji i programów ORLEN nie został sprawdzony w pełnym tekście (kwoty 2026, limit wieku, kwalifikowalność symulacji). Wyników finału Explory 2026 nie znaleziono. Koszt Twojego sprzętu nie jest udokumentowany w projekcie.

## Źródła

Notatki wejściowe (folder `/Users/admin/so101_fly_project/research_notes/Projekt mózgu muchy dla inwestorów/`):

[nw]: <../research_notes/Projekt mózgu muchy dla inwestorów/nasze_wyniki.md>
[kw]: <../research_notes/Projekt mózgu muchy dla inwestorów/konkurencja_stan_wiedzy.md>
[ri]: <../research_notes/Projekt mózgu muchy dla inwestorów/rynek_inwestorzy.md>
[ke]: <../research_notes/Projekt mózgu muchy dla inwestorów/konkurs_explory.md>

Źródła zewnętrzne (z notatek):

[ls]: https://livescience.com/health/neuroscience/new-map-of-a-male-fly-central-nervous-system-includes-all-166-000-neurons-and-enables-direct-comparisons-to-female-fly-brain
[shiu]: https://collaborate.princeton.edu/en/publications/a-drosophila-computational-brain-model-reveals-sensorimotor-proce/
[eon]: https://eon.systems/updates/embodied-brain-emulation
[eonfund]: https://untappedventures.substack.com/p/untapped-ventures-invests-in-eon
[fbb]: https://www.doriantodd.com/projects/fly-brain-bridge/
[fd]: https://raw.githubusercontent.com/SpikeCalls/FlyDrones/HEAD/README.md
[elektor]: https://elektormagazine.com/articles/ai-a-worm-brain-powering-a-lego-robot
[flybody]: https://janelia.org/news/artificial-intelligence-brings-a-virtual-fly-to-life
[cl]: https://en.wikipedia.org/wiki/Cortical_Labs
[opt]: https://tech.eu/2022/06/24/opteran-weaves-in-12-million-to-develop-ai-driven-by-brain-biomimicry-inspired-by-insects
[dealroom]: https://dealroom.co/companies/opteran/
[sandia]: https://arxiv.org/abs/2508.16792
[froststar]: https://github.com/Froststar16/connectome-control
[lerobot]: https://github.com/huggingface/lerobot
[mm]: https://www.marketsandmarkets.com/Market-Reports/neuromorphic-chip-market-227703024.html
[gv]: https://www.grandviewresearch.com/press-release/global-neuromorphic-computing-market
[rp]: https://www.reportprime.com/neuromorphic-computing-r11603
[bc]: https://www.businesswire.com/news/home/20251210514718/en/BrainChip-Announces-25-Million-USD-Funding-Ahead-of-CES-to-Power-Next-Gen-Edge-AI
[mf]: https://www.fool.com.au/2026/08/26/brainchip-shares-half-year-results-show-revenue-up-loss-widens/
[hala]: https://siliconangle.com/2024/04/17/intel-unveils-powerful-brain-inspired-neuromorphic-chip-system-energy-efficient-ai-workloads/
[innatera]: https://www.unite.ai/innatera-secures-21m-to-drive-neuromorphic-ai-to-1-billion-devices-by-2030
[iea]: https://www.iea.org/reports/energy-and-ai/executive-summary
[figure]: https://www.therobotreport.com/figure-ai-raises-1b-in-series-c-funding-toward-humanoid-robot-development/
[pi]: https://dealroom.co/news/127095-robot-ai-startup-physical-intelligence-seeks-1b-at-11b-valuation/
[techcrunch]: https://techcrunch.com/2025/04/28/hugging-face-releases-a-3d-printed-robotic-arm-starting-at-100
[iprz]: https://wartowiedziec.pl/polityka-spoleczna/81788-100-grantow-dla-mlodych-naukowcow-po-2-tys-zl-na-wlasne-badania
[mw]: https://wartowiedziec.pl/rozwoj-i-fundusze/81832-trwa-nabor-do-programu-moge-wiecej-na-stypendia-przeznaczono-1-mln-zl
[skylight]: https://www.orlen.pl/en/about-the-company/innovations/news/We-have-announced-the-14th-round-of-recruitment-for-the-ORLEN-Skylight-accelerator-program
[vc]: https://vc.orlen.pl/en/about-us
[orlen19]: https://www.orlen.pl/en/about-the-company/media/press-releases/archive/2019/december/modern-technologies-improve-the-security-of-orlens-production-plant-in-plock
[bankier]: https://www.bankier.pl/wiadomosc/PKN-Orlen-chce-zwiekszyc-wykorzystanie-dronow-8268084.html
[anybotics]: https://www.businesswire.com/news/home/20230516005081/en/ANYbotics-Secures-50M-Series-B-Funding-to-Revolutionize-Industrial-Inspection-with-its-Four-Legged-Robotic-Workforce
[byb]: https://blog.backyardbrains.com/2017/05/the-3000000-spike-byb-sales-milestone/
[sdg9]: https://sdgs.un.org/goals/goal9
[reg]: https://cloud.fzt.org.pl/index.php/s/QQPhH8AuRP722oy
[sfe]: https://cloud.fzt.org.pl/index.php/s/uEAlkNcDpSmYXbu
[jurorzy]: https://cloud.fzt.org.pl/index.php/s/yjWrnSCa8QfyUPc
[uczestnik]: https://cloud.fzt.org.pl/index.php/s/GFOwfYpWQRZ0yIR
[zasady]: https://cloud.fzt.org.pl/index.php/s/1UBTzZbnW0V6vgT
[form]: https://explory.pl/wp-content/uploads/Konkurs_Explory_2027_-Zgloszenie.pdf
[isef]: https://www.societyforscience.org/isef/grand-award/criteria/
