# Huawei SmartLogger Home Assistant Integration

Dieses HACS-kompatible Custom-Component liest über Modbus TCP die String-Daten eines Huawei SmartLogger (z. B. für SUN2000-100KTL-M1 Wechselrichter) aus und stellt sie in Home Assistant als Sensoren bereit. Für jeden PV-String werden Spannung, Stromstärke und Leistung bereitgestellt, sodass Du die Werte in Home Assistant protokollieren und visualisieren kannst.

## Voraussetzungen

- Huawei SmartLogger mit aktiviertem Modbus TCP (Standardport 502)
- Home Assistant Installation mit HACS
- Netzwerk-Konnektivität zwischen Home Assistant und SmartLogger

## Installation über HACS

1. Repository zu HACS hinzufügen (`https://github.com/example/HuaweiWr2HA`).
2. Unter **HACS → Integrationen** nach "Huawei SmartLogger" suchen und installieren.
3. Home Assistant neu starten.

Alternativ kannst Du den Ordner `custom_components/huawei_smartlogger` manuell in Dein Home-Assistant-Konfigurationsverzeichnis kopieren.

## Konfiguration (configuration.yaml)

```yaml
huawei_smartlogger:
  host: 10.10.40.251
  port: 502
  slave_id: 1
  scan_interval: 30  # Sekunden
  strings:
    - name: "String 1"
      voltage_register: 32016
      current_register: 32017
      power_register: 32018
      voltage_scale: 0.1
      current_scale: 0.1
      power_scale: 1.0
    - name: "String 2"
      voltage_register: 32019
      current_register: 32020
      power_register: 32021
      voltage_scale: 0.1
      current_scale: 0.1
      power_scale: 1.0
    # ... weitere Strings
```

> 💡 **Hinweis:** Die oben verwendeten Registeradressen entsprechen dem offiziellen Huawei Modbus-Register-Mapping für SUN2000-Geräte. Bitte prüfe das aktuelle Dokument "SUN2000 Modbus Interface Definitions" für Dein Wechselrichter- bzw. SmartLogger-Modell und passe die Register ggf. an. Die Werte werden mit den angegebenen Skalierungsfaktoren multipliziert. Laut Modbus-Spezifikation liegen Spannung und Strom typischerweise in 0,1er-Schritten vor, während die Leistung bereits in Watt geliefert wird.

## Sensoren in Home Assistant

Nach der Konfiguration erstellt die Integration für jeden definierten String drei Sensoren:

- `<Stringname> Voltage` (V)
- `<Stringname> Current` (A)
- `<Stringname> Power` (W)

Alle Sensoren sind als `measurement` klassifiziert und eignen sich für die Langzeitaufzeichnung über den Recorder oder InfluxDB.

## Fehlerbehebung

- Prüfe mit `nc` oder `telnet`, dass der Port 502 erreichbar ist.
- Stelle sicher, dass der konfigurierte `slave_id` mit der SmartLogger-Einstellung übereinstimmt (Standard: 1).
- Aktiviere bei Bedarf das Debug-Logging in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.huawei_smartlogger: debug
```

## Lizenz

MIT License
