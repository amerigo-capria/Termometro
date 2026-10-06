# Termometro Xiaomi — Manuale utente

Applicazione per leggere temperatura e umidità dal sensore **Xiaomi Mi Temperature and Humidity Monitor 2** (modello **LYWSD03MMC** / **NUN4126GL**) tramite Bluetooth del PC.

---

## Cosa ti serve

- PC con **Windows 10 o 11**
- **Bluetooth** attivo
- Il termometro acceso e nelle vicinanze
- L’app **Xiaomi Home** chiusa sul telefono (se resta aperta può bloccare la connessione)

Non serve installare Python.

---

## Installazione (versione portatile)

1. Estrai lo ZIP `TermometroXiaomi-portatile.zip` in una cartella a scelta  
   (es. Desktop o Documenti).
2. Apri la cartella estratta `TermometroXiaomi`.
3. Avvia **`TermometroXiaomi.exe`**.

Importante: lascia insieme l’exe e la cartella **`_internal`**.  
Se sposti solo l’exe, il programma non funziona.

Non è necessario un installer.

---

## Primo avvio

All’apertura l’app:

1. Cerca i termometri Bluetooth nelle vicinanze (circa 8 secondi)
2. Li elenca ordinati per **segnale più forte** (di solito = più vicino)
3. Se ne trova almeno uno, legge subito temperatura e umidità

Sul display stile LCD vedi:

- temperatura in °C
- umidità in %
- faccina comfort (come sul sensore)
- barre del segnale Bluetooth

---

## Pulsanti e opzioni

| Comando | Cosa fa |
|--------|---------|
| **Aggiorna** | Nuova lettura a richiesta. Si collega pochi secondi, poi si disconnette. |
| **Scansiona** | Cerca di nuovo i sensori e aggiorna i livelli di segnale. |
| **Sensore** | Scegli quale termometro usare se ne hai più di uno. |
| **Auto ogni N min** | Letture automatiche. Consigliato: 10 minuti o più. |
| **Solo LCD** | Riduce la finestra al solo display. |

### Modalità Solo LCD

- Resta solo il rettangolo del display, sempre in primo piano
- **Trascina** con il mouse per spostarlo
- **Doppio click**, **click destro** oppure **Esc** per tornare alla finestra completa

---

## Batteria del sensore

Per non scaricare troppo la batteria:

- preferisci **Aggiorna** solo quando ti serve
- se usi l’auto-refresh, tieni intervalli lunghi (es. **10–30 minuti**)
- ogni lettura apre una connessione breve e poi la chiude

Non lasciare il telefono connesso in continua all’app Xiaomi Home sullo stesso sensore.

---

## Più sensori: quale è il più vicino?

Nell’elenco **Sensore** vedi:

- barre segnale (`████`, `███░`, …)
- valore in **dBm** (es. `-55 dBm` è più forte di `-75 dBm`)
- eventuale segno **★ vicino** sul migliore

Dopo una scansione, il primo della lista è di solito quello più vicino.

---

## Problemi frequenti

**Non trova nessun termometro**

- Attiva il Bluetooth del PC
- Avvicina il sensore
- Chiudi Xiaomi Home sul telefono
- Premi di nuovo **Scansiona**

**Errore di connessione / nessuna lettura**

- Il sensore potrebbe essere già connesso a un altro dispositivo
- Allontanati da interferenze Wi‑Fi/USB 3 molto vicine all’antenna Bluetooth
- Riprova con **Aggiorna**

**“Failed to load Python DLL”**

- Stai avviando un file sbagliato, oppure manca la cartella `_internal`
- Usa solo `TermometroXiaomi.exe` dentro la cartella completa estratta dallo ZIP

**La finestra Solo LCD non torna grande**

- Usa doppio click / Esc / click destro sul display
- Se resta strana, chiudi e riapri l’applicazione

---

## Privacy e rete

Il programma funziona **solo in locale** sul PC.  
Non invia dati su Internet e non richiede account.

---

## Note tecniche (facoltative)

- Protocollo: Bluetooth Low Energy (BLE)
- Lettura via notifiche GATT del firmware stock Xiaomi
- Build portatile generata con PyInstaller

Per assistenza sullo sviluppo del progetto, consulta i file sorgente nella cartella del progetto Cursor `Termometro`.
