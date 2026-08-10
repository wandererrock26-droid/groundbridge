# Установка

Один установщик на все поддержанные платы: **Raspberry Pi 5**, **Raspberry
Pi 4** и **Radxa ROCK 5C**. Плату он определяет сам и от неё выбирает, какой
UART поднять и каким способом, какой порт вписать в конфиг и какие пакеты
доставить. Отдельных инструкций под каждую плату нет — различия описаны в
[boards.md](boards.md), но знать их для установки не требуется.

Сборки раздаются в `.tar.gz` — распаковка одинаковая на всех платах, и
права на файлы сохраняются, так что возвращать `chmod +x` скриптам не нужно:

```bash
cd ~/roverlink && tar -xzf ~/roverlink-<версия>.tar.gz
```

## 0. Доставка проекта на плату

Проще всего — клонировать с GitHub прямо на плату:

```bash
git clone https://github.com/wandererrock26-droid/roverlink.git
cd roverlink
```

Либо залить по scp со своего компьютера (SSH на Pi должен быть включён —
`sudo raspi-config` → Interface Options → SSH, или в Raspberry Pi Imager при
прошивке карты):

```bash
scp -r roverlink pi@raspberrypi.local:~/
# или по IP, если .local не резолвится:
scp -r roverlink pi@192.168.1.50:~/
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
cd roverlink
chmod +x install.sh
./install.sh
```

Скрипт идемпотентен (можно запускать повторно) и делает всё сам:

- ставит системные пакеты (python3-venv, ffmpeg, v4l-utils,
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
  поднимает **WiFi-точку доступа** RoverLink (см. [wifi-ap.md](wifi-ap.md));
- добавляет пользователя в группы `dialout`, `input`, `video`;
- устанавливает systemd-сервис `roverlink`;
- открывает порты в ufw, если он активен.

Полезные флаги:

```bash
./install.sh --yes                 # без вопросов
./install.sh --uart uart3          # другой overlay для CRSF-UART
./install.sh --sbus-uart uart3     # настроить ВТОРОЙ UART под SBUS (см. docs/sbus.md)
./install.sh --dir /opt/roverlink
./install.sh --wifi-ssid "MyDrone" --wifi-password "пароль-от-8-символов"
                                   # свои SSID/пароль точки доступа (по умолчанию AP
                                   # поднимается и так: roverlink/roverlink —
                                   # см. docs/wifi-ap.md, смени пароль из панели!)
./install.sh --no-wifi-ap          # не настраивать точку доступа
./install.sh --no-reboot
```

После установки:

```bash
sudo reboot                          # применить UART и группы доступа
sudo systemctl start roverlink
sudo systemctl status roverlink
```

Веб-панель: `http://<IP_Pi>:8080`. Логи: `journalctl -u roverlink -f`.

Пароль входа в панель из коробки — **`roverlink`**. Он не секрет: нужен
только чтобы свежая установка сразу открывалась. **Смени его при первом
входе:** «Система» → «Пароль веб-панели». Подробности и сброс забытого
пароля — в [security.md](security.md).

## 1a. Обновление на новую версию

Распаковка архива заменяет только файлы проекта — зависимости, права на
скрипты и повторное усиление делает `tools/update.sh`:

```bash
cd ~ && unzip -o roverlink-vX.Y.zip
cd ~/roverlink && ./tools/update.sh
```

Скрипт доустановит новые Python-зависимости, при необходимости повторно
применит `harden.sh`, перезапустит сервис и покажет статус. Личные настройки
(`config.yaml`, `data/` с ключом активации и настройками панели) не
затрагиваются.

После обновления в браузере нажми **Ctrl+F5** — иначе панель подхватит
старый кэш стилей и скриптов.

## 1b. Переезд со старого имени (GroundBridge → RoverLink)

До версии 2.0 проект назывался **GroundBridge**, ставился в `~/groundbridge`
и работал сервисом `groundbridge`. Обычным `update.sh` это не обновляется:
поменялись имена каталога, юнита systemd, sudoers-правил и хелперов в
`/usr/local/bin`. Для переезда есть отдельный скрипт:

```bash
cd ~ && unzip -o roverlink-2.0-betaN.zip
cd ~/roverlink && ./tools/migrate_from_groundbridge.sh
./install.sh
```

Что делает `migrate_from_groundbridge.sh`:

- переносит `config.yaml` и папку `data/` из `~/groundbridge` — **ключ
  активации остаётся действительным** (он привязан к железу, а не к имени
  проекта), вместе с ним переезжают пароль панели, failsafe, выбранный
  режим и настройки ZeroTier;
- останавливает, выключает и удаляет старый сервис `groundbridge`;
- удаляет старые `/etc/sudoers.d/groundbridge-*` и
  `/usr/local/bin/groundbridge-*.sh`;
- переименовывает профиль WiFi-точки `groundbridge-ap` → `roverlink-ap`,
  чтобы панель снова могла им управлять. **SSID и пароль самой сети не
  меняются** — переподключаться к точке не нужно.

Дальше `install.sh` собирает venv, юнит и правила уже под именем `roverlink`.
Старый venv не переносится специально: внутри него зашиты абсолютные пути
на прежний каталог, после переезда он бы просто не запустился.

Старый каталог `~/groundbridge` скрипт **не удаляет** — это страховка.
Убедился, что новая установка работает — удали сам:

```bash
rm -rf ~/groundbridge
```

## 2. Настройка UART вручную (если не через install.sh)

В `/boot/firmware/config.txt` добавь дополнительный UART, чтобы не
конфликтовать с системной консолью (она обычно на UART0/ttyAMA0):

```
dtoverlay=uart2
```

Затем `sudo raspi-config` → Interface Options → Serial Port:
login shell — **No**, serial hardware — **Yes**. Перезагрузись и проверь
устройство: `ls /dev/ttyAMA*` на Raspberry или `ls /dev/ttyS*` на Radxa
(для `uart2` на Pi 5 обычно `/dev/ttyAMA2` —
впиши фактическое в `config.yaml` → `uart.port`).

Подключение к ESP32 (**общий GND обязателен**; уровни 3.3V совпадают,
преобразователь не нужен):

```
Pi GPIO TXD (uart2)  ---> ESP32 RX
Pi GPIO RXD (uart2)  <--- ESP32 TX   (нужен только для телеметрии обратно)
Pi GND               ---  ESP32 GND
```

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
sudo cp systemd/roverlink.service /etc/systemd/system/
# поправь User= и пути в юните, если ставишь не в /home/pi/roverlink
sudo systemctl daemon-reload
sudo systemctl enable --now roverlink
```
