import Foundation

/// Research-only additions. Existing pronunciations are referenced, not copied.
enum TechnicalLexicon {
    static let additions:[String:String] = [
        "TCP":"ти си пи", "IP":"ай пи", "URL":"ю ар эл", "URI":"ю ар ай",
        "NoSQL":"ноу эс кью эль", "YAML":"ямл", "CI":"си ай", "CD":"си ди",
        "SLI":"эс эл ай", "KPI":"кей пи ай", "OKR":"оу кей ар", "MVP":"эм ви пи",
        "A/B":"эй би", "B2B":"би ту би", "B2C":"би ту си", "CRM":"си ар эм", "ERP":"и ар пи",
        "IAM":"ай эм", "SSO":"эс эс оу", "OAuth":"оу аут", "JWT":"джей дабл ю ти",
        "SDK":"эс ди кей", "CLI":"си эл ай", "IDE":"ай ди и", "JVM":"джей ви эм",
        "DB":"ди би", "DBMS":"ди би эм эс", "ETL":"и ти эл", "ELT":"и эл ти",
        "CDC":"си ди си", "OLTP":"оу эл ти пи", "OLAP":"олап", "QA":"кью эй",
        "DevOps":"девопс", "SRE":"эс ар и", "RTO":"ар ти оу", "RPO":"ар пи оу",
        "Postgres":"постгрес", "Docker Compose":"докер компоуз", "Docker":"докер",
        "Git":"гит", "GitLab":"гитлаб", "GitHub":"гитхаб", "Java":"джава", "Kotlin":"котлин",
        "Swift":"свифт", "Python":"пайтон", "JavaScript":"джаваскрипт", "TypeScript":"тайпскрипт",
        "React":"реакт", "Redis":"редис", "MongoDB":"монго ди би", "Oracle":"оракл", "Linux":"линукс",
        "nginx":"энджин икс", "Grafana":"графана", "Prometheus":"прометеус", "Jira":"джира",
        "Confluence":"конфлюенс", "Jenkins":"дженкинс", "RabbitMQ":"рэббит эм кью", "Debezium":"дебезиум",
        "iOS":"ай оу эс", "CPU":"си пи ю", "RAM":"оперативной памяти", "RPS":"ар пи эс", "TPS":"ти пи эс",
        "WAL":"вал", "MAU":"эм эй ю", "DAU":"ди эй ю", "Conversion":"конверсия",
        "Lead time":"лид тайм", "merge request":"мёрдж реквест", "pull request":"пул реквест",
        "pipeline":"пайплайн", "release":"релиз", "deploy":"деплой", "commit":"коммит",
        "GB":"гигабайт", "MB":"мегабайт", "KB":"килобайт", "TB":"терабайт"
    ]
    static let entries = SpeechTextProcessor.pronunciations.merging(additions) { original,_ in original }
    static let letters:[String:String] = ["a":"эй","b":"би","c":"си","d":"ди","e":"и","f":"эф","g":"джи","h":"эйч","i":"ай","j":"джей","k":"кей","l":"эл","m":"эм","n":"эн","o":"оу","p":"пи","q":"кью","r":"ар","s":"эс","t":"ти","u":"ю","v":"ви","w":"дабл ю","x":"экс","y":"уай","z":"зед"]
}
