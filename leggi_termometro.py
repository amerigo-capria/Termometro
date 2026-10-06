"""
Lettura temperatura/umidità da Xiaomi Mijia Thermometer 2 (LYWSD03MMC / NUN4126GL)
via Bluetooth Low Energy (BLE).

Uso CLI:
  python leggi_termometro.py
  python leggi_termometro.py --scan
  python leggi_termometro.py AA:BB:CC:DD:EE:FF

GUI (display LCD):
  python gui_termometro.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from mijia_ble import read_once, scan_devices


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Legge dati da Xiaomi NUN4126GL / LYWSD03MMC via Bluetooth"
    )
    parser.add_argument(
        "address",
        nargs="?",
        help="Indirizzo MAC/UUID BLE del termometro (opzionale)",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Solo scansiona e elenca i termometri trovati",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=8.0,
        help="Secondi di scansione (default: 8)",
    )
    args = parser.parse_args()

    if args.scan or not args.address:
        print(f"Scansione BLE per {args.timeout:.0f}s...\n")
        devices = await scan_devices(timeout=args.timeout)
        if not devices:
            print(
                "Nessun termometro trovato.\n"
                "- Attiva il Bluetooth sul PC\n"
                "- Tieni il sensore vicino\n"
                "- Chiudi l'app Xiaomi Home sul telefono"
            )
            return 1

        print("Dispositivi candidati:")
        for i, d in enumerate(devices, 1):
            rssi = d.rssi if d.rssi is not None else "?"
            print(f"  {i}. {d.name}  [{d.address}]  RSSI={rssi}")

        if args.scan:
            return 0

        address = devices[0].address
        name = devices[0].name
        print(f"\nUso il primo: {address}\n")
    else:
        address = args.address
        name = "LYWSD03MMC"

    print(f"Connessione a {address}...")
    reading = await read_once(address, name=name)
    print("Connesso e disconnesso (lettura breve).\n")
    print(f"Temperatura: {reading.temperature:.2f} C")
    print(f"Umidita:     {reading.humidity} %")
    if reading.voltage is not None:
        print(f"Tensione:    {reading.voltage:.3f} V")
    if reading.battery_percent is not None:
        print(f"Batteria:    {reading.battery_percent} %")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nInterrotto.")
        raise SystemExit(130)
    except Exception as exc:  # noqa: BLE001
        print(f"Errore: {exc}", file=sys.stderr)
        raise SystemExit(1)
