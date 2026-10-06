#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

magick assets/gwitg_logo.png \
  -background white -alpha remove -alpha off \
  assets/gwitg_logo_on_white.png

magick assets/gwitg_logo.png \
  -crop 310x248+155+25 +repage -resize '512x410!' \
  -background white -gravity center -extent 512x512 \
  assets/gwitg_mark_on_white.png

magick -size 1280x640 xc:white \
  \( assets/gwitg_logo.png -resize 560x420 \) \
  -gravity center -composite \
  assets/gwitg_social_preview.png
