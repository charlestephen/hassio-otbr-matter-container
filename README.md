# hassio-otbr-matter-container

Multi-arch OpenThread Border Router image plus a **Compose** stack that runs
stock **Home Assistant Container**, **OTBR**, and the official **Python Matter
Server** together on host networking so Thread/Matter works without Home
Assistant OS.

**OTBR image** (multi-arch `linux/amd64` + `linux/arm64`):

- GHCR: `ghcr.io/charlestephen/hassio-otbr-matter-container:latest`
- Docker Hub: `docker.io/charlestephen/hassio-otbr-matter-container:latest`

**Base:** `homeassistant/{amd64,aarch64}-addon-otbr:latest` (HA OTBR **3.3.0** /
OTBR POSIX v2026.09.0). Packaging lineage:
[ownbee/hass-otbr-docker](https://github.com/ownbee/hass-otbr-docker),
multi-arch pattern from
[wittdennis/homeassistant-otbr](https://github.com/wittdennis/homeassistant-otbr).

Defaults target a **ConBee II** flashed with Phoscon Thread RCP firmware
(experimental; Phoscon prefers ConBee III for production Thread).

Build definition: `Containerfile`. Stack definition: `compose.yml`.

## How the three containers talk

All three services use `network_mode: host`. That is intentional: Matter/Thread
need the host’s IPv6 stack, mDNS, and (for commissioning) Bluetooth/D-Bus.
There is no bridge “link” to configure.

| Piece | Listens on host | Home Assistant uses |
|-------|-----------------|---------------------|
| OTBR REST | `http://127.0.0.1:8081` | **Open Thread Border Router** integration URL |
| OTBR web (optional) | `http://127.0.0.1:8080` | Browser only |
| Matter Server WebSocket | `ws://127.0.0.1:5580/ws` | **Matter** integration URL |
| Home Assistant UI | `http://127.0.0.1:8123` | You |

Because HA shares the host network namespace, `127.0.0.1` inside the HA
container **is** the host — so Matter and OTBR are reached without publishing
extra ports or putting containers on a user-defined network.

```text
  ┌─────────────────────────────────────────────────────────────┐
  │ Host network namespace                                      │
  │  HA :8123  ←→  Matter :5580/ws  ←→  Thread/Matter devices   │
  │  HA        ←→  OTBR   :8081     ←→  ConBee II RCP (Thread)  │
  └─────────────────────────────────────────────────────────────┘
```

If Home Assistant already runs elsewhere (not in this compose file), point its
integrations at the **host IP** instead of loopback, e.g.
`http://10.0.3.4:8081` and `ws://10.0.3.4:5580/ws`, and still run `otbr` +
`matter-server` with host networking on the machine that has the radio + BT.

## Prerequisite (host + LAN)

1. **IPv6 on LAN** (ULA is fine). UniFi: static ULA (e.g. from
   https://unique-local-ipv6.com/), SLAAC, IPv6 DNS; enable mDNS/IGMP as needed.
2. **Host sysctl:**

   ```
   net.ipv6.conf.all.disable_ipv6 = 0
   net.ipv4.conf.all.forwarding = 1
   net.ipv6.conf.all.forwarding = 1
   net.ipv6.conf.all.accept_ra_rt_info_max_plen = 64
   net.ipv6.conf.all.accept_ra = 2
   ```

3. `modprobe tun`. Firewall: allow `8123`, `8081`, `8080`, `5580` if filtered.
4. ConBee II flashed with Phoscon OT RCP (GCFFlasher +
   [conbee2 firmware](https://phoscon.de/downloads/openthread/firmware/conbee2/)),
   **not** Nabu Casa `universal-silabs-flasher`.

## ConBee II OTBR settings

| Setting | Value | Why |
|---------|--------|-----|
| `DEVICE` | by-id `…Thread_RCP__ConBee_II…` | Stable path |
| `BAUDRATE` | `115200` | Not ZBT-1’s `460800` |
| `FLOW_CONTROL` | `1` | Phoscon: HW flow control **on** (ConBee III: off) |
| `AUTOFLASH_FIRMWARE` | `0` | Never flash Nabu Casa firmware onto a ConBee |
| Volume | `…:/data/thread` | Persistent Thread dataset |

## Bring-up (stock HA + OTBR + Matter)

1. Copy env and set radio + uplink:

   ```bash
   cp .env.example .env
   # edit DEVICE / DEVICE_HOST / BACKBONE_IF (ip -br link)
   mkdir -p ha_config otbr_data matter_data
   ```

2. Start the stack (`podman compose` or `docker compose`):

   ```bash
   podman compose up -d
   ```

3. Open Home Assistant (`http://<host>:8123`) and finish onboarding if new.

4. **Open Thread Border Router** → Add integration → URL:

   ```text
   http://127.0.0.1:8081
   ```

   (Use the host LAN IP if HA is not on this compose/`host` network.)

5. **Thread** → Configure → select the OTBR network → **Make preferred** →
   enable **Used for Android + iOS credentials**. Reset border router only if
   you intend to wipe the Thread dataset.

6. **Matter** → Add integration → connect to the Matter Server WebSocket:

   ```text
   ws://127.0.0.1:5580/ws
   ```

   HA Container does **not** auto-install the Matter add-on; this WebSocket is
   how the stock container is wired to Matter Server.

7. Companion app → Troubleshooting → **Sync Thread credentials** (often twice
   until it reports the phone and HA share the same network).

8. Add Matter devices via the companion app (Bluetooth for first commission).

Optional: set Thread credentials in the Matter dashboard
(`/config/matter/dashboard`) from the Thread integration “i” dataset if
commissioning stalls.

### Already have Home Assistant Container?

Keep your existing `homeassistant` service; compose only `otbr` +
`matter-server` from this file (or delete/disable the `homeassistant` service).
Requirements that do not change:

- HA must use **`network_mode: host`** (or otherwise reach host `:8081` / `:5580`).
- Mount `/run/dbus` into HA if you want BT-assisted flows from HA’s side too.
- Same integration URLs as above (`127.0.0.1` when HA is host-networked on the
  same machine).

### Health checks

```bash
podman compose ps
curl -sf http://127.0.0.1:8081/node/dataset/active | head
curl -sf http://127.0.0.1:5580/   # Matter Server info page
podman logs otbr --tail 80
podman logs matter-server --tail 80
```

OTBR log should show `uart-baudrate=115200` and `&uart-flow-control` for ConBee II.
Spinel timeouts usually mean wrong baud, flow control, device path, or firmware.

## OTBR environment reference

| ENV | Description |
|-----|-------------|
| `DEVICE` | Serial path for the RCP |
| `BAUDRATE` | ConBee II: `115200` |
| `FLOW_CONTROL` | `1` = hardware RTS/CTS |
| `AUTOFLASH_FIRMWARE` | Keep `0` for ConBee |
| `OTBR_LOG_LEVEL` | `debug`…`emergency` |
| `OTBR_REST_PORT` / `OTBR_WEB_PORT` | Default `8081` / `8080` |
| `OTBR_WEB` | `1`/`0` web UI |
| `FIREWALL` / `NAT64` | OTBR firewall / NAT64 |
| `BACKBONE_IF` / `TREL_IF` | Host uplink (and optional TREL) |
| `THREAD_BETA` | `1` for HA image beta OTBR binaries |

Further reading:

* https://github.com/home-assistant-libs/python-matter-server/blob/main/docs/docker.md
* https://www.home-assistant.io/integrations/matter
* https://www.home-assistant.io/integrations/thread
* https://www.phoscon.de/en/openthread/doc
* https://github.com/home-assistant/addons/tree/master/openthread_border_router

## Build

CI builds each arch (`ARCH=amd64` / `ARCH=aarch64`) from `Containerfile`,
pushes digests to GHCR, publishes a multi-arch manifest, and mirrors tags to
Docker Hub (`DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`).

```bash
podman build -f Containerfile --build-arg ARCH=aarch64 --build-arg VERSION=latest -t otbr:local .
```

## Sponsor

[Buy Me a Coffee](https://buymeacoffee.com/charlestephen)
