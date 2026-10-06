"""Funzioni BLE condivise per Xiaomi LYWSD03MMC / NUN4126GL."""

from __future__ import annotations

import asyncio
import struct
from dataclasses import dataclass
from datetime import datetime

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

SERVICE_UUID = "ebe0ccb0-7a0a-4b0c-8a1a-6ff2997da3a6"
TEMP_HUM_UUID = "ebe0ccc1-7a0a-4b0c-8a1a-6ff2997da3a6"
BATTERY_UUID = "00002a19-0000-1000-8000-00805f9b34fb"


@dataclass
class Reading:
    address: str
    name: str
    temperature: float
    humidity: int
    voltage: float | None = None
    battery_percent: int | None = None
    timestamp: datetime | None = None

    def comfort_face(self) -> str:
        """Faccia comfort come sul display originale Xiaomi."""
        t, h = self.temperature, self.humidity
        if 18.0 <= t <= 28.0 and 40 <= h <= 60:
            return "happy"
        if t < 16.0 or t > 30.0 or h < 30 or h > 70:
            return "sad"
        return "neutral"


@dataclass
class DeviceInfo:
    address: str
    name: str
    rssi: int | None = None


def looks_like_thermometer(device: BLEDevice, adv: AdvertisementData) -> bool:
    name = (device.name or adv.local_name or "").lower()
    if not name:
        return False
    if name in ("lywsd03mmc", "mijia_lywsd03mmc"):
        return True
    return any(name.startswith(prefix) for prefix in ("atc_", "pvvx"))


def parse_temp_humidity(data: bytearray | bytes) -> tuple[float, int, float | None]:
    if len(data) < 3:
        raise ValueError(f"Payload troppo corto: {data.hex()}")

    temperature = struct.unpack_from("<h", data, 0)[0] / 100.0
    humidity = int(data[2])
    voltage_v: float | None = None
    if len(data) >= 5:
        voltage_mv = struct.unpack_from("<H", data, 3)[0]
        voltage_v = voltage_mv / 1000.0
    return temperature, humidity, voltage_v


def rssi_bars(rssi: int | None) -> str:
    """Indicatore testuale del segnale (4 barre). RSSI più alto = più vicino."""
    if rssi is None:
        return "····"
    if rssi >= -55:
        return "████"
    if rssi >= -65:
        return "███░"
    if rssi >= -75:
        return "██░░"
    if rssi >= -85:
        return "█░░░"
    return "░░░░"


def rssi_label(rssi: int | None) -> str:
    if rssi is None:
        return "n/d"
    return f"{rssi} dBm"


async def scan_devices(timeout: float = 8.0) -> list[DeviceInfo]:
    """Scansiona e restituisce i sensori ordinati dal segnale più forte al più debole."""
    found: dict[str, DeviceInfo] = {}

    def callback(device: BLEDevice, adv: AdvertisementData) -> None:
        if not looks_like_thermometer(device, adv):
            return
        name = device.name or adv.local_name or "LYWSD03MMC"
        rssi = adv.rssi if getattr(adv, "rssi", None) is not None else None
        prev = found.get(device.address)
        if prev is None:
            found[device.address] = DeviceInfo(device.address, name, rssi)
            return
        # Tiene il nome più completo e l'RSSI più recente (o il migliore visto)
        if name and name != "LYWSD03MMC":
            prev.name = name
        if rssi is not None and (prev.rssi is None or rssi > prev.rssi):
            prev.rssi = rssi

    async with BleakScanner(detection_callback=callback):
        await asyncio.sleep(timeout)

    if not found:
        devices = await BleakScanner.discover(timeout=timeout)
        for d in devices:
            name = (d.name or "").lower()
            if any(k in name for k in ("lywsd", "mijia", "atc", "temp", "pvvx")):
                found[d.address] = DeviceInfo(d.address, d.name or "LYWSD03MMC", None)

    return sorted(
        found.values(),
        key=lambda d: d.rssi if d.rssi is not None else -999,
        reverse=True,
    )


async def read_once(
    address: str,
    *,
    name: str = "LYWSD03MMC",
    timeout: float = 20.0,
    notify_timeout: float = 12.0,
) -> Reading:
    """
    Connette, aspetta UNA notifica, disconnette subito.
    Minimizza il tempo di connessione (impatto batteria basso).
    """
    async with BleakClient(address, timeout=timeout) as client:
        if not client.is_connected:
            raise RuntimeError("Connessione fallita")

        battery: int | None = None
        try:
            raw = await client.read_gatt_char(BATTERY_UUID)
            battery = int(raw[0])
        except Exception:
            pass

        event = asyncio.Event()
        payload: dict[str, float | int | None] = {}

        def on_notify(_handle: int, data: bytearray) -> None:
            try:
                temp, hum, volt = parse_temp_humidity(data)
            except ValueError:
                return
            payload["temperature"] = temp
            payload["humidity"] = hum
            payload["voltage"] = volt
            event.set()

        await client.start_notify(TEMP_HUM_UUID, on_notify)
        try:
            await asyncio.wait_for(event.wait(), timeout=notify_timeout)
        except asyncio.TimeoutError as exc:
            raise TimeoutError(
                "Nessuna notifica dal sensore. Vicino? App Xiaomi Home chiusa?"
            ) from exc
        finally:
            try:
                await client.stop_notify(TEMP_HUM_UUID)
            except Exception:
                pass

    return Reading(
        address=address,
        name=name,
        temperature=float(payload["temperature"]),  # type: ignore[arg-type]
        humidity=int(payload["humidity"]),  # type: ignore[arg-type]
        voltage=payload.get("voltage"),  # type: ignore[arg-type]
        battery_percent=battery,
        timestamp=datetime.now(),
    )
