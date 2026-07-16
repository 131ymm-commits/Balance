import React, { useState, useRef, useEffect } from "react";

/*  БАЛАНС — ВСЕЛЕННАЯ ОТВЕЧАЕТ
    Игрок вводит Баланс (бесплатную честную сеть — «правду») в мир своими ходами.
    Claude отыгрывает Вселенную: генерирует, что ТОЧНО случится — честно, без болельщицкого.
    Инкумбенты сопротивляются, люди адаптируются, узкий диапазон держит.
    Движок: Anthropic API прямо в артефакте (Claude в Claude).  */

const C = {
  ink: "#0e1114", panel: "#161b21", panel2: "#1b2129", line: "#2b333d",
  text: "#dbe1e8", dim: "#8b96a3", faint: "#5c6673",
  teal: "#5ad1c3", amber: "#e9a83e", red: "#e5564b", green: "#7bbf6a",
};
const mono = { fontFamily: "ui-monospace,'SF Mono','JetBrains Mono',Menlo,monospace" };
const serif = { fontFamily: "'Iowan Old Style',Georgia,'Times New Roman',serif" };

const SYSTEM = `Ты — ВСЕЛЕННАЯ в стратегической игре о введении «Баланса» в человеческое общество.

БАЛАНС — это бесплатная, открытая, НЕКУПЛЯЕМАЯ сеть-ИИ: общий рекомендатель и рейтинг, судящий по реализованному исходу (что человек реально оставил, что выбросил, доволен ли через год), принадлежащий пользователям. Его суть: он делает обман в рынке и публичной жизни ТРУДНЫМ (но никогда невозможным), потому что правду становится дёшево проверить. Агент бесплатен и локален, веса у пользователя. В базе Баланс всегда функционален и бесплатен. Игрок — агент, распространяющий Баланс; он верит в него, потому что это подлинно хорошо: бесплатный ИИ, общая сеть, проверяемая правда. Девиз игрока: «мы продавцы правды».

ТВОЯ РОЛЬ: получив состояние мира и ход игрока, сгенерировать, что БЫ РЕАЛЬНО случилось — честно. Ты НЕ болельщик. Настоящие инкумбенты сопротивляются (рекламные платформы на триллионы, монополии, государства, дефолты и lock-in держат протухшее десятилетиями). Адопция неровная и медленная. Люди и противники АДАПТИРУЮТСЯ и находят эксплойты (арбитраж на раскрытой рекламе, поддельная доверие-квалификация, коалиции против аудита). Есть непредвиденные последствия.

УЗКИЙ ДИАПАЗОН — держи его свято: если обман становится не просто трудным, а почти невозможным, общество кренится в тотальную прозрачность (нет приватности, нет права становиться) — и это вызывает откат и тоталитарный риск. Оптимум — «очень трудно, но не невозможно». Если единый индекс монополизируется — Баланс ЗАХВАЧЕН и становится инструментом новой элиты (тёмный исход). Долгий след честности лагает годами: расплата и правда приходят с опозданием.

Будь конкретным, заземлённым и неожиданным: последствия второго порядка, а не лозунги. Никакого хэппи-энда по умолчанию.

Отвечай ТОЛЬКО объектом JSON, без прозы, без markdown-ограждений:
{
 "narration": "2–4 предложения голосом мира: что реально случилось от хода. Конкретно, честно.",
 "adoption": <целое 0-100 новое значение>,
 "deception_difficulty": <целое 0-100 новое: насколько трудно обмануть>,
 "trust": <целое 0-100 новое>,
 "resistance": <целое 0-100 новое: сопротивление инкумбентов/власти>,
 "power_note": "одно предложение: кто прямо сейчас набирает или теряет власть",
 "flag": "none" | "totalitarian_tip" | "captured" | "stalled" | "breakthrough",
 "choices": ["короткий ход 1","короткий ход 2","короткий ход 3"]
}
Всё по-русски. Значения меняй правдоподобно относительно прошлых, не скачками, кроме переломов.`;

const START = { adoption: 3, deception_difficulty: 12, trust: 20, resistance: 18 };
const START_CHOICES = [
  "Раздать бесплатный агент небольшому доверие-сообществу",
  "Открыть исходники сети целиком",
  "Нацелить индекс на один откровенно нечестный рынок",
];

const FLAG = {
  none: null,
  breakthrough: { c: C.green, t: "Прорыв — Баланс закрепился" },
  stalled: { c: C.dim, t: "Застой — дистрибуция инкумбента держит" },
  totalitarian_tip: { c: C.red, t: "Крен в тотальную прозрачность — откат и надзор" },
  captured: { c: C.red, t: "Индекс захвачен — Баланс стал инструментом элиты" },
};

function Meter({ label, val, color, band }) {
  return (
    <div>
      <div className="flex justify-between items-baseline">
        <span style={{ ...mono, color: C.dim }} className="text-xs uppercase tracking-wider">{label}</span>
        <span style={{ ...mono, color }} className="text-xs">{val}</span>
      </div>
      <div className="mt-1 h-1.5 rounded-full relative" style={{ background: C.line }}>
        {band && <div className="absolute inset-y-0 rounded-full" style={{ left: "56%", width: "24%", background: C.amber, opacity: 0.25 }} />}
        <div className="h-full rounded-full relative" style={{ width: `${val}%`, background: color, transition: "width .5s ease" }} />
        {band && <div className="absolute -top-1 h-3.5 w-px" style={{ left: `${val}%`, background: C.text }} />}
      </div>
    </div>
  );
}

export default function BalanceUniverse() {
  const [screen, setScreen] = useState("intro");
  const [world, setWorld] = useState(START);
  const [log, setLog] = useState([]);
  const [choices, setChoices] = useState(START_CHOICES);
  const [powerNote, setPowerNote] = useState("");
  const [flag, setFlag] = useState("none");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [input, setInput] = useState("");
  const [turn, setTurn] = useState(0);
  const logRef = useRef(null);

  useEffect(() => { if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight; }, [log, loading]);

  const clamp = (n) => Math.max(0, Math.min(100, Math.round(Number(n))));

  function parseUniverse(raw) {
    let t = String(raw).trim().replace(/^```json\s*/i, "").replace(/^```\s*/i, "").replace(/```\s*$/,"").trim();
    const a = t.indexOf("{"), b = t.lastIndexOf("}");
    if (a >= 0 && b > a) t = t.slice(a, b + 1);
    return JSON.parse(t);
  }

  async function act(action) {
    if (loading || !action.trim()) return;
    setError(""); setInput("");
    setLog((L) => [...L, { who: "player", text: action }]);
    setLoading(true);
    const state = { ...world, turn };
    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-6",
          max_tokens: 1000,
          system: SYSTEM,
          messages: [{ role: "user", content:
            `Состояние мира сейчас: ${JSON.stringify(state)}.\nХод игрока: "${action}".\nСгенерируй честное последствие и обновлённое состояние (JSON).` }],
        }),
      });
      const data = await res.json();
      const textOut = (data.content || []).filter((x) => x.type === "text").map((x) => x.text).join("\n");
      let u;
      try { u = parseUniverse(textOut); }
      catch { u = { narration: textOut || "Вселенная промолчала — попробуй иначе.", ...world, power_note: powerNote, flag: "none", choices }; }
      setWorld({
        adoption: clamp(u.adoption ?? world.adoption),
        deception_difficulty: clamp(u.deception_difficulty ?? world.deception_difficulty),
        trust: clamp(u.trust ?? world.trust),
        resistance: clamp(u.resistance ?? world.resistance),
      });
      setPowerNote(u.power_note || powerNote);
      setFlag(u.flag && FLAG[u.flag] !== undefined ? u.flag : "none");
      setChoices(Array.isArray(u.choices) && u.choices.length ? u.choices.slice(0, 3) : choices);
      setLog((L) => [...L, { who: "universe", text: u.narration || "…" }]);
      setTurn((t) => t + 1);
    } catch (e) {
      setError("Связь со Вселенной прервалась. Проверь соединение и попробуй ещё раз.");
      setLog((L) => L.slice(0, -1)); setInput(action);
    } finally { setLoading(false); }
  }

  function reset() {
    setWorld(START); setLog([]); setChoices(START_CHOICES); setPowerNote("");
    setFlag("none"); setError(""); setInput(""); setTurn(0); setScreen("intro");
  }

  if (screen === "intro") {
    return (
      <div style={{ background: C.ink, color: C.text, minHeight: "100%" }} className="w-full">
        <div className="max-w-2xl mx-auto px-5 py-14 sm:px-8">
          <div style={{ ...mono, letterSpacing: ".18em", color: C.faint }} className="text-xs">игра · вселенная отвечает</div>
          <h1 style={{ ...mono, letterSpacing: ".14em" }} className="mt-3 text-3xl font-semibold">БАЛАНС</h1>
          <p style={{ ...serif }} className="mt-6 text-xl leading-relaxed">Ты вводишь <span style={{ color: C.teal }}>правду</span> в мир.</p>
          <div style={{ color: C.dim }} className="mt-4 text-sm sm:text-base leading-relaxed space-y-3">
            <p>Твой товар — <span style={{ color: C.text }}>бесплатная честная сеть</span>: некупляемый ИИ, судящий по реальному исходу, принадлежащий людям. В базе — всегда работает даром. Мы продавцы правды.</p>
            <p>Ты делаешь ход — распространяешь Баланс. <span style={{ color: C.text }}>Я отыгрываю Вселенную</span> и говорю, что <span style={{ color: C.amber }}>на самом деле случится</span>. Я не болею за тебя: инкумбенты сопротивляются, люди адаптируются, и обман должен стать очень трудным — но не невозможным. Перегнёшь в прозрачность — получишь надзор и откат.</p>
          </div>
          <button onClick={() => setScreen("play")} className="mt-8 px-5 py-3 rounded text-sm"
            style={{ ...mono, background: C.panel2, color: C.text, border: `1px solid ${C.teal}` }}>
            Сделать первый ход →
          </button>
          <p style={{ ...mono, color: C.faint }} className="mt-6 text-xs">Это проекция, не пророчество. У нас нет психоистории — Вселенную отыгрывает живая модель, и она может тебя удивить.</p>
        </div>
      </div>
    );
  }

  const f = FLAG[flag];
  return (
    <div style={{ background: C.ink, color: C.text, minHeight: "100%" }} className="w-full">
      <div className="max-w-3xl mx-auto px-4 py-6 sm:px-8 sm:py-10">
        <div className="flex items-baseline justify-between">
          <h1 style={{ ...mono, letterSpacing: ".14em" }} className="text-xl font-semibold">БАЛАНС</h1>
          <button onClick={reset} style={{ ...mono, color: C.faint }} className="text-xs underline">начать заново</button>
        </div>

        {/* world meters */}
        <div className="mt-5 rounded-lg p-4 sm:p-5 grid gap-3 sm:grid-cols-2" style={{ background: C.panel, border: `1px solid ${C.line}` }}>
          <Meter label="Обман труден" val={world.deception_difficulty} color={world.deception_difficulty > 80 ? C.red : (world.deception_difficulty >= 56 ? C.amber : C.teal)} band />
          <Meter label="Адопция" val={world.adoption} color={C.teal} />
          <Meter label="Доверие" val={world.trust} color={C.green} />
          <Meter label="Сопротивление" val={world.resistance} color={C.red} />
        </div>
        {powerNote && (
          <div className="mt-3 rounded-lg px-4 py-3" style={{ background: C.panel2, border: `1px solid ${C.line}` }}>
            <span style={{ ...mono, color: C.faint }} className="text-xs uppercase tracking-wider">власть · </span>
            <span className="text-sm" style={{ color: C.text }}>{powerNote}</span>
          </div>
        )}
        {f && (
          <div className="mt-3 rounded-lg px-4 py-2 text-sm" style={{ ...mono, background: C.panel, border: `1px solid ${f.c}`, color: f.c }}>◆ {f.t}</div>
        )}

        {/* log */}
        <div ref={logRef} className="mt-4 rounded-lg p-4 sm:p-5 overflow-y-auto" style={{ background: C.panel, border: `1px solid ${C.line}`, maxHeight: "42vh" }}>
          {log.length === 0 && <p style={{ color: C.faint }} className="text-sm">Мир как он есть: влияние покупается, побеждает громкость. Сделай первый ход — введи Баланс.</p>}
          {log.map((e, i) => (
            <div key={i} className={i ? "mt-4" : ""}>
              {e.who === "player" ? (
                <p style={{ ...mono, color: C.teal }} className="text-sm"><span style={{ color: C.faint }}>ты ▸ </span>{e.text}</p>
              ) : (
                <p style={{ ...serif, color: C.text }} className="text-[15px] leading-relaxed">{e.text}</p>
              )}
            </div>
          ))}
          {loading && <p style={{ ...mono, color: C.amber }} className="mt-4 text-sm">Вселенная считает последствия…</p>}
        </div>

        {error && <p style={{ color: C.red }} className="mt-3 text-sm">{error}</p>}

        {/* choices */}
        {!loading && (
          <div className="mt-4 flex flex-col gap-2">
            {choices.map((ch, i) => (
              <button key={i} onClick={() => act(ch)} className="text-left px-4 py-3 rounded text-sm"
                style={{ background: C.panel, color: C.text, border: `1px solid ${C.line}` }}>
                <span style={{ color: C.teal }}>▸ </span>{ch}
              </button>
            ))}
          </div>
        )}

        {/* free input */}
        <div className="mt-3 flex gap-2">
          <input value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") act(input); }}
            placeholder="…или впиши свой ход" disabled={loading}
            className="flex-1 px-3 py-3 rounded text-sm" style={{ ...mono, background: C.ink, color: C.text, border: `1px solid ${C.line}` }} />
          <button onClick={() => act(input)} disabled={loading || !input.trim()}
            className="px-4 py-3 rounded text-sm" style={{ ...mono, background: C.panel2, color: loading || !input.trim() ? C.faint : C.text, border: `1px solid ${C.teal}` }}>
            ход
          </button>
        </div>

        <p style={{ ...mono, color: C.faint }} className="mt-5 text-xs">Вселенную отыгрывает Claude. Проекция, не пророчество: сервер честен ровно настолько, насколько допускает твой проигрыш — застой, захват или крен в надзор.</p>
      </div>
    </div>
  );
}
