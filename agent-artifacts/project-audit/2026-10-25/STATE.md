# Единая точка входа — 25 октября 2026

Рабочий чат: текущий чат пользователя. Последнее указание: вся дальнейшая работа ведётся здесь. Не требуется переносить задания/файлы между чатами. Этот документ — обзор, а не замена authoritative runtime или manifest. Production-изменения и авторинг этим аудитом не выполнялись.

## Что проверено

Инвентаризировано 3851 файлов вне генерируемых/служебных каталогов (inventory.json содержит точный список и исключения). Прочитаны текущие точки входа приложения, persistence, scoring, сборочные скрипты, изменения Git, отчёты импорта, текущий manifest, последние QA/planning/orchestration и релизные отчёты. Не заявляется построчное прочтение всех исторических кейсов и бинарных моделей. 14 protected-input hashes из STATE.json совпадают с физическими файлами (protected-hashes.json).

## Реальное приложение

- SwiftUI App → постоянный BookView / WKWebView с bundled WebContent.
- Учебник: 129 тем; отдельный учебный банк интервью: 100 вопросов / 300 вариантов. Это не банк тренажёра.
- TrainerView открывается fullScreenCover; озвучивание учебника ставится на паузу.
- Тренажёр реализует обучение, повторение, диагностику, историю и профиль; authoritative файлы в InteractiveBook/Trainer/.
- TrainerContent/cases.json: 100 кейсов TC-001…100 / 400 вариантов, 67 standalone и 33 linked. Linked исключены из обычной диагностики.
- Учебник хранит bookState в UserDefaults; standalone HTML — localStorage. SavedExcerptStore также использует UserDefaults.
- Тренажёр: Application Support/Trainer/state.json, persistence schema 3, миграции с backup, snapshots в попытках и истории. Новая редакция bundled bank не подменяет старые снимки.
- SpeechReaderManager управляет общей очередью, подсветкой и аудиосессией. Apple TTS и Silero — отдельные движки; Silero использует ONNX Runtime и Swift preprocessing/DSP.

## Утверждённое и экспериментальное

Production bank SHA-256: 6becf4f8ccdb914e9ebd51ca780902174ecdd7914824408139b40477cd25c6a3.
Замороженный blueprint — manifests/CURRENT.md → v2.2.3. Принятый накопительный кандидат для дальнейшей переработки — v2.3-hardtail-b2-candidate, SHA 625d6b2529c74da2bf51c4ae349f77d44182472fac9263a47f8f33f47b734ced.
Это не готовый к импорту банк: 72 unresolved; readyToFreeze=false, importEligible=false. B2 QA принимает routing/no-change, а не все оставшиеся кейсы.
Batch04: 0/25 полноценных кейсов; исторический preflight заблокирован качеством manifest.
Последняя неудачная U-EXP: 0 применимых изменений; TC-221/263 остаются unresolved. Актуальный planning delta рекомендует replacement architecture review двух разных Middle ролей. Не повторять четыре отклонённых варианта. TC-261 имеет открытый minor HT1-261-M01 перед freeze.

## Автоматизация

orchestration/STATE.json: ARCHITECTURE_READY / BOOTSTRAP_ONLY; CURRENT-TASK.json=null. Последний heartbeat сообщает HELD. Это инфраструктура маршрутизации, не выполненная генерация кейсов. В этом аудите не запускались supervisor workers, новые чаты или авторинг; состояние автоматики не менялось. Факт наличия plist не доказывает установленное расписание.

## Git и релизы

HEAD b61b1cd — checkpoint на 75 кейсах. Рабочий production содержит уже 100. Незакоммиченные изменения: импорт batch03 и числовые тесты; reader/navigation и web layout; CURRENT; project.pbxproj (включая DEVELOPMENT_TEAM). Много untracked content/QA/pipeline/orchestration артефактов. Без разбора не делать git add . или откат.
SideStore beta-75 ASCII-name IPA — отдельный исторический артефакт: packaging/name patch внесён в IPA, не в source. Будущая сборка не наследует автоматически исправление display-name. Успешная установка у получателя не подтверждена в прочитанных отчётах. Это не релиз текущего 100-case состояния.
Последний выданный standalone HTML: agent-artifacts/web-sidebar-layout/Управление процессами и проектами.html. Меню docked только в web build, iOS сохраняет overlay.

## Порядок дальнейшей работы

1. Этот чат — единое управление задачами; факты и результаты сохранять в syllabus/agent-artifacts.
2. Перед изменениями различать production, approved candidate и rejected/history.
3. Для продолжения контентной ветки следующий содержательный шаг — review замены U-EXP, а не слепой импорт или повторный авторинг batch04.
4. Для следующего релиза — отдельно собрать актуальные 100 кейсов и воспроизводимо применить SideStore packaging/name fix; не выдавать beta-75 за новый релиз.
5. Git checkpoint возможен отдельным контролируемым действием после разбора изменений. Аудит не выполняет commit/push.

Свежие результаты scripts/check.sh: см. checks-result.txt и check.log рядом. Старые отчёты не заменяют новый прогон. Успех автоматических тестов не означает ручную приёмку на физическом iPhone.

## Уточнение после продолжения 25 октября

Найден ранее не учтённый replacement-architecture/u-exp/architecture-review.md от20октября: TC-263 имеет выбранный blueprint263-A; TC-221 не имеет viable replacement. Предыдущая рекомендация повторить architecture review устарела. Новый изолированный черновик строки263: test-bank/replacement-authoring/tc263-r1 (относительно agent-artifacts). Не принят, independent QA NOT_RUN, production/manifest unchanged, unresolved72. Следующий шаг — review этого конкретного предложения, не повторная генерация архитектуры.

### Результат self-review TC-263 R1

replacement-review/tc263-r1/verdict.json: REVISION_REQUIRED,3Major. Не доказана единственность сильнейшего решения (не определена относительная цена задержки поиска и потери карточки), альтернативы искусственно отсекаются сроком; методологическое утверждение о retest требует ограничения. Это self-review, не independent QA. Старый R1 сохранён неизменным и не допускается к promotion. Следующий шаг — правка skeleton с равноправными исполнимыми стратегиями и достаточными decisive facts. Production/manifest unchanged; unresolved72.

## Текущий указатель после поручения завершить проект

Дальнейший консолидированный прогресс: agent-artifacts/project-completion/CURRENT.md. Сам аудит25октября — исторический снимок. TC263R2 получил независимый FIX_REQUIRED;193 на review; воспроизводимая упаковка и100-case Release прошли отдельную проверку.
