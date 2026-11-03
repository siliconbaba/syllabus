# TC-183 — Middle self-QA

Middle сравнивает три допустимых маршрута, учитывая дефицит общего эксперта и разные последствия задержки технического и персонального процессов. Выбирает меньшую полную цену, сохраняя качество проверки, безопасный режим и доказательность решения об ответственности.

## Why Junior reasoning is insufficient

Правило blameless не выбирает очередность: ни один допустимый маршрут не наказывает за ошибку и не отменяет ответственность. Правило «сначала исправить систему» тоже недостаточно: сервис уже защищён обходом, а отсрочка разбора имеет самостоятельную цену. Нужно связать календарь общего ресурса с последствиями обеих отсрочек и ценой параллельного исполнения.

## Real competing strategies

- Protection first: admissible,60.
- Fact review first: admissible,40, strongest.
- Paid parallel execution: admissible,55.

Both work products are mandatory and substantively useful. No blame conclusion is preselected. Safety and procedure quality are held fixed; the scarce witness cannot do5 hours in4. The decision trades one day of safe workaround against the cost of waiting for a later fact-review slot and the price of extra expertise.

The prompt supplies constraints and costs, not an instruction to cancel a pointless meeting. First-choice self-QA: choose fact review today after checking that safe workaround permits this; then compare full consequences, not technical speed alone.

Counterfactuals: coverage30→protection first; specialist35→parallel; workaround70→parallel. The strongest therefore depends on three decisive fact groups, not a fixed blameless slogan.

PASS — author self-QA; independent retest pending. No full questions/options authored.
