# stand/ — экспериментальный стенд (арка 001)

Headless-ядро из [../docs/GAME.md](../docs/GAME.md): переживает ли некупляемый индекс по исходу купленного инкумбента с дефолтной позицией. Все отчёты — на русском; предсказания фиксировались **до** запусков и проверялись поимённо.

## Карта файлов

| Скрипт | Пре-регистрация | Отчёт | Артефакты |
|---|---|---|---|
| `exp_balance_001_core.py` | `prereg/PREREG_EXP-BALANCE-001.md` | `results/RESULTS_EXP-BALANCE-001.md` | `results/phase_maps.png`, `results/trajectories.png`, `results/results_001.json` |
| `exp_balance_001b.py` | `prereg/PREREG_EXP-BALANCE-001b.md` | `results/RESULTS_EXP-BALANCE-001b.md` | `results/fig_001b.png`, `results/results_001b.json` |
| `exp_balance_001c.py` (**баг сохранён**) и `exp_balance_001c_fix.py` | `prereg/PREREG_EXP-BALANCE-001c.md` | `results/RESULTS_EXP-BALANCE-001c.md` | `results/fig_001c.png`, `fig_001c_fix.png`, `results_001c.json`, `results_001c_fix.json` |
| `exp_balance_001d.py` | `prereg/PREREG_EXP-BALANCE-001d.md` | `results/RESULTS_EXP-BALANCE-001d.md` | `results/fig_001d.png`, `results/results_001d.json` |

Сводка арки: [`STAND_SUMMARY.md`](STAND_SUMMARY.md).

## Integrity-заметки

- **`results/archive/`** — итерации 0 и 1 эксперимента 001: стенд дважды провалил собственный критерий валидности, обе калибровки задокументированы и опубликованы, а не затёрты (файлы `*_iter0.*`, `*_iter1.*`).
- **`exp_balance_001c.py` намеренно сохраняет знаковую ошибку** в члене удержания η (ручка «удержание» фактически выталкивала когорту). Ошибка была поймана по бессмысленному направлению результата, раскрыта с диагностикой в отчёте (§0), и исправлена **только по знаку** в `exp_balance_001c_fix.py`. Оба прогона опубликованы рядом — это часть записи, не мусор.
- Калибровочный бюджет каждого эксперимента ограничивался пре-регистрацией (≤2 документированных итераций); при срабатывании стоп-правила негатив публиковался как основной результат.

## Запуск

```bash
pip install -r ../requirements.txt
python3 exp_balance_001_core.py    # ~1–2 мин
python3 exp_balance_001b.py        # ~2–4 мин (горизонт ×8)
python3 exp_balance_001c_fix.py    # ~2 мин
python3 exp_balance_001d.py        # ~2–3 мин
```

Сиды зафиксированы в коде; выходные файлы пишутся в текущую директорию. Каноничные результаты уже закоммичены в `results/` — перезапуск нужен только для верификации.

## Итог арки одной строкой

Эндогенной петли роста нет: ни время, ни посев, ни удержание, ни ретро-аудит, ни сетевой эффект качества не выводят честный индекс из стационара ~0.30. Недостающее звено названо точно — видимость качества индекса **до** перехода. Продолжение — в [`../predictor/`](../predictor/).
