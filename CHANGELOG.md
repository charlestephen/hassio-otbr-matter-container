# Changelog

All notable changes to this project are documented here. Upstream OpenThread
Border Router app notes are quoted from
[home-assistant/addons `openthread_border_router`](https://github.com/home-assistant/addons/tree/master/openthread_border_router).

## 3.3.0

- Initial public release of `hassio-otbr-matter-container` (multi-arch OTBR image
  plus Compose stack for stock Home Assistant Container + Matter Server).
- Pin base image to `homeassistant/{amd64,aarch64}-addon-otbr:3.3.0`.
- ConBee II defaults: baud `115200`, hardware flow control on, autoflash off.
- CI publishes GHCR + Docker Hub manifests; Slack notify on build failures/recovery.
- Renovate bumps the OTBR base; Publish GitHub Release fills the Releases page with local + upstream notes.

> Upstream Home Assistant OTBR app 3.3.0:
>
> - Bump to OTBR POSIX version fd872ab9 (tag v2026.09.0)
>   - Thread 1.4 Credentials Sharing (ePSKc): share Thread network credentials with other devices directly from the Web UI
>   - Web UI: QR codes are now generated locally instead of using a remote service
>   - Various fixes and stability improvements in OpenThread and OTBR
> - Bump beta to OTBR POSIX version cb4bdae2 (tag v2026.10.0)
>   - Routes to external networks announced by other Border Routers in the Thread network (e.g. Apple/Google) are no longer added to the host, which avoids routing loops and mesh congestion on multi Border Router networks. Routes to Thread devices are not affected
>   - Channel changes (pending dataset) are now confirmed with the Thread leader instead of being applied locally
>   - Various fixes and stability improvements in OpenThread and OTBR
> - Explicitly request the network permissions the app needs, in preparation for an upcoming Supervisor change
