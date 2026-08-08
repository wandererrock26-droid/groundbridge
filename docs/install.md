# Установка

## 0. Доставка проекта на Raspberry Pi

Проще всего — клонировать с GitHub прямо на Pi:

```bash
git clone https://github.com/wandererrock26-droid/groundbridge.git
cd groundbridge
```

Либо залить по scp со своего компьютера (SSH на Pi должен быть включён —
`sudo raspi-config` → Interface Options → SSH, или в Raspberry Pi Imager при
прошивке карты):

```bash
scp -r groundbridge pi@raspberrypi.local:~/
# или по IP, если .local не резолвится:
scp -r groundbridge pi@192.168.1.50:~/
```

Либо автоматическими скриптами (сами проверяют SSH, исключают venv/pycache и
по желанию сразу запускают install.sh):

```bash
# Linux/macOS
./scripts/deploy.sh pi@raspberrypi.local            # только залить
./scripts/deploy.sh pi@raspberrypi.local --install  # залить и установить
./scripts/deploy.sh pi@192.168.1.50 --port 2222     # нестандартный SSH-порт

# Windows (PowerShell, встроенный OpenSSH-клиент)
.\scripts\deploy.ps1 -Target pi@raspberrypi.local
.\scripts\deploy.ps1 -Target pi@raspberrypi.local -Install
```

Если не знаешь IP Pi — на самой Pi выполни `hostname -I`, либо посмотри в
списке устройств роутера. `raspberrypi.local` обычно работает благодаря mDNS.

## 1. Автоматическая установка (рекомендуется)

```bash
cd groundbridge
chmod +x install.sh
./install.sh
```

Скрипт идемпотентен (можно запускать повторно) и делает всё сам:

- ставит системные пакеты (python3-venv, joystick, ffmpeg, v4l-utils,
  libsdl2, шрифты для OSD);
- создаёт `config.yaml` из шаблона `config.example.yaml` (при первом запуске);
- создаёт venv и ставит Python-зависимости;
- включает дополнительный UART (`dtoverlay=uart2` по умолчанию) в
  `/boot/firmware/config.txt` и отключает login shell на serial;
- скачивает и настраивает **MediaMTX** (RTSP-сервер, systemd-сервис
  `mediamtx`) и локальную копию `socket.io.min.js` для офлайн-работы панели;
- устанавливает **ZeroTier** и узкие sudoers-правила для root-хелперов
  (см. [security.md](security.md));
- выставляет регион WiFi (RU по умолчанию), снимает rfkill-блокировку и
  поднимает **WiFi-точку доступа** GroundBridge (см. [wifi-ap.md](wifi-ap.md));
- добавляет пользователя в группы `dialout`, `input`, `video`;
- устанавливает systemd-сервис `groundbridge`;
- открывает порты в ufw, если он активен.

Полезные флаги:

```bash
./install.sh --yes                 # без вопросов
./install.sh --uart uart3          # другой overlay для CRSF-UART
./install.sh --sbus-uart uart3     # настроить ВТОРОЙ UART под SBUS (см. docs/sbus.md)
./install.sh --dir /opt/groundbridge
./install.sh --wifi-ssid "MyDrone" --wifi-password "пароль-от-8-символов"
                                   # свои SSID/пароль точки доступа (по умолчанию AP
                                   # поднимается и так: groundbridge/groundbridge —
                                   # см. docs/wifi-ap.md, смени пароль из панели!)
./install.sh --no-wifi-ap          # не настраивать точку доступа
./install.sh --no-reboot
```

После установки:

```bash
sudo reboot                          # применить UART и группы доступа
sudo systemctl start groundbridge
sudo systemctl status groundbridge
```

Веб-панель: `http://<IP_Pi>:8080`. Логи: `journalctl -u groundbridge -f`.

## 2. Настройка UART вручную (если не через install.sh)

В `/boot/firmware/config.txt` добавь дополнительный UART, чтобы не
конфликтовать с системной консолью (она обычно на UART0/ttyAMA0):

```
dtoverlay=uart2
```

Затем `sudo raspi-config` → Interface Options → Serial Port:
login shell — **No**, serial hardware — **Yes**. Перезагрузись и проверь
устройство: `ls /dev/ttyAMA*` (для `uart2` на Pi 5 обычно `/dev/ttyAMA2` —
впиши фактическое в `config.yaml` → `uart.port`).

Подключение к ESP32 (**общий GND обязателен**; уровни 3.3V совпадают,
преобразователь не нужен):

```
Pi GPIO TXD (uart2)  ---> ESP32 RX
Pi GPIO RXD (uart2)  <--- ESP32 TX   (нужен только для телеметрии обратно)
Pi GND               ---  ESP32 GND
```

## 3. Джойстик (пульт в режиме USB Joystick)

На пульте включи режим USB Joystick (например, на Radiomaster TX12:
`SYS → USB Joystick`). Подключи к Pi и проверь:

```bash
jstest /dev/input/js0
```

Если оси откликаются — поправь при необходимости `axis_map`/`invert` в
`config.yaml` под свою раскладку (4 основных канала: roll/pitch/throttle/yaw).

### Тумблеры и кнопки (каналы 5–16)

По умолчанию читаются только 4 стика. Тумблеры/кнопки пульта в режиме USB
Joystick приходят как pygame-кнопки — назначь их на каналы через гибкий
микшер `mixes` в `config.yaml` (секция `joystick`):

```yaml
joystick:
  mixes:
    - {channel: 0, source_type: axis,   source_index: 0, invert: false}  # Roll
    - {channel: 1, source_type: axis,   source_index: 1, invert: false}  # Pitch
    - {channel: 2, source_type: axis,   source_index: 2, invert: false}  # Throttle
    - {channel: 3, source_type: axis,   source_index: 3, invert: false}  # Yaw
    - {channel: 4, source_type: button, source_index: 0, invert: false}  # Arm
    - {channel: 5, source_type: button, source_index: 1, invert: false}  # Режим
```

Если `mixes` задан — он используется **вместо** `axis_map`/`invert`.
Номера осей/кнопок показывает `jstest` (кнопки — отдельной строкой).

## 4. Ручной запуск (без systemd)

```bash
source venv/bin/activate
python3 run.py --config config.yaml
# только мост, без веб-панели:
python3 run.py --no-webapp
```

## 5. Автозапуск (systemd)

`install.sh` делает это сам. Вручную:

```bash
sudo cp systemd/groundbridge.service /etc/systemd/system/
# поправь User= и пути в юните, если ставишь не в /home/pi/groundbridge
sudo systemctl daemon-reload
sudo systemctl enable --now groundbridge
```
