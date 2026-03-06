import { useState, useEffect, useRef } from "react";

const COLORS = {
    bg: "#0A0E17",
    surface: "#111827",
    surfaceHover: "#1A2234",
    card: "#161F31",
    cardHover: "#1C2740",
    border: "#1E293B",
    borderLight: "#2A3A52",
    accent: "#6366F1",
    accentHover: "#818CF8",
    accentSoft: "rgba(99,102,241,0.12)",
    accentGlow: "rgba(99,102,241,0.25)",
    green: "#10B981",
    greenSoft: "rgba(16,185,129,0.12)",
    greenBorder: "rgba(16,185,129,0.3)",
    amber: "#F59E0B",
    amberSoft: "rgba(245,158,11,0.12)",
    amberBorder: "rgba(245,158,11,0.3)",
    red: "#EF4444",
    redSoft: "rgba(239,68,68,0.12)",
    redBorder: "rgba(239,68,68,0.3)",
    cyan: "#06B6D4",
    cyanSoft: "rgba(6,182,212,0.12)",
    purple: "#A855F7",
    purpleSoft: "rgba(168,85,247,0.12)",
    textPrimary: "#F1F5F9",
    textSecondary: "#94A3B8",
    textMuted: "#64748B",
};

const font = `'DM Sans', -apple-system, sans-serif`;
const monoFont = `'JetBrains Mono', 'Fira Code', monospace`;

// Shared Components
const Badge = ({ children, color = COLORS.accent, bg = COLORS.accentSoft, border }) => (
    <span style={{
        display: "inline-flex", alignItems: "center", gap: 4,
        padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 600,
        fontFamily: font, color, background: bg, letterSpacing: 0.3,
        border: border ? `1px solid ${border}` : "none",
    }}>{children}</span>
);

const StatCard = ({ label, value, color = COLORS.accent, icon }) => (
    <div style={{
        flex: 1, padding: "16px 18px", borderRadius: 14, background: COLORS.card,
        border: `1px solid ${COLORS.border}`, position: "relative", overflow: "hidden",
    }}>
        <div style={{
            position: "absolute", top: -10, right: -10, width: 60, height: 60,
            borderRadius: "50%", background: color, opacity: 0.06,
        }} />
        <div style={{ fontSize: 11, color: COLORS.textMuted, fontFamily: font, fontWeight: 500, textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>{label}</div>
        <div style={{ fontSize: 28, fontWeight: 700, color, fontFamily: font, lineHeight: 1 }}>{value}</div>
    </div>
);

const Button = ({ children, primary, danger, small, onClick, disabled, style: s = {} }) => (
    <button onClick={onClick} disabled={disabled} style={{
        padding: small ? "6px 14px" : "10px 20px",
        borderRadius: 10, border: "none", cursor: disabled ? "not-allowed" : "pointer",
        fontFamily: font, fontWeight: 600, fontSize: small ? 12 : 13,
        background: danger ? COLORS.redSoft : primary ? COLORS.accent : COLORS.surfaceHover,
        color: danger ? COLORS.red : primary ? "#fff" : COLORS.textSecondary,
        transition: "all 0.2s", opacity: disabled ? 0.5 : 1, letterSpacing: 0.2,
        ...s,
    }}>{children}</button>
);

const Input = ({ label, placeholder, large, mono, value, onChange }) => (
    <div style={{ marginBottom: 14 }}>
        {label && <div style={{ fontSize: 12, fontWeight: 600, color: COLORS.textSecondary, fontFamily: font, marginBottom: 6, letterSpacing: 0.3 }}>{label}</div>}
        {large ? (
            <textarea placeholder={placeholder} value={value} onChange={onChange} rows={3} style={{
                width: "100%", padding: "12px 14px", borderRadius: 10, border: `1px solid ${COLORS.border}`,
                background: COLORS.surface, color: COLORS.textPrimary, fontFamily: mono ? monoFont : font,
                fontSize: 13, resize: "vertical", outline: "none", boxSizing: "border-box",
            }} />
        ) : (
            <input placeholder={placeholder} value={value} onChange={onChange} style={{
                width: "100%", padding: "11px 14px", borderRadius: 10, border: `1px solid ${COLORS.border}`,
                background: COLORS.surface, color: COLORS.textPrimary, fontFamily: font,
                fontSize: 13, outline: "none", boxSizing: "border-box",
            }} />
        )}
    </div>
);

const Select = ({ label, options, value, onChange }) => (
    <div style={{ marginBottom: 14, flex: 1 }}>
        {label && <div style={{ fontSize: 12, fontWeight: 600, color: COLORS.textSecondary, fontFamily: font, marginBottom: 6, letterSpacing: 0.3 }}>{label}</div>}
        <select value={value} onChange={onChange} style={{
            width: "100%", padding: "11px 14px", borderRadius: 10, border: `1px solid ${COLORS.border}`,
            background: COLORS.surface, color: COLORS.textPrimary, fontFamily: font, fontSize: 13, outline: "none",
            appearance: "none", cursor: "pointer",
        }}>
            {options.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
    </div>
);

const Pill = ({ active, children, onClick }) => (
    <button onClick={onClick} style={{
        padding: "8px 18px", borderRadius: 10, border: active ? `1px solid ${COLORS.accent}` : `1px solid ${COLORS.border}`,
        background: active ? COLORS.accentSoft : "transparent", color: active ? COLORS.accent : COLORS.textMuted,
        fontFamily: font, fontWeight: 600, fontSize: 13, cursor: "pointer", transition: "all 0.2s",
    }}>{children}</button>
);

// Notification Bell
const NotifBell = ({ count }) => (
    <div style={{ position: "relative", cursor: "pointer", padding: 8 }}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={COLORS.textSecondary} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {count > 0 && <div style={{
            position: "absolute", top: 4, right: 4, width: 16, height: 16, borderRadius: "50%",
            background: COLORS.red, color: "#fff", fontSize: 10, fontWeight: 700, display: "flex",
            alignItems: "center", justifyContent: "center", fontFamily: font,
        }}>{count}</div>}
    </div>
);

// Top Nav Bar
const NavBar = ({ view, course, sessionStatus }) => (
    <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "12px 20px", borderBottom: `1px solid ${COLORS.border}`, background: COLORS.surface,
    }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={COLORS.textMuted} strokeWidth="2" style={{ cursor: "pointer" }}>
                <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            <span style={{ fontFamily: font, fontWeight: 700, fontSize: 16, color: COLORS.textPrimary }}>{course}</span>
            <Badge color={sessionStatus === "Active" ? COLORS.green : COLORS.amber}
                bg={sessionStatus === "Active" ? COLORS.greenSoft : COLORS.amberSoft}
                border={sessionStatus === "Active" ? COLORS.greenBorder : COLORS.amberBorder}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: sessionStatus === "Active" ? COLORS.green : COLORS.amber, display: "inline-block" }} />
                {sessionStatus}
            </Badge>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <NotifBell count={3} />
            <div style={{
                width: 32, height: 32, borderRadius: "50%", background: COLORS.accentSoft,
                display: "flex", alignItems: "center", justifyContent: "center",
                color: COLORS.accent, fontFamily: font, fontWeight: 700, fontSize: 13, cursor: "pointer",
            }}>{view === "Student" ? "DS" : view === "TA" ? "TA" : "PR"}</div>
        </div>
    </div>
);

// =================== STUDENT VIEW ===================
const StudentView = () => {
    const [submitted, setSubmitted] = useState(false);
    const [showSimilar, setShowSimilar] = useState(true);
    const [title, setTitle] = useState("");
    const [category, setCategory] = useState("Debugging");
    const [priority, setPriority] = useState("Medium");
    const [claimed, setClaimed] = useState(false);

    useEffect(() => {
        if (submitted) {
            const t = setTimeout(() => setClaimed(true), 4000);
            return () => clearTimeout(t);
        }
    }, [submitted]);

    if (submitted) {
        return (
            <div style={{ padding: 20 }}>
                <NavBar view="Student" course="CS5340 - HCI" sessionStatus="Active" />
                <div style={{ maxWidth: 480, margin: "40px auto", textAlign: "center" }}>
                    <div style={{
                        width: 72, height: 72, borderRadius: "50%", margin: "0 auto 20px",
                        background: claimed ? COLORS.greenSoft : COLORS.accentSoft,
                        display: "flex", alignItems: "center", justifyContent: "center",
                        border: `2px solid ${claimed ? COLORS.greenBorder : "transparent"}`,
                        transition: "all 0.4s",
                    }}>
                        {claimed ? (
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke={COLORS.green} strokeWidth="2.5"><path d="M20 6L9 17l-5-5" /></svg>
                        ) : (
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke={COLORS.accent} strokeWidth="2">
                                <circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" />
                            </svg>
                        )}
                    </div>

                    {claimed ? (
                        <>
                            <div style={{ fontFamily: font, fontSize: 20, fontWeight: 700, color: COLORS.green, marginBottom: 8 }}>Your question is being answered!</div>
                            <div style={{ fontFamily: font, fontSize: 14, color: COLORS.textSecondary, marginBottom: 24 }}>TA Sarah M. has claimed your question and is reviewing it now.</div>
                            <div style={{
                                padding: 16, borderRadius: 14, background: COLORS.card, border: `1px solid ${COLORS.greenBorder}`,
                                textAlign: "left",
                            }}>
                                <div style={{ fontSize: 12, color: COLORS.textMuted, fontFamily: font, marginBottom: 4 }}>Your Question</div>
                                <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.textPrimary, fontFamily: font }}>Segfault in linked list delete function</div>
                                <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                                    <Badge color={COLORS.purple} bg={COLORS.purpleSoft}>Debugging</Badge>
                                    <Badge color={COLORS.amber} bg={COLORS.amberSoft}>Medium</Badge>
                                </div>
                            </div>
                        </>
                    ) : (
                        <>
                            <div style={{ fontFamily: font, fontSize: 20, fontWeight: 700, color: COLORS.textPrimary, marginBottom: 8 }}>You're in the queue!</div>
                            <div style={{ fontFamily: font, fontSize: 14, color: COLORS.textSecondary, marginBottom: 30 }}>We'll notify you when a TA picks up your question.</div>
                            <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
                                <StatCard label="Position" value="#3" color={COLORS.accent} />
                                <StatCard label="Est. Wait" value="~12m" color={COLORS.amber} />
                            </div>
                            <div style={{
                                padding: 16, borderRadius: 14, background: COLORS.card, border: `1px solid ${COLORS.border}`,
                                textAlign: "left", marginBottom: 16,
                            }}>
                                <div style={{ fontSize: 12, color: COLORS.textMuted, fontFamily: font, marginBottom: 4 }}>Your Question</div>
                                <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.textPrimary, fontFamily: font }}>Segfault in linked list delete function</div>
                                <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                                    <Badge color={COLORS.purple} bg={COLORS.purpleSoft}>Debugging</Badge>
                                    <Badge color={COLORS.amber} bg={COLORS.amberSoft}>Medium</Badge>
                                </div>
                            </div>
                            <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
                                <Button small>Edit Question</Button>
                                <Button small danger>Withdraw</Button>
                            </div>
                        </>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div>
            <NavBar view="Student" course="CS5340 - HCI" sessionStatus="Active" />
            <div style={{ maxWidth: 520, margin: "0 auto", padding: "24px 20px" }}>
                {/* Similar Questions */}
                {showSimilar && title.length > 5 && (
                    <div style={{
                        marginBottom: 20, padding: 16, borderRadius: 14,
                        background: "rgba(6,182,212,0.06)", border: `1px solid rgba(6,182,212,0.15)`,
                    }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={COLORS.cyan} strokeWidth="2"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg>
                            <span style={{ fontFamily: font, fontSize: 13, fontWeight: 600, color: COLORS.cyan }}>Similar resolved questions</span>
                            <span onClick={() => setShowSimilar(false)} style={{ marginLeft: "auto", fontSize: 11, color: COLORS.textMuted, cursor: "pointer", fontFamily: font }}>Dismiss</span>
                        </div>
                        {[
                            { title: "Segfault when deleting head node in linked list", time: "2 days ago", votes: 5 },
                            { title: "Null pointer crash in doubly linked list remove()", time: "1 week ago", votes: 3 },
                        ].map((q, i) => (
                            <div key={i} style={{
                                padding: "10px 12px", borderRadius: 10, background: COLORS.card,
                                marginBottom: i === 0 ? 8 : 0, cursor: "pointer", display: "flex", alignItems: "center", gap: 10,
                                border: `1px solid ${COLORS.border}`,
                            }}>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontFamily: font, fontSize: 13, fontWeight: 600, color: COLORS.textPrimary }}>{q.title}</div>
                                    <div style={{ fontFamily: font, fontSize: 11, color: COLORS.textMuted, marginTop: 2 }}>{q.time} · {q.votes} found helpful</div>
                                </div>
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={COLORS.textMuted} strokeWidth="2"><path d="m9 18 6-6-6-6" /></svg>
                            </div>
                        ))}
                    </div>
                )}

                {/* Form */}
                <div style={{ fontFamily: font, fontSize: 18, fontWeight: 700, color: COLORS.textPrimary, marginBottom: 18 }}>Submit a Question</div>
                <Input label="Title" placeholder="Brief summary of your issue" value={title} onChange={e => setTitle(e.target.value)} />
                <Input label="Description" placeholder="Explain the problem in detail..." large />
                <Input label="Code Snippet (optional)" placeholder="Paste relevant code here..." large mono />
                <Input label="Error Message (optional)" placeholder="Paste error output..." large mono />
                <Input label="What I've Tried" placeholder="Describe what you've already attempted..." large />
                <div style={{ display: "flex", gap: 12 }}>
                    <Select label="Category" options={["Debugging", "Conceptual", "Setup/Config", "Assignment Clarification", "Other"]} value={category} onChange={e => setCategory(e.target.value)} />
                    <Select label="Priority" options={["Low", "Medium", "High"]} value={priority} onChange={e => setPriority(e.target.value)} />
                </div>
                <Button primary onClick={() => setSubmitted(true)} style={{ width: "100%", padding: "14px 0", fontSize: 15, marginTop: 8, borderRadius: 12 }}>
                    Submit Question
                </Button>
            </div>
        </div>
    );
};

// =================== TA VIEW ===================
const TAView = () => {
    const [expandedId, setExpandedId] = useState(null);
    const [questions, setQuestions] = useState([
        { id: 1, title: "Segfault in linked list delete function", student: "David S.", category: "Debugging", priority: "High", wait: "14m", status: "queued", desc: "My delete function crashes when trying to remove the head node. I think the issue is with pointer reassignment but I'm not sure.", code: "void delete(Node** head, int key) {\n  Node* temp = *head;\n  while(temp->data != key)\n    temp = temp->next;\n  free(temp); // crashes here\n}", error: "Segmentation fault (core dumped)", tried: "I tried checking if temp is NULL before freeing but it still crashes." },
        { id: 2, title: "Confusion about virtual functions vs templates", student: "Alex K.", category: "Conceptual", priority: "Medium", wait: "9m", status: "queued", desc: "When should I use virtual functions for polymorphism versus templates? Both seem to let me write generic code.", code: "", error: "", tried: "I read the textbook chapter but the distinction is still unclear to me." },
        { id: 3, title: "Makefile not linking math library", student: "Priya R.", category: "Setup/Config", priority: "Medium", wait: "6m", status: "queued", desc: "Getting undefined reference errors for math functions even though I included math.h.", code: "gcc -o main main.c\n# undefined reference to `sqrt`", error: "undefined reference to `sqrt`", tried: "I tried adding #include <math.h> at the top." },
        { id: 4, title: "HW3 Q2 expected output unclear", student: "Jordan L.", category: "Assignment Clarification", priority: "Low", wait: "3m", status: "queued", desc: "The expected output for question 2 shows 5 but I think the correct answer should be 4 given the input.", code: "", error: "", tried: "I checked Piazza but didn't find any clarification." },
    ]);

    const claimQuestion = (id) => {
        setQuestions(qs => qs.map(q => q.id === id ? { ...q, status: "in_progress" } : q));
    };
    const resolveQuestion = (id) => {
        setQuestions(qs => qs.map(q => q.id === id ? { ...q, status: "resolved" } : q));
    };
    const deferQuestion = (id) => {
        setQuestions(qs => {
            const deferred = qs.find(q => q.id === id);
            const rest = qs.filter(q => q.id !== id);
            return [...rest, { ...deferred, status: "queued", wait: "0m" }];
        });
    };

    const queued = questions.filter(q => q.status === "queued");
    const inProgress = questions.filter(q => q.status === "in_progress");
    const resolved = questions.filter(q => q.status === "resolved");

    const priorityOrder = { High: 0, Medium: 1, Low: 2 };
    const sortedQueued = [...queued].sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

    const priorityColor = (p) => p === "High" ? { c: COLORS.red, bg: COLORS.redSoft, bd: COLORS.redBorder } : p === "Medium" ? { c: COLORS.amber, bg: COLORS.amberSoft, bd: COLORS.amberBorder } : { c: COLORS.green, bg: COLORS.greenSoft, bd: COLORS.greenBorder };
    const catColor = (cat) => cat === "Debugging" ? { c: COLORS.purple, bg: COLORS.purpleSoft } : cat === "Conceptual" ? { c: COLORS.cyan, bg: COLORS.cyanSoft } : cat === "Setup/Config" ? { c: COLORS.amber, bg: COLORS.amberSoft } : cat === "Assignment Clarification" ? { c: COLORS.green, bg: COLORS.greenSoft } : { c: COLORS.textMuted, bg: COLORS.surfaceHover };

    return (
        <div>
            <NavBar view="TA" course="CS5340 - HCI" sessionStatus="Active" />
            <div style={{ maxWidth: 600, margin: "0 auto", padding: "20px 20px" }}>
                {/* Stats */}
                <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
                    <StatCard label="Queued" value={queued.length} color={COLORS.accent} />
                    <StatCard label="In Progress" value={inProgress.length} color={COLORS.amber} />
                    <StatCard label="Resolved" value={resolved.length} color={COLORS.green} />
                </div>

                {/* Queue */}
                <div style={{ fontFamily: font, fontSize: 14, fontWeight: 700, color: COLORS.textMuted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 12 }}>Queue</div>
                {sortedQueued.length === 0 && inProgress.length === 0 && (
                    <div style={{ textAlign: "center", padding: 40, color: COLORS.textMuted, fontFamily: font }}>
                        No questions in queue. Nice work! 🎉
                    </div>
                )}

                {/* In Progress */}
                {inProgress.map(q => {
                    const pc = priorityColor(q.priority);
                    const cc = catColor(q.category);
                    const expanded = expandedId === q.id;
                    return (
                        <div key={q.id} style={{
                            marginBottom: 12, borderRadius: 14, background: COLORS.card,
                            border: `1px solid ${COLORS.amberBorder}`, overflow: "hidden", transition: "all 0.2s",
                        }}>
                            <div onClick={() => setExpandedId(expanded ? null : q.id)} style={{ padding: "14px 16px", cursor: "pointer" }}>
                                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                                    <Badge color={COLORS.amber} bg={COLORS.amberSoft} border={COLORS.amberBorder}>In Progress</Badge>
                                    <span style={{ marginLeft: "auto", fontFamily: font, fontSize: 12, color: COLORS.textMuted }}>{q.wait}</span>
                                </div>
                                <div style={{ fontFamily: font, fontSize: 15, fontWeight: 600, color: COLORS.textPrimary, marginBottom: 6 }}>{q.title}</div>
                                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                    <span style={{ fontFamily: font, fontSize: 12, color: COLORS.textSecondary }}>{q.student}</span>
                                    <Badge color={cc.c} bg={cc.bg}>{q.category}</Badge>
                                    <Badge color={pc.c} bg={pc.bg} border={pc.bd}>{q.priority}</Badge>
                                </div>
                            </div>
                            {expanded && (
                                <div style={{ padding: "0 16px 14px", borderTop: `1px solid ${COLORS.border}`, marginTop: 0, paddingTop: 14 }}>
                                    <div style={{ fontFamily: font, fontSize: 13, color: COLORS.textSecondary, marginBottom: 10 }}>{q.desc}</div>
                                    {q.code && <pre style={{ fontFamily: monoFont, fontSize: 12, color: COLORS.textPrimary, background: COLORS.bg, padding: 12, borderRadius: 10, overflowX: "auto", marginBottom: 10, border: `1px solid ${COLORS.border}` }}>{q.code}</pre>}
                                    {q.error && <div style={{ fontFamily: monoFont, fontSize: 12, color: COLORS.red, background: COLORS.redSoft, padding: "8px 12px", borderRadius: 8, marginBottom: 10 }}>{q.error}</div>}
                                    {q.tried && <div style={{ fontFamily: font, fontSize: 12, color: COLORS.textMuted, fontStyle: "italic", marginBottom: 12 }}>Tried: {q.tried}</div>}
                                    <div style={{ display: "flex", gap: 8 }}>
                                        <Button small primary onClick={() => resolveQuestion(q.id)}>✓ Resolve</Button>
                                        <Button small onClick={() => deferQuestion(q.id)}>Defer</Button>
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}

                {/* Queued */}
                {sortedQueued.map(q => {
                    const pc = priorityColor(q.priority);
                    const cc = catColor(q.category);
                    const expanded = expandedId === q.id;
                    return (
                        <div key={q.id} style={{
                            marginBottom: 12, borderRadius: 14, background: COLORS.card,
                            border: `1px solid ${COLORS.border}`, overflow: "hidden", transition: "all 0.2s",
                        }}>
                            <div onClick={() => setExpandedId(expanded ? null : q.id)} style={{ padding: "14px 16px", cursor: "pointer" }}>
                                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                                    <div style={{ display: "flex", gap: 8 }}>
                                        <Badge color={cc.c} bg={cc.bg}>{q.category}</Badge>
                                        <Badge color={pc.c} bg={pc.bg} border={pc.bd}>{q.priority}</Badge>
                                    </div>
                                    <span style={{ fontFamily: font, fontSize: 12, color: COLORS.textMuted }}>{q.wait}</span>
                                </div>
                                <div style={{ fontFamily: font, fontSize: 15, fontWeight: 600, color: COLORS.textPrimary, marginBottom: 4 }}>{q.title}</div>
                                <div style={{ fontFamily: font, fontSize: 12, color: COLORS.textSecondary }}>{q.student}</div>
                            </div>
                            {expanded && (
                                <div style={{ padding: "0 16px 14px", borderTop: `1px solid ${COLORS.border}`, marginTop: 0, paddingTop: 14 }}>
                                    <div style={{ fontFamily: font, fontSize: 13, color: COLORS.textSecondary, marginBottom: 10 }}>{q.desc}</div>
                                    {q.code && <pre style={{ fontFamily: monoFont, fontSize: 12, color: COLORS.textPrimary, background: COLORS.bg, padding: 12, borderRadius: 10, overflowX: "auto", marginBottom: 10, border: `1px solid ${COLORS.border}` }}>{q.code}</pre>}
                                    {q.error && <div style={{ fontFamily: monoFont, fontSize: 12, color: COLORS.red, background: COLORS.redSoft, padding: "8px 12px", borderRadius: 8, marginBottom: 10 }}>{q.error}</div>}
                                    {q.tried && <div style={{ fontFamily: font, fontSize: 12, color: COLORS.textMuted, fontStyle: "italic", marginBottom: 12 }}>Tried: {q.tried}</div>}
                                    <div style={{ display: "flex", gap: 8 }}>
                                        <Button small primary onClick={() => claimQuestion(q.id)}>Claim</Button>
                                        <Button small onClick={() => deferQuestion(q.id)}>Defer</Button>
                                        <Button small>Redirect</Button>
                                        <Button small primary onClick={() => resolveQuestion(q.id)}>Resolve</Button>
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

// =================== PROFESSOR VIEW ===================
const ProfessorView = () => {
    const [tab, setTab] = useState("overview");

    const catData = [
        { name: "Debugging", pct: 38, color: COLORS.purple },
        { name: "Setup/Config", pct: 25, color: COLORS.cyan },
        { name: "Conceptual", pct: 20, color: COLORS.green },
        { name: "Assignment", pct: 12, color: COLORS.amber },
        { name: "Other", pct: 5, color: COLORS.red },
    ];

    const weeklyData = [
        { week: "W1", questions: 18, bar: 36 },
        { week: "W2", questions: 32, bar: 64 },
        { week: "W3", questions: 45, bar: 90 },
        { week: "W4", questions: 38, bar: 76 },
        { week: "W5", questions: 28, bar: 56 },
        { week: "W6", questions: 22, bar: 44 },
        { week: "W7", questions: 15, bar: 30 },
    ];

    const taData = [
        { name: "Sarah M.", resolved: 47, avgTime: "8.2 min", rating: 4.8 },
        { name: "James C.", resolved: 34, avgTime: "11.5 min", rating: 4.5 },
        { name: "Priya R.", resolved: 29, avgTime: "9.1 min", rating: 4.7 },
    ];

    const sessions = [
        { title: "Midterm Review", date: "Feb 18", questions: 24, avgWait: "6.2 min", avgResolve: "9.8 min" },
        { title: "HW3 Help", date: "Feb 20", questions: 18, avgWait: "4.1 min", avgResolve: "7.3 min" },
        { title: "General OH", date: "Feb 22", questions: 12, avgWait: "3.5 min", avgResolve: "6.9 min" },
    ];

    return (
        <div>
            <NavBar view="Professor" course="CS5340 - HCI" sessionStatus="Active" />
            <div style={{ maxWidth: 640, margin: "0 auto", padding: "20px 20px" }}>
                {/* Header */}
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
                    <div style={{ fontFamily: font, fontSize: 20, fontWeight: 700, color: COLORS.textPrimary }}>Analytics Dashboard</div>
                    <Button small style={{ background: COLORS.greenSoft, color: COLORS.green }}>
                        ↓ Export CSV
                    </Button>
                </div>

                {/* Tabs */}
                <div style={{ display: "flex", gap: 8, marginBottom: 24, flexWrap: "wrap" }}>
                    {["overview", "categories", "trends", "ta performance"].map(t => (
                        <Pill key={t} active={tab === t} onClick={() => setTab(t)}>
                            {t.charAt(0).toUpperCase() + t.slice(1)}
                        </Pill>
                    ))}
                </div>

                {/* Overview Tab */}
                {tab === "overview" && (
                    <>
                        <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
                            <StatCard label="Total Questions" value="183" color={COLORS.accent} />
                            <StatCard label="Avg Wait" value="5.2m" color={COLORS.amber} />
                            <StatCard label="Avg Resolve" value="8.4m" color={COLORS.green} />
                        </div>
                        <div style={{ fontFamily: font, fontSize: 14, fontWeight: 700, color: COLORS.textMuted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 12 }}>Recent Sessions</div>
                        {sessions.map((s, i) => (
                            <div key={i} style={{
                                padding: "14px 16px", borderRadius: 14, background: COLORS.card,
                                border: `1px solid ${COLORS.border}`, marginBottom: 10,
                            }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                                    <div style={{ fontFamily: font, fontSize: 15, fontWeight: 600, color: COLORS.textPrimary }}>{s.title}</div>
                                    <span style={{ fontFamily: font, fontSize: 12, color: COLORS.textMuted }}>{s.date}</span>
                                </div>
                                <div style={{ display: "flex", gap: 16 }}>
                                    <span style={{ fontFamily: font, fontSize: 12, color: COLORS.textSecondary }}>{s.questions} questions</span>
                                    <span style={{ fontFamily: font, fontSize: 12, color: COLORS.textSecondary }}>Wait: {s.avgWait}</span>
                                    <span style={{ fontFamily: font, fontSize: 12, color: COLORS.textSecondary }}>Resolve: {s.avgResolve}</span>
                                </div>
                            </div>
                        ))}
                    </>
                )}

                {/* Categories Tab */}
                {tab === "categories" && (
                    <>
                        <div style={{ fontFamily: font, fontSize: 14, fontWeight: 700, color: COLORS.textMuted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 16 }}>Questions by Category</div>
                        {catData.map((c, i) => (
                            <div key={i} style={{ marginBottom: 16 }}>
                                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                                    <span style={{ fontFamily: font, fontSize: 13, fontWeight: 600, color: COLORS.textPrimary }}>{c.name}</span>
                                    <span style={{ fontFamily: font, fontSize: 13, fontWeight: 700, color: c.color }}>{c.pct}%</span>
                                </div>
                                <div style={{ height: 10, borderRadius: 6, background: COLORS.surface, overflow: "hidden" }}>
                                    <div style={{
                                        height: "100%", width: `${c.pct}%`, borderRadius: 6,
                                        background: `linear-gradient(90deg, ${c.color}, ${c.color}88)`,
                                        transition: "width 0.8s ease",
                                    }} />
                                </div>
                            </div>
                        ))}
                        <div style={{
                            marginTop: 24, padding: 16, borderRadius: 14, background: COLORS.card,
                            border: `1px solid ${COLORS.border}`,
                        }}>
                            <div style={{ fontFamily: font, fontSize: 13, fontWeight: 600, color: COLORS.cyan, marginBottom: 8 }}>💡 Insight</div>
                            <div style={{ fontFamily: font, fontSize: 13, color: COLORS.textSecondary, lineHeight: 1.5 }}>
                                Debugging questions make up 38% of all submissions. Consider dedicating a session specifically to common debugging patterns, or adding a debugging guide to the course resources.
                            </div>
                        </div>
                    </>
                )}

                {/* Trends Tab */}
                {tab === "trends" && (
                    <>
                        <div style={{ fontFamily: font, fontSize: 14, fontWeight: 700, color: COLORS.textMuted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 16 }}>Question Volume by Week</div>
                        <div style={{
                            padding: 20, borderRadius: 14, background: COLORS.card,
                            border: `1px solid ${COLORS.border}`, marginBottom: 20,
                        }}>
                            <div style={{ display: "flex", alignItems: "flex-end", gap: 10, height: 140, paddingBottom: 8 }}>
                                {weeklyData.map((d, i) => (
                                    <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
                                        <span style={{ fontFamily: font, fontSize: 11, color: COLORS.textSecondary, fontWeight: 600 }}>{d.questions}</span>
                                        <div style={{
                                            width: "100%", height: d.bar * 1.2, borderRadius: "6px 6px 2px 2px",
                                            background: `linear-gradient(180deg, ${COLORS.accent}, ${COLORS.accent}44)`,
                                            transition: "height 0.6s ease",
                                            minHeight: 8,
                                        }} />
                                        <span style={{ fontFamily: font, fontSize: 11, color: COLORS.textMuted }}>{d.week}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div style={{ display: "flex", gap: 12 }}>
                            <StatCard label="Peak Week" value="W3" color={COLORS.red} />
                            <StatCard label="Peak Session" value="Tue 3pm" color={COLORS.amber} />
                        </div>
                    </>
                )}

                {/* TA Performance Tab */}
                {tab === "ta performance" && (
                    <>
                        <div style={{ fontFamily: font, fontSize: 14, fontWeight: 700, color: COLORS.textMuted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 16 }}>TA Performance</div>
                        {taData.map((ta, i) => (
                            <div key={i} style={{
                                padding: "16px 18px", borderRadius: 14, background: COLORS.card,
                                border: `1px solid ${COLORS.border}`, marginBottom: 10,
                                display: "flex", alignItems: "center", gap: 14,
                            }}>
                                <div style={{
                                    width: 42, height: 42, borderRadius: "50%", background: COLORS.accentSoft,
                                    display: "flex", alignItems: "center", justifyContent: "center",
                                    fontFamily: font, fontWeight: 700, color: COLORS.accent, fontSize: 15,
                                    flexShrink: 0,
                                }}>
                                    {ta.name.split(" ").map(n => n[0]).join("")}
                                </div>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontFamily: font, fontSize: 15, fontWeight: 600, color: COLORS.textPrimary }}>{ta.name}</div>
                                    <div style={{ display: "flex", gap: 16, marginTop: 4 }}>
                                        <span style={{ fontFamily: font, fontSize: 12, color: COLORS.textSecondary }}>{ta.resolved} resolved</span>
                                        <span style={{ fontFamily: font, fontSize: 12, color: COLORS.textSecondary }}>Avg: {ta.avgTime}</span>
                                    </div>
                                </div>
                                <div style={{
                                    padding: "4px 12px", borderRadius: 8, background: COLORS.greenSoft,
                                    fontFamily: font, fontSize: 14, fontWeight: 700, color: COLORS.green,
                                }}>★ {ta.rating}</div>
                            </div>
                        ))}
                    </>
                )}
            </div>
        </div>
    );
};

// =================== MAIN APP ===================
export default function App() {
    const [view, setView] = useState("Student");
    const views = ["Student", "TA", "Professor"];

    return (
        <div style={{ background: COLORS.bg, minHeight: "100vh", fontFamily: font }}>
            <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,500;0,9..40,600;0,9..40,700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />

            {/* View Switcher */}
            <div style={{
                display: "flex", justifyContent: "center", gap: 4, padding: "12px 20px",
                background: COLORS.surface, borderBottom: `1px solid ${COLORS.border}`,
            }}>
                {views.map(v => (
                    <button key={v} onClick={() => setView(v)} style={{
                        padding: "8px 24px", borderRadius: 8, border: "none", cursor: "pointer",
                        fontFamily: font, fontWeight: 600, fontSize: 13,
                        background: view === v ? COLORS.accent : "transparent",
                        color: view === v ? "#fff" : COLORS.textMuted,
                        transition: "all 0.2s",
                    }}>{v} View</button>
                ))}
            </div>

            {/* Render View */}
            {view === "Student" && <StudentView />}
            {view === "TA" && <TAView />}
            {view === "Professor" && <ProfessorView />}
        </div>
    );
}