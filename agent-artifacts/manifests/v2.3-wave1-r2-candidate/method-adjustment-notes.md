# Предложения после calibration QA — pending independent acceptance

## Senior realization gate
Если strongest сводится к аккуратному сравнению уже данных constraints, dependencies, ресурсов и порогов, это Middle. До присвоения Senior PASS сформулировать, какой системный механизм кандидат должен построить или изменить, какая существенная неопределённость меняет решение и почему обычный расчёт готовых альтернатив её не снимает. Проверять это по scenario/facts/boundary, а не по словам в whyLevel. Если механизм уже дан целиком — gate не пройден. Масштаб и число условий не повышают уровень.

## Metadata re-derivation after substantive redesign
Выводить scenario → decisive facts → actual decision → strongest reasoning → patterns/domain → Swift runtime заново. Для primary и каждого secondary указать конкретный проверяемый выбор. Малое вложение в закрытие само по себе не является reversible-investment. Не подбирать код ради категории scoring; считать новую coverage только после семантического выбора. Сохранение прежнего кода также требует обоснования.

Основной TEST-BANK-RUNBOOK.md не изменён. Эти предложения и применение к TC-184/TC-291 ожидают independent focused calibration retest.
