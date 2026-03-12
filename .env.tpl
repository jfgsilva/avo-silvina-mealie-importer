# Mealie Importer — Secret Template
# Copy to .env and fill in values, or inject via 1Password / Bitwarden.

# ── Cleartext ────────────────────────────────────────────────────────────────
# MEALIE_URL=https://mealie.example.com
# MEALIE_TOKEN=your-api-token

# ── 1Password (op inject -i .env.tpl -o .env) ────────────────────────────────
MEALIE_URL={{ op://YourVault/Mealie/url }}
MEALIE_TOKEN={{ op://YourVault/Mealie/token }}

# ── Bitwarden (run after `bw unlock`) ────────────────────────────────────────
# MEALIE_URL=$(bw get item "Mealie" | jq -r '.fields[] | select(.name=="url") | .value')
# MEALIE_TOKEN=$(bw get password "Mealie API Token")

# ── Optional tuning ──────────────────────────────────────────────────────────
# IMPORT_DELAY_SECONDS=1.0
