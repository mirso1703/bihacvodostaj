# Bihać Vodostaj za Home Assistant

Integracija čita javne podatke hidroloških stanica Agencije za vodno područje rijeke Save sa vodostaji.voda.ba. Ne treba token ni SolarSense server.

## Instalacija

Kopiraj `custom_components/bihac_vodostaj` u `/config/custom_components/bihac_vodostaj`, restartuj Home Assistant i dodaj **Bihać Vodostaj** iz Postavke → Uređaji i usluge. Izaberi jednu ili više stanica. Ripač (Una, 2035) je početni izbor. Stanice se kasnije mogu promijeniti kroz Konfiguriši.

## Senzori i alarmi

Svaka stanica dobija vodostaj (cm), proticaj (m³/s), službeni status, vrijeme mjerenja, porast u 3/24 h i promjenu cm/h iz prethodnih satnih mjerenja. Ripač ima lokalne pragove 180 cm (dijelovi puta), 200 cm (put poplavljen) i 250 cm (voda na parcelama).

Integracija emituje događaj `bihac_vodostaj_alert` za dostignut prag, približavanje (15 i 10 cm) i brzi rast. Događaj nosi `severity: urgent`, `title`, `message`, `station`, `level_cm` i `kind`. Napravi Home Assistant automatizaciju koja na taj događaj poziva `notify.mobile_app_...`; uključi kritičnu obavijest u notify pozivu ako želiš da probije nečujni režim. Primjer:

```yaml
alias: Hitni vodostaj
triggers:
  - trigger: event
    event_type: bihac_vodostaj_alert
actions:
  - action: notify.mobile_app_telefon
    data:
      title: "{{ trigger.event.data.title }}"
      message: "{{ trigger.event.data.message }}"
      data:
        push:
          sound:
            name: default
            critical: 1
            volume: 1
```

Zadani prag za Ripač je 180 cm, upozorenja su 15/10 cm prije praga, a brzi rast je 15 cm za 3 sata. Ostale stanice dobijaju isti podesivi prag; prag, margine i rast mijenjaju se u opcijama integracije. Izvor uglavnom osvježava mjerenja jednom na sat; integracija provjerava svakih 15 minuta. Podatak stariji od 6 sati označen je kao zastario.

Vodostaj u cm je očitanje vodomjera, ne dubina vode niti direktna procjena poplave na drugoj lokaciji. Lokalni pragovi treba da odgovaraju izabranoj stanici i mjestu.
