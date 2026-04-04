# znamdizivis

A CLI tool that searches Croatian cadastral records ([uredjenazemlja.hr](https://oss.uredjenazemlja.hr)) for a person's name across all land parcels in a given geographic area.

It fetches every cadastral parcel ID within a bounding box via the WFS API, then checks each parcel's possession sheet for a name match.

## Usage

```bash
pip install -r requirements.txt
python main.py
```

You will be prompted for:
1. **Bounding box** — `lat_min, lon_min, lat_max, lon_max` (WGS84 / EPSG:4326)
2. **Name** — the name or surname to search for (case-insensitive)

Example coordinates for a small area in Zagreb:
```
45.82, 16.05, 45.83, 16.06
```

## Resume support

Progress is saved under `data/<name>/` after each parcel is checked:

| File | Contents |
|------|----------|
| `data/<name>/checked.txt` | Parcel IDs already inspected (no match) |
| `data/<name>/matches.json` | Parcels where the name was found |

If the run is interrupted (e.g. by rate limiting), simply re-run with the same inputs. Already-checked parcels are skipped automatically, and any matches found so far are preserved.

## Notes

- The API returns at most 1000 parcel IDs per request; larger areas are paginated automatically.
- The tool searches `possessionSheets[].possessors[].name` in the parcel info response.
- The `data/` directory is excluded from version control via `.gitignore`.
