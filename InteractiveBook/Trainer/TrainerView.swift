import SwiftUI

struct TrainerView: View {
    @ObservedObject var store: TrainerStore
    @Environment(\.dismiss) private var dismiss
    @State private var active = false
    @State private var assessmentActive = false
    @State private var shownResultID: UUID?
    @State private var bank: TrainerBank?
    @State private var bankError: String?
    @State private var catalog: TrainerCatalog?
    private enum Setup { case mixed, sections, section(String), sizes([TrainerCase], TrainerSession), mistakes, diagnostic, history, profile }
    private struct Launch { let cases: [TrainerCase]; let session: TrainerSession }
    @State private var setup: Setup?
    @State private var pending: Launch?
    private enum Confirmation { case replace, attempt, progress, diagnostic }
    @State private var confirmation: Confirmation = .attempt
    @State private var resetRequested = false
    private let accent = Color(red: 0.72, green: 0.05, blue: 0.18)

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    if let id = shownResultID, let result = store.diagnosticHistory.results.first(where: { $0.id == id }) {
                        diagnosticSummary(result)
                    } else if assessmentActive, let attempt = store.diagnostic {
                        diagnosticSession(attempt)
                    } else if active, let attempt = store.attempt {
                        if attempt.phase == .completed { summary(attempt) }
                        else { session(attempt) }
                    } else { home }
                }
                .frame(maxWidth: 680, alignment: .leading)
                .padding(20).frame(maxWidth: .infinity)
            }
            .id(shownResultID?.uuidString ?? (assessmentActive ? "diagnostic-\(store.diagnostic?.index ?? 0)" : active ? "\(store.attempt?.index ?? 0)-\(store.attempt?.phase.rawValue ?? "")" : setupIdentity))
            .background(Color(uiColor: .systemGroupedBackground))
            .navigationTitle("Тренажёр")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    if active || assessmentActive || shownResultID != nil || setup != nil { Button("К началу") { goHome() } }
                    else { Button("В учебник") { dismiss() } }
                }
                ToolbarItem(placement: .primaryAction) {
                    Menu {
                        Button("В учебник") { dismiss() }
                        if let a = store.attempt, a.phase != .completed {
                            Button("Сбросить текущую тренировку", role: .destructive) { ask(.attempt) }
                        }
                        if store.diagnostic != nil {
                            Button("Сбросить диагностику", role: .destructive) { ask(.diagnostic) }
                        }
                        Button("Сбросить учебный прогресс", role: .destructive) { ask(.progress) }
                    } label: { Image(systemName: "ellipsis.circle").frame(minWidth: 44, minHeight: 44) }
                    .accessibilityLabel("Действия тренажёра")
                }
            }
            .tint(accent)
            .confirmationDialog(confirmationTitle, isPresented: $resetRequested, titleVisibility: .visible) {
                Button(confirmationAction, role: .destructive) {
                    switch confirmation {
                    case .replace: if let pending = pending { launch(pending, replacing: true) }
                    case .attempt: if store.resetAttempt() { active = false; setup = nil }
                    case .progress: if store.resetProgress() { goHome() }
                    case .diagnostic: if store.resetDiagnostic() { goHome() }
                    }
                    pending = nil
                }
                Button("Отмена", role: .cancel) { pending = nil }
            } message: { Text(confirmationMessage) }
            .alert("Не удалось сохранить или восстановить попытку", isPresented: Binding(get: {store.error != nil}, set: {if !$0 {store.error = nil}})) {
                Button("Понятно") { store.error = nil }
            } message: { Text(store.error ?? "") }
            .task {
                guard bank == nil else { return }
                do {
                    guard let url = Bundle.main.url(forResource: "TrainerContent", withExtension: nil)?.appendingPathComponent("cases.json") else { throw TrainerError.invalidBank }
                    let loadedBank = try TrainerBank.load(url: url)
                    catalog = try TrainerCatalog.load(url: url.deletingLastPathComponent().appendingPathComponent("topics.json"))
                    bank = loadedBank
                } catch { bankError = error.localizedDescription }
            }
        }
    }

    private func goHome() { active = false; assessmentActive = false; shownResultID = nil; setup = nil }
    private var setupIdentity: String {
        switch setup {
        case .none: return "home"
        case .mixed: return "mixed"
        case .sections: return "sections"
        case .section(let id): return "section-" + id
        case .sizes(_, let session): return "sizes-" + session.title
        case .mistakes: return "mistakes"
        case .diagnostic: return "diagnostic"
        case .history: return "history"
        case .profile: return "profile"
        }
    }
    private var confirmationTitle: String {
        switch confirmation {
        case .replace: return "Заменить незавершённую тренировку?"
        case .attempt: return "Сбросить текущую тренировку?"
        case .progress: return "Сбросить учебный прогресс?"
        case .diagnostic: return "Сбросить незавершённую диагностику?"
        }
    }
    private var confirmationAction: String {
        switch confirmation { case .replace: return "Заменить и начать"; case .attempt: return "Сбросить тренировку"; case .progress: return "Удалить учебный прогресс"; case .diagnostic: return "Сбросить диагностику" }
    }
    private var confirmationMessage: String {
        switch confirmation {
        case .replace: return "Набор и место остановки текущей тренировки будут заменены. Накопленные ошибки сохранятся."
        case .attempt: return "Будет удалена только незавершённая тренировка. Накопленные ошибки сохранятся."
        case .progress: return "Будут удалены тренировка, учебные результаты и ошибки, активная диагностика и вся история диагностик. Учебник, сохранённые фрагменты и настройки озвучивания останутся."
        case .diagnostic: return "Будет удалена только незавершённая диагностика. История диагностик и учебный прогресс сохранятся. Уже подтверждённые ситуации не станут новыми."
        }
    }
    private func ask(_ intent: Confirmation) { confirmation = intent; resetRequested = true }
    private func request(_ cases: [TrainerCase], session: TrainerSession, count: Int? = nil) {
        let value = Launch(cases: TrainerCatalog.sample(cases, count: count), session: session)
        guard !value.cases.isEmpty else { return }
        if let a = store.attempt, a.phase != .completed { pending = value; ask(.replace) }
        else { launch(value, replacing: store.attempt != nil) }
    }
    private func launch(_ value: Launch, replacing: Bool) {
        if store.start(cases: value.cases, session: value.session, replacing: replacing) { setup = nil; active = true }
    }
    private func choose(_ cases: [TrainerCase], session: TrainerSession) {
        if cases.count > 15 { setup = .sizes(cases, session) }
        else { request(cases, session: session) }
    }
    @ViewBuilder private var home: some View {
        if case .profile = setup {
            TrainerProfileView(profile: TrainerScoringEngine.profile(history: store.diagnosticHistory)) { setup = .diagnostic }
        } else if case .history = setup {
            diagnosticHistoryView
        } else if let setup = setup, let bank = bank, let catalog = catalog {
            switch setup {
            case .history, .profile: EmptyView()
            case .diagnostic: diagnosticSetup(bank)
            case .mixed: sizes(bank.trainingCases, session: TrainerSession(kind: .mixed, title: "Смешанная"))
            case .sizes(let cases, let session): sizes(cases, session: session)
            case .sections:
                Text("По разделу").font(.largeTitle.bold())
                ForEach(catalog.availableSections(in: bank.cases)) { section in
                    choice(section.title, detail: "Ситуаций: \(catalog.casesForSection(section.id, in: bank.cases).count)") { self.setup = .section(section.id) }
                }
            case .section(let id):
                let title = catalog.sections.first { $0.id == id }?.title ?? "Раздел"
                Text(title).font(.title.bold())
                primary("Весь раздел") { choose(catalog.casesForSection(id, in: bank.cases), session: TrainerSession(kind: .section, title: title, sectionID: id)) }
                ForEach(catalog.availableTopics(sectionID: id, in: bank.cases)) { topic in
                    choice(topic.title, detail: "Ситуаций: \(catalog.casesForTopic(topic.id, in: bank.cases).count)") {
                        choose(catalog.casesForTopic(topic.id, in: bank.cases), session: TrainerSession(kind: .topic, title: topic.title, sectionID: id, topicID: topic.id))
                    }
                }
            case .mistakes:
                let cases = store.progress.unresolved(in: bank.cases)
                Text("Работа над ошибками").font(.largeTitle.bold())
                if cases.isEmpty { Text("Ошибок для повторения пока нет").font(.title3) }
                else {
                    Text("Ситуаций для повторения: \(cases.count)")
                    Text("Выберите наиболее сильное решение, чтобы отметить ошибку как исправленную.").foregroundStyle(.secondary)
                    primary("Повторить ошибки") { request(cases, session: TrainerSession(kind: .mistakes, title: "Работа над ошибками")) }
                }
            }
        } else {
            VStack(alignment: .leading, spacing: 20) {
                Text("Тренажёр управленческого мышления").font(.largeTitle.bold())
                Text("Тренировки с разбором, диагностика на новых ситуациях и профиль управленческого мышления.").font(.title3)
                if let a = store.attempt {
                    if a.phase != .completed {
                        Text("\(a.title) · \(a.index + 1) из \(a.cases.count)").font(.headline)
                        primary("Продолжить тренировку") { active = true }
                        Button("Сбросить текущую тренировку", role: .destructive) { ask(.attempt) }.frame(minHeight: 44)
                    } else { primary("Итог последней тренировки") { active = true } }
                }
                if let a = store.diagnostic {
                    Text("Диагностика · \(a.index + 1) из \(a.cases.count)").font(.headline)
                    primary("Продолжить диагностику") { assessmentActive = true }
                    Button("Сбросить диагностику", role: .destructive) { ask(.diagnostic) }.frame(minHeight: 44)
                }
                if !store.recoveryRequired {
                    choice("Профиль", detail: "Уровень, области и мышление по завершённым диагностикам") { setup = .profile }
                    choice("История диагностик", detail: "Завершено: \(store.diagnosticHistory.results.count)") { setup = .history }
                }
                if store.recoveryRequired {
                    Text("Сохранённые данные недоступны и не будут заменены без подтверждения.")
                    Button("Сбросить учебный прогресс", role: .destructive) { ask(.progress) }
                } else if let bank = bank {
                    choice("Диагностика", detail: "Серия новых ситуаций без подсказок и разбора по ходу. Результаты и разбор — после завершения.") { setup = .diagnostic }
                    choice("Смешанная тренировка", detail: "5, 10, 15 или все ситуации") { setup = .mixed }
                    choice("По разделу", detail: "Весь раздел или отдельная тема") { setup = .sections }
                    choice("Работа над ошибками", detail: "Для повторения: \(store.progress.unresolved(in: bank.cases).count)") { setup = .mistakes }
                    Button("Сбросить учебный прогресс", role: .destructive) { ask(.progress) }.frame(minHeight: 44)
                } else if let error = bankError { Text(error).foregroundStyle(.secondary) }
                else { ProgressView("Загрузка ситуаций…") }
            }
        }
    }
    private func sizes(_ cases: [TrainerCase], session: TrainerSession) -> some View {
        VStack(alignment: .leading, spacing: 20) {
            Text(session.title).font(.title.bold())
            Text("Сколько ситуаций пройти?").font(.title3)
            ForEach([5, 10, 15].filter { $0 <= cases.count }, id: \.self) { count in
                primary("\(count) ситуаций") { request(cases, session: session, count: count) }
            }
            primary("Все доступные (\(cases.count))") { request(cases, session: session) }
        }
    }
    private func choice(_ title: String, detail: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 8) {
                Text(title).font(.headline)
                Text(detail).font(.subheadline).foregroundStyle(.secondary)
            }.frame(maxWidth: .infinity, minHeight: 56, alignment: .leading).padding(16)
                .background(Color(uiColor: .secondarySystemGroupedBackground)).clipShape(RoundedRectangle(cornerRadius: 12))
        }.buttonStyle(.plain).multilineTextAlignment(.leading)
    }

    @ViewBuilder private func session(_ a: TrainerAttempt) -> some View {
        let c = a.cases[a.index]
        Text("\(a.title) · \(a.index + 1) из \(a.cases.count)").font(.subheadline.weight(.semibold)).foregroundStyle(.secondary)
        Text(c.topicTitle).font(.title2.bold())
        Text(c.context).font(.title3).lineSpacing(5)
        Text(c.question).font(.headline)
        if a.phase == .answer {
            answerOptions(c, draft: a.draftOptionID, select: store.select, confirm: store.confirm)
        } else if let selected = a.answers[c.id] {
            TrainerReview(test: c, selectedID: selected)
            primary(a.index == a.cases.count - 1 ? "К итогу" : "Следующий вопрос") { store.next() }
        }
    }

    private func answerOptions(_ c: TrainerCase, draft: String?, select: @escaping (String) -> Void, confirm: @escaping () -> Void) -> some View {
        VStack(alignment: .leading, spacing: 24) {
            ForEach(c.options) { option in
                Button { select(option.id) } label: {
                    HStack(alignment: .top, spacing: 12) {
                        Image(systemName: draft == option.id ? "checkmark.circle.fill" : "circle").font(.title2)
                        Text(option.text).font(.body).frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .padding(16).frame(minHeight: 56)
                    .foregroundStyle(Color.primary)
                    .background(Color(uiColor: .secondarySystemGroupedBackground))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .overlay(RoundedRectangle(cornerRadius: 12).stroke(draft == option.id ? accent : Color.secondary.opacity(0.3), lineWidth: draft == option.id ? 2 : 1))
                }.buttonStyle(.plain).accessibilityAddTraits(draft == option.id ? .isSelected : [])
            }
            primary("Подтвердить ответ", action: confirm).disabled(draft == nil)
            Text("До подтверждения можно изменить выбор.").font(.footnote).foregroundStyle(.secondary)
        }
    }
    private func diagnosticSetup(_ bank: TrainerBank) -> some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Диагностика").font(.largeTitle.bold())
            Text("Разбор появится только после завершения. Подтверждённые ответы нельзя изменить.")
            if let a = store.diagnostic {
                Text("Есть незавершённая диагностика: \(a.index + 1) из \(a.cases.count)")
                primary("Продолжить диагностику") { assessmentActive = true; setup = nil }
                Button("Сбросить диагностику", role: .destructive) { ask(.diagnostic) }.frame(minHeight: 44)
            } else {
                let available = store.unseen(in: bank.cases).count
                Text("Новых ситуаций доступно: \(available)")
                if available == 0 { Text("Новых ситуаций для диагностики пока нет").font(.title3) }
                else {
                    if available >= 10 { primary("10 ситуаций") { startDiagnostic(bank, count: 10) } }
                    else { Text("Для диагностики на 10 ситуаций новых кейсов недостаточно. Можно пройти все оставшиеся.").foregroundStyle(.secondary) }
                    primary("Все доступные новые ситуации (\(available))") { startDiagnostic(bank, count: nil) }
                }
            }
        }
    }
    private func startDiagnostic(_ bank: TrainerBank, count: Int?) {
        if store.startDiagnostic(bank: bank, count: count) { assessmentActive = true; active = false; setup = nil }
    }
    private func diagnosticSession(_ a: DiagnosticAttempt) -> some View {
        let c = a.cases[a.index]
        return VStack(alignment: .leading, spacing: 24) {
            Text("Диагностика · \(a.index + 1) из \(a.cases.count)").font(.subheadline.weight(.semibold)).foregroundStyle(.secondary)
            Text(c.context).font(.title3).lineSpacing(5)
            Text(c.question).font(.headline)
            answerOptions(c, draft: a.draftOptionID, select: { store.selectDiagnostic($0, testID: c.id) }, confirm: {
                if store.confirmDiagnostic(testID: c.id), store.diagnostic == nil {
                    shownResultID = a.id; assessmentActive = false; setup = nil
                }
            })
        }
    }
    private var diagnosticHistoryView: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("История диагностик").font(.largeTitle.bold())
            if store.diagnosticHistory.results.isEmpty { Text("Завершённых диагностик пока нет") }
            ForEach(store.diagnosticHistory.results.reversed()) { result in
                choice(result.completedAt.formatted(date: .abbreviated, time: .shortened),
                       detail: "\(result.cases.count) ситуаций · \(result.strongestCount) из \(result.cases.count)") { shownResultID = result.id; setup = nil }
            }
        }
    }
    private func diagnosticSummary(_ result: DiagnosticResult) -> some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Диагностика завершена").font(.largeTitle.bold())
            Text(result.completedAt.formatted(date: .abbreviated, time: .shortened)).foregroundStyle(.secondary)
            Text("Ситуаций: \(result.cases.count)")
            Text("\(result.strongestCount) из \(result.cases.count) решений совпали с наиболее сильной стратегией в сохранённой версии ситуаций.").font(.title3)
            Text("Результат относится к сохранённой версии ситуаций. Это не оценка профессионального уровня.").foregroundStyle(.secondary)
            primary("На главный экран тренажёра") { goHome() }
            reviews(cases: result.cases, answers: result.answers)
            primary("Вернуться в учебник") { dismiss() }
        }
    }

    private func summary(_ a: TrainerAttempt) -> some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Разобрано ситуаций: \(a.cases.count)").font(.largeTitle.bold())
            let bestCount = a.cases.filter { c in c.options.contains { $0.id == a.answers[c.id] && $0.isBest } }.count
            Text("\(bestCount) из \(a.cases.count) решений совпали с наиболее сильной стратегией").font(.title3)
            if a.mode == .mistakes {
                Text("Исправлено этой тренировкой: \(a.resolvedIDs?.count ?? 0)")
                Text("Осталось для повторения: \(store.progress.unresolved(in: bank?.cases ?? a.cases).count)")
            }
            primary("На главный экран тренажёра") { active = false; setup = nil }
            Text("Вернитесь к любому решению и перечитайте разбор. Это учебная попытка, а не оценка вашего уровня.")
            reviews(cases: a.cases, answers: a.answers)
            primary("Вернуться в учебник") { dismiss() }

        }
    }
    private func reviews(cases: [TrainerCase], answers: [String: String]) -> some View {
        VStack(alignment: .leading, spacing: 20) {
            ForEach(Array(cases.enumerated()), id: \.element.id) { index, c in
                NavigationLink {
                    ScrollView {
                        VStack(alignment: .leading, spacing: 20) {
                            Text(c.topicTitle).font(.title2.bold())
                            Text(c.context).font(.title3)
                            Text(c.question).font(.headline)
                            TrainerReview(test: c, selectedID: answers[c.id] ?? "")
                        }.padding(20).frame(maxWidth: 680)
                    }.navigationTitle("Разбор \(index + 1)").navigationBarTitleDisplayMode(.inline)
                } label: {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("\(index + 1). \(c.topicTitle)").font(.headline)
                        Text(c.question).foregroundStyle(.primary)
                        Text("Ваше решение: " + (c.options.first(where: {$0.id == answers[c.id]})?.text ?? "")).foregroundStyle(.secondary)
                        Text("Открыть разбор →").foregroundStyle(accent)
                    }.frame(maxWidth: .infinity, alignment: .leading).padding(16)
                        .background(Color(uiColor: .secondarySystemGroupedBackground)).clipShape(RoundedRectangle(cornerRadius: 12))
                }.buttonStyle(.plain).multilineTextAlignment(.leading)
            }
        }
    }
    private func primary(_ title: String, action: @escaping () -> Void) -> some View {
        Button(action: action) { Text(title).font(.headline).frame(maxWidth: .infinity, minHeight: 44) }
            .buttonStyle(.borderedProminent)
    }
}

private struct TrainerReview: View {
    let test: TrainerCase
    let selectedID: String
    var body: some View {
        VStack(alignment: .leading, spacing: 22) {
            if let chosen = test.options.first(where: {$0.id == selectedID}) {
                block("Ваше решение", chosen.text)
                Text(chosen.explanation)
                if !chosen.isBest { block("Почему этот ответ привлекателен", chosen.whyTempting); block("Что он упускает", chosen.whyNotBest) }
            }
            if let best = test.options.first(where: \.isBest) { block("Лучшее решение в этой ситуации", best.text); Text(best.explanation) }
            block("Что нужно было заметить", test.keyInsight)
            ForEach(test.decisiveFacts, id: \.self) { Text("• " + $0) }
            block("Модель мышления", test.mentalModel)
            ForEach(test.options) { option in
                DisclosureGroup("Подробнее о варианте \(option.id.uppercased())") {
                    VStack(alignment: .leading, spacing: 12) {
                        Text(option.text).font(.headline)
                        Text(option.explanation)
                        block("Почему привлекателен", option.whyTempting)
                        block("Ограничения решения", option.whyNotBest)
                        block("Когда был бы лучшим", option.whenItWouldBeBest)
                    }.padding(.vertical, 12)
                }.padding(.vertical, 6)
            }
        }.textSelection(.enabled)
    }
    private func block(_ title: String, _ text: String) -> some View {
        VStack(alignment: .leading, spacing: 8) { Text(title).font(.headline); Text(text).lineSpacing(3) }
    }
}
