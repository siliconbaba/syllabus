# Global manifest audit — v2.3 candidate

**BLOCKED. READY FOR INDEPENDENT GLOBAL MANIFEST QA: NO.**

Проверены blueprint TC-101…TC-300: 200/200. Полные cases не создавались. Исходный v2.2.4-r2 использован как seed, не как authoritative. Сравнение изменений выполнено с v2.2.3.

## Что закончено и что не закончено

Глобальные findings материализованы для всех 200 строк. Выполнено 8 standalone redesign. Остальные отмеченные повторы и дефекты уровня ещё не устранены; эта редакция не завершает требуемый глобальный redesign. Не утверждается, что учебник не позволяет реализовать оставшиеся уровни. Frozen levels сохранены.

## Semantic review

Классификация считается по planned rows, по максимальному риску среди найденных аналогов; controlled siblings не считаются дубликатами. Pipeline retrieve применён к production и remaining planned с top-N и обязательным same-topic/primary coverage. Все boundary TC-101…300 сопоставлены по предмету решения; retrieval score не использовался как semantic verdict. Перечни retrieval — evidence для focused повторной проверки, не утверждение о 39 900 независимых экспертных вердиктах.

Initial: {'ALLOWED REINFORCEMENT': 92, 'NO CLOSE ANALOG': 13, 'DUPLICATE': 39, 'NEAR DUPLICATE': 56}. Blocking rows found: 95; resolved: 8; remaining: 87.

TC-295 закрыт без изменения строки: переработан единственный указанный аналог TC-164. Восемь новых blueprint и различия с ближайшими решениями приведены в source-grounding-redesign.json.

## Level review

PASS 79/200; level redesign 4; unresolved 121.

Основные дефекты: готовая threshold/policy вместо Middle trade-off; наличие/отсутствие authority вместо Senior reasoning; одноразовое применение готового критерия вместо Head governance design. Предыдущий QA seed не переносится на весь оставшийся банк. TC-115/122 остаются авторскими PASS, независимое принятие впереди.

## Families

Проверено 31 remaining families. Global pass не менял семьи. Семейные semantic blockers: 28; схемная согласованность всех 43 contracts PASS.

F-PR-T01: граница «общий каркас + локальные варианты» и «общие принципы + отдельные процессы» пока не делает третью стратегию однозначно сильнейшей. Families с threshold/authority findings не получают PASS лишь за корректную структуру JSON.

## Regression vs authoritative

Changed rows: 23; unchanged: 252. Changed family contracts: 3 (F-TD-T01, F-PM-P01, F-PA-P02), все унаследованы из seed. Unexpected TC-026…100 changes: 0. Production unchanged: PASS.

Structural/runtime PASS: 275 IDs, no duplicates, topic/part, valid codes, eligibility, 181 standalone/94 linked, 35 pairs/8 triplets, 11×25, no split. Derived runtime применён только к восьми изменённым semantic boundaries; coverage пересчитан. Context evidence=0; primary 1, secondary .5, max category dedupe и normalization. Unknown codes=0.

Metadata Head feasibility сохранена, но она не подтверждает семантическую достаточность спорных Head. Уровни J42/M122/S76/H35 новых, J44/M143/S78/H35 all300, J32/M99/S46/H23 assessment200; квоты не подгонялись.

## Remaining IDs

TC-106, TC-107, TC-126, TC-127, TC-128, TC-129, TC-130, TC-131, TC-132, TC-133, TC-134, TC-135, TC-136, TC-138, TC-139, TC-141, TC-144, TC-145, TC-146, TC-148, TC-150, TC-151, TC-152, TC-153, TC-154, TC-155, TC-156, TC-157, TC-158, TC-159, TC-160, TC-162, TC-166, TC-167, TC-170, TC-171, TC-174, TC-175, TC-176, TC-177, TC-178, TC-179, TC-180, TC-181, TC-182, TC-183, TC-184, TC-186, TC-187, TC-188, TC-190, TC-191, TC-192, TC-193, TC-194, TC-195, TC-199, TC-200, TC-201, TC-202, TC-203, TC-204, TC-205, TC-206, TC-207, TC-208, TC-209, TC-210, TC-211, TC-212, TC-213, TC-214, TC-215, TC-217, TC-218, TC-220, TC-221, TC-222, TC-223, TC-225, TC-226, TC-227, TC-228, TC-229, TC-230, TC-231, TC-232, TC-233, TC-234, TC-236, TC-237, TC-238, TC-239, TC-242, TC-243, TC-244, TC-248, TC-251, TC-252, TC-253, TC-254, TC-255, TC-256, TC-257, TC-258, TC-259, TC-260, TC-261, TC-263, TC-264, TC-265, TC-266, TC-267, TC-268, TC-269, TC-270, TC-271, TC-272, TC-274, TC-275, TC-276, TC-277, TC-278, TC-279, TC-280, TC-281, TC-282, TC-283, TC-284, TC-286, TC-287, TC-288, TC-289, TC-290, TC-291, TC-292, TC-293, TC-294, TC-296, TC-298, TC-299, TC-300

Точные основания и аналоги — duplication-audit-global.csv, level-audit-global.csv, family-audit-global.csv. Их нельзя считать закрытыми на основании этого отчёта.

Source grounding выполненных redesign: 8/8 PASS; выдержки привязаны к исходному index.html по SHA-256, полные нужные темы сохранены в source-topics/. Все числа новых сценариев — авторские условия.

Freeze, authoring, import, production/schema/scoring/app changes, commit/push не выполнялись.
