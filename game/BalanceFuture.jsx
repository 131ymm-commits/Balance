import React, { useState, useMemo } from "react";

/*  БАЛАНС — ИГРА В БУДУЩЕЕ
    Баланс спустя N лет. Крутишь: насколько трудно обмануть (узкий диапазон —
    не невозможно). Выбираешь сервер. Смотришь, как меняется мир и чьи дети им правят.
    Проекция, не пророчество. У нас нет психоистории. */

const C = {
  ink: "#0e1114", panel: "#161b21", panel2: "#1b2129", line: "#2b333d",
  text: "#dbe1e8", dim: "#8b96a3", faint: "#5c6673",
  teal: "#5ad1c3", amber: "#e9a83e", red: "#e5564b", green: "#7bbf6a",
};

const ZONES = [
  { key: 0, name: "Легко обмануть", short: "сегодня", color: C.dim },
  { key: 1, name: "Труднее", short: "переход", color: C.teal },
  { key: 2, name: "Очень трудно", short: "узкий диапазон", color: C.amber },
  { key: 3, name: "Почти невозможно", short: "тотальная прозрачность", color: C.red },
];
// value 0..100 → zone. Sweet spot (amber) is the NARROW band 56–80.
function zoneOf(v) { return v < 30 ? 0 : v < 56 ? 1 : v <= 80 ? 2 : 3; }

const DOMAINS = [
  ["society", "Общество"], ["culture", "Культура"],
  ["labor", "Труд"], ["food", "Еда"], ["economy", "Экономика"],
];

// realistic = full 4 zones. fantastical/dark override z2/z3; fall back to realistic for z0/z1.
const REAL = {
  society: [
    "Доверие дорого проверять. Репутацию покупают, гейткиперы берут ренту за доступ, посредники множатся. Кто громче — тот и прав.",
    "Рядом с купленной выдачей появляются некупляемые индексы. Часть людей уходит к проверяемому доверию; институты пока прежние.",
    "Доверие дёшево проверяемо по исходу. Издержки падают, посредники-гейткиперы отмирают, институтов меньше и они тоньше. Полицентрично: много форкаемых индексов, ни одного центра. Репутацию не купить — её надо удержать.",
    "Обман невозможен, но и приватности нет: всё видно всем и государству. Легибельность тотальна — а это тоталитаризм. Общество без тайны — общество без границы.",
  ],
  culture: [
    "Вирусность, кликбейт, захват внимания. Громкость побеждает глубину; хайп обесценивает медленное.",
    "Медленная репутация начинает конкурировать с вирусной. Появляется спрос на честное.",
    "Компаундится доверие, не хайп. Вирусность теряет рычаг: подделку ловят по исходу. Меньше шума, больше долгого — но своеобразие живёт, потому что диапазон узкий, видно не всё.",
    "Всё измерено и оптимизировано под метрику. Культура схлопывается в безопасную одинаковость; риск, странность, приватное искусство исчезают. Гудхарт победил с другой стороны.",
  ],
  labor: [
    "Наём по резюме и связям; репутацию работника накручивают; кто громче себя продал, тот и взят.",
    "Рядом с резюме-накруткой появляются проверяемые репутации по реальному результату.",
    "Наём по реализованному результату, а не по саморекламе. Накрутить резюме не окупается; тихий, кто делает, обходит громкого, кто продаёт. Но приватность работника цела — не тотальный профиль.",
    "Каждый шаг работника записан и виден всем: ноль права на ошибку, ноль приватности, безопасная одинаковость. Рост через провал исчезает.",
  ],
  food: [
    "Еда конкурирует упаковкой и рекламой; здоровье — прокси на этикетке. Побеждает бюджет, не продукт.",
    "Некупляемые индексы состава рядом с рекламой; часть покупателей смотрит на честный сигнал.",
    "Еда конкурирует по реализованному исходу — вернулся ли ты, стало ли лучше. Маркетинг без продукта не окупается; честный мелкий производитель обходит гиганта рекламы. Состав не спрячешь — но и не тотальный надзор: вкус, культура, региональное живы.",
    "Каждый ингредиент и шаг записан и виден. Ноль тайны рецепта, ноль риска, ноль своеобразия — безопасная одинаковость. Кулинария как приватное искусство исчезает.",
  ],
  economy: [
    "Реклама-driven, Гудхарт: побеждает платящий за внимание, не делающий лучший продукт.",
    "Фитнес-функции по исходу появляются в быстрых доменах; медленные пока вслепую.",
    "Рынок судит по долгому следу покупки. Продавцы конкурируют качеством; зрение (почему проиграл) продаётся, место — нет. Эволюция к качеству вместо к громкости.",
    "Всё видно — рынок оптимизирован до плановой прозрачности. Риск и предпринимательская тайна исчезают; инновация без права на ошибку глохнет.",
  ],
};
const REAL_POWER = [
  "Правят владеющие вниманием и капиталом. Власть наследуется через деньги и медиа — детьми тех, кто купил рупор.",
  "Купленное влияние ещё работает, но слабеет. Появляется второй путь наверх — реальный исход.",
  "Захват внимания и покупка влияния перестают работать. Власть смещается к тем, чей реальный вклад доставляет, — и к их детям. Меритократия исхода вместо капитала. Но кто держит некупляемые весы, держит рычаг; всё висит на том, останется ли индекс форкаемым и ничьим.",
  "Правит тот, кто видит всё. Прозрачность для подданных, непрозрачность для власти — старейшая формула тирании в новой оболочке.",
];

const FANT = {
  society: [null, null,
    "Государства-гейткиперы растворяются; управление — сеть форкаемых репутационных контуров. Гражданство сменяется членством в локальных сообществах, а переезд между ними — базовое право (анти-захват).",
    "Единый индекс-разум видит каждого; общество прозрачно как стекло и мертво как стекло."],
  culture: [null, null,
    "Слава по исходу: художника помнят за то, что его вещи держат через тридцать лет, не за вирусный пик. Рождается «медленная культура» с горизонтом в поколение.",
    "Только измеримое под метрику разрешено; всё непредсказуемое отсеяно как «шум»."],
  labor: [null, null,
    "Работа течёт к тем, чей вклад держится годами; репутация переносима между работодателями; рождается «медленная карьера» с горизонтом в десятилетие.",
    "Каждый работник прозрачен как стекло; наём алгоритмичен и мёртв."],
  food: [null, null,
    "Локальные честные фермы; еда под индивидуальный профиль здоровья; исход меряется биомаркерами, не этикеткой. Реклама еды исчезла как класс.",
    "Питание назначается по показаниям сенсоров; удовольствие и культура еды атрофируются."],
  economy: [null, null,
    "Деньги — производная доверия; зрение (градиент поражения) — главный товар; рынок эволюционирует со скоростью долгого следа.",
    "Идеальная прозрачность = идеальный план; предпринимательство как ставка в неизвестность исчезает."],
};
const FANT_POWER = [null, null,
  "Правят дети тех, чей вклад держался поколениями: не богатейшие, а те, чей реальный след оказался самым долгим. Династия по исходу, а не по капиталу.",
  "Мир-паноптикум под одним честным весом — и его хозяин бог. Фантастика показывает ровно то, почему монополия индекса недопустима."];

const DARK = {
  society: [null, null,
    "«Честный» индекс один, и он чей-то. Обман извне труден — но владелец весов решает, что есть правда. Полицентризм не сложился; вернулся центр.",
    "Захваченный тотальный индекс правит всем и зовётся правдой."],
  culture: [null, null,
    "Разрешена только культура, измеримая под метрику владельца; «нечестное» = не одобренное индексом. Инакомыслие исчезает как «низкий рейтинг».",
    "Единый рейтинг диктует вкус; несогласие статистически стёрто."],
  labor: [null, null,
    "«Честную» репутацию работника считает один индекс, и он чей-то; кто вне его — «ненадёжен»; несогласие = «низкий рейтинг».",
    "Единый индекс решает, кто работает; альтернативы нет."],
  food: [null, null,
    "Что ты ешь, решает рейтинг; «неодобренное» вымывается с полок. Честность стала инструментом одного.",
    "Единый весовщик назначает рацион всем; альтернативы нет."],
  economy: [null, null,
    "Плановая экономика через «честный» рейтинг — новый Госплан в оболочке доверия.",
    "Рынок упразднён: индекс распределяет, потому что «знает лучше»."],
};
const DARK_POWER = [null, null,
  "Правят дети тех, кто первым монополизировал весы. «Честность» — их наследственный инструмент: некупляемое стало неотчуждаемо-их. Вот почему форкаемость индекса — не деталь, а всё.",
  "Захваченный тотальный индекс = совершенная тирания, называющая себя правдой."];

const SERVERS = {
  realistic: { label: "Реалистичный", note: "заземлённая проекция из механики Баланса", domains: REAL, power: REAL_POWER, tone: C.teal },
  fantastical: { label: "Фантастический", note: "результаты доведены до предела — мысленный предел, не прогноз", domains: FANT, power: FANT_POWER, tone: C.amber },
  dark: { label: "Тёмный", note: "некупляемые весы захвачены — что бывает, если антимонополия провалилась", domains: DARK, power: DARK_POWER, tone: C.red },
};

function pick(server, domain, zone) {
  const s = SERVERS[server];
  const cell = s.domains[domain] && s.domains[domain][zone];
  return cell != null ? cell : REAL[domain][zone];
}
function pickPower(server, zone) {
  const cell = SERVERS[server].power[zone];
  return cell != null ? cell : REAL_POWER[zone];
}

export default function BalanceFuture() {
  const [difficulty, setDifficulty] = useState(68); // start in the sweet spot
  const [year, setYear] = useState(30);
  const [server, setServer] = useState("realistic");

  const zone = zoneOf(difficulty);
  const z = ZONES[zone];
  const inSweet = zone === 2;
  const settled = year >= 25 ? "устоялся" : year >= 8 ? "складывается" : "только начался";

  const mono = { fontFamily: "ui-monospace, 'SF Mono', 'JetBrains Mono', Menlo, monospace" };
  const serif = { fontFamily: "'Iowan Old Style', Georgia, 'Times New Roman', serif" };

  const gradient = useMemo(() =>
    `linear-gradient(90deg, ${C.dim} 0%, ${C.dim} 28%, ${C.teal} 32%, ${C.teal} 54%, ${C.amber} 58%, ${C.amber} 79%, ${C.red} 84%, ${C.red} 100%)`, []);

  return (
    <div style={{ background: C.ink, color: C.text, minHeight: "100%" }} className="w-full">
      <style>{`
        .bf-range{ -webkit-appearance:none; appearance:none; width:100%; height:34px; background:transparent; cursor:pointer; }
        .bf-range:focus{ outline:none; }
        .bf-range:focus-visible::-webkit-slider-thumb{ box-shadow:0 0 0 3px ${C.ink}, 0 0 0 5px ${C.teal}; }
        .bf-range::-webkit-slider-thumb{ -webkit-appearance:none; appearance:none; width:14px; height:34px; border-radius:3px; background:${C.text}; border:2px solid ${C.ink}; }
        .bf-range::-moz-range-thumb{ width:14px; height:34px; border-radius:3px; background:${C.text}; border:2px solid ${C.ink}; }
        @media (prefers-reduced-motion: no-preference){ .bf-fade{ transition: opacity .25s ease, border-color .25s ease; } }
      `}</style>

      <div className="max-w-5xl mx-auto px-5 py-8 sm:px-8 sm:py-12">

        {/* header */}
        <div className="flex items-baseline justify-between flex-wrap gap-2">
          <h1 style={{ ...mono, letterSpacing: "0.18em" }} className="text-2xl sm:text-3xl font-semibold">БАЛАНС</h1>
          <div style={{ ...mono, color: C.faint }} className="text-xs">игра в будущее · v0</div>
        </div>
        <p style={{ color: C.dim }} className="mt-2 text-sm sm:text-base max-w-2xl">
          Баланс спустя годы. Мир, где обманывать становится <span style={{ color: C.text }}>очень трудно</span> — заметь, не невозможно, и в узком диапазоне. Крути и смотри, что меняется.
        </p>

        {/* servers */}
        <div className="mt-7 flex flex-wrap gap-2">
          {Object.entries(SERVERS).map(([k, s]) => {
            const on = server === k;
            return (
              <button key={k} onClick={() => setServer(k)}
                className="bf-fade px-3 py-2 rounded text-xs sm:text-sm"
                style={{ ...mono, background: on ? C.panel2 : "transparent", color: on ? C.text : C.dim,
                  border: `1px solid ${on ? s.tone : C.line}` }}>
                <span style={{ color: on ? s.tone : C.faint }}>●</span> сервер: {s.label}
              </button>
            );
          })}
        </div>
        <p style={{ color: C.faint, ...mono }} className="mt-2 text-xs">{SERVERS[server].note}</p>

        {/* THE SCALE — signature */}
        <div className="mt-8 rounded-lg p-5 sm:p-6" style={{ background: C.panel, border: `1px solid ${C.line}` }}>
          <div className="flex items-baseline justify-between">
            <span style={{ ...mono, color: C.dim }} className="text-xs uppercase tracking-widest">насколько трудно обмануть</span>
            <span style={{ ...mono, color: z.color }} className="text-sm font-semibold">{z.name.toUpperCase()} · {z.short}</span>
          </div>

          {/* track */}
          <div className="mt-4 relative">
            <div className="h-2 rounded-full" style={{ background: gradient, opacity: 0.85 }} />
            {/* sweet-spot bracket */}
            <div className="absolute -top-1 h-4" style={{ left: "58%", width: "21%", borderLeft: `2px solid ${C.amber}`, borderRight: `2px solid ${C.amber}` }} />
            {/* marker */}
            <div className="absolute -top-2 h-6 w-0.5" style={{ left: `calc(${difficulty}% - 1px)`, background: C.text }} />
            <input className="bf-range absolute -top-4 left-0" type="range" min="0" max="100" value={difficulty}
              onChange={(e) => setDifficulty(+e.target.value)} aria-label="Насколько трудно обмануть" />
          </div>
          <div className="flex justify-between mt-6" style={{ ...mono, color: C.faint }}>
            <span className="text-xs">сегодня</span>
            <span className="text-xs" style={{ color: inSweet ? C.amber : C.faint }}>◆ узкая полоса равновесия</span>
            <span className="text-xs">тотальная прозрачность</span>
          </div>

          {/* year */}
          <div className="mt-6 pt-5" style={{ borderTop: `1px solid ${C.line}` }}>
            <div className="flex items-baseline justify-between">
              <span style={{ ...mono, color: C.dim }} className="text-xs uppercase tracking-widest">спустя лет</span>
              <span style={{ ...mono, color: C.text }} className="text-sm">{year} · мир {settled}</span>
            </div>
            <input className="bf-range mt-2" type="range" min="1" max="60" value={year}
              onChange={(e) => setYear(+e.target.value)} aria-label="Спустя сколько лет" />
          </div>

          {/* zone caption / warnings */}
          <div className="mt-4 text-sm" style={{ color: inSweet ? C.amber : (zone === 3 ? C.red : C.dim) }}>
            {zone === 0 && "Это сегодняшний мир: влияние покупается, побеждает громкость."}
            {zone === 1 && "Переход: честный сигнал появился, но рядом с купленным. Всё шатко."}
            {zone === 2 && "Полоса равновесия. Обман дорог и обычно пойман — но не невозможен, и приватность цела. Ровно сюда целится Баланс."}
            {zone === 3 && "За полосой: обман невозможен ценой тотальной прозрачности. Границы нет — ни у человека, ни у общества. Это уже не Баланс, а надзор."}
          </div>
        </div>

        {/* domains */}
        <div className="mt-8 grid gap-3 sm:grid-cols-2">
          {DOMAINS.map(([k, label]) => (
            <div key={k} className="bf-fade rounded-lg p-4 sm:p-5" style={{ background: C.panel, border: `1px solid ${inSweet ? "#3a3527" : C.line}` }}>
              <div style={{ ...mono, color: z.color }} className="text-xs uppercase tracking-widest">{label}</div>
              <p className="mt-2 text-sm leading-relaxed" style={{ color: C.text }}>{pick(server, k, zone)}</p>
            </div>
          ))}
        </div>

        {/* POWER — the core question */}
        <div className="mt-4 rounded-lg p-5 sm:p-7" style={{ background: C.panel2, border: `1px solid ${SERVERS[server].tone}` }}>
          <div style={{ ...mono, color: SERVERS[server].tone }} className="text-xs uppercase tracking-widest">власть</div>
          <h2 style={{ ...serif }} className="mt-1 text-xl sm:text-2xl">Чьи дети будут этим править?</h2>
          <p className="mt-3 text-sm sm:text-base leading-relaxed" style={{ color: C.text }}>{pickPower(server, zone)}</p>
        </div>

        {/* honest footer */}
        <div className="mt-8 text-xs leading-relaxed" style={{ ...mono, color: C.faint }}>
          <p>Это проекция, не пророчество. <span style={{ color: C.dim }}>У нас нет психоистории</span> — посчитать нельзя, можно только запустить с живыми людьми, которые подстраиваются. Сервера показывают развилки, а не судьбу.</p>
          <p className="mt-2">Узкий диапазон — весь смысл: слишком легко обмануть = сегодня; слишком трудно = тотальная прозрачность и конец приватного. Между ними — тонкая янтарная полоса.</p>
        </div>
      </div>
    </div>
  );
}
