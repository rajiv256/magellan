# magellan

DNA sequence designer and possibly illustrator. 

## File structure

```javascript
magellan/
├── frontend/
│   ├── public/
│   │   ├── index.html                 # Basic HTML template
│   │   └── favicon.ico               # App icon
│   ├── src/
│   │   ├── components/
│   │   │   ├── OligoDesigner.jsx     # Main React component (from artifacts)
│   │   │   └── OligoDesigner.css     # Component styles (from artifacts)
│   │   ├── App.js                    # App entry point (from artifacts)
│   │   ├── App.css                   # Global app styles (optional)
│   │   └── index.js                  # React entry point
│   ├── package.json                  # Frontend dependencies
│   └── package-lock.json            # Lock file
├── backend/
│   ├── core/
│   │   ├── __init__.py              # Empty file
│   │   ├── models.py                # Data models
│   │   ├── thermodynamics.py        # Your calculations
│   │   ├── generator.py             # Sequence generation
│   │   └── validator.py             # Validation logic
│   ├── api/
│   │   ├── __init__.py              # Empty file
│   │   └── routes.py                # API endpoints
│   ├── data/
│   │   ├── sequences.json           # Cached sequences (backup)
│   │   └── config.json              # Settings
│   ├── venv/                        # Virtual environment
│   ├── app.py                       # Main Flask app (from artifacts)
│   ├── config.py                    # Configuration (from artifacts)
│   ├── populate_redis.py            # Advanced Redis loader (from artifacts)
│   ├── load_sequences.py            # Simple Redis loader (from artifacts)
│   ├── requirements.txt             # Python dependencies
│   └── __init__.py                  # Empty file
├── scripts/
│   ├── setup.sh                     # Setup script (from artifacts)
│   ├── start-backend.sh             # Backend startup
│   ├── start-frontend.sh            # Frontend startup
│   └── load-redis.sh               # Redis loading script
├── docs/
│   └── README.md                    # Project documentation
└── .env 
```


`backend/core/validator.py`

✅ Domain-Level Validation:

Length: Exact sequence length matching
GC Content: Within specified range
Melting Temperature: Appropriate for hybridization
Hairpin Formation: Secondary structure checks
Self-Dimerization: Homodimer formation
Sequence Patterns: Problematic motifs detection

🧬 3' End Stringent Checks:

3' Hairpin: More critical than general hairpin
3' Self-Dimer: Enhanced sensitivity at primer ends
3' GC Clamp: Prevents excessive G/C at 3' end
3' Cross-Dimer: Inter-strand interactions at critical region

🔗 Strand-Level Validation:

Composition: Matches constituent domains
Full-Length: Complete strand properties
Cross-Interactions: Between different strands

⚠️ Problematic Pattern Detection:

Homopolymers: AAAA, TTTT, GGGG, CCCC runs
Simple Repeats: ATAT, CGCG patterns
Restriction Sites: Common enzyme sites
Purine/Pyrimidine Runs: Problematic base clustering

📊 Smart Reporting:

Pass/Fail Status: Clear validation results
Detailed Metrics: Actual vs threshold values
Summary Statistics: Overall validation health
Critical vs Warning: Severity classification