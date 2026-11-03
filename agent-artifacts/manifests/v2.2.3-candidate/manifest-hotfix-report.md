# Surgical manifest candidate v2.2.3 — TC-085

**Manifest defect confirmed. READY FOR FOCUSED QA: YES (author self-verdict). Candidate не frozen и не импортирован.**

Сопоставлены production TC-004, frozen row TC-085 и authored Batch03/r2. Во всех случаях ядро старого085 — достаточный targeted regression вместо полного дорогого либо недостаточного быстрого набора. Совпадают ошибка кандидата, решающие факты и выбор evidence. Подтверждение не основано на сходстве слов: original-defect-confirmation.json.

## Source-first выбор

Тема3.9 прочитана целиком из index.html, сохранена в source-topic-t3-9.txt. Рассмотрены положения о flaky/разборе падений, приоритизации автоматизации по частоте и стабильности, разложении полного цикла регресса, расходуемых согласованных тестовых данных и ограничениях добавления среды. Выбран важный самостоятельный judgment: подготовка повторяемого состояния данных при неизменных проверках. Flaky/bocking близок047; выбор автоматизируемых сценариев —286; общая платформа сред была бы Senior/Head scope. Причины выбора и skeleton до авторинга: source-first-design.json.

**TC-004 tests:** достаточно ли evidence для hotfix и какую недостающую проверку добавить перед staged rollout.

**Old TC-085 tested:** достаточный targeted вместо дорогого полного регресса — тот же диагностический стержень.

**New TC-085 tests:** куда вложить ограниченное время для шести повторных циклов с расходуемыми согласованными данными, сохраняя весь набор проверок.

- Different decisive fact: данные меняют состояние и требуют повторной подготовки; известны отдельно стоимость восстановления и исполнения, разовые вложения, срок первого старта и общая ёмкость.
- Different candidate mistake: ускорить видимое выполнение тестов или добавить незанятую среду, не сняв повторный труд по данным; недооценить сумму ручных повторений.
- Different actual decision: выбрать способ подготовки данных и вложение ёмкости; не выбирать полноту regression evidence или rollout.
- Different strongest reasoning: сравнить полную цену повторений и готовность стартового состояния, удержав межсистемные связи; не обменивать полноту проверки на скорость выпуска.

004↔085 — ALLOWED REINFORCEMENT. Source support и Middle self-check PASS. Синтетические числа реализуют правило учебника, не выдаются за цитаты.

## Surgical scope и runtime

Изменена только planned row TC-085: concept/facts/boundary, whyLevel, primary/secondary patterns и derived thinking. Domain release_and_quality сохранён; topic t-3-9, part3, Middle, batch/block, standalone/null family, eligibility true/true неизменны. Остальные274 rows и43 family contracts равны baseline. Export family CSV также побайтово скопирован. Все остальные semantic top-level records неизменны; обновлены только version label и coverage. Inherited freezeProvenance и прежние revision records относятся к baseline2.2.2, не утверждают freeze этого candidate.

Primary process-economics → proportionality; secondary bottleneck → dependencies. Это выбор полной стоимости локального процесса с учётом ограничителя, не измерение полноты evidence. Actual Swift mapping/engine скомпилированы;300 impulse responses PASS, unknown0. Primary1/secondary0.5, aliases max по case/category, нормализация max(1,sum), context evidence0.

Для085 прежний вклад evidence2/3+risk1/3 заменён proportionality2/3+dependencies1/3. Thinking primary/secondary/union и normalized weights пересчитаны в New/Final и assessment subsets. Domain/level tables, Gold25, Head breadth feasibility и pools не меняются. Импортированные026…075 не добавлялись второй раз: manifest coverage — Gold001…025 + New026…300. Current300/assessment200 — проектируемые pools, не факт production import.

Сохранены275 planned,181 standalone,94 linked,35 pairs+8 triplets,11×25. Batch03:25,16standalone/9linked,4families,J5/M12/S5/H3. Проверены IDs, topic/part, family consistency/no split и eligibility. validation-result.json содержит автоматический результат. change-log содержит одну строку с точными before/after.

## Collision scan

299 сравнений: production001…075, authored r2 076…084 и future frozen086…300. duplication-audit-v2_2_3.csv хранит другую boundary и причину различия. Ноль near/duplicates для085. Особенно рассмотрены004,008,013,042,045,047,076…078,086,091,095,131/132,173/174,245,286,298. 174 о wait state внешнего согласования — здесь очереди нет;286 выбирает сценарии автоматизации — здесь набор неизменен;245 спрашивает о проверке окупаемости — здесь нужен исполнимый план по двум ограничениям и состоянию данных. Future scan относится к blueprint, не к ещё не созданным options.

Новый TC-085 реализован в batch-03-r3 после формирования candidate. Оба слоя передаются на один focused independent QA. Production, baseline manifest, r2, независимые QA-файлы, schema и Swift сохранены по hashes. Commit/push, импорт и freeze не выполнялись.
