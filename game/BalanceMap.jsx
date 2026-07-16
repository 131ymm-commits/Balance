import React, { useState } from "react";

/*  БАЛАНС — КАРТА ВЛАСТИ (политический слой игры)
    Каждый игрок географичен и правит территорией. Власть ДРОБИТСЯ по числу игроков:
    один правит всей страной; с приходом новых — земли, районы, общины.
    Первый — в Нижней Саксонии (Дипхольц). Всевластны в рамках демократии.
    Это антимонополия и принцип 8 Остром (вложенные общины) — географически:
    власть не может сконцентрироваться, новые игроки её дробят.
    Схема: реальный деплой лёг бы поверх Google Maps/Leaflet с настоящими границами. */

const C = {
  ink: "#0e1114", panel: "#161b21", panel2: "#1b2129", line: "#2b333d",
  text: "#dbe1e8", dim: "#8b96a3", faint: "#5c6673",
  teal: "#5ad1c3", amber: "#e9a83e", red: "#e5564b", green: "#7bbf6a",
};
const mono = { fontFamily: "ui-monospace,'SF Mono','JetBrains Mono',Menlo,monospace" };
const serif = { fontFamily: "'Iowan Old Style',Georgia,'Times New Roman',serif" };

// tiers of territory, home lineage first (Дипхольц, Нижняя Саксония, Германия)
const TIERS = [
  { max: 1, tier: "вся страна", home: "Германия",
    names: ["Германия"] },
  { max: 16, tier: "земли", home: "Нижняя Саксония",
    names: ["Нижняя Саксония", "Бавария", "Сев. Рейн-Вестфалия", "Баден-Вюртемберг", "Гессен", "Саксония", "Рейнланд-Пфальц", "Берлин", "Шлезвиг-Гольштейн", "Бранденбург", "Тюрингия", "Саксония-Анхальт", "Гамбург", "Мекленбург", "Саар", "Бремен"] },
  { max: 60, tier: "районы", home: "Дипхольц",
    names: ["Дипхольц", "Ганновер", "Оснабрюк", "Ольденбург", "Целле", "Люнебург", "Гёттинген", "Хильдесхайм", "Штаде", "Ферден", "Ротенбург", "Нинбург", "Куксхафен", "Гослар", "Аурих", "Эмсланд", "Лер", "Вольфсбург", "Гифхорн", "Пайне"] },
  { max: 999, tier: "общины", home: "Дипхольц (город)",
    names: ["Дипхольц (город)", "Штурр", "Вагенфельд", "Барнсторф", "Твистринген", "Лемфёрде", "Реден", "Зульинген", "Бассум", "Зюке"] },
];
function tierFor(n) { return TIERS.find((t) => n <= t.max) || TIERS[TIERS.length - 1]; }

export default function BalanceMap() {
  const [players, setPlayers] = useState(2); // сейчас двое решают за всех
  const t = tierFor(players);
  const share = (100 / players);
  const cols = Math.ceil(Math.sqrt(players));
  const rows = Math.ceil(players / cols);
  const showNames = players <= 36;

  const cells = Array.from({ length: players }, (_, i) => {
    const home = i === 0;
    const name = home ? t.home : (t.names[i] || `Община ${i + 1}`);
    return { i, home, name, labeled: i < t.names.length || home };
  });

  const set = (v) => setPlayers(Math.max(1, Math.min(144, v)));

  return (
    <div style={{ background: C.ink, color: C.text, minHeight: "100%" }} className="w-full">
      <div className="max-w-3xl mx-auto px-4 py-7 sm:px-8 sm:py-10">
        <div className="flex items-baseline justify-between flex-wrap gap-1">
          <h1 style={{ ...mono, letterSpacing: ".14em" }} className="text-xl font-semibold">БАЛАНС · КАРТА ВЛАСТИ</h1>
          <span style={{ ...mono, color: C.faint }} className="text-xs">политический слой</span>
        </div>
        <p style={{ color: C.dim }} className="mt-2 text-sm max-w-2xl">
          Каждый игрок правит территорией. Власть <span style={{ color: C.text }}>дробится по числу игроков</span>: один — вся страна; с приходом новых — земли, районы, общины. Всевластны, но в рамках демократии.
        </p>

        {/* readouts */}
        <div className="mt-6 grid grid-cols-3 gap-3">
          <div className="rounded-lg p-3" style={{ background: C.panel, border: `1px solid ${C.line}` }}>
            <div style={{ ...mono, color: C.faint }} className="text-xs uppercase tracking-wider">игроков</div>
            <div style={{ ...mono, color: C.teal }} className="text-2xl mt-1">{players}</div>
          </div>
          <div className="rounded-lg p-3" style={{ background: C.panel, border: `1px solid ${C.line}` }}>
            <div style={{ ...mono, color: C.faint }} className="text-xs uppercase tracking-wider">власти у каждого</div>
            <div style={{ ...mono, color: C.amber }} className="text-2xl mt-1">{share < 1 ? share.toFixed(1) : Math.round(share)}%</div>
          </div>
          <div className="rounded-lg p-3" style={{ background: C.panel, border: `1px solid ${C.line}` }}>
            <div style={{ ...mono, color: C.faint }} className="text-xs uppercase tracking-wider">масштаб</div>
            <div style={{ ...mono, color: C.text }} className="text-base mt-2">{t.tier}</div>
          </div>
        </div>

        {/* control */}
        <div className="mt-4 flex items-center gap-3">
          <button onClick={() => set(players - 1)} className="w-10 h-10 rounded text-lg" style={{ ...mono, background: C.panel2, color: C.text, border: `1px solid ${C.line}` }}>−</button>
          <input type="range" min="1" max="144" value={players} onChange={(e) => set(+e.target.value)}
            className="flex-1" style={{ accentColor: C.teal }} aria-label="Число игроков" />
          <button onClick={() => set(players + 1)} className="w-10 h-10 rounded text-lg" style={{ ...mono, background: C.panel2, color: C.text, border: `1px solid ${C.line}` }}>+</button>
        </div>

        {/* map */}
        <div className="mt-5 rounded-lg p-3 sm:p-4" style={{ background: C.panel, border: `2px solid ${C.line}` }}>
          <div className="grid gap-0.5" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)`, aspectRatio: `${cols} / ${rows}` }}>
            {cells.map((c) => (
              <div key={c.i} className="flex items-center justify-center text-center overflow-hidden rounded-sm"
                style={{
                  background: c.home ? "rgba(233,168,62,0.16)" : "rgba(90,209,195,0.06)",
                  border: `1px solid ${c.home ? C.amber : C.line}`,
                  minHeight: 0,
                }}>
                {showNames && (
                  <span style={{ ...mono, color: c.home ? C.amber : (c.labeled ? C.dim : C.faint), fontSize: cols > 5 ? "8px" : "10px", lineHeight: 1.1, padding: "2px" }}>
                    {c.name}
                  </span>
                )}
                {!showNames && c.home && <span style={{ color: C.amber }}>●</span>}
              </div>
            ))}
          </div>
          <div className="flex items-center justify-between mt-3">
            <span style={{ ...mono, color: C.amber }} className="text-xs">● Нижняя Саксония / Дипхольц — первый игрок, твой дом</span>
            <span style={{ ...mono, color: C.faint }} className="text-xs">схема · деплой = Google/Leaflet</span>
          </div>
        </div>

        {/* state note */}
        <div className="mt-5 rounded-lg p-4 sm:p-5" style={{ background: C.panel2, border: `1px solid ${players === 2 ? C.amber : C.line}` }}>
          {players === 1 && <p style={{ ...serif }} className="text-lg">Один игрок — и он правит всей страной. Максимальная концентрация власти.</p>}
          {players === 2 && <p style={{ ...serif }} className="text-lg">Их двое — и они решают за всех. Власть поделена надвое, каждый всевластен в своей половине.</p>}
          {players > 2 && <p style={{ ...serif }} className="text-lg">Игроков {players}. Власть рассыпалась на {players} рук — {t.tier}. Ни у кого нет большинства над другими.</p>}
          <p style={{ color: C.dim }} className="mt-2 text-sm">
            Это <span style={{ color: C.text }}>антимонополия</span> географически: власть <span style={{ color: C.text }}>не может сконцентрироваться</span>, потому что каждый новый игрок её дробит. И принцип 8 Остром: вложенные общины, ни одного центра. Всевластие — только внутри своей территории и только в рамках демократических правил сети.
          </p>
        </div>

        <p style={{ ...mono, color: C.faint }} className="mt-6 text-xs leading-relaxed">
          Политический слой соединяется с игрой: по мере роста адопции и числа игроков карта дробится, а Вселенная отыгрывает, что это делает с обществом. Творцы держат территорию — я держу следствия.
        </p>
      </div>
    </div>
  );
}
