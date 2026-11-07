# Base is arch-specific (homeassistant/amd64-addon-otbr vs aarch64-addon-otbr).
# CI passes ARCH=amd64 / ARCH=aarch64 per platform, then stitches a multi-arch manifest.
# Renovate bumps ARG VERSION (and upstream_version.txt) when HA publishes a new OTBR app.
#
# renovate: datasource=docker depName=homeassistant/amd64-addon-otbr versioning=docker
ARG VERSION=3.3.0
ARG ARCH=amd64
FROM docker.io/homeassistant/${ARCH}-addon-otbr:${VERSION}

COPY rootfs /
