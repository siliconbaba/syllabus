import SwiftUI

struct SavedExcerptsView: View {
    @ObservedObject var store: SavedExcerptStore
    var body: some View {
        NavigationStack {
            Group {
                if store.excerpts.isEmpty {
                    Text("Здесь появятся сохранённые фрагменты учебника.")
                        .foregroundStyle(.secondary).multilineTextAlignment(.center).padding(32)
                } else {
                    List {
                        ForEach(store.excerpts) { item in
                            Button {
                                store.isPresented = false
                                store.openSource?(item)
                            } label: {
                                VStack(alignment: .leading, spacing: 8) {
                                    Text(item.text).foregroundStyle(.primary).lineLimit(6)
                                    Text(item.topicTitle).font(.caption).foregroundStyle(.secondary)
                                    if let section = item.sectionTitle, !section.isEmpty {
                                        Text(section).font(.caption2).foregroundStyle(.secondary)
                                    }
                                }.padding(.vertical, 6)
                            }
                        }.onDelete { offsets in store.delete(ids: Set(offsets.map { store.excerpts[$0].id })) }
                    }
                }
            }
            .navigationTitle("Сохранённое")
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Готово") { store.isPresented = false } } }
        }
    }
}
