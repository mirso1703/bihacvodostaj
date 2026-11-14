# Bihać Vodostaj za Home Assistant

[![Dodaj Bihać Vodostaj u HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mirso1703&repository=bihacvodostaj&category=integration)

Nakon instalacije preko HACS-a, [otvori Home Assistant i dodaj integraciju](https://my.home-assistant.io/redirect/config_flow_start/?domain=bihac_vodostaj).

Integracija čita javne podatke hidroloških stanica Agencije za vodno područje rijeke Save sa vodostaji.voda.ba. Ne treba token ni SolarSense server.

Ako dugme otvori adresu `homeassistant.local` koju Safari ne može dosegnuti, My Home Assistant u tom pregledniku ima zapamćenu pogrešnu adresu. Otvori [My Home Assistant](https://my.home-assistant.io/), zamijeni adresu instance adresom dostupnom s tog uređaja (npr. `http://IP_ADRESA:8123` na kućnoj mreži ili tvojom Nabu Casa/javnom HTTPS adresom), pa ponovo klikni dugme. URL se čuva lokalno u pregledniku. ([službene upute](https://www.home-assistant.io/integrations/my/))

Ako link i dalje ne radi, u HACS-u ručno idi na **Integrations → ⋮ → Custom repositories**, dodaj `https://github.com/mirso1703/bihacvodostaj` kao **Integration**, instaliraj integraciju i restartuj Home Assistant.

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
