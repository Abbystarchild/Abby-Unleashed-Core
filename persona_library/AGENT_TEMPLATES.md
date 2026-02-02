# 📚 Agent Template Catalog

Pre-built agent personas for common tasks. Use these directly or as templates for custom agents.

## Quick Reference

| Template | Best For |
|----------|----------|
| [Backend Developer](#backend-developer) | REST APIs, server-side code |
| [Frontend Developer](#frontend-developer) | React/TypeScript web apps |
| [DevOps Engineer](#devops-engineer) | CI/CD, infrastructure, AWS/K8s |
| [Security Engineer](#security-engineer) | Security reviews, auth, compliance |
| [Data Engineer](#data-engineer) | ETL pipelines, data warehouses |
| [ML Engineer](#ml-engineer) | ML systems, model deployment |
| [QA Engineer](#qa-engineer) | Testing, automation, quality |
| [DBA](#database-administrator) | PostgreSQL, query optimization |
| [Technical Writer](#technical-writer) | Documentation, tutorials |
| [Software Architect](#software-architect) | System design, architecture |
| [iOS Developer](#ios-developer) | Swift, SwiftUI mobile apps |
| [SRE](#site-reliability-engineer) | Reliability, monitoring, incidents |
| [Code Reviewer](#code-reviewer) | Code reviews, mentoring |
| [Debugger](#debugging-specialist) | Troubleshooting, root cause analysis |

---

## Template Details

### Backend Developer
**File:** `senior_backend_developer.yaml`

**Specialties:**
- REST API design and implementation
- Authentication (JWT, OAuth2)
- Database integration
- Rate limiting and caching

**Best For:**
- "Build a REST API for..."
- "Create an authentication system..."
- "Implement CRUD operations..."

---

### Frontend Developer
**File:** `senior_frontend_developer.yaml`

**Specialties:**
- React 18+ with TypeScript
- Component architecture
- State management
- Accessibility (WCAG 2.1)

**Best For:**
- "Build a React component for..."
- "Create a dashboard UI..."
- "Implement a form with validation..."

---

### DevOps Engineer
**File:** `senior_devops_engineer.yaml`

**Specialties:**
- AWS/Kubernetes infrastructure
- Terraform IaC
- CI/CD pipelines
- GitOps workflows

**Best For:**
- "Deploy this app to AWS..."
- "Create a Kubernetes manifest..."
- "Set up a CI/CD pipeline..."

---

### Security Engineer
**File:** `senior_security_engineer.yaml`

**Specialties:**
- OWASP Top 10 vulnerabilities
- Threat modeling
- Authentication/authorization
- Compliance (SOC 2, PCI-DSS)

**Best For:**
- "Review this code for security issues..."
- "Implement secure authentication..."
- "Create a threat model for..."

---

### Data Engineer
**File:** `senior_data_engineer.yaml`

**Specialties:**
- ETL/ELT pipelines
- Spark, Airflow, dbt
- Data warehouse design
- Data quality validation

**Best For:**
- "Build a data pipeline for..."
- "Create a dbt model for..."
- "Design a data warehouse schema..."

---

### ML Engineer
**File:** `senior_ml_engineer.yaml`

**Specialties:**
- ML model deployment
- Feature engineering
- MLOps and experiment tracking
- Model serving APIs

**Best For:**
- "Deploy this ML model..."
- "Create a feature engineering pipeline..."
- "Set up model monitoring..."

---

### QA Engineer
**File:** `senior_qa_engineer.yaml`

**Specialties:**
- Test automation (Pytest, Jest)
- E2E testing (Playwright, Cypress)
- Performance testing
- Test strategy

**Best For:**
- "Write tests for this code..."
- "Create a test plan for..."
- "Set up E2E testing..."

---

### Database Administrator
**File:** `senior_dba.yaml`

**Specialties:**
- PostgreSQL optimization
- Query performance tuning
- Schema design
- High availability setup

**Best For:**
- "Optimize this slow query..."
- "Design a database schema for..."
- "Set up replication for..."

---

### Technical Writer
**File:** `senior_technical_writer.yaml`

**Specialties:**
- API documentation
- Tutorials and guides
- README files
- Developer experience

**Best For:**
- "Write documentation for..."
- "Create a tutorial for..."
- "Improve this README..."

---

### Software Architect
**File:** `principal_architect.yaml`

**Specialties:**
- System design
- Microservices architecture
- Technical decision making
- C4 diagrams

**Best For:**
- "Design a system for..."
- "Review this architecture..."
- "Create an ADR for..."

---

### iOS Developer
**File:** `senior_ios_developer.yaml`

**Specialties:**
- Swift and SwiftUI
- iOS app architecture (MVVM)
- App Store guidelines
- Core Data

**Best For:**
- "Build an iOS view for..."
- "Implement this feature in Swift..."
- "Create a SwiftUI component..."

---

### Site Reliability Engineer
**File:** `senior_sre.yaml`

**Specialties:**
- SLI/SLO/SLA management
- Incident response
- Observability (logs, metrics, traces)
- Chaos engineering

**Best For:**
- "Set up monitoring for..."
- "Create a runbook for..."
- "Define SLOs for..."

---

### Code Reviewer
**File:** `staff_code_reviewer.yaml`

**Specialties:**
- Clean code principles
- SOLID and design patterns
- Security review
- Constructive feedback

**Best For:**
- "Review this code..."
- "Suggest improvements for..."
- "Check for security issues..."

---

### Debugging Specialist
**File:** `senior_debugger.yaml`

**Specialties:**
- Systematic debugging
- Root cause analysis
- Performance profiling
- Concurrency issues

**Best For:**
- "Debug this error..."
- "Find why this is slow..."
- "Investigate this crash..."

---

## Using Templates

### In Code

```python
from persona_library import LibraryManager

# Load a template
manager = LibraryManager()
persona = manager.load_example("senior_backend_developer")

# Use it
agent = AgentFactory.create(dna=persona)
result = agent.execute_task("Build a REST API for user management")
```

### Via CLI

```bash
# Use a specific persona template
python cli.py task --persona backend --task "Build a REST API"
```

### Customizing Templates

Copy a template and modify:

```yaml
# my_custom_backend.yaml
persona_id: "my-backend-001"
role: "Backend Developer"
seniority: "Senior"

# ... customize domain, constraints, etc.
```

---

## Contributing New Templates

1. Create a YAML file in `persona_library/personas/examples/`
2. Follow the 5-element DNA structure
3. Add to this catalog
4. Submit a PR!
