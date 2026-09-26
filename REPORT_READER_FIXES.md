# Исправления читалки

26 сентября 2026. Работа на main с сохранением незакоммиченных изменений «Сохранённого» и жестов.

## Причины и реализация

1. Production-проба до исправления: framework → «эф ар эй эм и дабл ю оу ар кей», deployment → названия букв, streaming → названия букв. backend/pipeline/API уже были словарными. Причина — единый буквенный fallback для любого `[A-Za-z]+`.
2. Сначала применяется прежний case-insensitive словарь. Затем неизвестные ALL CAPS длиной до 3 или до 5 без гласных считаются сокращениями; остальные токены — слова. camelCase и acronym+Word разделяются. Известные словарные части сохраняют произношение. Регистр PIPELINE не отменяет словарь.
3. Добавлены явные IT-произношения; неизвестные слова проходят детерминированную кириллическую транслитерацию с группами букв. Это приближение, не универсальный английский фонемизатор. Видимый текст не меняется, сети/ML нет. Все существовавшие словарные записи проверены. Apple normalizer не менялся.
4. «Слушать отсюда» рядом с «Сохранить» в общей contextual панели использует единый selection payload. Одного слова достаточно. Запускается стандартный beginLoading/reset → snapshot темы → finishLoading(startBlockID:) → обычная очередь до конца темы.
5. Semantic ID: topicID + `-block-` + структурный путь элемента (tag + порядковый номер среди одноимённых содержательных siblings). Он не зависит от видимости/фильтра или очередности extraction. Старые аудио-ID зависели от счётчика видимых блоков и не подходили для сохранения. Теперь audio highlight, Save, Listen используют одну функцию audio-reader.js. Старая saved-anchor схема поддерживается только для чтения старых записей; текстовый fallback сохранён.
6. Apple/Silero выбирают первый fragment нужного blockID. beginLoading сбрасывает старый playback, requests и Silero generation epoch/prebuffer. Отсутствующий блок сообщает ошибку, а не начинает тему с заголовка. Tests покрывают первый/средний/list/последний блок, повторный старт во время чтения и после паузы, stale events, highlight и завершение для обоих engine adapters.
7. Воспроизведённый дефект Save: обработчик click заново запрашивал живой DOM Selection. После pointerdown и потери selection перед click payload становился null, сообщение не отправлялось и не было ошибки. WebKit regression воспроизводил этот порядок до исправления. Это воспроизведение дефекта в event path, а не подтверждение всех возможных причин на физическом iPhone. Store уже был общим; архитектурного дублирования store не обнаружено.
8. Action фиксирует проверенный payload при начале касания; touchend/click использует snapshot. touchcancel очищает его; подавляется повторный compatibility click. На scroll/обычной отмене selection снимок очищается. После Save можно сразу выбрать Listen. Feedback приходит от Swift после записи и публикации состояния.
9. Single source of truth — App.@StateObject SavedExcerptStore, переданный тому же BookView.Coordinator и SavedExcerptsView. UserDefaults `saved.excerpts`; повреждённые данные сохраняются в recovery. Кодирует/записывает новый массив перед @Published обновлением. Debug логирует только count, без текста цитат.
10. BookMessageTrust вынесен в общий проверяемый helper. Проверяется тот же WebView/controller, main frame и точный локальный путь index.html. Hash navigation допустима, удалённые страницы не допускаются. WebKit smoke теперь использует production trust helper, а не только отдельный обработчик без проверки происхождения.

## Проверки

- Перед изменениями production build/check прошли; baseline probe зафиксировала English fallback; отсутствие «Слушать отсюда» и безусловный currentIndex=0 подтверждены исходной реализацией.
- `bash scripts/check.sh` — PASS: production build, WebKit 390/320, существующие Apple/engine tests, Saved tests, start-from-block tests, 34 новых English cases и 94 объединённых cases.
- WebKit regression: actual action pointerdown → selection cleared → click → production trust check → Swift store. Затем Listen с тем же block ID, source navigation, text/topic fallback, фильтры и повторная extraction. Это автоматическая DOM-интеграционная проверка на macOS WebKit.
- Исходный technical-corpus.json и capture parity не переписаны. Новый technical-regression-corpus.json содержит 60 старых случаев (4 намеренно обновлённых ожидания: team, frobnicate, example.com, myAPI) и 34 новых. Проверка словаря выполняется отдельно для всех entries.
- Модели, ONNX, auxiliary preprocessing и DSP не менялись. Аудиты сохранённых research captures (audit_ios, audit_preprocessing, audit_technical) — PASS; это не новый синтез всех WAV.

## Simulator и границы подтверждения

Исправленная production сборка установлена и запущена в iPhone 17 Pro Simulator. Видна реальная тема 10.5. Полный ручной сценарий с двумя выделениями, Save, перезапуском и Listen на обоих движках не подтверждён: доступный инструмент управления не воспроизводит long press/маркеры выделения в WebKit. Поэтому автоматические тесты не обозначаются как выполненный ручной сценарий. Субъективное звучание English в Simulator также не подтверждено прослушиванием; проверена точная TTS-копия на входе в неизменённый синтезатор.

## Git

Целевой commit: `fix: improve reading navigation and saved excerpts`. Точный hash и фактический push status приводятся в итоговом сообщении после операции (коммит не может содержать собственный hash). В commit входят исходники и тесты, включая ранее локальные Saved/gestures. Generated models/audio/tensors/results и личный signing config исключены через .gitignore.
