# Explory 2026 – odpowiedzi do formularza zgłoszeniowego

Wersja docelowa zatwierdzona przez właściciela projektu 9 XI 2026 (redakcja ChatGPT, pkt 23 skrócony do limitu 255 znaków).
Ten tekst wyznacza, jak mówimy o projekcie: plakat, pitch i kolejne raporty mają być z nim zgodne.

### 22. Tytuł projektu (70/80 znaków)

Czy biologiczny konektom muszki może sterować ramieniem robota SO-101?

### 23. Krótki opis projektu (245/255 znaków)

Z konektomu MaleCNS buduję sieć impulsową inspirowaną mózgiem muszki owocowej. W symulacji MuJoCo sprawdzam, czy rzeczywiste połączenia mogą sterować ramieniem SO-101 i czy ich układ ma znaczenie wobec sieci kontrolnych i regulatora klasycznego.

### 24. Liczba autorów

1

### 25. Liczba mentorów

1 (rodzic; regulamin dopuszcza rodzica jako mentora, który tylko doradza)

### 26. Rola autora

Jestem autorem projektu i odpowiadam za jego koncepcję oraz kierunek badań. Wybieram pytania badawcze, formułuję hipotezy, decyduję o porównywanych wariantach i analizuję wyniki. Korzystam z narzędzi AI do pomocy w programowaniu, analizie kodu i przeglądzie literatury. Mentor pomaga mi w organizacji projektu i sprawach sprzętowych. Szczegółowy podział pracy człowieka i AI opisuję w punkcie 36.

*Uwaga: autor powinien dopasować ten tekst do rzeczywistego zakresu swojej samodzielnej pracy. Nie należy przypisywać sobie implementacji, której faktycznie dokonało AI.*

### 27. Inspiracja

Naukowcy udostępniają coraz dokładniejsze mapy połączeń neuronów, czyli konektomy. Zaciekawiło mnie, czy taka mapa może służyć nie tylko do badania mózgu, ale również do sterowania urządzeniem. Postanowiłem sprawdzić to na przykładzie muszki owocowej i otwartego ramienia robota SO-101. Interesuje mnie nie tylko to, czy sieć potrafi wywołać ruch, lecz także czy rzeczywista organizacja połączeń neuronowych ma znaczenie dla uzyskanego zachowania.

### 28. Kategoria

Nauki inżynieryjno-techniczne (automatyka, informatyka techniczna)

### 29. Kategoria STEAM

M – Informatyka (E – Inżynieria dopiero po teście na prawdziwym ramieniu)

### 30. Cel Zrównoważonego Rozwoju

Cel 9: Innowacyjność, przemysł, infrastruktura (9.5 – wzmacnianie badań naukowych)

### 31. Pełny opis projektu

Konektom to mapa połączeń między neuronami. W projekcie wykorzystuję publiczne dane MaleCNS, opisujące układ nerwowy samca muszki owocowej, udostępnione przez naukowców z Janelia Research Campus.

Z wybranych fragmentów konektomu buduję impulsową sieć neuronową (SNN). Neurony komunikują się za pomocą impulsów, a struktura i wagi połączeń są wyprowadzane z danych konektomicznych. Nie jest to kompletny cyfrowy mózg muszki, lecz model wybranych obwodów nerwowych.

Sieć jest połączona z symulatorem fizycznym MuJoCo, w którym znajduje się robotyczne ramię SO-101. Jednym z badanych obwodów jest droga od neuronów wzrokowych LC10a przez neurony pośrednie do neuronów zstępujących DNa02. U muszki neurony zstępujące uczestniczą w sterowaniu ruchem. W moim modelu aktywność DNa02 jest wykorzystywana do sterowania obrotem podstawy ramienia w odpowiedzi na położenie obserwowanego obiektu.

Drugim kierunkiem jest rozszerzenie modelu o informacje dotykowe. Badam, czy wybrane obwody mechanosensoryczne nóg muszki można wykorzystać do przetwarzania informacji o kontakcie robota z obiektem. Jest to osobny, eksperymentalny kierunek: nie zakładam, że biologiczny obwód dotykowy muszki jest automatycznie odpowiednikiem mechanizmu chwytania przez robotyczny chwytak.

Najważniejsza jest metoda badawcza. Porównuję sieć z danymi z odpowiednimi wariantami kontrolnymi, między innymi z sieciami o zmienionej organizacji połączeń, oraz z klasycznym regulatorem. Dzięki temu sprawdzam, czy wyniki rzeczywiście zależą od struktury biologicznej, a nie tylko od samego faktu użycia sieci neuronowej.

Oddzielam też sterowanie badanym modelem od mechanizmów bezpieczeństwa symulatora. Nie zakładam z góry, że sieć biologiczna jest lepsza od klasycznych metod — chcę to sprawdzić eksperymentalnie.

Obecnie badania prowadzone są w symulacji. Dalszym celem jest stopniowa walidacja modelu i, po spełnieniu wymagań technicznych oraz bezpieczeństwa, przeniesienie go na fizyczne ramię SO-101.

### 32. Podobne rozwiązania i różnice

Istnieją projekty wykorzystujące konektomy i biologicznie inspirowane modele układów nerwowych do sterowania symulowanymi lub robotycznymi ciałami. Przykładami są badania nad symulowanym ciałem muszki, takie jak NeuroMechFly i flybody, oraz projekty łączące dane konektomiczne z robotyką.

Mój projekt koncentruje się na innym problemie: wykorzystaniu wybranych obwodów konektomu muszki do sterowania ramieniem-manipulatorem SO-101.

Istotną częścią pracy są eksperymenty kontrolne. Nie wystarczy mi pokazać, że sieć potrafi wywołać ruch. Sprawdzam również, jak zmienia się wynik po zmianie organizacji połączeń oraz jak wypada on na tle klasycznego regulatora.

Projekt ma charakter badawczy: jego celem jest sprawdzenie, jaki wkład w sterowanie może mieć struktura biologicznego konektomu, a nie udowodnienie z góry, że takie rozwiązanie jest lepsze od innych metod.

### 33. Dotychczasowe testy i niebezpieczne substancje

Wszystkie dotychczasowe testy opisane w tym zgłoszeniu przeprowadzono w symulacji MuJoCo. Nie wykonywałem jeszcze testów sterowania na fizycznym ramieniu SO-101.

W jednym z testów celowania w piłeczkę sieć oparta na danych konektomicznych osiągnęła 38 trafień na 40 prób. W tym samym zestawie testów sieć z przetasowanymi połączeniami osiągnęła 3/40, a sieć z zamienionymi stronami 0/40. Klasyczny regulator osiągnął 40/40, czyli w tym zadaniu był dokładniejszy.

W innych eksperymentach badałem, czy przewaga sieci opartej na danych utrzymuje się przy zmianie odległości obiektu i innych warunków. Wyniki wskazują, że wpływ dokładnej struktury połączeń nie jest jednakowy we wszystkich warunkach. Nie traktuję więc pojedynczego udanego testu jako dowodu ogólnej przewagi konektomu.

Przeprowadziłem również wstępne testy związane z dotykiem i sterowaniem chwytakiem. Ich wyniki traktuję jako pilotażowe: samo osiągnięcie poprawnego ruchu nie dowodzi jeszcze, że odpowiada za niego konkretna biologiczna organizacja połączeń.

Ważną częścią projektu jest dokumentowanie również hipotez, które nie potwierdziły się w eksperymentach. Nie używam niebezpiecznych substancji ani nie prowadzę doświadczeń na zwierzętach lub ludziach.

### 34. Badania na zwierzętach lub ludziach

Nie. Korzystam wyłącznie z publicznych danych (konektom MaleCNS). Sam nie prowadzę żadnych doświadczeń na zwierzętach ani na ludziach.

### 35. Wpływ na środowisko

Bardzo mały. Projekt zużywa tylko prąd do laptopa i małego ramienia robota. Nie produkuje odpadów ani zanieczyszczeń. Nie twierdzę, że projekt oszczędza energię, bo tego nie mierzyłem.

### 36. Pomoc sztucznej inteligencji

Tak. W dużym zakresie korzystałem z narzędzi sztucznej inteligencji, przede wszystkim Claude Code, a także ChatGPT. AI pomagało mi w programowaniu, analizie kodu, przygotowywaniu i sprawdzaniu eksperymentów, wyszukiwaniu literatury oraz krytycznej ocenie wyników.

Claude Code wygenerował znaczną część kodu sieci neuronowej i symulacji na podstawie przygotowanych przeze mnie poleceń i założeń. Narzędzia AI pomagały również w wykonywaniu części analiz i eksperymentów. Nie przedstawiam więc całego kodu jako napisanego samodzielnie.

Moim zadaniem było określanie kierunku projektu, wybór pytań i hipotez badawczych, podejmowanie decyzji o kolejnych testach oraz analiza i ocena uzyskanych wyników. Korzystałem z AI również do szukania błędów i słabych punktów w przyjętych założeniach. Ostateczne wnioski muszą być jednak uzasadnione wynikami i sprawdzone, a nie przyjmowane tylko dlatego, że zaproponowało je narzędzie AI.

AI pomagało mi także w redagowaniu zgłoszenia na konkurs.
