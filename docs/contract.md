# Kontrakt danych MQTT — wersja v1

## 1. Struktura topicow MQTT

### Format topicu

```
lab/<group_id>/<device_id>/<sensor>
```

### Segmenty

| Segment      | Opis                          | Przyklad             |
|--------------|-------------------------------|----------------------|
| `lab`        | Glowny obszar projektu        | `lab`                |
| `group_id`   | Identyfikator grupy lab.      | `g03`                |
| `device_id`  | Identyfikator urzadzenia      | `esp32-AB12CD34`     |
| `sensor`     | Rodzaj danych / typ sensora   | `temperature`        |

### Przyklady topicow

```
lab/g03/esp32-AB12CD34/temperature
lab/g03/esp32-AB12CD34/humidity
lab/g03/esp32-AB12CD34/pressure
```

### Topic statusowy

Komunikaty statusowe sa oddzielone od pomiarowych:

```
lab/<group_id>/<device_id>/status
```

### Zasady nazewnictwa

- male litery (z wyjatkiem identyfikatora urzadzenia generowanego z MAC)
- bez spacji i polskich znakow
- stala kolejnosc segmentow: `lab / group / device / sensor`
- wartosc pomiarowa NIE jest czescia nazwy topicu
- topic opisuje klase komunikatu, nie pojedyncza probke

### Filtrowanie (wildcard)

| Wzorzec                          | Co filtruje                        |
|----------------------------------|------------------------------------|
| `lab/g03/#`                      | Wszystkie dane grupy g03           |
| `lab/g03/esp32-AB12CD34/#`       | Wszystkie dane jednego urzadzenia  |
| `lab/+/+/temperature`            | Pomiary temperatury ze wszystkich  |
| `lab/+/+/+`                      | Wszystkie wiadomosci pomiarowe     |

---

## 2. Wiadomosc pomiarowa JSON (v1)

### Przykladowa wiadomosc

```json
{
  "schema_version": 1,
  "group_id": "g03",
  "device_id": "esp32-AB12CD34",
  "sensor": "temperature",
  "value": 24.5,
  "unit": "C",
  "ts_ms": 1742030400000,
  "seq": 15
}
```

### Opis pol

| Pole              | Typ      | Wymagane | Opis                                              |
|-------------------|----------|----------|----------------------------------------------------|
| `device_id`       | string   | tak      | Identyfikator urzadzenia (niepusty)                |
| `sensor`          | string   | tak      | Rodzaj sensora / typ danych                        |
| `value`           | number   | tak      | Wartosc pomiaru (liczba, nie tekst)                |
| `ts_ms`           | integer  | tak      | Czas pomiaru — milisekundy od epoch Unix (>0)      |
| `schema_version`  | integer  | nie      | Wersja kontraktu danych (domyslnie 1)              |
| `group_id`        | string   | nie      | Identyfikator grupy laboratoryjnej                 |
| `unit`            | string   | nie      | Jednostka fizyczna (np. "C", "%", "hPa")           |
| `seq`             | integer  | nie      | Numer sekwencyjny wiadomosci (>=0)                 |

---

## 3. Pola wymagane

Kazda wiadomosc pomiarowa **musi** zawierac:

- `device_id` — niepusty string
- `sensor` — string
- `value` — number (int lub float)
- `ts_ms` — dodatnia liczba calkowita (Unix epoch w milisekundach)

---

## 4. Pola opcjonalne

Pola zalecane, ale nieobowiazkowe:

- `schema_version` — wersja kontraktu (integer, domyslnie 1)
- `group_id` — identyfikator grupy (string)
- `unit` — jednostka pomiaru (string, powinna odpowiadac typowi sensora)
- `seq` — numer sekwencyjny (integer >= 0)

---

## 5. Reguly walidacji

| Pole        | Regula                                                       |
|-------------|--------------------------------------------------------------|
| `device_id` | Niepusty string                                              |
| `sensor`    | Niepusty string                                              |
| `value`     | Musi byc liczba (int lub float), NIE string                  |
| `ts_ms`     | Dodatnia liczba calkowita (> 0)                              |
| `unit`      | Jesli obecne, musi byc stringiem odpowiadajacym sensorowi    |
| `seq`       | Jesli obecne, musi byc liczba calkowita >= 0                 |

Wiadomosc niespelniajaca powyzszych regul powinna zostac odrzucona lub zalogowana jako bledna przez ingestor.

---

## 6. Przyklad wiadomosci poprawnej

**Topic:** `lab/g03/esp32-AB12CD34/temperature`

```json
{
  "schema_version": 1,
  "group_id": "g03",
  "device_id": "esp32-AB12CD34",
  "sensor": "temperature",
  "value": 24.5,
  "unit": "C",
  "ts_ms": 1742030400000,
  "seq": 1
}
```

---

## 7. Przyklady wiadomosci blednych

### Blad 1: `value` jako string zamiast liczby + brak `ts_ms`

```json
{
  "device_id": "esp32-AB12CD34",
  "sensor": "temperature",
  "value": "24.5",
  "unit": "C"
}
```

**Powod odrzucenia:** Pole `value` jest stringiem (`"24.5"`) zamiast liczba (`24.5`). Brakuje wymaganego pola `ts_ms`.

### Blad 2: brak `device_id`

```json
{
  "sensor": "humidity",
  "value": 55.2,
  "unit": "%",
  "ts_ms": 1742030400000
}
```

**Powod odrzucenia:** Brak wymaganego pola `device_id`.

### Blad 3: `ts_ms` jako wartosc ujemna

```json
{
  "device_id": "esp32-AB12CD34",
  "sensor": "temperature",
  "value": 22.1,
  "ts_ms": -100
}
```

**Powod odrzucenia:** Pole `ts_ms` musi byc dodatnia liczba calkowita.

---

## 8. Wiadomosc statusowa

**Topic:** `lab/<group_id>/<device_id>/status`

```json
{
  "schema_version": 1,
  "device_id": "esp32-AB12CD34",
  "status": "online",
  "ts_ms": 1742030400000
}
```

Komunikaty statusowe pozwalaja sledzic dostepnosc urzadzen. Mozliwe wartosci pola `status`: `"online"`, `"offline"`.