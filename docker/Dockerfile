FROM python:3.12.4-slim

ENV MPLBACKEND=Agg \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work

COPY requirements-lock.txt /tmp/requirements-lock.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /tmp/requirements-lock.txt

CMD ["python", "scripts/run_reproducibility_checks.py"]
