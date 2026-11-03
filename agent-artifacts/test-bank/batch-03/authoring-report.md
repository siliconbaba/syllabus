# Batch 03 — авторский candidate для независимого QA

Созданы TC-076…TC-100: 25/25, 16 standalone, 9 linked, 4 семьи (3 пары и 1 триплет). J5 / M12 / S5 / H3. Ключи A6 / B6 / C6 / D7. Standalone — training/assessment true/true, linked — true/false.

Authoritative baseline — frozen manifest v2.2.2, SHA-256 `c4f8600132a4099a655c31c4c97356c52265da7c0895e04d9a99f04503821e41`. Production TC-001…075 сохранён: `2540570c2b907ea0e48cb9752e715486126e006a6100bd27e2f9f170d2c99689`. Контроль всех protected inputs — authoring-input-hashes.json. Manifest, Swift, schema и production content не менялись.

Сначала сформированы decision-skeletons.json, затем authored context/question/options. Источник содержательных принципов только InteractiveBook/WebContent/index.html. source-trace.csv связывает все 25 решений с положениями и дословными фрагментами локального учебника; роли и количественные условия синтетические. В runtime-схеме whatToNotice представлен decisiveFacts (1–3), thinkingModel — mentalModel.

## Содержательная самопроверка

25/25 unique strongest; 75 попарных сравнений с distractors в pairwise-self-check.csv. Для каждого указаны доступные до ответа факты, причина привлекательности альтернативы, проигрывающий trade-off и условие применимости всего варианта. Варианты используют разные оценки зрелости; равные 0.75 у C/D в TC-077 отражают одинаковый чистый эффект. Это авторская проверка, не независимое blind QA.

Senior: TC-083/084 исправляют пересекающиеся денежные потоки и sunk cost, сравнивают диапазон неопределённости с альтернативой и ценой ожидания; TC-091 перестраивает временную enabling-модель с ограниченной учебной ёмкостью и условием выхода; TC-096 сокращает чужую нагрузку с учётом системных последствий и будущего владения; TC-099 связывает новый SLO с архитектурой отказов, стоимостью эксплуатации и вытесняемой capacity.

Head: TC-090 пересобирает портфель и sourcing с финансированием передачи критических знаний; TC-097 меняет scope руководителя менеджеров после двух безрезультатных циклов поддержки, сохраняя его сильную роль и автономию подчинённых; TC-098 разделяет права и правила доступа к управленческому и проектному резервам.

## Linked families

4/4 PASS. Literal sibling diff в family-diff-analysis.json. Actor, base context, question, options и порядок идентичны; меняется только frozen logical variable.

- F-DR-T01: L=0/6/18, ключи C/A/D; реальные границы L=4 и L=8. Полезность автоматизации 0.5L−2, ручного шага L−6, удаления 0. Повторное исследование уже надёжной оценки добавляет расход без новой информации.
- F-TD-P01: завершённая допустимость vs подтверждение получения; ключи B/C, вызваны только смыслом продуктового ответа.
- F-PE-P01: неизвестный vs подтверждённый драйвер; D/A.
- F-BV-P02: PV16–20 vs PV4–7 при неизменных остальных условиях; B/D. NPV8–12 vs −4…−1 при альтернативе +5.

## Повторы и surface

Full wording сопоставлен с TC-001…075. duplication-audit.csv: NO CLOSE ANALOG 2, ALLOWED REINFORCEMENT 23, NEAR DUPLICATE 0, DUPLICATE 0. Дополнительный full-wording-retrieval.json содержит все 1875 пар; лексическая близость служит навигацией, не доказательством семантического совпадения. Внутренний аудит 300 пар — 0 near/duplicates; контролируемые siblings отмечены отдельно.

78 простых правил проверяют длину, пунктуацию, clauses/actions proxies, числа, Latin technical terms, conditional markers и комбинации. Лучшее правило 9/25, максимум ожидаемых попаданий при случайном разрешении ties — 9.83/25. Объединённый корпус: 35/100 против 28/75 до Batch 03, доля не выросла. Применена та же family-preserving permutation, что в предыдущем QA. Это sanity check заданных правил, а не доказательство отсутствия любой возможной подсказки. Статус PASS в этих пределах.

## Валидация и передача

Штатный TrainerBank.load загружает candidate; schema и runtime vocabulary PASS, unknown codes 0. Автоматически сверены все IDs, metadata frozen manifest, eligibility, levels, позиции, family constants и неизменность protected inputs. schema-validation.log содержит результат загрузки.

Исторические preflight-файлы сохранены в history-preflight-v2.2.1/. Старые root input-hashes.json, manifest-extract.json, duplication-preflight.csv, cross-bank-retrieval-evidence.json — исторические свидетельства, не источник текущего authoring. Текущие доказательства: frozen-manifest-extract-v2_2_2.json, authoring-input-hashes.json и отчёты выше.

Unresolved IDs: []. READY FOR INDEPENDENT QA: YES. Импорт не выполнялся; решение об импорте не заявляется. Независимый QA должен проверить содержательные авторские суждения. Batch 04 и Slice 5 не начаты; commit/push не выполнялись.

Candidate SHA-256: `df3943383897c243bb8a352e6cd829414711a17035d125d5795361fe928b5379`.
