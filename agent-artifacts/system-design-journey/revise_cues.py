"""Editorial authoring map. Resolve selected sentences to exact build-time excerpts.
Run only when intentionally revising the editorial map; build.py never guesses cues.
"""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
chapters=sum([json.loads(p.read_text()) for p in sorted(ROOT.glob('chapters-*.json'))],[])
# Definition anchors, additional key-thought anchors, boundary section, terms.
# Each anchor is chosen for meaning, not frequency or paragraph position.
SPECS=[
(['Состояние —','Функциональное требование описывает'],['Требование качества задаёт','Цена, применённая при оформлении'],5,['Состояние','Источник истины','Функциональное требование']),
(['HTTP задаёт','Аутентификация отвечает','Авторизация —'],['Проверка только в интерфейсе','Граница доверия проходит'],1,['HTTP','Аутентификация','Авторизация']),
(['Первичный ключ устойчиво','Нормализация уменьшает','Журнал предзаписи, WAL'],['Снимок названия товара','Сумму тоже нельзя'],5,['Первичный ключ','Нормализация','WAL']),
(['Транзакция объединяет','Изоляция определяет','Резерв —'],['Проверка и изменение выполняются','Читатель получает видимые'],5,['Транзакция','MVCC','Резерв']),
(['B-tree хранит','EXPLAIN показывает'],['Каждый дополнительный индекс','Читать его полезно от листьев'],5,['B-tree','EXPLAIN','селективностью']),
(['Вертикальное масштабирование','L4 —','Сессия связывает'],['Процесс может существовать','Это полезная оптимизация'],4,['Вертикальное масштабирование','L4','Сессия']),
(['Кэш хранит','TTL задаёт'],['Роль определяет','между фиксацией и удалением'],5,['Кэш','TTL','cache-aside']),
(['Шардирование делит','Репликация создаёт'],['Дисковая сохранность также','При потере узла'],2,['Шардирование','Репликация','RDB']),
(['Идемпотентной называют'],['Следовательно, это свидетельство','Статус failed допустим'],3,['Идемпотентной','payment_attempt','unknown']),
(['ESB, корпоративная','Webhook переворачивает'],['Интеграция начинается','Партнёр должен различать'],5,['ESB','Webhook','gRPC']),
(['Событие «платёж подтверждён»'],['Если за минуту приходит','Kafka естественна'],3,['Kafka','offset','RabbitMQ']),
(['Saga описывает','CQRS разделяет','CDC, change data capture'],['В одной транзакции потребитель','Требуется явная корректировка'],5,['Saga','CQRS','CDC','outbox']),
(['Инвертированный индекс связывает','Документная модель хранит'],['Поэтому обязательные ограничения','Outbox или CDC из предыдущей главы'],3,['Инвертированный индекс','ранжирование','фасеты']),
(['Пространственный индекс организует','Map matching сопоставляет'],['Прямая дистанция полезна','Точка на линии полигона'],4,['Пространственный индекс','ST_DWithin','Map matching']),
(['Matching, сопоставление'],['В базе назначения нужен','Система оптимальна на снимках'],4,['Matching','атомарный переход','временные окна']),
([],['Один транспортный ack','Авторизация проверяется','не всякая команда безопасна'],5,['WebSocket','sequence','heartbeat']),
(['Согласованность, consistency','Гарантия read-your-writes'],['Временная липкость','Договор read-your-writes проходит'],4,['Согласованность','read-your-writes','Failover']),
(['Ключ шарда определяет'],['Хеш order_id даёт','Равный объём диска'],2,['Ключ шарда','Хеш','Перебалансировка']),
(['Lease —'],['Это свойство множеств становится','Нужен способ подтвердить'],4,['Lease','Raft','кворум']),
(['Service level indicator','Service level objective','Recovery point objective'],['Когда входящий поток превышает','Среднее количество запросов'],2,['SLI','SLO','RPO','RTO']),
(['Online transaction processing','Extract-transform-load','Extract-load-transform'],['Grain, зернистость','В колоночном представлении'],5,['OLTP','OLAP','ETL','ELT']),
(['Event time —','Processing time —'],['Если строить маршрут по времени приёма','Подтверждение брокера означает'],5,['Event time','MQTT','Time series']),
(['Content delivery network'],['Сумма задержек захвата','короткоживущие подписанные права'],5,['CDN','origin','манифест']),
(['Tenant, арендатор','Workflow, рабочий процесс'],['Самый полезный тест арендаторов','Общая схема с tenant_id'],2,['Tenant','Workflow','Noisy neighbor']),
(['Дрейф данных означает'],['Предсказание не равно причинному эффекту','Accuracy неудобна'],2,['Precision','recall','training/serving skew']),
(['ACL —'],['Поисковый слой фильтрует','При конфликте двух источников'],0,['ACL','LLM','prompt injection']),
(['Агентом здесь называется','Инструмент —'],['Доступ агента ограничен','Ключ создаёт приложение'],4,['Агентом','Идемпотентность','prompt injection']),
(['TCO, total cost','SLO — целевой'],['Если помощник стал отвечать дешевле','Экономия не принимается'],4,['TCO','SLO','предельную стоимость']),
(['Ограниченный контекст —','Control plane —','Data plane —'],['Два сервиса, которые пишут','Но это свойство нужно построить'],2,['DDD','Ограниченный контекст','Control plane','Data plane']),
(['Миграцией называют','Cutover —'],['Expand-migrate-contract означает','Равное количество строк'],4,['Expand-migrate-contract','Cutover','CDC']),
(['Модель угроз описывает','Минимизация означает','Аудит отвечает'],['Проверенный pull request','Ни один вид не заменяет'],2,['Модель угроз','Аудит','Runbook']),
(['Сценарий качества задаёт'],['Профессиональный перенос начинается','Компонент становится частью аргумента'],2,['Сценарий качества','инварианта','RTO'])
]
def sentences(c):
 for i,s in enumerate(c['sections']):
  for p in re.findall(r'<p>(.*?)</p>',s['html'],re.S):
   if '<table' in p or '<pre' in p:continue
   for sentence in re.split(r'(?<=[.!?])\s+',p):
    yield i,sentence

def select(c,anchor):
 hits=[(i,s) for i,s in sentences(c) if anchor in re.sub('<[^>]+>','',s)]
 if len(hits)!=1:
  raise ValueError((c['id'],anchor,len(hits)))
 return hits[0]
result={}
for c,(definitions,keys,boundary,terms) in zip(chapters,SPECS):
 cues=[]
 for kind,anchors in [('definition',definitions),('key',keys)]:
  for anchor in anchors:
   i,fragment=select(c,anchor)
   if fragment is None:continue
   cues.append({'section':i,'kind':kind,'html':fragment})
 # A boundary explains consequences, so retain its whole short paragraph.
 fragment=re.search(r'<p>(.*?)</p>',c['sections'][boundary]['html'],re.S).group(1)
 # Do not stack a second cue on an already labelled boundary paragraph.
 cues=[cue for cue in cues if not(cue['section']==boundary and cue['html'] in fragment)]
 cues.append({'section':boundary,'kind':'boundary','html':fragment})
 for term in terms:
  hits=[i for i,s in enumerate(c['sections']) if term in re.sub('<[^>]+>','',s['html'])]
  if not hits:
   raise ValueError((c['id'],'term',term))
  cues.append({'section':hits[0],'kind':'term','html':term})
 result[c['id']]=cues
(ROOT/'reading-cues.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('Saved exact editorial cues for',len(result),'chapters')
