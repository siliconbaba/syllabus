"""Offline SVG figures for the integrated textbook. No runtime library."""
from html import escape as esc
import textwrap

def node(key, label, x, y, kind='service', w=210):
    h=76
    shape=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{2 if kind=="external" else 12}" />'
    if kind=='database':
        shape=f'<path d="M{x},{y+12} a{w/2},12 0 0 1 {w},0 v{h-24} a{w/2},12 0 0 1 -{w},0 Z"/><ellipse cx="{x+w/2}" cy="{y+12}" rx="{w/2}" ry="12"/>'
    elif kind=='queue':
        shape=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2"/><path d="M{x+7},{y+7} H{x+w-7} M{x+7},{y+h-7} H{x+w-7}"/>'
    lines=textwrap.wrap(label,22,break_long_words=False)
    text=''.join(f'<tspan x="{x+w/2}" dy="{0 if i==0 else 19}">{esc(line)}</tspan>' for i,line in enumerate(lines))
    return f'<g class="diagram-node {kind}">{shape}<text x="{x+w/2}" y="{y+29-(len(lines)-2)*8}" text-anchor="middle">{text}</text></g>'

def shell(key,title,scope,width,height,svg,description):
    return f'''<div class="system-diagram" id="{key}">
<h6>{esc(title)}</h6><p class="diagram-scope">Граница разбора: {esc(scope)}</p>
<div class="diagram-scroll" tabindex="0" role="region" aria-label="{esc(title)} — схема с горизонтальной прокруткой">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="--diagram-width:{width}px" role="img" aria-label="{esc(title)}">
<defs><marker id="{key}-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="currentColor"/></marker></defs>{svg}</svg></div>
<p class="diagram-legend" aria-hidden="true">Сервис — скруглённый блок · БД — цилиндр · Брокер — двойная рамка · Внешняя система — пунктирная рамка. Сплошная стрелка — sync; пунктир — async/callback. Для автомата двойная рамка — terminal.</p>
<p class="diagram-description">{esc(description)}</p></div>'''

def architecture(key,title,labels,edges,description,scope='контейнеры сервиса; внешние участники вне пунктирной границы'):
    # Positions are authored, not inferred by a layout engine.
    height=max(n[3]+76 for n in labels)+28
    out=f'<rect class="system-boundary" x="12" y="110" width="796" height="{height-240}" rx="18"/><text class="boundary-label" x="26" y="132">Наша система</text>'
    if key=='sd-architecture-payments':
        out=f'<path class="system-boundary" d="M12 110 H808 V270 H565 V405 H808 V{height-130} H12 Z"/><text class="boundary-label" x="26" y="132">Наша система</text>'
    byid={n[0]:n for n in labels}
    for a,b,label,async_ in edges:
        aa,bb=byid[a],byid[b];ax,ay=aa[2]+105,aa[3]+38;bx,by=bb[2]+105,bb[3]+38
        if abs(ay-by)<5:
            sx=ax+(105 if bx>ax else -105);ex=bx+(-105 if bx>ax else 105)
            path=f'M{sx},{ay} H{ex}';lx=(sx+ex)/2;ly=ay-12
        else:
            sy=ay+(38 if by>ay else -38);ey=by+(-38 if by>ay else 38)
            mid=(sy+ey)/2
            path=f'M{ax},{sy} V{mid} H{bx} V{ey}'
            lx=(ax+bx)/2 if ax!=bx else ax+8;ly=mid-9
        out+=f'<path class="diagram-edge {"async" if async_ else ""}" d="{path}" marker-end="url(#{key}-arrow)"/><text class="edge-label" x="{lx}" y="{ly}" text-anchor="{"middle" if ax!=bx else "start"}">{esc(label)}</text>'
    for args in labels:out+=node(*args)
    return shell(key,title,scope,820,height,out,description)

def sequence(key,actors,steps):
    width=max(650,len(actors)*160);height=125+len(steps)*69
    xs=[80+i*(width-160)/(len(actors)-1) for i in range(len(actors))]
    out='<text class="boundary-label" x="10" y="18">Время ↓ · шаги сверху вниз</text>'
    for i,a in enumerate(actors):
        x=xs[i];out+=f'<rect class="sequence-actor" x="{x-69}" y="30" width="138" height="50" rx="8"/>'
        for j,line in enumerate(textwrap.wrap(a,18)):out+=f'<text x="{x}" y="{51+j*17}" text-anchor="middle">{esc(line)}</text>'
        out+=f'<path class="lifeline" d="M{x},80 V{height-10}"/>'
    prose=[]
    for i,(a,b,label,async_) in enumerate(steps):
        y=118+i*69;ax,bx=xs[a],xs[b];start,end=ax,bx
        path=f'M{start},{y} H{end}' if a!=b else f'M{ax},{y} h38 v24 h-38'
        out+=f'<path class="diagram-edge {"async" if async_ else ""}" d="{path}" marker-end="url(#{key}-arrow)"/>'
        for j,line in enumerate(textwrap.wrap(f'{i+1}. {label}',max(24,int(abs(ax-bx)/8)))):out+=f'<text class="edge-label" x="{(ax+bx)/2 if a!=b else ax+45}" y="{y-25+j*17}" text-anchor="{"middle" if a!=b else "start"}">{esc(line)}</text>'
        prose.append(f'{i+1}. {actors[a]} → {actors[b]}: {label}.')
    return shell(key,'Последовательность основного сценария','порядок запросов и событий; альтернативы отмечены явно',width,height,out,' '.join(prose))

def payment_states():
    key='sd-payment-states';w=800;h=785
    states=[('CREATED',290,20),('LIMITS_CHECKED',290,135),('HELD',290,250),('SENT',290,365),('CONFIRMED',30,505),('REJECTED',550,505),('TIMEOUT',290,505),('RELEASED',550,680)]
    edges=[(0,1,'лимиты',False),(1,2,'резерв',False),(2,3,'отправка',True),(3,4,'успех',True),(3,5,'отказ',True),(3,6,'нет ответа',True),(5,7,'компенсация',False),(6,7,'неуспех подтверждён',False)]
    out=''
    for a,b,label,async_ in edges:
        _,ax,ay=states[a];_,bx,by=states[b];ax+=105;bx+=105
        out+=f'<path class="diagram-edge {"async" if async_ else ""}" d="M{ax},{ay+76} V{(ay+76+by)/2} H{bx} V{by}" marker-end="url(#{key}-arrow)"/><text class="edge-label" x="{(ax+bx)/2+7}" y="{(ay+76+by)/2-8}">{esc(label)}</text>'
    for label,x,y in states:
        out+=node(label,label,x,y,'service')
        if label in ['CONFIRMED','RELEASED']:out+=f'<rect class="terminal" x="{x+5}" y="{y+5}" width="200" height="66" rx="8"/>'
    return shell(key,'Жизненный цикл перевода','статус операции, резерв и подтверждение внешнего результата',w,h,out,'CREATED: запрос записан. LIMITS_CHECKED: проверки пройдены. HELD: средства зарезервированы. SENT: запрос передан оператору. CONFIRMED — подтверждённый успех; REJECTED — подтверждённый отказ, после компенсации RELEASED. TIMEOUT означает неизвестный результат, а не доказанный отказ: сначала опрос статуса, сверка или подтверждённая отмена; затем CONFIRMED либо REJECTED и RELEASED. Возврат из terminal в CREATED запрещён; возврат денег после успеха — отдельная операция. Сам таймер не даёт права считать перевод неисполненным.')

ARCH={
'payments':(
 [('client','Клиент · Mobile / Web',305,15,'external'),('gateway','API Gateway',305,160,'service'),('risk','Антифрод + лимиты',35,300,'service'),('transfer','Transfer Service',305,300,'service'),('ledger','Ledger / АБС',575,300,'external'),('db','Transfers DB + Outbox',305,440,'database'),('bus','Kafka transfer-events',305,580,'queue'),('connector','PSP Connector',305,720,'service'),('consumers','Уведомления + история',575,720,'service'),('operator','Оператор → банк получателя',305,860,'external')],
 [('client','gateway','HTTPS',False),('gateway','transfer','request',False),('transfer','risk','check',False),('transfer','ledger','hold',False),('transfer','db','transaction',False),('db','bus','event / async',True),('bus','connector','event',True),('bus','consumers','event',True),('connector','operator','request / callback',True)],
 'Клиент входит через шлюз. Transfer Service проверяет антифрод и лимиты, резервирует средства в ledger и сохраняет перевод с outbox. Publisher передаёт событие в Kafka; независимые потребители — PSP Connector, уведомления и история. Коннектор общается с оператором и банком-получателем. Сверка сопоставляет журнал переводов с реестром оператора; её расхождения получает операционная команда. Ledger и платёжная сеть — отдельные контуры, одной транзакции между ними и нашей БД нет.'),
'notifications':(
 [('client','Сервисы + кампании',305,15,'external'),('ingest','Ingest API',305,160,'service'),('prefs','Профили + шаблоны',35,300,'database'),('bus','Kafka: critical / normal / bulk',305,300,'queue'),('router','Router',305,440,'service'),('senders','Push / SMS / Email Senders',305,580,'service'),('status','Status Processor + deliveries',575,580,'database'),('dlq','DLQ + разбор ошибок',575,720,'queue'),('providers','APNs / FCM / RuStore · SMS / email',305,860,'external')],
 [('client','ingest','API / dedup_key',False),('ingest','bus','async',True),('bus','router','consume',True),('router','prefs','read',False),('router','senders','channel queues',True),('senders','providers','send / rate limit',True),('senders','status','SENT / callback',True),('status','dlq','исчерпаны попытки',True)],
 'Приём валидирует и дедуплицирует сообщение. Физически раздельные приоритеты critical, normal и bulk изолируют нагрузку. Router читает предпочтения, выбирает канал и публикует в очереди push, SMS или email. Sender ограничивает скорость к провайдеру; callbacks обновляют deliveries через status-events и Status Processor. Исчерпанные попытки направляются в DLQ, критичные сообщения переключаются на резерв по политике.'),
'gateway':(
 [('client','Клиенты / партнёры',305,15,'external'),('entry','DNS / anycast + L4',305,160,'service'),('config','Config + ключи JWT',35,300,'service'),('gateway','API Gateway × N',305,300,'service'),('counters','KV: счётчики + TTL',575,440,'database'),('limit','Auth + Rate Limiter',305,440,'service'),('router','Router: timeout / retry',305,580,'service'),('metrics','Логи / usage / метрики',575,580,'service'),('backends','Внутренние backend-сервисы',305,860,'external')],
 [('client','entry','HTTPS',False),('entry','gateway','route',False),('config','gateway','push policy',True),('gateway','limit','local first',False),('limit','counters','atomic update',False),('limit','router','allow / 429',False),('router','metrics','async',True),('router','backends','proxy',False)],
 'DNS/anycast выбирает ДЦ, L4 — экземпляр шлюза. JWT проверяется локально по закэшированному ключу. Rate Limiter сначала проверяет локальные бакеты, затем при необходимости распределённый счётчик. Превышение даёт 429 и Retry-After без вызова backend. Router применяет бюджет timeout/retry. Политики доставляются Config Service, логи и usage собираются отдельно. Между ДЦ счётчики синхронизируются асинхронно.'),
'migration':(
 [('client','Клиенты',305,15,'external'),('facade','Strangler Facade + флаги',305,160,'service'),('old','Монолит',35,300,'service'),('new','Orders Service + ACL',575,300,'service'),('olddb','Старая БД',35,460,'database'),('sync','CDC / Outbox / сверка',305,610,'queue'),('newdb','Orders DB',575,460,'database'),('report','Read API / отчётность',305,860,'external')],
 [('client','facade','request',False),('facade','old','old route',False),('facade','new','new / shadow',False),('old','olddb','read/write',False),('new','newdb','read/write',False),('olddb','sync','CDC: expand',True),('newdb','sync','outbox: write cutover',True),('sync','report','проекции / сверка',True)],
 'Фасад переключает маршруты по флагу. Новый Orders использует собственную БД и anti-corruption layer для старых контрактов. На expand CDC догоняет новую БД из старой; после переключения владельца записи outbox поддерживает старую проекцию для отката. Это разные фазы, не неконтролируемая двусторонняя запись. Сверка читает обе БД и служит входом Go/No-Go. Внешняя отчётность получает read API или реплику проекции.'),
'taxi':(
 [('client','Водитель / пассажир',305,15,'external'),('loc','Location Gateway + Kafka',35,160,'queue'),('order','API + Order Service',575,160,'service'),('geo','Location Service + геоиндекс',35,320,'database'),('db','Orders DB + order-events',575,320,'database'),('dispatch','Dispatch + Routing / ETA',305,480,'service'),('surge','Surge + zone_state',35,610,'service'),('offer','Offer Service',305,700,'service'),('app','Приложения: push / socket',305,860,'external')],
 [('client','loc','координаты / WS',True),('client','order','HTTPS',False),('loc','geo','event',True),('order','db','transaction',False),('db','dispatch','order event',True),('geo','dispatch','кандидаты',False),('surge','dispatch','сигнал зоны',False),('dispatch','offer','кандидаты + ETA',False),('offer','app','offer / accept',True)],
 'Потоки разделены: частые координаты идут через Location Gateway и Kafka в геоиндекс в памяти; заказы — через Order Service в надёжную БД и order-events. Dispatch читает соседние ячейки, запрашивает ETA и ранжирует кандидатов. Offer отправляет предложение с таймаутом, Order Service атомарно подтверждает единственное назначение. Surge обновляет zone_state; Estimates использует цену и ETA. Архиватор отдельно пишет историю координат в холодное хранилище.'),
'flags':(
 [('admin','Владелец флага',305,15,'external'),('control','Управление + аудит + права',305,160,'service'),('db','Версии правил в БД',305,300,'database'),('dist','Раздача + кэш',305,440,'service'),('sdk','SDK: snapshot + defaults',305,580,'service'),('app','40 сервисов / mobile',305,860,'external')],
 [('admin','control','изменение',False),('control','db','write version',False),('db','dist','read',False),('dist','sdk','push + pull',True),('sdk','app','локальная оценка',False)],
 'Владелец меняет правило через управление с правами и аудитом. Версионированные правила попадают в раздачу. SDK опрашивает её и принимает ускоряющий push, хранит последний валидный снапшот на диске. Проверка флага локальна; отказ сервиса флагов не блокирует бизнес-запрос. Последний рубеж — безопасные дефолты в коде.'),
'dora':(
 [('sources','Трекер / Git / CI / инциденты',305,15,'external'),('connect','Коннекторы + лимиты API',305,160,'service'),('raw','Неизменяемый сырой слой',305,300,'database'),('model','Нормализация + справочник',305,440,'service'),('mart','Модель + витрина метрик',305,580,'database'),('checks','Качество + lineage',575,580,'service'),('users','Команды / еженедельный отчёт',305,860,'external')],
 [('sources','connect','API раз в час',False),('connect','raw','append',False),('raw','model','read',False),('model','mart','расчёт',False),('mart','checks','валидация',False),('mart','users','дашборд / отчёт',False)],
 'Коннекторы инкрементально забирают события с ретраями и лимитами API. Сырой слой сохраняет исходные записи. Нормализация связывает команду, сервис, репозиторий, релиз и инцидент по справочнику. Версионированный расчёт строит витрину; от каждой цифры можно перейти к модельным и сырым событиям. Проверки полноты, свежести, аномалий и непривязанных событий направляются владельцам данных.')
}
SEQ={
'payments':(['Клиент','Transfer','Ledger','DB / Outbox','PSP / оператор'],[(0,1,'POST + Idempotency-Key',False),(1,1,'антифрод / лимиты',False),(1,2,'hold с ID перевода',False),(2,1,'резерв подтверждён',False),(1,3,'перевод + событие',False),(1,0,'ACCEPTED + transfer_id',False),(3,4,'publisher → Kafka → connector',True),(4,1,'callback / результат опроса',True),(1,2,'capture либо release',False),(1,0,'статус + уведомление',True),(1,4,'при timeout: запрос статуса; не новый перевод',False)]),
'notifications':(['Инициатор','Ingest','Kafka / Router','Sender','Провайдер'],[(0,1,'POST + dedup_key',False),(1,2,'priority event',True),(1,0,'202 + notification_id',False),(2,3,'канал + шаблон + preferences',True),(3,4,'send с rate limit',False),(4,3,'SENT / provider ID',False),(4,3,'callback → Status Processor',True),(3,3,'временная ошибка: backoff + jitter',True),(3,2,'лимит попыток: DLQ / fallback по политике',True)]),
'gateway':(['Клиент','Gateway','Limiter / KV','Backend'],[(0,1,'HTTPS / JWT',False),(1,1,'локальная проверка подписи',False),(1,2,'локальный бакет; при необходимости KV',False),(2,1,'allow либо deny',False),(1,0,'deny → 429 + Retry-After',False),(1,3,'allow → proxy с timeout',False),(3,1,'response',False),(1,3,'при сетевом сбое: один retry только идемпотентного',False),(1,0,'response + Request ID',False)]),
'migration':(['Клиент','Фасад','Монолит','Новый сервис','CDC / сверка'],[(0,1,'запрос',False),(1,2,'старый путь',False),(1,3,'shadow: только безопасное чтение',True),(2,1,'ответ пользователю',False),(3,4,'сравнение результатов',True),(4,1,'Go / No-Go по SLI и расхождениям',False),(1,3,'после Go: 1 → 10 → 50 → 100%',False),(3,4,'после write cutover: outbox в старую проекцию',True),(4,1,'сбой до contract: согласованный rollback',False)]),
'taxi':(['Водитель','Location / Geo','Order','Dispatch / Offer','Пассажир'],[(0,1,'координаты каждые 4 с через Kafka',True),(4,2,'POST order + ключ',False),(2,3,'SEARCHING event',True),(3,1,'кандидаты из соседних ячеек',False),(3,3,'ETA batch + ранжирование',False),(3,0,'offer с timeout',True),(0,2,'accept: атомарная проверка версии',False),(2,4,'ASSIGNED + ETA',True),(3,0,'при timeout: следующий кандидат',True)])
}
def overview(key):
    nodes,edges,desc=ARCH[key]
    return architecture('sd-architecture-'+key,'Архитектура: '+{'payments':'платёжный контур','notifications':'доставка уведомлений','gateway':'шлюз и лимиты','migration':'поэтапное разделение монолита','taxi':'подбор водителя','flags':'фича-флаги','dora':'метрики поставки'}[key],nodes,edges,desc)
def flow(key): return sequence('sd-sequence-'+key,*SEQ[key])

def deployment():
    key='sd-gateway-deployment';out=''
    for x,name in [(20,'ДЦ A'),(420,'ДЦ B')]:
        out+=f'<rect class="system-boundary" x="{x}" y="20" width="350" height="445" rx="16"/><text x="{x+18}" y="48">{name}</text>'
        out+=node(name+'gw','Gateway × N / локальные бакеты',x+65,90)
        out+=node(name+'kv','KV cluster / primary + replicas',x+65,270,'database')
        out+=f'<path class="diagram-edge" d="M{x+170},166 V270" marker-end="url(#{key}-arrow)"/><text class="edge-label" x="{x+180}" y="222">atomic update</text>'
    out+=f'<path class="diagram-edge async" d="M295,312 H485" marker-end="url(#{key}-arrow)"/><text class="edge-label" x="390" y="295" text-anchor="middle">async delta</text>'
    return shell(key,'Развёртывание и отказ: лимиты в двух ДЦ','локальные кластеры и асинхронная межцентровая синхронизация',790,490,out,'DNS/anycast направляет клиента в ближайший доступный ДЦ, L4 распределяет запросы между несколькими gateway. В каждом ДЦ свой кластер счётчиков с репликами. Дельты между ДЦ синхронизируются асинхронно: при разделении сети лимит может быть превышен в пределах согласованной погрешности. Для строгого тарифа заранее выбирают fail closed; для массового некритичного трафика — ограниченный fail open с локальным бакетом. После отказа ДЦ оставшийся контур должен выдержать перераспределённую нагрузку.')
