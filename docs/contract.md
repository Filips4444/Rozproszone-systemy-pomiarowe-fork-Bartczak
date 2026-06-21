## Dokumentacja Projektu: Rozproszone Systemy Pomiarowe

### 1. Architektura i Stos Technologiczny
System realizuje kompletny przepływ danych (end-to-end) od fizycznego pomiaru, aż po analizę i wizualizację.
* **Urządzenia brzegowe:** Mikrokontrolery ESP32 programowane z wykorzystaniem środowiska PlatformIO.
* **Warstwa komunikacyjna (Docker):** Broker MQTT pełniący rolę centralnej magistrali danych.
* **Backend (Docker):** * **Ingestor:** Skrypt napisany w języku Python odpowiadający za odbiór wiadomości MQTT, ich walidację i przekazywanie do bazy.
    * **Baza Danych:** Relacyjna baza PostgreSQL przechowująca metadane urządzeń oraz historię pomiarów.
    * **REST API:** Aplikacja w frameworku Flask udostępniająca dane klientom.
* **Klient i Wizualizacja:** Wizualizacja danych wykonana za pomocą aplikacji przeglądarkowej.

### 2. Przepływ Danych (End-to-End)
1. ESP32 generuje unikalny identyfikator na podstawie fizycznych adresów układu (eFuse/MAC) i łączy się z siecią Wi-Fi.
2. Mikrokontroler cyklicznie przesyła zebrane dane na wyznaczony temat brokera MQTT.
3. Ingestor nasłuchuje (subskrybuje) określonych tematów MQTT, po czym parsuje i waliduje przychodzące pliki JSON.
4. Po pozytywnej weryfikacji Ingestor tworzy nowy rekord w tabeli `measurements` w bazie PostgreSQL.
5. Serwis Flask odczytuje dane z bazy na żądanie HTTP i przesyła je w postaci JSON do klienta.

### 3. Kontrakt Danych
Zarówno układ pomiarowy, jak i baza danych wykorzystują ściśle zdefiniowany standard wiadomości.

**Struktura Tematów MQTT:**
* Pomiary: `lab/<group_id>/<device_id>/<sensor>`.
* Status układu: `lab/<group_id>/<device_id>/status`.

**Wymagany format JSON (Pomiary):**
Każda wiadomość przesyłana z czujnika musi bezwzględnie zawierać następujące pola:
* `device_id`: Unikalny ciąg znaków (napis).
* `sensor`: Zdefiniowany typ czujnika (napis).
* `value`: Zmierzona wartość (liczba).
* `ts_ms`: Znacznik czasu w formacie Unix Epoch (w milisekundach) generowany na podstawie synchronizacji z serwerem NTP.

**Przykładowy format danych JSON:**
```json
{
  "schema_version": 1,
  "group_id": "g03",
  "device_id": "esp32-ab12cd34",
  "sensor": "temperature",
  "value": 24.5,
  "unit": "C",
  "ts_ms": 1742030400000,
  "seq": 15
}
```
*(Uwaga: Pola takie jak `schema_version`, `group_id`, `unit` czy `seq` są opcjonalne*

### 4. Główne Endpointy REST API (Metody GET)
* `/health` - Służy do diagnostyki i sprawdzenia, czy serwis Flask działa poprawnie.
* `/measurements` - Zwraca listę 20 ostatnich pomiarów w systemie.
* `/measurements/latest` - Zwraca pojedynczy, najnowszy odnotowany pomiar.
* `/measurements/history` - Umożliwia filtrowanie wyników z bazy poprzez parametry URL, takie jak `device_id`, `sensor` oraz `limit`.
* `/dashboard` - Prezentuje pomiary z bazy danych w postaci wykresu (warstwa prezentacyjna)

### 5. Bezpieczeństwo i Niezawodność
* **Bezpieczeństwo Sieciowe:** Konfiguracja w pliku `docker-compose.yml` izoluje usługi w dedykowanej sieci wewnętrznej (`bridge`), likwidując publiczną ekspozycję kontenerów oraz bazy danych. Broker MQTT nasłuchuje na standardowym, wewnętrznym porcie 1883.
* **Monitorowanie Sieci:** W kodzie C++ (PlatformIO) zaimplementowano funkcje non-blocking do wznawiania utraconych sesji Wi-Fi i MQTT.
* **Raportowanie Awarii:** Wdrożono wzorzec *Last Will and Testament (LWT)*, dzięki któremu broker samoistnie opublikuje flagę statutu `offline`, w sytuacji nagłego zaniku zasilania lub komunikacji ESP32.

---

### 6. Znane Problemy w Działaniu
**Brak komunikacji pomiędzy Brokerem MQTT a bazą PostgreSQL.**
* **Opis defektu:** Dane z ESP32 prawidłowo trafiają do brokera MQTT, jednak nie następuje ich zapis do odpowiednich tabel bazy PostgreSQL.
* **Prawdopodobna przyczyna:** Głównym obszarem problemowym jest kontener **Ingestora**. Należy poddać weryfikacji skrypt Pythona odpowiedzialny za działanie tego serwisu. Wąskim gardłem może być niepoprawna definicja subskrybowanego tematu w funkcji wywoławczej `on_connect`, zbyt rygorystyczne reguły odrzucania wiadomości JSON podczas walidacji w funkcji `on_message` lub nieautoryzowana komunikacja (błędy uwierzytelniania) podczas łączenia się Ingestora z bazą PostgreSQL przez skrypt `db.py`.
**Brak sygnalizacji utraty połączenia z urządzeniem:**
* **Opis defektu:** W momencie, gdy połączenie z mikrokontrolerem ESP32 zostanie przerwane, system nie generuje ani nie wyświetla żadnego komunikatu informującego o tym, że urządzenie znajduje się w stanie offline. Mimo obecności mechanizmu LWT na poziomie brokera, informacja ta nie trafia do warstwy prezentacyjnej.
**Generowanie danych pomiarowych:**
* **Opis defektu:** Płytka pomiarowa nie wykonuje w tym momencie rzeczywistych odczytów z fizycznych sensorów. Przesyłane pakiety danych zawierają wartości liczbowe ustawione na sztywno bezpośrednio w kodzie źródłowym oprogramowania.
**Decoupling warstwy prezentacyjnej:**
* Aktualnie wykresy pomiarów prezentowane są bezpośrednio z poziomu aplikacji Flask (/dashboard). W celu separacji, powłoka prezentacyjna powinna zostać całkowicie oddzielona w formie autonomicznej aplikacji webowej. Backend będzie pełnił wówczas rolę bezstanowego REST API dostarczającego dane w formacie JSON.
