# Real GTFS Data Provenance

Both source ZIPs were manually obtained through the official data-request mechanisms, as reported by the project owner. Their contents were inspected read-only from the original archives in `data/external/`. The archives were not extracted to disk, transformed, or overwritten. No Mobility Database mirror was used.

Retrieval dates and direct download URLs are **Not determined from available source material.** The filesystem modification times (2026-09-29 08:51 for TGSRTC and 2026-09-29 08:50 for HMRL, as displayed locally) are not treated as verified retrieval timestamps.

## TGSRTC

- **Dataset:** TGSRTC static GTFS Schedule feed
- **Producer organization:** Telangana State Road Transport Corporation (agency name observed in `agency.txt`)
- **Source organization:** Telangana State Road Transport Corporation
- **Source URL:** [TGSRTC Open Data](https://tgsrtc.telangana.gov.in/open-data)
- **Direct download URL:** Not determined from available source material.
- **Source type:** Official source; not a mirror
- **Acquisition method:** Manually obtained through the official data-request mechanism, as reported by the project owner. The official page links to a request form; the direct file-delivery URL is not determined.
- **Retrieval date:** Not determined from available source material.
- **Original filename:** `TGSRTC_GTFS.zip`
- **File size:** 37,364,557 bytes (37.364557 MB, decimal)
- **SHA-256:** `74f343762f6900a6e23ecacb08beeb13df00bcc25e0859d93867ca02d8a7500a`
- **ZIP entries:** 8
- **GTFS service period:** 2026-09-01 through 2031-09-01, observed in both `calendar.txt` and `feed_info.txt`
- **Feed version:** `20260901`, observed in `feed_info.txt`
- **License/terms:** [TGSRTC Open Data terms](https://tgsrtc.telangana.gov.in/open-data). The page states free, non-exclusive use subject to its terms, attribution, no implication of endorsement, and provision as-is; terms are governed by Indian law.
- **Required attribution:** “Contains data provided by TGSRTC”
- **Known limitations:** Static scheduled service only; it does not provide observed passenger counts. The publisher states updates are not guaranteed. This archive omits optional calendar-exception and fare tables. The verified retrieval date and direct ZIP URL are unavailable.
- **Access notes:** Official source request mechanism, manually completed by the project owner. No automated form submission, scraping, or mirror access was used in this work.

## HMRL

- **Dataset:** HMRL static GTFS Schedule feed
- **Producer organization:** Hyderabad Metro Rail (agency name observed in `agency.txt`)
- **Source organization:** Hyderabad Metro Rail Ltd.
- **Source URL:** [HMRL Open Data](https://hmrl.co.in/open-data/)
- **Direct download URL:** Not determined from available source material.
- **Source type:** Official source; not a mirror
- **Acquisition method:** Manually obtained through the official data-request mechanism, as reported by the project owner. The official page links to a request form; the direct file-delivery URL is not determined.
- **Retrieval date:** Not determined from available source material.
- **Original filename:** `HMRL_GTFS.zip`
- **File size:** 2,996,166 bytes (2.996166 MB, decimal)
- **SHA-256:** `c35bda6768e71fdef742080d1436a5d751d7b2a64f6882839574d768a6498f2a`
- **ZIP entries:** 10
- **GTFS service period:** 2026-09-02 through 2030-01-01, observed in both `calendar.txt` and `feed_info.txt`
- **Feed version:** Not determined from available source material; `feed_info.txt` has no `feed_version` column
- **License/terms:** [HMRL Open Data terms](https://hmrl.co.in/open-data/). The page states free, non-exclusive use subject to its terms, attribution, no implication of endorsement, and provision as-is; terms are governed by Indian law.
- **Required attribution:** “Contains data provided by Hyderabad Metro Rail Ltd.”
- **Known limitations:** Static scheduled service only; it does not provide observed passenger counts. The publisher states updates are not guaranteed. Some optional fields are blank (reported in the quality report). The verified retrieval date and direct ZIP URL are unavailable.
- **Access notes:** Official source request mechanism, manually completed by the project owner. No automated form submission, scraping, or mirror access was used in this work.

## Verification Notes

SHA-256 checksums were computed from the original files in place. Each ZIP passed Python ZIP integrity checking (`testzip()` returned no bad member). The manifest at `data/external/manifest.json` contains the machine-readable subset of these verified facts. The two feeds remain separate and must not be merged before a feed-aware normalization step.