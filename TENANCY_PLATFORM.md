# Multi-Tenant Platform & Organization Management

The Multi-Tenant Platform transforms Kisan Mitra AI into a scalable SaaS platform capable of serving multiple independent tenant organizations. It ensures complete isolation across storage, context, workflows, observabilities, memory, and security controls while retaining a shared application runtime.

---

## 1. Architecture Overview

Tenancy boundaries are enforced dynamically via task-local variables (`contextvars`), filesystem hooks, and object attributes partitioning descriptors:

```mermaid
graph TD
    Request[Incoming Query] -->|1. Parse Claims & Headers| API[FastAPI Query Router]
    API -->|2. Set ContextVar| Context[TenantContext - tenant_id / organization_id]
    
    Context -->|3. Route File Operations| FS[Patched builtins.open]
    FS -->|Disk Partition| TenantStorage[data/tenants/{tenant_id}/...]
    
    Context -->|4. Partition Class Dicts/Lists| Descriptors[TenantIsolated Descriptors]
    Descriptors -->|In-Memory Isolation| Modules[Memory / Observability / Jobs / Vector Stores]
    
    Context -->|5. Run Agent Reasonings| Orchestrator[AgentOrchestrator]
```

---

## 2. Tenant Context Propagation

Tenant context parameters are propagated automatically through the AI execution chain using `contextvars.ContextVar`:
- **`tenant_id_var`**: Tracks active tenant identifier.
- **`organization_id_var`**: Tracks active organization / division unit.
- **`execution_id_var`**: Tracks active execution token (usually request ID).

Context parameters are extracted at the API gateway layer from JWT claims or request headers (`X-Tenant-ID` / `X-Organization-ID`) and bound using the `set_tenant_context` context manager block. Downstream specialist agents and tasks receive these directly via `AgentContext`.

---

## 3. Data Isolation Model

To guarantee complete separation of tenant state with zero data bleed:

### A. Physical File Isolation
Python's native `builtins.open` call is globally patched under the `IsolationEngine`. Whenever a system component opens a file located under the `data/` path, the call is transparently redirected:
```
data/farmers/profiles.json  -->  data/tenants/{tenant_id}/farmers/profiles.json
```
This isolates persistent JSON tables and disk indexes.

### B. In-Memory Data Isolation
Class properties are wrapped dynamically using custom descriptors (`TenantIsolatedDictDescriptor` and `TenantIsolatedListDescriptor`). This partitions state maps in-memory based on the active task-local tenant ID for:
- **Persistent Memory**: Profile, long-term memory, and conversation caches.
- **Digital Twins**: Predictive twin details and risk profiles.
- **Learning**: Recommendation, agent, and knowledge feedback logs.
- **Observability**: Execution metrics and tracing spans.
- **Workflow Jobs**: Background priority queues and job stores.
- **Knowledge Engine**: Local document storage collections.

---

## 4. Organization Unit Hierarchy

Organizations map a multi-layered hierarchical unit structure under each tenant:

```
Tenant
  └── Organization (e.g. Cooperative)
        └── Department (e.g. Region Office)
              └── Team (e.g. Support Unit)
                    └── Operator (Viewer / Operator / Admin)
```

Operators are assigned to specific Teams and inherit hierarchical scopes.

---

## 5. Security & RBAC Roles

Role-Based Access Control is extended to support SaaS operational structures:

| Role Name | Scope & Capabilities | Hierarchy Inheritance |
| :--- | :--- | :--- |
| **Tenant Admin** | Wildcard access (`*`) to all features under their tenant. | Admin, Operator, Support, Farmer, Viewer |
| **Organization Admin** | Full dashboard, analytics, query, specialist agent, and knowledge access. | Operator, Support, Farmer, Viewer |
| **Operator** | Query execution, dashboard access, and key specialist agents (Weather, Market, etc.). | Support, Farmer, Viewer |
| **Viewer** | Read-only access to dashboard pages and basic weather/market query parameters. | *None* |
