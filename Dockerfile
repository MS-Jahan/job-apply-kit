# Smoke-test image: proves the kit's tests pass with a clean tectonic + poppler toolchain.
# Not for running the apply skills (those need a real browser and real Google credentials,
# neither of which belongs in an image). No credentials, no browser, nothing personal.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# tectonic: single static binary, no TeX Live install needed. Fetched directly (not via the
# drop-sh.fullyjustified.net installer) because that installer's architecture auto-detection picks
# the glibc build on aarch64 Linux, but upstream only publishes a musl build for that target; the
# musl binary runs fine on a glibc host since it is statically linked.
ARG TECTONIC_VERSION=0.17.0
RUN set -eu; \
    arch="$(uname -m)"; \
    case "$arch" in \
      x86_64) target="x86_64-unknown-linux-musl" ;; \
      aarch64) target="aarch64-unknown-linux-musl" ;; \
      *) echo "unsupported arch: $arch" >&2; exit 1 ;; \
    esac; \
    url="https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40${TECTONIC_VERSION}/tectonic-${TECTONIC_VERSION}-${target}.tar.gz"; \
    curl -fsSL "$url" | tar -xz -C /usr/local/bin tectonic

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# tectonic fetches its LaTeX format bundle (fonts/styles) file-by-file over the network on first use
# and caches each one under ~/.cache/tectonic — compiling a bare "hello world" document only warms the
# handful of core files it needs, NOT the extra packages (fontenc, lmodern, geometry, titlesec,
# enumitem, hyperref, xcolor) the real templates use. Warm the cache now, at build time (network
# available), by compiling one real CV and one real cover letter — the two distinct package sets in
# this repo's templates — so later `docker run --network none` (a sandboxed test run or CI) does not
# fail with "this bundle isn't cached, and we couldn't get it from the internet".
RUN mkdir -p /tmp/warm \
    && cp examples/templates/CV_FULLSTACK.tex examples/templates/CL_FULLSTACK.tex /tmp/warm/ \
    && cd /tmp/warm && tectonic -X compile CV_FULLSTACK.tex && tectonic -X compile CL_FULLSTACK.tex \
    && cd /app && rm -rf /tmp/warm

CMD ["bash", "tests/run.sh"]
