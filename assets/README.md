# Logo assets

`gwitg_logo.png` is the adopted primary logo. Keep this file unchanged. It has a transparent background and dark lettering, so use it on light surfaces.

`gwitg_mark_on_white.png` is a compact crop of the existing symbol, with a white background. Use it at 32 CSS pixels or larger; below that size, the branching lines and node details may lose clarity.

For dark surfaces, use `gwitg_logo_on_white.png` or `gwitg_mark_on_white.png`. Each file has an opaque white background that provides contrast. Keep the white surface visible around the artwork rather than placing the transparent logo directly on a dark color.

`gwitg_social_preview.png` is a 1280 × 640 image with a white background, ready for GitHub Social Preview.

## Regenerate derived assets

Run `assets/build_assets.sh` from any directory with ImageMagick 7 installed. It only composites the adopted logo on white, crops the symbol, and places the logo on the Social Preview canvas. The script does not modify `gwitg_logo.png`.

The adopted source checksum is `6456d7c6422ff02e7dddd3bff8a30d543ffd8214c98c3348ae4bee951f5c135d` (SHA-256).
