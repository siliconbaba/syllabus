# ONNX Runtime + независимый DSP: Silero v5_5_ru

Дата: 2026-09-24. Продолжение исходного feasibility, без изменений production/iOS/preprocessing. Baseline SHA256: `50081637b602126ee06cb3bc8a744d25651d2da149ee8864b9a379bfdd934437`; xenia, CPU, 48000 Hz, исходные восемь prepared fixtures.

## Вывод

**Численный критерий выполнен на 8/8 fixtures:** пять ONNX-графов с неизменёнными float32-весами + host orchestration + независимый DSP воспроизводят исходный waveform с одинаковыми длинами и малыми ошибками. Предсказанные целочисленные durations совпали полностью. В цепочке синтеза нет вызова monolithic TorchScript waveform graph. Дополнительно `run_onnx_only.py` повторил все восемь результатов в отдельном процессе без импорта PyTorch; `reports/onnx-dsp/onnx-only-parity.json` фиксирует `torch_loaded=false`.

Полный перцептивный критерий ещё не закрыт: WAV сохранены, но слепого A/B-прослушивания не проводилось. Метрики убедительно поддерживают близость, но не заменяют слуховой тест. На физическом iPhone этот путь пока не запускался.

## 1. Точная real-valued boundary

Выбрана непосредственно **после `vocoder.head.out(backbone_output).transpose(1,2)`**, до split/exp/trigonometry/complex construction. Исходник: `artifacts/package/.data/ts_code/code/__torch__/vocoder/hifigan/vocos/vocos/heads.py`.

Вход в head: float32 `[B,F,512]` (проверено по исходному linear weight `[2402,512]`). Выход linear/transpose: float32 `[1,2402,F]`. Первая половина каналов — 1201 log-magnitude bins, вторая — 1201 phase bins в радианах. 1201 = FFT/2+1; это **не** сохранённые real/imag части.

```text
log_mag, phase = split(spectral, 2, channel_axis)
magnitude = min(exp(log_mag), 100)
real = magnitude * cos(phase)
imag = magnitude * sin(phase)
S = magnitude * (cos(phase) + i*sin(phase))
```

В ONNX остаются backbone и финальный linear, в host DSP вынесены exp/clamp, cos/sin и первая complex-операция. В `capture_spectral.py` копия inlined graph возвращает дополнительный tensor, не меняя вычислений оригинала; проверяется exact equality возвращённого waveform с сохранённым golden. Дополнительно сохранены durations, pitch и mel.

## 2. Независимый DSP

`onnx_dsp.py` использует только NumPy, не импортирует Silero/PyTorch и не вызывает исходный ISTFT:

1. Восстанавливает spectrum по формулам выше, complex64.
2. `irfft(n=2400, axis=frequency, norm='backward')`.
3. Умножает каждый frame на исходное окно 2400 samples.
4. Размещает frame k со сдвигом `k*600` и суммирует overlap.
5. Отдельно суммирует `window**2` в тех же позициях.
6. Обрезает 900 samples слева и справа: `(2400-600)/2`.
7. Делит waveform на обрезанную window-envelope.

Итоговая длина: `600*F`. Сохранён именно исходный float32 window buffer (`artifacts/onnx-dsp/window.npy`). Это periodic Hann; повторная генерация текущим PyTorch отличается максимум на `5.96e-8`, поэтому для строгого parity используются исходные коэффициенты. Перенос на iOS должен сохранить их или отдельно проверить генерацию.

Результат DSP-only: длины совпали 8/8; max abs ≤ 2.3842e-7; RMSE ≤ 1.4061e-8; relative L2 ≤ 1.0928e-7; SNR 139.23–139.60 dB. Полная таблица ниже и `reports/onnx-dsp/dsp-parity.json`. Ошибка соответствует различию float32 FFT/порядка суммирования, а не изменению window/crop/length.

## 3. Экспортированная цепочка

```text
prepared sequence / speaker_ids / type_ids
    ├─ duration.onnx → predicted log durations
    │      → host: exp, clamp, round, original duration endpoint rules
    └─ pitch.onnx → pitch
           → host: original abs(pitch)<0.001 threshold
    → encoder.onnx → token-rate acoustic representation
    → host repeat_interleave using PREDICTED durations
    → decoder.onnx → mel
    → spectral.onnx (original vocoder backbone + head linear)
    → float32 [1,2402,F]
    → independent NumPy DSP
    → waveform
```

Пять файлов: duration, pitch, encoder, decoder, spectral. Суммарный размер 88614894 байта (~84.51 MiB). Opset 18, стандартные ONNX operators, без ATen fallback/custom runtime operators. `onnx.checker` прошёл для каждого; каждый загружен ONNX Runtime CPU. Веса не квантизировались и не переводились в float16. Audit: `reports/onnx-dsp/graph-audit.json`.

В host orchestration перенесены операции, уже присутствовавшие в оригинале. Ограничения durations на начальных/конечных позициях, включая исходную константу 13, — **штатная математика Silero**, не подгонка по fixtures. Ни одна длительность не берётся из captured reference при runtime-синтезе. Reference durations использовались только для изолированных промежуточных проверок и example inputs экспортера.

Host path ограничен проверяемым baseline: batch=1, `symb_durs={}`, `focus_mask=None`, `pitch_coefs=1`, 48000 Hz; эти условия проверяются assertions. Иные prosody/focus/SSML inputs не заявляются поддержанными. `durs_rate` приходит из fixture и применяется штатно. Нулевая punctuation-loop ветка оригинала при batch=1 не добавляет изменений pitch; многобатчевый контракт не переносился.

## 4. Минимальные обходы exporter blockers

Прямой ScriptModule export после специализации `is_nested=False` и autocast=False всё ещё падал на `ScalarType UNKNOWN_SCALAR` внутри ONNX-конвертации `prim::If`. Эти неудачные пробы сохранены в `export_predictors.py`, `export_utils.py`, `reports/onnx-dsp/*-onnx-error.txt`.

Рабочий путь — export-only `nn.Module` adapters в `eager_components.py`, повторяющие packaged tensor math с теми же параметрами:

- Dense self-attention: те же QKV projections, head reshape, scale, mask, softmax, matmul, output projection; убраны runtime-проверки nested/autocast/fastpath, а не attention.
- Dropout в eval — identity; исходные norm/conv/linear/embeddings скопированы без изменения весов.
- Duration branching и length expansion вынесены на host; `np.repeat` эквивалентен исходному `repeat_interleave` для baseline, не interpolation.
- Hourglass decoder: динамический padding до multiple=3, тот же pooling, linear upsample и crop. Сохранено необычное поведение исходника: оба shortened blocks получают один и тот же downsampled input; первый результат не используется. Исправления архитектуры не было.
- Spectral wrapper остался scripted/frozen и содержит **исходные** backbone/head linear, без complex graph. Это устранило frontend trace registration error.

Математические операции не приближались: нет замены predictor/vocoder, retraining, изменения весов или ручного waveform alignment. Порядок float32 вычислений и реализация fused attention меняются, поэтому побитового совпадения после ONNX не ожидается. Это проверено отдельным PyTorch adapter-parity и конечными метриками.

## 5. Intermediate parity

Максимальные absolute errors по всем восьми случаям, reference → end-to-end ONNX path:

| Tensor | Max abs |
|---|---:|
| Predicted log duration | 3.69549e-6 |
| Rounded/processed duration | **0, exact 8/8** |
| Raw pitch | 2.02656e-6 |
| Mel | 1.51694e-5 |
| Raw spectral log-mag/phase | 2.20184e-2 |

Raw phase может иметь большую величину; абсолютная ошибка raw spectral сама по себе не является амплитудной ошибкой waveform. Поэтому дополнительно измерены waveform и log-spectral distance. Наихудший final случай — technical, он явно оставлен в отчёте, а не исключён.

Отдельные проверки на одинаковых промежуточных inputs:

- Исходный PyTorch duration → eager adapter: max abs 2.86102e-6.
- Исходный PyTorch pitch → eager adapter: 2.50340e-6.
- Исходный mel → eager acoustic adapters при исходных pitch/durations: 1.23978e-5.
- Eager encoder → ORT encoder: 1.00136e-5.
- Eager decoder → ORT decoder: 1.41859e-5.
- Исходный spectral head/backbone → ORT на одном mel: 6.36292e-3.

Все per-fixture RMSE/relative L2 доступны в `reports/onnx-dsp/onnx-parity.json`. Никаких одинаковых входов между разными кейсами не подставлялось.

## 6. Dynamic shapes

Один набор из пяти ONNX файлов прогнан на всех исходных token lengths: **59, 30, 81, 53, 34, 62, 19, 274**. Спектральные frames: **232, 125, 383, 225, 146, 243, 96, 1051**. Соответственно waveform от 57600 до 630600 samples. Model re-export/session recreation для смены длины не требуется.

Входы encoder/predictors имеют динамический token axis, decoder — динамический expanded-frame axis, spectral — динамический mel-frame axis. Padding/crop decoder динамические. Нет hardcoded T от question fixture. Ограничение batch=1 намеренное; произвольно большие длины и все возможные thresholds за пределами корпуса не проверялись. Positional encoding сохраняет исходную конечную ёмкость.

## 7. Производительность

Apple M4, macOS arm64, ONNX Runtime 1.30.0 CPU, 4 intra-op threads, 1 inter-op thread, стандартные graph optimizations runtime, float32. Без tuning/quantization.

Инициализация пяти sessions из файлов — **86.23 ms суммарно** в данном запуске, с уже тёплым filesystem cache; это не холодный запуск приложения. Время чтения fixtures, загрузка reference TorchScript и сравнение метрик не входят в synthesis timing. Таблица даёт median трёх повторений после первого прогона; сумма component medians — ориентир, не статистический benchmark. На iPhone значения не переносить.

## 8. Практический статус и следующий шаг

1. **Boundary:** выход исходного spectral linear до complex construction.
2. **Contract:** float32 `[1,2402,F]`: log magnitude + phase, 1201 bins каждая.
3. **External DSP:** успешен 8/8, одинаковые lengths.
4. **DSP metrics:** около 139 dB SNR, ≤2.38e-7 max abs.
5. **ONNX components:** duration, pitch, acoustic encoder, acoustic decoder, vocoder backbone+linear.
6. **Graphs:** пять, а не один monolith.
7. **Обходы:** dense attention adapters, host duration rules и repeat expansion, динамический pad/crop, scripted spectral wrapper.
8. **Математика:** сохранена; изменились порядок float32 операций и fused-kernel implementation.
9. **Dynamic lengths:** подтверждены на 8/8 разных T; нет static waveform size.
10. **Intermediate errors:** приведены выше и в JSON.
11. **Final waveform:** SNR 69.88–99.04 dB, relative L2 ≤3.205e-4, одинаковые durations/lengths.
12. **RTF:** 0.00683–0.02152 на Mac, без text preprocessing и session initialization.
13. **Переносимость синтезирующего ядра:** подтверждена на ONNX Runtime CPU Mac в данном baseline. Стандартные ops делают следующий ORT Mobile тест обоснованным, но устройство ещё не проверено.
14. **Оставшиеся риски:** host DSP parity на Accelerate/другом FFT, float32 rounding durations рядом с порогом .5 на новых текстах/backend, memory/latency на устройстве, preprocessing и две auxiliary-модели из предыдущего отчёта, непроверенные SSML/focus/другие speakers. Они не опровергают результат, но не позволяют объявить готовый полный iOS-порт.
15. **Ровно следующий минимальный технический шаг — отдельный iOS ONNX Runtime CPU fixture test**, с этими пятью моделями, исходным окном и теми же prepared tensors. Без UI/preprocessing/background и без production target. Сначала сравнить intermediate tensors, затем waveform с точным host DSP. До утверждения «без слышимой разницы» нужен слепой A/B готовых Mac WAV, особенно technical; ещё один Mac export experiment сейчас не требуется.

## Артефакты и границы вывода

- Новые captures: `artifacts/onnx-dsp/*-spectral.pt`, включая original waveform/durations/pitch/mel.
- Модели: `artifacts/onnx-dsp/{duration,pitch,encoder,decoder,spectral}.onnx`.
- A/B: `*-original.wav`, `*-external-dsp.wav`, `*-onnx-dsp.wav` в том же каталоге.
- Runtime outputs: `*-onnx-intermediates.npz`.
- JSON: `reports/onnx-dsp/`.
- `audit_stage2.py`: проверяет 8 lengths, exact durations, standard ONNX ops, типы и заданные численные regression bounds (это не psychoacoustic threshold).

Исходные golden fixtures/WAV не переписывались. Все stage-2 файлы находятся в исследовательском каталоге. Production diff остался прежним: только ранее существовавшие локальные Team настройки. GitHub не изменён.

## Полные численные таблицы

### External DSP против reference

| Fixture | Samples | Max abs | RMSE | Rel L2 | SNR dB | LSD dB |
|---|---:|---:|---:|---:|---:|---:|
| statement | 139200 | 1.78814e-07 | 1.2333e-08 | 1.04838e-07 | 139.590 | 0.000327008 |
| question | 75000 | 1.78814e-07 | 1.2959e-08 | 1.04692e-07 | 139.602 | 0.00034601 |
| homograph | 229800 | 2.38419e-07 | 1.25878e-08 | 1.07961e-07 | 139.335 | 0.000311335 |
| yo | 135000 | 1.78814e-07 | 1.27855e-08 | 1.07717e-07 | 139.354 | 0.000315794 |
| number | 87600 | 1.49012e-07 | 1.40607e-08 | 1.09279e-07 | 139.229 | 0.000387553 |
| technical | 145800 | 1.49012e-07 | 1.37566e-08 | 1.06262e-07 | 139.472 | 0.000355255 |
| abbreviations | 57600 | 1.78814e-07 | 1.24919e-08 | 1.07976e-07 | 139.333 | 0.000315846 |
| long | 630600 | 2.38419e-07 | 1.0757e-08 | 1.07047e-07 | 139.408 | 0.000308609 |

### ONNX + external DSP против reference

| Fixture | Samples | Max abs | RMSE | Rel L2 | SNR dB | LSD dB |
|---|---:|---:|---:|---:|---:|---:|
| statement | 139200 | 0.000164464 | 4.38441e-06 | 3.72701e-05 | 88.573 | 0.000713335 |
| question | 75000 | 2.74181e-05 | 1.38266e-06 | 1.11701e-05 | 99.039 | 0.000609344 |
| homograph | 229800 | 0.000412324 | 7.29473e-06 | 6.2564e-05 | 84.074 | 0.0019698 |
| yo | 135000 | 6.49691e-05 | 3.83026e-06 | 3.22698e-05 | 89.824 | 0.000805032 |
| number | 87600 | 0.000181884 | 8.74824e-06 | 6.79912e-05 | 83.351 | 0.00114362 |
| technical | 145800 | 0.00178294 | 4.14881e-05 | 0.000320473 | 69.884 | 0.00447924 |
| abbreviations | 57600 | 0.000248995 | 1.38812e-05 | 0.000119985 | 78.417 | 0.00423405 |
| long | 630600 | 9.2268e-05 | 3.5556e-06 | 3.53832e-05 | 89.024 | 0.000822582 |

LSD: RMS разницы log magnitude в dB, Hann 1024 / hop 256, floor -100 dB относительно максимума reference spectrum; без временного выравнивания или gain normalization. SNR = 20 log10(norm(reference)/norm(error)).

### Mac timing

| Fixture | Audio s | ORT ms | Host ms | DSP ms | Total ms | RTF |
|---|---:|---:|---:|---:|---:|---:|
| statement | 2.9000 | 23.645 | 0.051 | 4.638 | 28.333 | 0.00977 |
| question | 1.5625 | 21.043 | 0.081 | 2.861 | 23.985 | 0.01535 |
| homograph | 4.7875 | 25.467 | 0.065 | 7.601 | 33.133 | 0.00692 |
| yo | 2.8125 | 23.649 | 0.100 | 4.544 | 28.293 | 0.01006 |
| number | 1.8250 | 18.324 | 0.061 | 2.713 | 21.099 | 0.01156 |
| technical | 3.0375 | 23.895 | 0.108 | 4.484 | 28.487 | 0.00938 |
| abbreviations | 1.2000 | 23.175 | 0.083 | 2.563 | 25.821 | 0.02152 |
| long | 13.1375 | 70.005 | 0.149 | 19.616 | 89.769 | 0.00683 |
