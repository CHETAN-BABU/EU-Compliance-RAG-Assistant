# 🎬 Interview Demo Script

> **Goal**: Show off advanced RAG features in 5-7 minutes. Build to each feature with clear talking points.

---

## 🎯 Pre-Demo Setup

1. **Terminal 1**: Start Ollama (if using offline)
   ```bash
   ollama serve
   ```

2. **Terminal 2**: Start offline app
   ```bash
   cd offline
   streamlit run app.py
   ```

3. **Terminal 3** (optional): Start online app for comparison
   ```bash
   cd online
   streamlit run app.py
   ```

---

## Part 1: Introduction (30 seconds)

**Script:**
> "I built a compliance RAG system that handles GDPR, EU AI Act, and DORA. But more importantly, I added production-grade features that actually matter in real compliance workflows. Let me show you..."

**Show:**
- Browser with offline app loaded
- Sidebar showing configuration options
- Demo scenarios visible

---

## Part 2: Confidence Scoring & Quality Metrics (90 seconds)

**Action:**
1. Click "Demo 1: GDPR DSAR Workflow" button
2. Wait for answer to generate
3. Click "📊 Answer Quality Metrics" expander

**Script:**
> "Every answer comes with confidence metrics. See this answer scored 82% confidence because:
> - We retrieved 5 relevant documents
> - 87% keyword match with the question
> - Semantic strength at 79%
>
> In regulated industries, this transparency is critical. We're not just answering—we're proving the answer is grounded in retrieved sources."

**Key Point:**
> "Interviewers love this because it shows you understand RAG limitations and how to measure quality."

---

## Part 3: Self-Evaluation Loop (60 seconds)

**Action:**
1. Click "🔍 Self-Evaluation Results" expander
2. Show completeness and accuracy scores

**Script:**
> "This is where it gets sophisticated. After generating an answer, the system evaluates itself. In this case:
> - Completeness: 85% (is the answer covering all aspects?)
> - Accuracy: 89% (is it factually correct?)
> - Missing elements: [shows any gaps]
>
> This is a form of self-critique. The system knows what it doesn't know. This mirrors professional compliance review workflows."

**Key Point:**
> "This demonstrates advanced thinking about hallucination mitigation and answer quality assurance."

---

## Part 4: Legal Article Citations (60 seconds)

**Action:**
1. Click "📜 Legal Articles Referenced" expander
2. Show exact article numbers

**Script:**
> "Standard RAG systems cite 'gdpr_pack.md line 45'. This system cites exact legal articles:
> - GDPR Article 17 (Right to Erasure)
> - GDPR Article 5 (Principles)
> - GDPR Recital 45
>
> Why? Compliance teams need precise references. When they're building evidence for audits, they need to point to exact sections of EU legislation. This level of precision is what separates demo systems from production systems."

**Key Point:**
> "Shows you understand compliance workflows—teams need traceable evidence, not guesses."

---

## Part 5: Compliance Checklist Export (90 seconds)

**Action:**
1. Ask a new question: "I'm building an AI hiring tool—what do I need to do?"
2. Wait for answer
3. Click "📋 Download Compliance Checklist" button
4. Show downloaded file

**Script:**
> "Notice the system detected this is about both GDPR and EU AI Act. I clicked 'Download Compliance Checklist' and it generated an actionable checklist:
>
> [Show file content]
>
> - GDPR items: Assess if screening involves automated decisions, document lawful basis...
> - EU AI Act items: Classify as high-risk, implement testing procedures...
>
> This is what I actually deliver to compliance teams. It's structured, ready for Jira, and immediately actionable."

**Key Point:**
> "This is your differentiator. You're not just answering questions—you're generating output that teams actually use."

---

## Part 6: Query Complexity Detection (45 seconds)

**Action:**
1. Go to sidebar, show "Query Type" in metadata (not visible in UI but mention it)
2. Ask two questions:
   - Simple: "What is GDPR?"
   - Complex: "How do GDPR, EU AI Act, and DORA intersect for a fintech company?"

**Script:**
> "Behind the scenes, the system detects query complexity. Simple questions get direct answers. Complex multi-regulation questions trigger different retrieval. This enables adaptive depth and focused sub-query generation."

**Optional Deep Dive:**
> "For super complex questions, the system can decompose them into focused sub-queries: Q1 about GDPR, Q2 about EU AI Act, Q3 about integration—then synthesize a unified answer."

---

## Part 7: Offline-First Reliability (45 seconds)

**Script:**
> "Show the difference between modes. This offline mode works on an air-gapped machine with no internet. Regulated financial institutions love this.
>
> The online mode [switch to online app] adds Azure OpenAI integration and live web sources, but everything—all the confidence scoring, self-evaluation, article extraction—works in both modes."

**Key Point:**
> "You've solved the same compliance problem two ways: cloud-augmented AND air-gapped. That's production thinking."

---

## Part 8: Closing (60 seconds)

**Final Script:**

> "So what makes this different from standard RAG?
>
> 1. **Confidence Scoring** - Transparent quality metrics for every answer
> 2. **Self-Evaluation** - System knows when it doesn't know
> 3. **Article Extraction** - Precise legal references, not file names
> 4. **Compliance Artifacts** - Checklists used by real teams
> 5. **Dual Deployment** - Air-gapped AND cloud-augmented
>
> I didn't just build a chatbot. I built production infrastructure for compliance workflows."

**Questions They Might Ask:**
- **"How do you measure hallucination?"** → "Through self-evaluation completeness scores, keyword match rates, and citation verification."
- **"What about latency?"** → "Offline: ~2-3 seconds per answer. Online: ~1-2 seconds with Azure. Checklists cached for fast generation."
- **"Can you add custom documents?"** → "Yes. Vector database is persistent. PDF ingestion is built in. Try uploading a policy PDF."
- **"How do you handle regulatory updates?"** → "Official EUR-Lex documents are bundled. Can auto-update via GitHub Actions."

---

## 📊 Success Metrics During Demo

Interview listeners should leave thinking:

- ✅ "This person understands RAG limitations and how to measure quality"
- ✅ "They've thought about compliance workflows, not just chatbots"
- ✅ "They can deploy in multiple environments (offline/online)"
- ✅ "They deliver production artifacts (checklists, not just chat)"
- ✅ "They built inference quality checks (confidence/self-eval)"

---

## 🎬 Demo Timing (Total: 7 minutes)

| Segment | Time | Focus |
|---------|------|-------|
| Intro | 0:30 | Hook attention |
| Confidence | 1:30 | Quality metrics |
| Self-Eval | 2:30 | System intelligence |
| Articles | 3:30 | Legal precision |
| Checklist | 4:30 | Practical value |
| Complexity | 5:15 | Advanced features |
| Offline/Online | 6:00 | Deployment options |
| Closing | 7:00 | Impact summary |

---

## 💡 Pro Tips

1. **Prepare example PDFs** - Have a sample compliance document ready to upload
2. **Pre-warm vector store** - Ingest official docs before demo so queries are faster
3. **Have offline mode ready** - Show reliability without internet
4. **Be ready to open code** - Reviewers might ask to see implementation
5. **Mention architecture** - "Modular design in compliance_utils.py allows easy feature addition"

---

## 🚨 Potential Issues & Solutions

| Issue | Solution |
|-------|----------|
| Ollama slow | Pre-warm with `ollama pull gemma3:4b` |
| Long retrieval | Adjust top_k from 7 to 3 for faster results |
| Web API fails | Toggle "Use internet snippets" off |
| LLM eval slow | Disable self-eval in sidebar for demo speed |
| No articles found | Use official EUR-Lex documents in question |

---

## 🎯 After Demo - Next Questions

**Interviewer:** "How would you scale this?"
**You:** "Currently local/single-instance. For production: distributed vector indexing (Qdrant/Weaviate), caching layer (Redis), multi-region deployment, usage tracking."

**Interviewer:** "What about bias or inaccuracy?"
**You:** "Multi-layered: keyword-reranking, citation verification, self-evaluation scoring, human review workflows, audit logging."

**Interviewer:** "Cost considerations?"
**You:** "Offline mode: ~$0. Azure online: ~$0.005 per query. Vectorized search scales logarithmically. Can optimize token usage with prompt caching."

---

## 📸 Screenshot/Recording Tips

If doing async interview:
1. Record in browser at 1280x800 resolution
2. Zoom to 125% so text is readable
3. Show sidebar first, then demo
4. Narrate each click and observation
5. Keep pacing 60% slower than live (people watch 1.5x)

Total recording: 6-8 minutes tops.

---

**You've got this! 🚀**
