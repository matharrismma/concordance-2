#!/usr/bin/env bash
# Vendor the Rampart ML layer for 100% sovereign self-hosting — no runtime CDN, no Hugging Face.
# Produces (gitignored, ~90 MB):
#   site/vendor/transformers/transformers.web.min.js   (transformers.js browser ESM)
#   site/vendor/ort/ort-wasm-simd-threaded*.wasm + .jsep.mjs   (ONNX Runtime Web)
#   site/vendor/rampart/index.js                       (Rampart guard ESM)
#   site/models/nationaldesignstudio/rampart/...        (config + tokenizer + q4 ONNX)
#
# Build-time only: needs node+npm and curl. NOTHING runs node at serve time — these are static
# assets served by the engine. The page's import map + rampart-ml.js wire them up.
#
#   bash tools/vendor_rampart.sh [SITE_DIR]      # default SITE_DIR: site
set -euo pipefail

S="${1:-site}"
RV=0.1.3   # @nationaldesignstudio/rampart  (pinned)
TV=4.2.0   # @huggingface/transformers      (pinned)
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "vendoring Rampart $RV + transformers.js $TV into $S/ (staging in $TMP)…"
( cd "$TMP" && npm init -y >/dev/null 2>&1 && \
  npm install "@nationaldesignstudio/rampart@$RV" "@huggingface/transformers@$TV" >/dev/null 2>&1 )
NM="$TMP/node_modules"

mkdir -p "$S/vendor/transformers" "$S/vendor/ort" "$S/vendor/rampart" \
         "$S/models/nationaldesignstudio/rampart/onnx"
cp "$NM/@huggingface/transformers/dist/transformers.web.min.js" "$S/vendor/transformers/"
cp "$NM/@huggingface/transformers/dist/ort-wasm-simd-threaded.jsep.mjs" "$S/vendor/ort/"
cp "$NM"/onnxruntime-web/dist/ort-wasm-simd-threaded*.wasm "$S/vendor/ort/"
cp "$NM/@nationaldesignstudio/rampart/dist/index.js" "$S/vendor/rampart/"

B=https://huggingface.co/nationaldesignstudio/rampart/resolve/main
for f in config.json tokenizer.json tokenizer_config.json special_tokens_map.json vocab.txt; do
  curl -sL "$B/$f" -o "$S/models/nationaldesignstudio/rampart/$f"
done
curl -sL "$B/onnx/model_q4.onnx" -o "$S/models/nationaldesignstudio/rampart/onnx/model_q4.onnx"

echo "done. vendored:"
du -sh "$S/vendor/transformers" "$S/vendor/ort" "$S/vendor/rampart" "$S/models/nationaldesignstudio/rampart"
