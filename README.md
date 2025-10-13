# Lipi-os 
```
Операционная система на python (типа) 
(ru) Описание: 
lipi os - моя ос (оболочка) на python. Хочу сделать что-то по типу: 
ms-dos с win и с функционалом как у ubuntu 
реалицованно на текущей версии lipi os v8 (минимальный функционал): 
  Программы: 
        название_приложения/ 
           сама_программа.py 
           описание.json 
  Команды: 
      базовые команды из ubuntu(ls, cd, nano, mkdir ...) 
  Файловый менеджер: 
      как приложение 
Структура проекта:

lipi-os/
├── core/                  # Shell Core
│   ├── shell.py           # CLI command interpreter
│   ├── gui_engine.py      # Custom GUI engine (based on Tkinter/PyQt/or a custom)
│   ├── task_manager.py    # Task Manager
│   ├── app_store.py       # The app store
│   └── compiler_hub.py    # A module for compiling code
├── apps/                  # Embedded Applications
│   ├── file_manager/
│   │   ├── main.py
│   │   └── description.json
│   ├── calculator/
│   ├── text_editor/
│   ├── games/
│   └── ...
├── settings/
│   ├── config.json        # Language, theme, path to compilers ...
│   └── lang/
│       ├── ru.json
│       └── en.json
├── commands/              # Implementing commands (ls, cd ...)
│   ├── ls.py
│   ├── cd.py
│   └── ...
├── main.py                
├── README.md          #about 
└──info_and_apdate.txt #apdate and info
```
