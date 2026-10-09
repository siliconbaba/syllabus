import SwiftUI

struct TrainerProfileView: View {
    let profile: TrainerProfile
    let openDiagnostic: () -> Void
    private func percent(_ score: Double?) -> String { score.map { String(format: "%.0f%%", $0 * 100) } ?? "—" }
    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
            Text("Профиль").font(.largeTitle.bold())
            if profile.eligibleCount == 0 {
                Text("Пока нет данных профиля").font(.title2.bold())
                Text("Пройдите диагностику: профиль учитывает только чистые первые ответы из завершённых диагностик.")
                Button("Пройти диагностику", action: openDiagnostic).buttonStyle(.borderedProminent).frame(minHeight: 44)
            } else {
                if let level = profile.levelTitle { Text(level).font(.largeTitle.bold()) }
                else { Text(profile.missingEvidence > 0 ? "Пока недостаточно данных для устойчивой оценки уровня" : "Уровень пока не подтверждён").font(.title2.bold()) }
                Text("\(profile.confidence.title) · чистых диагностических ситуаций: \(profile.eligibleCount)").font(.headline)
                Text("Уверенность в уровне определяется самым малым из необходимых наборов ответов. Ситуаций в таком наборе: \(profile.relevantEvidenceCount). Она отражает объём данных, а не уверенность в себе.").font(.footnote).foregroundStyle(.secondary)
                Text("Уровень показывает сложность ситуаций, в которых вы стабильно принимаете сильные контекстные решения. Это профиль внутри тренажёра, а не сертификация.")
                if profile.plus { Text("«+» — положительный сигнал по следующему уровню; его полный порог ещё не подтверждён.").foregroundStyle(.secondary) }
                if let next = profile.nextLevel {
                    Text("До \(next.title)").font(.title2.bold())
                    ForEach(profile.requirements, id: \.level) { requirement in
                        VStack(alignment: .leading, spacing: 6) {
                            Text("\(requirement.level.title): \(percent(requirement.evidence.score)) · нужно \(percent(requirement.threshold))").font(.headline)
                            Text("Ситуаций: \(requirement.evidence.count) · \(requirement.evidence.confidence.title)")
                            Text(requirement.met ? "Порог подтверждён" : requirement.missingCount > 0 ? "Дополнительных ситуаций этой сложности нужно минимум: \(requirement.missingCount)" : "Нужны более стабильные решения в ситуациях этой сложности").foregroundStyle(.secondary)
                        }
                    }
                    if profile.missingEvidence > 0 { Text("Для проверки порогов нужны дополнительные чистые ситуации соответствующей сложности — минимум \(profile.missingEvidence). Их может пока не быть в банке.") }
                    if next == .head {
                        Text("Области с достаточным числом ситуаций Senior/Head: \(profile.breadthDomains.count) из 5 областей (минимум \(TrainerScoringEngine.headDomainEvidence) ситуации на область).")
                        Text("Обязательны люди или стейкхолдеры и портфель/стратегия или финансы/бизнес. \(profile.breadthMet ? "Условие выполнено." : "Пока не подтверждено.")")
                    }
                }
                DisclosureGroup("Сложность ситуаций") {
                    ForEach(TrainerLevel.allCases, id: \.self) { level in
                        let metric = profile.buckets[level]!
                        Text("\(level.title): \(percent(metric.score)) · ситуаций: \(metric.count) · \(metric.confidence.title)").frame(maxWidth: .infinity, alignment: .leading).padding(.vertical, 8)
                    }
                }
                Text("Области").font(.title2.bold())
                ForEach(TrainerDomain.allCases) { domain in
                    metricRow(domain.title, profile.domains[domain]!)
                }
                Text("Мышление").font(.title2.bold())
                if profile.strengths.isEmpty { Text("Пока мало данных для выделения сильных паттернов и зон роста. Нужно минимум 5 ситуаций на категорию.") }
                else {
                    Text("Сильнее в текущем профиле").font(.headline)
                    ForEach(profile.strengths) { pattern in metricRow(pattern.title, profile.patterns[pattern]!) }
                    if !profile.growth.isEmpty {
                        Text("Зоны роста").font(.headline)
                        ForEach(profile.growth) { pattern in metricRow(pattern.title, profile.patterns[pattern]!) }
                    }
                }
                DisclosureGroup("Все наблюдения о мышлении") {
                    ForEach(TrainerThinking.allCases.filter { $0 != .context }) { pattern in
                        metricRow(pattern.title, profile.patterns[pattern] ?? .init(score: nil, count: 0)).padding(.vertical, 8)
                    }
                }
                Text("Контекстная чувствительность пока не рассчитывается: нужна отдельная проверка связанных пар ситуаций.").font(.footnote).foregroundStyle(.secondary)
            }
            if profile.excludedMetadataCount > 0 { Text("Не учтено ответов с неподдерживаемыми метаданными: \(profile.excludedMetadataCount)").foregroundStyle(.secondary) }
            Text("Scoring model v\(profile.scoringModelVersion)").font(.caption).foregroundStyle(.secondary)
        }
    }
    private func metricRow(_ title: String, _ metric: TrainerProfile.Metric) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title).font(.headline)
            Text("\(percent(metric.score)) · ситуаций: \(metric.count)\(metric.littleData ? " · мало данных" : "")")
            if let score = metric.score { ProgressView(value: score, total: 1) }
            Text(metric.confidence.title).font(.caption).foregroundStyle(.secondary)
        }.frame(maxWidth: .infinity, alignment: .leading)
    }
}
