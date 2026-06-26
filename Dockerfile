# Narrow Highway — Concordance 2.0
# Sovereign engine. The hot path is stdlib; sympy/scipy/numpy power the math moat and a
# few verifiers, cryptography powers seal signing. Data (the keeping, the WEB Bible,
# Strong's) is mounted at /data, never baked into the image (it is gitignored).
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY site ./site

# Engine + the optional runtime deps for full functionality (the moat + signing).
RUN pip install --no-cache-dir -e ".[math]" cryptography

# Data lives on a mounted volume; point every store at it.
ENV CONCORDANCE_DATA_DIR=/data \
    CONCORDANCE_STRONGS_DIR=/data/strongs \
    PYTHONUNBUFFERED=1

EXPOSE 8000
# Default = the secular .com reach. Override --surface witness for the .org face.
CMD ["python", "-m", "concordance", "serve", "--host", "0.0.0.0", "--port", "8000", "--surface", "secular"]
