# Mio

Mio is a local Subscription Converter deployment built from sub-web, subconverter, and a small mihomo YAML converter.

## Services

- `subweb`: customized Subscription Converter UI on `127.0.0.1:58080`.
- `subconverter`: local subconverter backend on `127.0.0.1:25500`.
- `mihomo-converter`: lightweight converter and editable direct-rule API on `127.0.0.1:25600`.

## Run

```bash
cp .env.example .env
docker compose up -d --build
```

Open `http://127.0.0.1:58080/`.

## Notes

- `DEFAULT_SOURCE_URL` is intentionally empty by default. Do not commit private subscription URLs.
- Direct rules are stored in `mihomo-converter/direct-rules.txt` and exposed through `GET/PUT /direct-rules`.
- The UI is customized at build time by `subweb-custom/customize-subconverter.js`.

