FROM python:3.11-bookworm AS builder
WORKDIR /build
COPY requirements.txt .
RUN python -m pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.11-slim-bookworm
WORKDIR /opt/wallet-check
COPY --from=builder /wheels /tmp/wheels
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --no-index --find-links=/tmp/wheels -r requirements.txt \
    && rm -rf /tmp/wheels
COPY Bech32PassHunter.py fasttrack.txt LICENSE ./
USER 65532:65532
ENTRYPOINT ["python", "-I", "-B", "Bech32PassHunter.py"]
