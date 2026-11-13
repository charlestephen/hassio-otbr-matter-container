# hassio-otbr-matter-container

A multi-arch (`linux/amd64`, `linux/arm64`) OpenThread Border Router image built on Home Assistant's OTBR app, plus a Docker Compose stack that runs **Home Assistant Container**, **OTBR** and the official **Python Matter Server** together. It lets Thread and Matter work without Home Assistant OS.

Defaults target a **ConBee II** flashed with Phoscon Thread RCP firmware, which is experimental. Other Thread radios work if you set the device, baud rate and flow control to match.

- Source and full documentation: https://github.com/charlestephen/hassio-otbr-matter-container
- Issues: https://github.com/charlestephen/hassio-otbr-matter-container/issues
- Also published at `ghcr.io/charlestephen/hassio-otbr-matter-container`

## Tags

| Tag | Meaning |
|---|---|
| `latest` | Most recent build of `main`. |
| `<version>`, `<major>.<minor>` | A release that follows the upstream OTBR app version, for example `3.3.0` and `3.3`. |
| `sha-<commit>` | The image built from that commit. |

## Host requirements

All three containers use host networking, because Matter and Thread need the host's IPv6 stack, mDNS and, for commissioning, Bluetooth and D-Bus.

1. **IPv6 on your LAN.** A unique local (ULA) prefix with SLAAC is fine.
2. **Kernel settings** on the Docker host:

   ```
   net.ipv6.conf.all.disable_ipv6 = 0
   net.ipv4.conf.all.forwarding = 1
   net.ipv6.conf.all.forwarding = 1
   net.ipv6.conf.all.accept_ra_rt_info_max_plen = 64
   net.ipv6.conf.all.accept_ra = 2
   ```

   Put them in `/etc/sysctl.d/` and run `sudo sysctl --system`.
3. **The `tun` module:** `sudo modprobe tun`.
4. **A Thread radio** (RCP) connected over USB, and a stable path to it such as `/dev/serial/by-id/...`.
5. **Firewall:** allow TCP 8123, 8081, 8080 and 5580 if you filter them.

## Quick start with Docker Compose

Create a working directory and an `.env` file. Replace every value below with your own:

```ini
TZ=America/New_York

# Your host's LAN network interface, from: ip -br link
BACKBONE_IF=eth0

# Radio path on the host (use the by-id path from: ls /dev/serial/by-id/)
DEVICE_HOST=/dev/serial/by-id/usb-REPLACE-WITH-YOUR-RADIO-if00
# Path the container uses internally. Leave as is.
DEVICE=/dev/ttyACM0

# ConBee II Thread RCP. Use your radio's values if it is different.
BAUDRATE=115200
FLOW_CONTROL=1

# Matter Bluetooth adapter index (hci0 is 0)
MATTER_BT_ADAPTER=0
```

Save this as `compose.yml`:

```yaml
services:
  hassio:
    container_name: hassio
    image: ghcr.io/home-assistant/home-assistant:stable
    restart: unless-stopped
    privileged: true
    network_mode: host
    environment:
      TZ: ${TZ:-America/New_York}
    volumes:
      - /srv/hassio:/config
      - /etc/localtime:/etc/localtime:ro
      - /run/dbus:/run/dbus:ro

  thread:
    container_name: thread
    image: charlestephen/hassio-otbr-matter-container:latest
    restart: unless-stopped
    privileged: true
    network_mode: host
    cap_add:
      - SYS_ADMIN
      - NET_ADMIN
    environment:
      DEVICE: ${DEVICE:-/dev/ttyACM0}
      BACKBONE_IF: ${BACKBONE_IF:-eth0}
      BAUDRATE: ${BAUDRATE:-115200}
      FLOW_CONTROL: ${FLOW_CONTROL:-1}
      AUTOFLASH_FIRMWARE: "0"
      FIREWALL: "1"
      NAT64: "1"
      OTBR_REST_PORT: "8081"
      OTBR_WEB_PORT: "8080"
      OTBR_WEB: "1"
      OTBR_LOG_LEVEL: notice
    devices:
      - ${DEVICE_HOST}:${DEVICE:-/dev/ttyACM0}
      - /dev/net/tun:/dev/net/tun
    volumes:
      - /srv/thread:/data/thread

  matter:
    container_name: matter
    image: ghcr.io/home-assistant-libs/python-matter-server:stable
    restart: unless-stopped
    network_mode: host
    privileged: true
    security_opt:
      - apparmor:unconfined
    volumes:
      - /srv/matter:/data
      - /run/dbus:/run/dbus:ro
      - /etc/localtime:/etc/localtime:ro
    command:
      - --storage-path
      - /data
      - --paa-root-cert-dir
      - /data/credentials
      - --bluetooth-adapter
      - ${MATTER_BT_ADAPTER:-0}
      - --primary-interface
      - ${BACKBONE_IF:-eth0}
```

Create the data directories and start it:

```bash
sudo mkdir -p /srv/hassio /srv/thread /srv/matter
docker compose --env-file .env up -d
docker compose ps
```

To update:

```bash
docker compose pull && docker compose up -d
```

If you already run Home Assistant Container, keep it and remove the `hassio` service. It must use `network_mode: host`, or otherwise be able to reach host ports 8081 and 5580.

## Running only the Thread border router

```bash
docker run -d --name thread --restart unless-stopped \
  --privileged --network host \
  --cap-add SYS_ADMIN --cap-add NET_ADMIN \
  --device /dev/serial/by-id/usb-REPLACE-WITH-YOUR-RADIO-if00:/dev/ttyACM0 \
  --device /dev/net/tun:/dev/net/tun \
  -e DEVICE=/dev/ttyACM0 \
  -e BACKBONE_IF=eth0 \
  -e BAUDRATE=115200 \
  -e FLOW_CONTROL=1 \
  -e AUTOFLASH_FIRMWARE=0 \
  -v /srv/thread:/data/thread \
  charlestephen/hassio-otbr-matter-container:latest
```

Replace the radio path with yours and `eth0` with your LAN interface. Keep `/srv/thread` on persistent storage: it holds your Thread network dataset.

## Connect Home Assistant

Once the stack is up (all three share the host network, so `127.0.0.1` reaches the host):

1. Open `http://<host>:8123` and finish onboarding if the instance is new.
2. Add the **Open Thread Border Router** integration with the URL `http://127.0.0.1:8081`.
3. In **Thread**, open the OTBR network, choose **Make preferred**, and enable **Used for Android + iOS credentials**.
4. Add the **Matter** integration with the URL `ws://127.0.0.1:5580/ws`. Home Assistant Container does not install the Matter add-on, so this WebSocket is how it reaches the Matter Server.
5. In the companion app, go to Troubleshooting and run **Sync Thread credentials** (it can take two tries). Then add Matter devices from the app, using Bluetooth for the first commissioning.

If Home Assistant runs on another machine, use the Docker host's LAN address instead of `127.0.0.1`.

## Ports

| Port | Use |
|---|---|
| 8081 | OTBR REST API (what Home Assistant uses) |
| 8080 | OTBR web UI (optional, `OTBR_WEB=0` turns it off) |
| 5580 | Matter Server WebSocket (`/ws`) |
| 8123 | Home Assistant UI |

## OTBR environment variables

| Variable | Description |
|---|---|
| `DEVICE` | Serial path of the radio (RCP) inside the container. |
| `BAUDRATE` | ConBee II uses `115200`. Other radios often use `460800`. |
| `FLOW_CONTROL` | `1` turns hardware RTS/CTS on. |
| `AUTOFLASH_FIRMWARE` | Keep `0` for ConBee radios, so Nabu Casa firmware is never flashed onto them. |
| `BACKBONE_IF` | Host network interface used as the uplink. |
| `TREL_IF` | Optional interface for TREL. |
| `OTBR_REST_PORT`, `OTBR_WEB_PORT` | Default `8081` and `8080`. |
| `OTBR_WEB` | `1` or `0` to turn the web UI on or off. |
| `OTBR_LOG_LEVEL` | `debug` to `emergency`. |
| `FIREWALL`, `NAT64` | Turn the OTBR firewall and NAT64 on or off. |
| `THREAD_BETA` | `1` to use the beta OTBR binaries from the Home Assistant image. |

## Health checks and logs

```bash
curl -sf http://127.0.0.1:8081/node/dataset/active | head
curl -sf http://127.0.0.1:5580/
docker logs thread --tail 80
docker logs matter --tail 80
```

For a ConBee II the OTBR log should show `uart-baudrate=115200` and `uart-flow-control`. Spinel timeouts usually mean the wrong baud rate, flow control, device path or firmware.

## License

See https://github.com/charlestephen/hassio-otbr-matter-container/blob/main/LICENSE
