# ZeroTier — удалённый доступ через интернет

## Как это работает

Веб-панель, приём MAVLink (14550/udp) и MediaMTX (RTSP/HLS/WebRTC) слушают
`0.0.0.0` — все интерфейсы. Как только у Pi появляется IP в сети ZeroTier,
все сервисы автоматически доступны и по нему — без проксирования и
дополнительного кода. Оператор с ноутбуком в той же ZeroTier-сети работает с
машиной из любой точки интернета.

## Подключение (вкладка «ZeroTier»)

1. Впиши **Network ID** — 16-значный hex-идентификатор твоей сети
   (создаётся на [my.zerotier.com](https://my.zerotier.com)).
2. Опционально — **Central API-токен** (Account → API Access Tokens): с ним
   нода авторизуется в сети автоматически. Без токена после «Подключиться»
   нужно вручную поставить галочку Auth новому устройству на my.zerotier.com
   (стандартное поведение ZeroTier).
   - Токен хранится локально в `data/zerotier_state.json` (права 0600) и не
     отправляется никуда, кроме официального `https://api.zerotier.com`.
3. **Подключиться** — `zerotier-cli join`. **Сохранить** — только запомнить
   настройки. **Отключиться** — `zerotier-cli leave`.
4. Блок «Статус»: Node ID, статус сети (`OK` — подключено и авторизовано,
   `ACCESS_DENIED` — ждёт авторизации), назначенный IP.

## Использование

- **Панель**: `http://<IP_ZeroTier>:8080` с любого устройства в той же сети.
- **Mission Planner**: UDPCl на `<IP_ZeroTier>:14550` — готовый адрес
  показывает вкладка «Управление».
- **Видео**: вкладка «Видео» → блок «Трансляция через ZeroTier» — RTSP-ссылка
  и GStreamer-pipeline на ZeroTier-IP, параллельно с локальными.

## Диагностика

```bash
sudo systemctl status zerotier-one
sudo zerotier-cli info
sudo zerotier-cli listnetworks
```

- «zerotier-cli не найден» в панели → переустанови ZeroTier
  (`curl -s https://install.zerotier.com | sudo bash`) и перезапусти сервис.
- Статус завис на `REQUESTING_CONFIGURATION`/`ACCESS_DENIED` → устройство не
  авторизовано на my.zerotier.com (или авто-авторизация по токену не
  сработала — смотри логи `journalctl -u roverlink`).

Права: `zerotier-cli` требует root — панель вызывает его через узкое
sudoers-правило NOPASSWD только на этот бинарник (см. [security.md](security.md)).
