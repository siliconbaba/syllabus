# Сборка с локальным нейросетевым голосом

Сначала выполните обычную настройку Xcode по README. Xcode получает закреплённый ONNX Runtime 1.24.2 через Swift Package Manager; интернет нужен для первой установки зависимости, но не для чтения.

Модели не входят в Git. Нужен существующий проверенный набор из `experiments/silero-ios-feasibility/`: пять synthesis ONNX в `artifacts/onnx-dsp`, accent/homograph/data.json в `artifacts/preprocessing`, window.bin в `ios/SileroIOSPoC/Fixtures`. Точные пути, размеры и SHA256 перечислены в `Config/SileroResources.json`.

Из корня репозитория:

```sh
bash scripts/prepare_silero_models.sh
bash scripts/check.sh
open InteractiveBook.xcodeproj
```

Скрипт работает офлайн: проверяет все исходные файлы, затем копирует единственный набор в `InteractiveBook/SileroResources`. При несовпадении SHA256 или отсутствии файла завершает работу с ошибкой. Не скачивает latest и не переэкспортирует модель. После изменения набора повторите подготовку и сборку.

В Xcode выберите свою Team и подключённый iPhone, затем Run. В меню скорости читалки выберите «Озвучивание → Нейросетевой».

Без проверенных исследовательских артефактов системная читалка остаётся доступной; нейросетевой режим сообщает об ошибке и возвращается к системному. Репозиторий сам по себе пока не содержит канала распространения весов. Не подменяйте отсутствующий набор произвольной моделью с похожим названием.

Не добавляйте модели, словари, golden WAV и fixtures в Git или дополнительные Xcode targets. Production folder содержит только семь ONNX, data.json, window.bin и manifest.json. Размер ресурсов — 220 189 054 байта плюс небольшой manifest.
