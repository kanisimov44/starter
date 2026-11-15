# Тестовое задание

- `ANSWERS.md` - части 1-2: вопросы к задаче и архитектура.
- `starter.py` - исправленная функция `recommend_price` (часть 3).
- `test_starter.py` - автоматические тесты (pytest).

## Запуск локально

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

python starter.py        # пример: price=4728.00, decision=APPLY
python -m pytest -v      # тесты
```

## Запуск в Docker

```bash
docker build -t starter-tests .
docker run --rm starter-tests                     # тесты
docker run --rm starter-tests python starter.py   # пример
```

## Что покрыто тестами

- Пример из задания: 4728.00, APPLY.
- Тайм-аут источника, исключение источника, статусы `partial` и `error` дают HOLD с текущей ценой.
- Нет подходящих предложений (MYSHOP в любом регистре, доставка больше 6 дней или `None`) - HOLD, даже если текущая цена ниже `min_price`.
- Нижняя граница `min_price`, округление вниз до копейки, границы доставки 0 и 6 дней.
- Граница 30%: ровно 30% в обе стороны даёт APPLY, на копейку больше - REVIEW.
