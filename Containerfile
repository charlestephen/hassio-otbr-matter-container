# Base is arch-specific (homeassistant/amd64-addon-otbr vs aarch64-addon-otbr).
# CI passes ARCH=amd64 / ARCH=aarch64 per platform, then stitches a multi-arch manifest.
#
# Pin/float: VERSION=latest tracks HA's current OTBR app image (3.3.0 as of 2026-10).
# renovate: datasource=docker depName=homeassistant/amd64-addon-otbr versioning=docker
ARG VERSION=latest
ARG ARCH=amd64
FROM docker.io/homeassistant/${ARCH}-addon-otbr:${VERSION}

COPY rootfs /
