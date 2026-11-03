# Coverage dependencies

Planning baseline unchanged.72 unresolved: {"middle": 31, "senior": 30, "junior": 8, "head": 3},32standalone/40linked.19families затронуты; accepted sibling235 добавляет один scope member только для соответствующей семьи. R5/R6:24unresolved rows,12units;2standalone/22linked. Полные vectors по каждой unit в coverage-baseline.json.

## Неподвижные структурные ограничения

275new =181standalone+94linked;35pairs+8triplets=43new families,11×25batches. Gold25=19standalone+6linked. Final300training/200ordinary standalone assessment после отдельной задачи отключения шести linked gold;46families/246max independent units. Production100 не редактируется. Replacement означает новую семантику тех же slots, не удаление IDs и не новую квоту. Нельзя превращать triplet в pair или перераспределять число slots между темами без отдельного решения.

New J42/M122/S76/H35; all300 J44/M143/S78/H35; assessment200 J32/M99/S46/H23. Исторический target45/120/90/45 имеет actual−target −1/+23/−12/−10. Этот inherited gap не исправлять данным планом и не компенсировать повышением иных строк. RequiredLevel сохраняется по каждому slot, а не только в сумме.

## Replacement риски

- U-F-PA-P04: два Head linked slots13.1. Head должен быть governance/ownership метрик, не разовая продуктовая ставка. Они не добавляют assessment breadth, поскольку linked=false для assessment.
- U-F-PR-T01 и U-F-PE-T01: каждый сохраняет 3Middle linked/две реальные границы. Удаление искусственного middle state не разрешает скрытый переход 3→2.
- G-AUTHORITY: три Senior пары в 9.4/5.7/5.5 сохраняют отдельный topic intent и domain intent; общая новая граница на все 6 слотов недопустима.
- U-F-PM-P03:2Senior planning slots2.4 нельзя перенести в API architecture10.1.
- U-F-PR-P02, U-F-DR-P04, U-F-PO-P04: сохранить Senior pair slots7.10/3.3/10.6. Если source не даёт level, остановить unit и запросить blueprint решение, не downgrade.
- R5 TC-296/299: это два assessment-eligible Senior; замена обязана сохранить диагностическую валидность соответствующих domain contributions. Не считать количество строк достаточной breadth.

## Runtime и thinking

Текущее распределение UI domains и primary/secondary/union/evidence weights сохранено в JSON. Для каждого replacement и axis reconstruction будущий автор обязан показать before/after topic,level,domain,patterns,derived fields и pools. Изменение смысла может потребовать другого pattern: нельзя наследовать ложный pattern ради покрытия. Если честная metadata уменьшает заявленное domain/thinking coverage, остановить принятие этой unit до явного coverage решения. Не подгонять mapping. Primary1/secondary0.5; max alias внутри case/category; normalization как engine; context evidence0.

Assessment архитектура: standalone true/true, linked true/false. Head breadth gate сверять на assessment-only S+H по UI domains, не по raw linkedHead. Current mechanically feasible breadth не означает 72 валидных content rows. Перед freeze пересчитать coverage после всех принятых replacements и сравнить quantitative и semantic validity отдельно.

## Проверки перед приёмкой unit

1. Числа IDs/families/batches и eligibility равны baseline.
2. Source intent каждого topic и level каждойстроки сохранены.
3. Авторитетные runtime codes известны; mapping/engine hash не изменён.
4. По всей кандидатной базе пересчитаны raw/assessment domain и thinking таблицы; loss не спрятан нормализацией.
5. Все accepted rows вне scope unchanged; TC-235 отдельно контролируетсяпри reopen.

План не содержит proposed after-vectors: концепты ещё не созданы. Их отсутствие — будущий gate, ане утверждение, что coverage автоматически сохранится.
