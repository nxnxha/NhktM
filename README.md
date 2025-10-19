
# Nhkt — Voice Lock (préfixe `$`) — GitHub ➜ Railway

- Salon vocal cible: `1400519979660742896`
- Rôles admin à bloquer: `1400518143595778079`, `1400518147097759815`
- Quand tu WL un user/role → accès au vocal accordé automatiquement.

## Local
```bash
pip install -r requirements.txt
cp .env.example .env  # ajoute ton token
python nhkt_bot.py
```

## Railway
- Déploie ce dossier via GitHub
- Variables: `DISCORD_TOKEN` (+ optionnel `PREFIX`, `VOICE_CHANNEL_ID`, `AUTHORIZED_ADMINS`, `BLOCKED_ADMIN_ROLE_IDS`)
- Le start est `python nhkt_bot.py`
