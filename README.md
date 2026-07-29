# Lipi OS

Операционная система-оболочка на Python (CLI + опциональный GUI на Tkinter).

## Запуск

```bash
cd code
pip install -r requirements.txt
python main.py --cli      # консоль
python main.py --gui      # GUI (нужен tkinter)
python main.py            # GUI если доступен, иначе CLI
```

## Что умеет сейчас (v8+)

- Shell: `ls`, `cd`, `pwd`, `mkdir`, `cat`, `echo`, `touch`, `cp`, `mv`, `rm`, `date`, `run`, `apps`, `help`, `exit`
- Системные команды: `settings`, `tasks`, `store`, `compile`
- Встроенные приложения: Calculator, File Manager
- Настройки языка (ru/en) и темы
- Диспетчер задач (psutil)
- Магазин приложений (.lipi / zip)
- Compiler Hub (Python, JS, C/C++, Rust и др.)

## Структура

```
lipi-os/
├── code/
│   ├── main.py
│   ├── paths.py
│   ├── i18n.py
│   ├── requirements.txt
│   ├── core/
│   ├── commands/
│   ├── apps/
│   └── settings/
├── iso/                   # Live ISO builder for real PCs
│   ├── build.sh
│   ├── grub.cfg
│   └── overlay/
├── dist/                  # output: lipi-os-live.iso (after build)
├── README.md
├── info_and_apdate.txt
└── LICENSE
```

## Загрузка на реальном ПК (Live ISO)

Lipi OS собирается как **свой дистрибутив на ядре Linux** (не приложение внутри чужой ОС):

```bash
sudo ./iso/build.sh
```

Образ: `dist/lipi-os-live.iso`. Запись на USB и загрузка — в [`iso/README.md`](iso/README.md).

## Формат приложения

```
apps/my_app/
  main.py
  description.json
```

Пример `description.json`:

```json
{
  "name": "My App",
  "version": "1.0.0",
  "author": "You",
  "description": "Short description"
}
```
