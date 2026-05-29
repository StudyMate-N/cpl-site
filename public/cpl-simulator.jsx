/* CPL — Case Simulator (interactive, scored clinical reasoning) */
const { useState, useMemo } = React;

const CASE = {
  name: "Bebe Babbitt",
  meta: "23F · recurrent severe headaches",
  initials: "BB",
  stages: [
    {
      key: "History",
      label: "Stage I",
      eyebrow: "Stage I · History",
      title: "Which questions are worth asking?",
      sub: "Select the history questions that earn points. iHuman weights pivotal differentiators highest — padding adds nothing.",
      options: [
        { id:"h1", text:"Any visual changes or aura before the pain?", pts:4, type:"key", note:"Pivotal — aura screening defines the migraine subtype." },
        { id:"h2", text:"Has it ever hit like a thunderclap — worst headache of your life, instantly?", pts:5, type:"key", note:"Must-not-miss — rules out subarachnoid hemorrhage." },
        { id:"h3", text:"Any sensitivity to light or sound during attacks?", pts:3, type:"key", note:"Core migraine criteria — document as photophobia/phonophobia." },
        { id:"h4", text:"How often, and have they changed over time?", pts:2, type:"minor", note:"Supports chronicity — modest points." },
        { id:"h5", text:"How would you rate the pain, 1 to 10?", pts:1, type:"minor", note:"Expected, but low-yield on its own." },
        { id:"h6", text:"Have you considered it's probably just stress?", pts:-3, type:"trap", note:"Leading and dismissive — costs communication points." }
      ]
    },
    {
      key: "Exam",
      label: "Stage II",
      eyebrow: "Stage II · Physical Exam",
      title: "What should you examine?",
      sub: "Choose the exam items that score. One option is a trap.",
      options: [
        { id:"e1", text:"Focused neurologic exam (cranial nerves, focal deficits)", pts:5, type:"key", note:"Essential — excludes focal pathology." },
        { id:"e2", text:"Fundoscopic exam for papilledema", pts:4, type:"key", note:"Screens for raised intracranial pressure." },
        { id:"e3", text:"Neck stiffness & meningeal signs", pts:3, type:"key", note:"Helps rule out meningitis / SAH." },
        { id:"e4", text:"Vital signs including blood pressure", pts:2, type:"minor", note:"Reasonable baseline." },
        { id:"e5", text:"Cardiac auscultation", pts:1, type:"minor", note:"Low yield here, but harmless." },
        { id:"e6", text:"Order a CT head right now", pts:-5, type:"trap", note:"Not an exam — and imaging here is a harmful-flag. This is a clinical diagnosis." }
      ]
    },
    {
      key: "DDx",
      label: "Stage III",
      eyebrow: "Stage III · Differential",
      title: "Build your differential",
      sub: "Pick the leading diagnosis and the must-not-miss conditions you'll document ruling out.",
      options: [
        { id:"d1", text:"Leading dx: Migraine with aura", pts:6, type:"key", note:"Correct — aura + classic features + normal exam." },
        { id:"d2", text:"Must-not-miss: Subarachnoid hemorrhage", pts:4, type:"key", note:"Always document the rule-out for thunderclap." },
        { id:"d3", text:"Must-not-miss: Intracranial mass", pts:3, type:"key", note:"Progressive headache warrants this rule-out." },
        { id:"d4", text:"Must-not-miss: Meningitis", pts:3, type:"key", note:"Reasonable to address given severity." },
        { id:"d5", text:"Leading dx: Tension-type headache", pts:1, type:"minor", note:"Plausible distractor — doesn't fit the aura." },
        { id:"d6", text:"Must-not-miss: Migraine", pts:-2, type:"trap", note:"That's the diagnosis, not a must-not-miss." }
      ]
    },
    {
      key: "Plan",
      label: "Stage IV",
      eyebrow: "Stage IV · Management",
      title: "Choose your management plan",
      sub: "Two options here are harmful-flag traps that zero out your plan score.",
      options: [
        { id:"p1", text:"Abortive triptan + NSAID for attacks", pts:5, type:"key", note:"First-line abortive therapy." },
        { id:"p2", text:"Trigger diary + lifestyle counseling", pts:3, type:"key", note:"Patient education scores with faculty." },
        { id:"p3", text:"Discuss prophylaxis given rising frequency", pts:3, type:"key", note:"Appropriate for frequent migraines." },
        { id:"p4", text:"Schedule follow-up to reassess", pts:2, type:"minor", note:"Good continuity of care." },
        { id:"p5", text:"Order MRI for reassurance", pts:-5, type:"trap", note:"Harmful-flag — imaging not indicated; Tests score drops to 0%." },
        { id:"p6", text:"Prescribe opioids for the pain", pts:-5, type:"trap", note:"Opioid-first is a classic harmful-flag trap in migraine." }
      ]
    }
  ]
};

function maxPositive(stage){ return stage.options.filter(o=>o.pts>0).reduce((a,o)=>a+o.pts,0); }
const TOTAL_MAX = CASE.stages.reduce((a,s)=>a+maxPositive(s),0);

function Simulator(){
  const [stageIdx, setStageIdx] = useState(0);
  const [selected, setSelected] = useState({});      // id -> true
  const [revealed, setRevealed] = useState(false);
  const [stageScores, setStageScores] = useState([]); // per-stage earned
  const [done, setDone] = useState(false);

  const stage = CASE.stages[stageIdx];
  const total = stageScores.reduce((a,b)=>a+b,0);

  function toggle(id){
    if(revealed) return;
    setSelected(s => ({...s, [id]: !s[id]}));
  }

  const stageEarned = useMemo(()=>{
    return stage.options.reduce((a,o)=> a + (selected[o.id] ? o.pts : 0), 0);
  }, [selected, stage]);

  function submitStage(){
    setRevealed(true);
  }
  function nextStage(){
    const earned = Math.max(0, stageEarned);
    const ns = [...stageScores]; ns[stageIdx] = earned; setStageScores(ns);
    if(stageIdx < CASE.stages.length-1){
      setStageIdx(stageIdx+1); setSelected({}); setRevealed(false);
    } else {
      setDone(true);
    }
  }
  function restart(){
    setStageIdx(0); setSelected({}); setRevealed(false); setStageScores([]); setDone(false);
  }

  const anySelected = Object.values(selected).some(Boolean);

  if(done){
    const finalTotal = stageScores.reduce((a,b)=>a+b,0);
    const pct = Math.round((finalTotal/TOTAL_MAX)*100);
    const grade = pct>=85 ? "Excellent" : pct>=70 ? "Strong" : pct>=50 ? "Getting there" : "Keep practicing";
    const C = 2*Math.PI*64;
    return (
      <div className="sim-shell">
        <div className="sim-topbar">
          <div className="sim-patient"><div className="sim-avatar">{CASE.initials}</div><div><div className="pn">{CASE.name}</div><div className="pc">{CASE.meta}</div></div></div>
          <div className="sim-scorebox"><div className="sl">Final</div><div className="sv">{finalTotal}/{TOTAL_MAX}</div></div>
        </div>
        <div className="sim-results">
          <div className="sim-score-ring">
            <svg width="150" height="150">
              <circle cx="75" cy="75" r="64" fill="none" stroke="#E4DCC8" strokeWidth="11"/>
              <circle cx="75" cy="75" r="64" fill="none" stroke="#14B896" strokeWidth="11" strokeLinecap="round"
                strokeDasharray={C} strokeDashoffset={C*(1-pct/100)}/>
            </svg>
            <div className="rv"><b>{pct}%</b><span>iHuman score</span></div>
          </div>
          <div className="sim-grade">{grade}</div>
          <h3>You scored {finalTotal} of {TOTAL_MAX} points</h3>
          <p>This is the reasoning iHuman rewards — pivotal questions, must-not-miss rule-outs, and avoiding harmful-flag traps. The full guide maps every scored item for the real case.</p>
          <div className="sim-breakdown">
            {CASE.stages.map((s,i)=>(
              <div className="sbd" key={s.key}><b>{stageScores[i]}</b><span>{s.key}</span></div>
            ))}
          </div>
          <div className="sim-results-ctas">
            <button className="btn btn-primary" onClick={restart}>Practice again ↻</button>
            <a className="btn btn-lime" data-order="Bebe Babbitt — Migraine with Aura" data-price="150">Get the full guide — $150</a>
            <a className="btn btn-ghost" href="/free-resources/">Free cheat sheets</a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="sim-shell">
      <div className="sim-topbar">
        <div className="sim-patient"><div className="sim-avatar">{CASE.initials}</div><div><div className="pn">{CASE.name}</div><div className="pc">{CASE.meta}</div></div></div>
        <div className="sim-scorebox"><div className="sl">Running score</div><div className="sv">{total}{revealed ? `+${Math.max(0,stageEarned)}` : ""}</div></div>
      </div>
      <div className="sim-stepper">
        {CASE.stages.map((s,i)=>(
          <div key={s.key} className={"sim-step " + (i===stageIdx?"active":"") + (i<stageIdx?" done":"")}>
            <span className="si">{s.label}</span>{s.key}
          </div>
        ))}
      </div>
      <div className="sim-stage">
        <div className="sim-prompt">
          <span className="pe">{stage.eyebrow}</span>
          <h3>{stage.title}</h3>
          <p>{stage.sub}</p>
        </div>
        <div className="sim-opts">
          {stage.options.map(o=>{
            const isSel = !!selected[o.id];
            let cls = "sim-opt";
            if(!revealed && isSel) cls += " sel";
            if(revealed){
              cls += " revealed";
              if(isSel){ cls += o.type==="trap" ? " r-trap" : o.pts>0 ? (o.type==="key"?" r-key":" r-minor") : " r-minor"; }
              else if(o.type==="key"){ cls += " r-missed"; }
            }
            const ptcls = o.pts>0 ? "plus" : o.pts<0 ? "minus" : "zero";
            return (
              <button type="button" key={o.id} className={cls} onClick={()=>toggle(o.id)}>
                <span className="sim-check">{isSel?"✓":""}</span>
                <span className="so-text">{o.text}
                  {revealed && (isSel || o.type==="key") && <span className="so-note">{!isSel && o.type==="key" ? <b>Missed — </b> : null}{o.note}</span>}
                </span>
                {revealed && <span className={"so-pts "+ptcls}>{o.pts>0?"+":""}{o.pts}{o.type==="key"&&!isSel?" missed":" pts"}</span>}
              </button>
            );
          })}
        </div>

        {revealed && (
          <div className="sim-feedback">
            You earned <span className="sf-delta">{Math.max(0,stageEarned)} / {maxPositive(stage)}</span> on this stage. {stageEarned < maxPositive(stage) ? "The dashed items are points left on the table — that's exactly what the full guide pins down." : "Clean sweep — that's clinician-level reasoning."}
          </div>
        )}

        <div className="sim-actions">
          <span className="sim-hint">{revealed ? "Review the scoring, then continue." : "Select every option you'd choose, then submit."}</span>
          {!revealed
            ? <button className="btn btn-primary" disabled={!anySelected} onClick={submitStage}>Submit stage →</button>
            : <button className="btn btn-primary" onClick={nextStage}>{stageIdx < CASE.stages.length-1 ? "Next stage →" : "See results →"}</button>}
        </div>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('sim-root')).render(<Simulator />);
