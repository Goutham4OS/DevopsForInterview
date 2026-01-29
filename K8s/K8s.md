all produvcation grade troubleshooting from scratch to advanced level in:
Helm

kubectl yaml 

kubectl commands and debug at different levels 

az cli  get login ,switch subscription, create resource group, create vm,aks cluster,

terraform 

azuredevops yamls cd ci

arm templates

---

# Production-Grade Troubleshooting Guide

---

# 1. HELM - Complete Troubleshooting

## Helm Basics - Quick Commands

```bash
# Check Helm version
helm version

# Add & update repos
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm repo list

# Search charts
helm search repo nginx
helm search hub wordpress
```

---

## Helm Install/Upgrade/Rollback

```bash
# Install
helm install <release-name> <chart> -n <namespace> --create-namespace
helm install myapp ./mychart -f values-prod.yaml

# Upgrade
helm upgrade <release-name> <chart>
helm upgrade myapp ./mychart --set image.tag=v2.0.0

# Install or Upgrade (UPSERT - most common in CI/CD)
helm upgrade --install myapp ./mychart -f values.yaml -n production

# Rollback
helm rollback <release-name> <revision>
helm rollback myapp 2

# Uninstall
helm uninstall myapp -n production
```

---

## Helm Troubleshooting Commands

| Issue | Command | Purpose |
|-------|---------|---------|
| **What's deployed?** | `helm list -A` | List all releases in all namespaces |
| **Release status** | `helm status myapp` | Check release status & notes |
| **Release history** | `helm history myapp` | See all revisions |
| **Get deployed values** | `helm get values myapp` | See values used |
| **Get all info** | `helm get all myapp` | Values + manifest + notes |
| **Get manifest** | `helm get manifest myapp` | See deployed YAML |
| **Debug template** | `helm template myapp ./mychart --debug` | Render locally |
| **Dry run** | `helm install myapp ./mychart --dry-run` | Test against cluster |
| **Lint chart** | `helm lint ./mychart` | Validate chart |

---

## Common Helm Errors & Fixes

### Error: "release already exists"
```bash
# Solution 1: Upgrade instead
helm upgrade --install myapp ./mychart

# Solution 2: Uninstall first
helm uninstall myapp
helm install myapp ./mychart

# Solution 3: Check for stuck release
helm list -A --pending
helm list -A --failed
```

### Error: "UPGRADE FAILED: another operation in progress"
```bash
# Check release status
helm status myapp

# Force rollback
helm rollback myapp 1 --force

# If stuck, delete secret
kubectl get secrets -l owner=helm
kubectl delete secret sh.helm.release.v1.myapp.v1
```

### Error: Template rendering failed
```bash
# Debug template
helm template myapp ./mychart --debug 2>&1 | head -50

# Check specific value
helm template myapp ./mychart --set image.tag=v1 --debug

# Validate YAML syntax
helm lint ./mychart
```

### Error: "context deadline exceeded" (timeout)
```bash
# Increase timeout
helm install myapp ./mychart --timeout 10m

# Check what's pending
kubectl get pods -n <namespace>
kubectl describe pod <pod-name>
```

---

## Helm Debug Workflow (Step-by-Step)

```bash
# 1. Check release exists and status
helm list -n production
helm status myapp -n production

# 2. Check history for failed upgrades
helm history myapp -n production

# 3. Compare values between revisions
helm get values myapp --revision 2
helm get values myapp --revision 3

# 4. See what changed in manifest
helm get manifest myapp --revision 2 > rev2.yaml
helm get manifest myapp --revision 3 > rev3.yaml
diff rev2.yaml rev3.yaml

# 5. Rollback if needed
helm rollback myapp 2 -n production

# 6. Verify rollback
helm status myapp -n production
```

---

# 2. KUBECTL YAML - Structure & Debugging

---

## Understanding Kubernetes API - From Ground Up

### What are API Resources?

Kubernetes organizes resources into **API Groups**. Think of it like a library with different sections.

```bash
# See ALL available API resources
kubectl api-resources

# Output shows:
# NAME          SHORTNAMES   APIVERSION    NAMESPACED   KIND
# pods          po           v1            true         Pod
# services      svc          v1            true         Service
# deployments   deploy       apps/v1       true         Deployment
# configmaps    cm           v1            true         ConfigMap
```

### Core API Group vs Named API Groups

```
┌─────────────────────────────────────────────────────────────────────┐
│                     KUBERNETES API GROUPS                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  CORE API GROUP (v1) - "Legacy" / Built-in                          │
│  ─────────────────────────────────────────                          │
│  apiVersion: v1        ← No group name, just version                │
│                                                                      │
│  Resources:                                                          │
│  • Pod                  • Service                                    │
│  • ConfigMap            • Secret                                     │
│  • Namespace            • Node                                       │
│  • PersistentVolume     • PersistentVolumeClaim                     │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  NAMED API GROUPS - Extensions / Add-ons                            │
│  ───────────────────────────────────────                            │
│  apiVersion: <group>/<version>                                      │
│                                                                      │
│  apps/v1:                                                            │
│  • Deployment           • ReplicaSet                                │
│  • StatefulSet          • DaemonSet                                 │
│                                                                      │
│  batch/v1:                                                           │
│  • Job                  • CronJob                                   │
│                                                                      │
│  networking.k8s.io/v1:                                              │
│  • Ingress              • NetworkPolicy                             │
│                                                                      │
│  rbac.authorization.k8s.io/v1:                                      │
│  • Role                 • ClusterRole                               │
│  • RoleBinding          • ClusterRoleBinding                        │
│                                                                      │
│  autoscaling/v2:                                                     │
│  • HorizontalPodAutoscaler                                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Why Both `apiVersion` AND `kind`?

**Question:** If `apiVersion: apps/v1` tells Kubernetes to use the apps group, why do we need `kind: Deployment`?

**Answer:** Because ONE API group contains MULTIPLE resource types!

```yaml
# Same API group (apps/v1), but DIFFERENT resources:

apiVersion: apps/v1
kind: Deployment        # ← Creates a Deployment
---
apiVersion: apps/v1
kind: ReplicaSet        # ← Creates a ReplicaSet
---
apiVersion: apps/v1
kind: StatefulSet       # ← Creates a StatefulSet
---
apiVersion: apps/v1
kind: DaemonSet         # ← Creates a DaemonSet
```

**Analogy:**
- `apiVersion` = Which **library section** (apps, batch, networking)
- `kind` = Which **specific book** in that section (Deployment, Job, Ingress)

```
┌──────────────────────────────────────────────────────────────┐
│  apiVersion: apps/v1                                         │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ kind: Deployment                                        ││
│  │ kind: ReplicaSet                                        ││
│  │ kind: StatefulSet                                       ││
│  │ kind: DaemonSet                                         ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  apiVersion: batch/v1                                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ kind: Job                                               ││
│  │ kind: CronJob                                           ││
│  └─────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

---

## The Deployment → ReplicaSet → Pod Hierarchy

### Why This Layered Architecture?

```
┌─────────────────────────────────────────────────────────────────────┐
│  YOU CREATE: Deployment                                             │
│  ───────────────────────                                            │
│  • Rolling updates, rollbacks                                       │
│  • Declarative updates                                              │
│  • History tracking                                                 │
│                                                                      │
│    ┌─────────────────────────────────────────────────────────────┐ │
│    │  K8s CREATES: ReplicaSet (automatically!)                   │ │
│    │  ─────────────────────────────────────                      │ │
│    │  • Maintains desired number of pods                         │ │
│    │  • Replaces failed pods                                     │ │
│    │  • You rarely create this directly                          │ │
│    │                                                              │ │
│    │    ┌─────────────────────────────────────────────────────┐ │ │
│    │    │  K8s CREATES: Pods (automatically!)                 │ │ │
│    │    │  ───────────────────────────────                    │ │ │
│    │    │  • Actual running containers                        │ │ │
│    │    │  • Ephemeral - can be replaced                      │ │ │
│    │    └─────────────────────────────────────────────────────┘ │ │
│    └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Where is the ReplicaSet Template?

**You don't write a ReplicaSet template!** It's embedded inside the Deployment.

```yaml
# ════════════════════════════════════════════════════════════════════
#                    COMPLETE DEPLOYMENT ANATOMY
# ════════════════════════════════════════════════════════════════════
apiVersion: apps/v1
kind: Deployment
metadata:                          # ─┐
  name: nginx-deployment           #  │ DEPLOYMENT METADATA
  labels:                          #  │ (identifies the Deployment itself)
    app: nginx                     # ─┘
    
spec:                              # ─┐ DEPLOYMENT SPEC
  replicas: 3                      #  │ 
  #                                #  │
  # ┌──────────────────────────────┼──┼─────────────────────────────────┐
  # │ REPLICASET IS CREATED FROM   │  │                                 │
  # │ replicas + selector + template  │                                 │
  # │                              │  │                                 │
  selector:                        #  │ ← ReplicaSet uses this to find pods
    matchLabels:                   #  │
      app: nginx                   #  │
  #                                #  │
  # └──────────────────────────────┼──┼─────────────────────────────────┘
  #                                #  │
  # ┌──────────────────────────────┼──┼─────────────────────────────────┐
  # │ POD TEMPLATE                 │  │                                 │
  # │ (This becomes the Pod spec)  │  │                                 │
  template:                        #  │
    metadata:                      #  │ ← Pod's metadata
      labels:                      #  │
        app: nginx                 #  │ ← MUST match selector above!
    spec:                          #  │
      containers:                  #  │ ← Pod's containers
      - name: nginx                #  │
        image: nginx:1.21          #  │
        ports:                     #  │
        - containerPort: 80        # ─┘
  # │                                                                   │
  # └───────────────────────────────────────────────────────────────────┘
```

### What ReplicaSet Actually Looks Like (Created by K8s)

When you apply a Deployment, Kubernetes creates a ReplicaSet automatically:

```bash
# You create Deployment
kubectl apply -f deployment.yaml

# Kubernetes creates ReplicaSet
kubectl get replicaset
# NAME                          DESIRED   CURRENT   READY
# nginx-deployment-5d66cc795f   3         3         3
#                  ↑
#                  Pod template hash (auto-generated)
```

```yaml
# This is what the auto-created ReplicaSet looks like:
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: nginx-deployment-5d66cc795f      # Auto-named
  labels:
    app: nginx
    pod-template-hash: 5d66cc795f        # Auto-added by K8s
  ownerReferences:                        # Links to parent Deployment
    - apiVersion: apps/v1
      kind: Deployment
      name: nginx-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
      pod-template-hash: 5d66cc795f      # Auto-added
  template:
    metadata:
      labels:
        app: nginx
        pod-template-hash: 5d66cc795f    # Auto-added
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
```

---

## Why matchLabels Selector is REQUIRED

### Question: "It's in the same YAML, can't it match automatically?"

**NO!** And here's why:

### Reason 1: Loose Coupling by Design

Kubernetes uses **labels** as the universal way to link resources. This allows:

```yaml
# Deployment in one file
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  selector:
    matchLabels:
      app: frontend      # ← "I manage pods with app=frontend"
  template:
    metadata:
      labels:
        app: frontend    # ← Pods get this label
---
# Service in another file (or same file)
apiVersion: v1
kind: Service
metadata:
  name: frontend-svc
spec:
  selector:
    app: frontend        # ← "Route traffic to pods with app=frontend"
  ports:
  - port: 80
```

### Reason 2: Multiple Controllers Can Manage Same Pods

```
                    ┌─────────────────┐
                    │  Pod            │
                    │  labels:        │
                    │    app: web     │
                    │    env: prod    │
                    │    version: v2  │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Deployment      │ │ Service         │ │ NetworkPolicy   │
│ selector:       │ │ selector:       │ │ podSelector:    │
│   app: web      │ │   app: web      │ │   env: prod     │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Reason 3: Explicit is Better Than Implicit

What if you have multiple pod templates in different Deployments? Without selectors, how would K8s know which pods belong to which Deployment?

---

## DANGER: What Happens with Wrong Labels?

### Scenario 1: Selector Doesn't Match Template Labels

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: broken-deployment
spec:
  selector:
    matchLabels:
      app: frontend     # ← Looking for "frontend"
  template:
    metadata:
      labels:
        app: backend    # ← But pods have "backend" ❌ MISMATCH!
    spec:
      containers:
      - name: app
        image: nginx
```

**Result:** ❌ **DEPLOYMENT FAILS TO CREATE**
```
The Deployment "broken-deployment" is invalid: 
spec.template.metadata.labels: Invalid value: 
"app":"backend": `selector` does not match template `labels`
```

### Scenario 2: Selector Matches ANOTHER Deployment's Pods

```yaml
# Deployment A - Already running
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deployment-a
spec:
  replicas: 3
  selector:
    matchLabels:
      app: shared-label    # ← Using "shared-label"
  template:
    metadata:
      labels:
        app: shared-label
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
---
# Deployment B - New deployment with SAME selector!
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deployment-b
spec:
  replicas: 2
  selector:
    matchLabels:
      app: shared-label    # ← SAME LABEL! ⚠️ DANGER!
  template:
    metadata:
      labels:
        app: shared-label
    spec:
      containers:
      - name: nginx
        image: nginx:1.21  # Different image
```

**Result:** ⚠️ **CHAOS! Both deployments fight over the same pods!**

```
┌─────────────────────────────────────────────────────────────────┐
│                        LABEL COLLISION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Deployment-A (wants 3 pods)     Deployment-B (wants 2 pods)    │
│         ↓                               ↓                        │
│         └─────────────┬─────────────────┘                       │
│                       ↓                                          │
│            Selector: app=shared-label                            │
│                       ↓                                          │
│    ┌──────────────────────────────────────┐                     │
│    │  All pods with app=shared-label      │                     │
│    │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐    │                     │
│    │  │Pod 1│ │Pod 2│ │Pod 3│ │Pod 4│    │                     │
│    │  └─────┘ └─────┘ └─────┘ └─────┘    │                     │
│    └──────────────────────────────────────┘                     │
│                                                                  │
│  Result:                                                         │
│  • Pods constantly being created and deleted                    │
│  • Deployment-A: "I need 3!" creates more                       │
│  • Deployment-B: "I need 2!" deletes some                       │
│  • ReplicaSets from both fight for control                      │
│  • Random pod versions (1.20 vs 1.21)                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Best Practice: Use UNIQUE Label Combinations

```yaml
# ✅ GOOD: Unique labels per deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-v1
spec:
  selector:
    matchLabels:
      app: frontend
      version: v1          # ← Add more labels for uniqueness
      component: web
  template:
    metadata:
      labels:
        app: frontend
        version: v1
        component: web
```

---

## How Selector Matching Works

### matchLabels (Simple - AND logic)

```yaml
selector:
  matchLabels:
    app: nginx
    env: prod
# Matches pods that have BOTH:
# - app=nginx AND
# - env=prod
```

### matchExpressions (Advanced - Complex logic)

```yaml
selector:
  matchLabels:
    app: nginx
  matchExpressions:
    - key: env
      operator: In
      values: [prod, staging]    # env IN (prod, staging)
    - key: version
      operator: NotIn
      values: [v1]               # version NOT IN (v1)
    - key: release
      operator: Exists           # has label "release" (any value)
    - key: deprecated
      operator: DoesNotExist     # doesn't have label "deprecated"
```

### Operators Available

| Operator | Meaning | Example |
|----------|---------|---------|
| `In` | Value is in list | `env In [prod, staging]` |
| `NotIn` | Value not in list | `version NotIn [v1, v2]` |
| `Exists` | Label key exists | `release Exists` |
| `DoesNotExist` | Label key doesn't exist | `deprecated DoesNotExist` |

---

## Quick Reference: Find API Version for Any Resource

```bash
# Method 1: kubectl api-resources
kubectl api-resources | grep -i deployment
# deployments    deploy    apps/v1    true    Deployment

# Method 2: kubectl explain
kubectl explain deployment
# KIND:     Deployment
# VERSION:  apps/v1

# Method 3: Get from existing resource
kubectl get deployment nginx -o yaml | head -5
```

### Common apiVersion Cheat Sheet

| Resource | apiVersion |
|----------|------------|
| Pod, Service, ConfigMap, Secret | `v1` |
| Deployment, ReplicaSet, StatefulSet, DaemonSet | `apps/v1` |
| Job, CronJob | `batch/v1` |
| Ingress | `networking.k8s.io/v1` |
| HPA | `autoscaling/v2` |
| PodDisruptionBudget | `policy/v1` |
| Role, ClusterRole | `rbac.authorization.k8s.io/v1` |

---

## YAML Structure Quick Reference

```yaml
apiVersion: apps/v1          # API version (kubectl api-resources)
kind: Deployment             # Resource type
metadata:                    # Identifiers
  name: myapp
  namespace: production
  labels:
    app: myapp
  annotations:
    description: "My app"
spec:                        # Desired state (varies by kind)
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:                  # Pod template
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: app
          image: nginx:1.21
status:                      # Actual state (read-only, set by K8s)
```

---

## YAML Validation Commands

```bash
# Validate YAML syntax
kubectl apply -f deployment.yaml --dry-run=client

# Validate against cluster (server-side)
kubectl apply -f deployment.yaml --dry-run=server

# Show what would be applied (diff)
kubectl diff -f deployment.yaml

# Explain any resource field
kubectl explain deployment.spec.replicas
kubectl explain pod.spec.containers.resources
kubectl explain ingress.spec.rules --recursive
```

---

## Rolling Update Strategies for Production

### The Two Key Parameters

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0      # How many pods can be DOWN during update
      maxSurge: 1            # How many EXTRA pods can be created
```

### Strategy by Criticality

```
┌─────────────────────────────────────────────────────────────────────┐
│                ROLLING UPDATE CHEAT SHEET                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  🔴 ZERO DOWNTIME (Critical Production):                            │
│  ────────────────────────────────────────                           │
│  maxUnavailable: 0       ← Never go below desired replicas          │
│  maxSurge: 1             ← Add 1 new, wait ready, remove 1 old      │
│  minReadySeconds: 10-30  ← Catch delayed failures                   │
│  readinessProbe: REQUIRED!                                          │
│                                                                      │
│  🟡 BALANCED (Most Production):                                     │
│  ──────────────────────────────                                     │
│  maxUnavailable: 1       ← Allow 1 pod down                         │
│  maxSurge: 1             ← Add 1 extra                              │
│                                                                      │
│  🟢 FAST (Dev/Staging):                                             │
│  ──────────────────────                                             │
│  maxUnavailable: 25%     ← Allow 25% down                           │
│  maxSurge: 25%           ← Add 25% extra                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Visual: How maxUnavailable: 0 Works

```
Replicas: 3, maxUnavailable: 0, maxSurge: 1

Step 1: ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
        │Old 1│ │Old 2│ │Old 3│ │New 1│  ← 4 pods (surge), wait New 1 ready
        └─────┘ └─────┘ └─────┘ └─────┘

Step 2: ┌─────┐ ┌─────┐ ┌─────┐
        │Old 2│ │Old 3│ │New 1│          ← Remove Old 1 (only after New 1 ready)
        └─────┘ └─────┘ └─────┘

Step 3: ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
        │Old 2│ │Old 3│ │New 1│ │New 2│  ← Add New 2, wait ready
        └─────┘ └─────┘ └─────┘ └─────┘

        ... continues until all pods are new ...

Result: Always 3+ pods running = Zero Downtime!
```

### Complete Critical Deployment Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: critical-app
spec:
  replicas: 3                    # Minimum 3 for HA
  
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0          # ← Zero downtime
      maxSurge: 1                # ← Conservative surge
  
  minReadySeconds: 10            # ← Wait 10s after ready before continuing
  revisionHistoryLimit: 5        # ← Keep 5 old ReplicaSets for rollback
  
  selector:
    matchLabels:
      app: critical-app
      
  template:
    metadata:
      labels:
        app: critical-app
    spec:
      containers:
      - name: app
        image: myapp:v2
        
        # CRITICAL: Proper probes!
        readinessProbe:          # ← Must pass before receiving traffic
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 3
          
        livenessProbe:           # ← Restart if unhealthy
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 10
          failureThreshold: 3
          
        # Graceful shutdown
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 10"]
              
      terminationGracePeriodSeconds: 30  # ← Time for graceful shutdown
      
      # Spread pods across nodes
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: critical-app
```

### Why Each Setting Matters

| Setting | Purpose | Critical Value |
|---------|---------|----------------|
| `maxUnavailable: 0` | Never go below desired replicas | **Required** for zero downtime |
| `maxSurge: 1` | Limit resource spike during rollout | Balance speed vs resources |
| `minReadySeconds: 10` | Prevent fast rollout if pod crashes after 5s | Catch delayed failures |
| `readinessProbe` | Only route traffic to healthy pods | **Absolutely required!** |
| `preStop` + `terminationGracePeriodSeconds` | Allow in-flight requests to complete | Prevents dropped connections |
| `topologySpreadConstraints` | Don't put all pods on one node | Survives node failure |

### Common Mistakes to Avoid

```yaml
# ❌ BAD: No readiness probe = pods marked ready immediately!
# Rolling update removes old pods before new ones are actually ready

# ❌ BAD: maxUnavailable: 1 with replicas: 1 = 100% downtime!

# ❌ BAD: No minReadySeconds = bad version can roll out to all pods
# if app crashes after 5 seconds of "ready"

# ❌ BAD: Using "Recreate" strategy for critical apps
strategy:
  type: Recreate  # ← Kills ALL pods first = GUARANTEED DOWNTIME!
```

### PodDisruptionBudget (Extra Protection)

Protects pods during node drains, cluster autoscaler, spot evictions:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: critical-app-pdb
spec:
  minAvailable: 2          # ← Always keep at least 2 pods running
  # OR: maxUnavailable: 1  # ← Never disrupt more than 1 at a time
  selector:
    matchLabels:
      app: critical-app
```

---

## Generate YAML Templates

```bash
# Generate Deployment YAML
kubectl create deployment myapp --image=nginx --dry-run=client -o yaml > deployment.yaml

# Generate Service YAML
kubectl create service clusterip myapp --tcp=80:8080 --dry-run=client -o yaml > service.yaml

# Generate ConfigMap YAML
kubectl create configmap myconfig --from-literal=key=value --dry-run=client -o yaml

# Generate Secret YAML
kubectl create secret generic mysecret --from-literal=password=secret --dry-run=client -o yaml

# Generate Job YAML
kubectl create job myjob --image=busybox --dry-run=client -o yaml -- echo "hello"

# Generate CronJob YAML
kubectl create cronjob mycron --image=busybox --schedule="*/5 * * * *" --dry-run=client -o yaml
```

---

## Fix Common YAML Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `error parsing YAML` | Indentation wrong | Use 2 spaces, no tabs |
| `unknown field` | Wrong field name | `kubectl explain <resource>` |
| `missing required field` | Required field absent | Check API docs |
| `invalid type` | String vs number | `port: 80` not `port: "80"` |
| `selector not matching` | Labels mismatch | Ensure selector matches pod labels |

---

# 3. KUBECTL COMMANDS - Complete Debug Guide

## Basic Operations

```bash
# Get resources
kubectl get pods                          # List pods
kubectl get pods -o wide                  # With node info
kubectl get pods -A                       # All namespaces
kubectl get all -n production             # All resource types
kubectl get pods -w                       # Watch (live updates)

# Describe (detailed info + events)
kubectl describe pod <pod-name>
kubectl describe node <node-name>

# Delete
kubectl delete pod <pod-name>
kubectl delete -f deployment.yaml
kubectl delete pods --all -n test         # Delete all pods

# Apply/Create
kubectl apply -f deployment.yaml
kubectl create -f deployment.yaml
```

---

## Debugging Pods (Level by Level)

### Understanding Pod Status vs Container Status (IMPORTANT!)

**The `STATUS` column in `kubectl get pods` is CONFUSING** because it shows a MIX of pod phase and container reasons!

```
┌─────────────────────────────────────────────────────────────────────┐
│  POD (wrapper)                                                       │
│  ─────────────                                                       │
│  Pod Phase: Running, Pending, Succeeded, Failed, Unknown            │
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │  Container 1    │  │  Container 2    │  │  Init Container │     │
│  │  State:         │  │  State:         │  │  State:         │     │
│  │  - Running      │  │  - Running      │  │  - Terminated   │     │
│  │  - Waiting      │  │  - Waiting      │  │    (Completed)  │     │
│  │  - Terminated   │  │  - Terminated   │  │                 │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Pod Phase (High-Level) vs Container State (Low-Level)

| Pod Phase | Meaning |
|-----------|---------|
| `Pending` | Pod accepted, but containers not created yet |
| `Running` | At least one container is running |
| `Succeeded` | All containers exited with code 0 |
| `Failed` | All containers terminated, at least one failed |
| `Unknown` | Can't get pod state (node communication issue) |

| Container State | Meaning | Details |
|-----------------|---------|---------|
| `Waiting` | Not running yet | reason: `ContainerCreating`, `ImagePullBackOff`, `CrashLoopBackOff` |
| `Running` | Executing | startedAt timestamp |
| `Terminated` | Finished | exitCode, reason, startedAt, finishedAt |

#### What `kubectl get pods` STATUS Actually Shows

```bash
kubectl get pods
# NAME       READY   STATUS             RESTARTS   AGE
# pod-1      1/1     Running            0          1h    ← Pod phase
# pod-2      0/1     CrashLoopBackOff   5          10m   ← Container reason!
# pod-3      0/1     ImagePullBackOff   0          5m    ← Container reason!
# pod-4      0/1     Pending            0          2m    ← Pod phase
# pod-5      0/1     ContainerCreating  0          30s   ← Container reason!
# pod-6      0/1     Error              0          1m    ← Container reason!
# pod-7      0/1     Init:0/2           0          1m    ← Init container status!
```

#### The Logic Behind STATUS Column

```
┌─────────────────────────────────────────────────────────────────────┐
│  kubectl get pods STATUS = "Most Useful Status to Show"            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  IF pod is being deleted          → "Terminating"                   │
│  ELSE IF init containers running  → "Init:X/Y"                      │
│  ELSE IF container waiting        → Container's waiting.reason      │
│                                     (CrashLoopBackOff, ImagePull..) │
│  ELSE IF container terminated     → Container's terminated.reason   │
│                                     (Error, OOMKilled, Completed)   │
│  ELSE IF pod has condition        → Condition reason                │
│  ELSE                             → Pod.status.phase                │
│                                     (Running, Pending, Succeeded)   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Side-by-Side: What You See vs Reality

| STATUS You See | Actual Pod Phase | Container State | Why Shown |
|----------------|------------------|-----------------|-----------|
| `Running` | Running | Running | Both healthy ✓ |
| `Pending` | Pending | - | No containers yet |
| `CrashLoopBackOff` | **Running** | Waiting | Container reason more useful! |
| `ImagePullBackOff` | **Pending** | Waiting | Container reason more useful! |
| `Error` | **Running/Failed** | Terminated | Container reason more useful! |
| `OOMKilled` | **Running** | Terminated | Container reason more useful! |
| `ContainerCreating` | **Pending** | Waiting | Container reason more useful! |
| `Init:1/3` | **Pending** | - | Init container progress |
| `Terminating` | Running | Running | Deletion in progress |

#### How to See the REAL Pod Phase

```bash
# Just the pod phase (the actual status)
kubectl get pod <pod> -o jsonpath='{.status.phase}'
# Running   ← Even when STATUS shows CrashLoopBackOff!

# See both in custom columns
kubectl get pods -o custom-columns="\
NAME:.metadata.name,\
PHASE:.status.phase,\
CONTAINER_STATE:.status.containerStatuses[0].state.waiting.reason"

# Full details
kubectl describe pod <pod>
# Look for:
#   Status:       Running        ← Actual Pod Phase
#   Containers:
#     myapp:
#       State:    Waiting        ← Actual Container State  
#       Reason:   CrashLoopBackOff  ← What kubectl get pods shows!
```

> **TL;DR:** `kubectl get pods` STATUS = "the most actionable thing to show", not strictly the pod phase. Container reasons like `CrashLoopBackOff` are more useful than just "Running"!

---

### Level 1: Pod Status Check
```bash
# Check pod status
kubectl get pods -n production

# Status meanings and troubleshooting:

# ═══════════════════════════════════════════════════════════════════
# PENDING → Can't be scheduled
# ═══════════════════════════════════════════════════════════════════
# Reasons:
#   - Insufficient CPU/Memory on nodes
#   - Node selector doesn't match any node
#   - Taints on nodes without matching tolerations
#   - PersistentVolumeClaim not bound
#   - ResourceQuota exceeded
#   - Pod affinity/anti-affinity rules can't be satisfied
#
# Debug:
kubectl describe pod <pod-name> | grep -A 10 "Events"
kubectl get nodes -o wide
kubectl describe node <node-name> | grep -A 5 "Allocated resources"
kubectl get pvc -n <namespace>
kubectl get resourcequota -n <namespace>
#
# Fix: Check events, increase node resources, fix selectors/tolerations

# ═══════════════════════════════════════════════════════════════════
# CONTAINERCREATING → Pulling image or mounting volumes
# ═══════════════════════════════════════════════════════════════════
# Reasons:
#   - Image is being pulled (large image, slow network)
#   - ImagePullSecret missing or invalid
#   - Volume mount in progress
#   - ConfigMap/Secret doesn't exist
#   - PVC not bound or volume attach failed
#
# Debug:
kubectl describe pod <pod-name> | tail -30
kubectl get events -n <namespace> --field-selector involvedObject.name=<pod-name>
kubectl get secrets -n <namespace>
kubectl get configmaps -n <namespace>
kubectl get pvc -n <namespace>
#
# Fix: Check image name, add imagePullSecrets, verify volumes exist

# ═══════════════════════════════════════════════════════════════════
# RUNNING → At least one container running
# ═══════════════════════════════════════════════════════════════════
# Note: Running doesn't mean healthy! Check:
#   - Readiness probe status
#   - Application logs for errors
#   - Service connectivity
#
# Debug:
kubectl logs <pod-name> -f
kubectl exec -it <pod-name> -- /bin/sh
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[*].ready}'
kubectl describe pod <pod-name> | grep -A 5 "Readiness"

# ═══════════════════════════════════════════════════════════════════
# COMPLETED → Container exited successfully (Jobs)
# ═══════════════════════════════════════════════════════════════════
# Normal for Jobs/CronJobs. If unexpected for Deployment:
#   - Container command finished (no long-running process)
#   - Missing entrypoint or CMD in Dockerfile
#
# Debug:
kubectl logs <pod-name>
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[*].state}'
#
# Fix: Ensure container runs a long-running process (e.g., server)

# ═══════════════════════════════════════════════════════════════════
# ERROR → Container exited with error
# ═══════════════════════════════════════════════════════════════════
# Reasons:
#   - Application crashed on startup
#   - Missing environment variables
#   - Wrong command/args
#   - Permission issues
#   - OOMKilled (out of memory)
#
# Debug:
kubectl logs <pod-name>
kubectl logs <pod-name> --previous  # If container restarted
kubectl describe pod <pod-name> | grep -A 5 "State"
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[*].lastState.terminated.reason}'
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[*].lastState.terminated.exitCode}'
#
# Exit codes: 0=success, 1=app error, 137=OOMKilled, 139=segfault, 143=SIGTERM

# ═══════════════════════════════════════════════════════════════════
# CRASHLOOPBACKOFF → Container keeps crashing
# ═══════════════════════════════════════════════════════════════════
# Reasons:
#   - Application error on startup
#   - Liveness probe failing repeatedly
#   - Missing dependencies (DB, config, secrets)
#   - Resource limits too low (OOMKilled)
#   - Filesystem read-only issues
#
# Debug:
kubectl logs <pod-name> --previous
kubectl describe pod <pod-name> | grep -A 10 "Last State"
kubectl get pod <pod-name> -o yaml | grep -A 10 "lastState"
kubectl describe pod <pod-name> | grep -i "oom\|killed\|memory"
#
# Fix: Check logs, fix app errors, increase memory limits, fix probes

# ═══════════════════════════════════════════════════════════════════
# IMAGEPULLBACKOFF → Can't pull image
# ═══════════════════════════════════════════════════════════════════
# Reasons:
#   - Image doesn't exist (typo in name/tag)
#   - Private registry without imagePullSecrets
#   - Registry authentication failed
#   - Network issues reaching registry
#   - Rate limiting (Docker Hub)
#
# Debug:
kubectl describe pod <pod-name> | grep -A 5 "Events"
kubectl get pod <pod-name> -o yaml | grep image:
kubectl get secrets -n <namespace> | grep docker
# Test image pull manually:
docker pull <image-name>
#
# Fix: Verify image name, create imagePullSecret, check registry access
kubectl create secret docker-registry regcred \
  --docker-server=<registry> \
  --docker-username=<user> \
  --docker-password=<pass>

# ═══════════════════════════════════════════════════════════════════
# TERMINATING → Being deleted (stuck)
# ═══════════════════════════════════════════════════════════════════
# Reasons:
#   - Finalizers preventing deletion
#   - Pod not responding to SIGTERM
#   - PVC/PV cleanup taking time
#   - Node unreachable
#
# Debug:
kubectl get pod <pod-name> -o yaml | grep -A 5 "finalizers"
kubectl describe pod <pod-name> | grep -A 5 "Conditions"
#
# Fix (force delete - use carefully!):
kubectl delete pod <pod-name> --grace-period=0 --force
```

### Level 2: Pod Events
```bash
# See events (scheduling, image pull, mount, etc.)
kubectl describe pod <pod-name> | tail -20

# Common events to look for:
# - FailedScheduling: No nodes match requirements
# - FailedMount: Volume mount issue
# - Failed: Container failed to start
# - Pulling: Pulling image
# - Unhealthy: Probe failed
```

### Level 3: Container Logs
```bash
# Current logs
kubectl logs <pod-name>
kubectl logs <pod-name> -c <container-name>    # Multi-container pod

# Previous container logs (after crash)
kubectl logs <pod-name> --previous

# Follow logs (tail -f)
kubectl logs <pod-name> -f

# Last N lines
kubectl logs <pod-name> --tail=100

# Logs with timestamps
kubectl logs <pod-name> --timestamps

# All pods with label
kubectl logs -l app=myapp --all-containers
```

### Level 4: Exec into Container
```bash
# Interactive shell
kubectl exec -it <pod-name> -- /bin/bash
kubectl exec -it <pod-name> -- /bin/sh        # If bash not available

# Run single command
kubectl exec <pod-name> -- env                 # Check env vars
kubectl exec <pod-name> -- cat /etc/hosts     # Check hosts
kubectl exec <pod-name> -- curl localhost:8080 # Test locally
kubectl exec <pod-name> -- ls -la /app        # Check files

# Multi-container pod
kubectl exec -it <pod-name> -c <container-name> -- /bin/sh
```

### Level 5: Debug with Ephemeral Container
```bash
# Add debug container to running pod (K8s 1.23+)
kubectl debug <pod-name> -it --image=busybox

# Debug with network tools
kubectl debug <pod-name> -it --image=nicolaka/netshoot

# Debug node
kubectl debug node/<node-name> -it --image=busybox
```

---

## Debugging Services & Networking

```bash
# Check service endpoints
kubectl get endpoints <service-name>

# Check if service has pods
kubectl describe service <service-name>

# Test service DNS from inside cluster
kubectl run tmp --image=busybox --rm -it --restart=Never -- nslookup <service-name>

# Test service connectivity
kubectl run tmp --image=busybox --rm -it --restart=Never -- wget -qO- <service-name>:<port>

# Port forward to test locally
kubectl port-forward svc/<service-name> 8080:80
kubectl port-forward pod/<pod-name> 8080:8080

# Check network policies
kubectl get networkpolicies -A
```

---

# PRODUCTION ISSUE: Pod-to-Pod Timeout (Sudden)

## Scenario
> Pod A was talking to Pod B without issues. Suddenly seeing timeout errors.
> - App code NOT changed
> - App NOT throttled (liveness probe would restart)
> - CoreDNS running fine
> - No resource crunch

## Root Cause Investigation (When Obvious Causes Ruled Out)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  RULED OUT:                           INVESTIGATE THESE:               │
│  ✓ App code unchanged                 → kube-proxy / iptables          │
│  ✓ Not throttled (liveness ok)        → Conntrack table full           │
│  ✓ CoreDNS working                    → NetworkPolicy (new/changed)    │
│  ✓ No resource crunch                 → Cloud NSG/Firewall rules       │
│  ✓ Pods running & ready               → CNI plugin issues              │
│                                        → MTU mismatch                   │
│                                        → Service mesh (Istio/Linkerd)  │
│                                        → Node-level network issues     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Check kube-proxy & iptables

```bash
# Is kube-proxy running on all nodes?
kubectl get pods -n kube-system -l k8s-app=kube-proxy -o wide

# Check kube-proxy logs for errors
kubectl logs -n kube-system -l k8s-app=kube-proxy --tail=50

# On the node (via kubectl debug or SSH):
kubectl debug node/<node-name> -it --image=ubuntu

# Check iptables rules (might be corrupted)
iptables -L -n -v | head -100
iptables -t nat -L -n | grep <service-name>

# Check if KUBE-SERVICES chain exists
iptables -t nat -L KUBE-SERVICES -n | head -20

# Restart kube-proxy to regenerate rules
kubectl rollout restart daemonset/kube-proxy -n kube-system
```

**Issue:** iptables rules can get corrupted or out-of-sync after node issues.

---

## Step 2: Check Conntrack Table (VERY COMMON!)

```bash
# On the node:
kubectl debug node/<node-name> -it --image=ubuntu

# Check conntrack table usage
cat /proc/sys/net/netfilter/nf_conntrack_count   # Current entries
cat /proc/sys/net/netfilter/nf_conntrack_max     # Maximum allowed

# If count is near max = TABLE FULL = packets dropped!

# Check for conntrack errors in dmesg
dmesg | grep -i "conntrack"
dmesg | grep -i "table full"

# Example output when full:
# "nf_conntrack: table full, dropping packet"
```

**Fix:** Increase conntrack table size:
```bash
# Temporary fix (on node):
sysctl -w net.netfilter.nf_conntrack_max=262144

# Permanent fix: Add to node configuration
# For AKS: Use node configuration profile
```

**Why it happens:**
- High number of short-lived connections
- Many pods with high connection rates
- Connection tracking entries not cleaned up fast enough

---

## Step 3: Check NetworkPolicy Changes

```bash
# List all network policies (including recently added)
kubectl get networkpolicy -A --sort-by='.metadata.creationTimestamp'

# Check if any policy affects the pods
kubectl describe networkpolicy -n <namespace>

# Check specific policy rules
kubectl get networkpolicy <policy-name> -n <namespace> -o yaml

# Test: Temporarily delete suspicious policy
kubectl delete networkpolicy <policy-name> -n <namespace>
# If it works now, policy was the issue!
```

**Common issue:** Someone added a default-deny policy without proper allow rules.

---

## Step 4: Check Cloud/Platform Network Rules

### Azure (AKS)
```bash
# Check NSG rules on AKS subnet
az network nsg rule list -g MC_<rg>_<cluster>_<region> --nsg-name <nsg-name> -o table

# Check if any rules were recently added
az network nsg rule list -g MC_<rg>_<cluster>_<region> --nsg-name <nsg-name> \
  --query "[].{Name:name, Priority:priority, Access:access, Direction:direction}"

# Check UDR (User Defined Routes) - might be routing traffic wrong
az network route-table route list -g <rg> --route-table-name <rt-name> -o table
```

### AWS (EKS)
```bash
# Check security groups
aws ec2 describe-security-groups --group-ids <sg-id>

# Check NACLs
aws ec2 describe-network-acls --network-acl-ids <nacl-id>
```

---

## Step 5: Check CNI Plugin Issues

```bash
# Check CNI pods (Calico/Flannel/Cilium/Azure CNI)
kubectl get pods -n kube-system | grep -E "calico|flannel|cilium|azure-cni"

# Check CNI pod logs
kubectl logs -n kube-system <cni-pod-name> --tail=100

# Check CNI config on node
kubectl debug node/<node-name> -it --image=ubuntu
cat /etc/cni/net.d/*.conf

# For Calico - check felix logs
kubectl logs -n kube-system -l k8s-app=calico-node --tail=50

# Check if CNI is creating routes correctly
ip route show
```

---

## Step 6: Check MTU Mismatch

```bash
# On Pod A - check MTU
kubectl exec <pod-a> -- ip link show eth0

# On Pod B - check MTU
kubectl exec <pod-b> -- ip link show eth0

# Check node MTU
kubectl debug node/<node-name> -it --image=ubuntu
ip link show

# Test with different packet sizes
kubectl exec <pod-a> -- ping -c 3 -M do -s 1400 <pod-b-ip>  # Should work
kubectl exec <pod-a> -- ping -c 3 -M do -s 1500 <pod-b-ip>  # Might fail if MTU mismatch
```

**Issue:** Cloud VPNs, overlay networks, or VXLAN can reduce effective MTU. Large packets get dropped silently.

---

## Step 7: Check Service Mesh (If Using)

```bash
# For Istio
kubectl get pods -n istio-system
kubectl logs -n istio-system -l app=istiod --tail=50

# Check sidecar proxy
kubectl logs <pod-a> -c istio-proxy --tail=50
kubectl logs <pod-b> -c istio-proxy --tail=50

# Check if mTLS is causing issues
istioctl analyze -n <namespace>

# For Linkerd
kubectl get pods -n linkerd
linkerd check
```

---

## Step 8: Advanced Node Network Debug

```bash
# On the problematic node:
kubectl debug node/<node-name> -it --image=nicolaka/netshoot

# Check listening sockets
ss -tulpn

# Check connection states (too many TIME_WAIT?)
ss -s
# State      Recv-Q Send-Q Local:Port Peer:Port
# ESTAB      0      0      ...
# TIME-WAIT  50000  0      ...   ← Too many = port exhaustion

# Check for dropped packets
netstat -s | grep -i drop
netstat -s | grep -i error

# Check network interface errors
ip -s link show

# Check ARP table
arp -n

# Trace the path
traceroute <pod-b-ip>
```

---

## Quick Diagnosis Commands

```bash
# ══════════════════════════════════════════════════════════════════════
# RUN THESE IN ORDER FOR QUICK DIAGNOSIS
# ══════════════════════════════════════════════════════════════════════

# 1. Check service endpoints are populated
kubectl get endpoints <service-b> -n <namespace>

# 2. Check kube-proxy is running
kubectl get pods -n kube-system -l k8s-app=kube-proxy

# 3. Check for network policies
kubectl get networkpolicy -n <namespace>

# 4. Check CNI pods
kubectl get pods -n kube-system | grep -E "calico|flannel|cilium|azure"

# 5. Test direct pod-to-pod (bypass service)
kubectl exec <pod-a> -- curl -v --connect-timeout 5 http://<pod-b-ip>:<port>

# 6. Check conntrack on node (needs node access)
kubectl debug node/<node> -it --image=ubuntu -- \
  sh -c "cat /proc/sys/net/netfilter/nf_conntrack_count; cat /proc/sys/net/netfilter/nf_conntrack_max"

# 7. Check for packet drops
kubectl debug node/<node> -it --image=ubuntu -- \
  sh -c "netstat -s | grep -i drop"
```

---

## Root Cause Summary (When App Is Fine)

| Check | Command | Issue If |
|-------|---------|----------|
| **kube-proxy** | `kubectl get pods -n kube-system -l k8s-app=kube-proxy` | Pods not running/crashing |
| **iptables** | `iptables -t nat -L KUBE-SERVICES` | Rules missing/corrupted |
| **Conntrack** | `cat /proc/sys/net/netfilter/nf_conntrack_count` | Near max limit |
| **NetworkPolicy** | `kubectl get networkpolicy -n <ns>` | New policy blocking |
| **CNI** | `kubectl logs -n kube-system <cni-pod>` | Errors in logs |
| **Cloud NSG** | Check cloud console | New deny rules |
| **MTU** | `ping -M do -s 1400 <ip>` | Large packets fail |
| **Conntrack drops** | `dmesg \| grep conntrack` | "table full" messages |

---

## Most Likely Hidden Causes

1. **Conntrack table full** - Very common in high-traffic clusters
2. **NetworkPolicy added** - By another team/automation
3. **kube-proxy issues** - iptables rules out of sync
4. **Cloud NSG/Firewall** - Platform team changed rules
5. **CNI plugin restart** - Lost network state temporarily
6. **MTU issues** - After VPN/peering changes

---

## Debugging Nodes

```bash
# Node status
kubectl get nodes
kubectl get nodes -o wide

# Node details
kubectl describe node <node-name>

# Check node resources
kubectl top nodes

# Check pods on specific node
kubectl get pods -A --field-selector spec.nodeName=<node-name>

# Cordon/Uncordon (prevent scheduling)
kubectl cordon <node-name>
kubectl uncordon <node-name>

# Drain node (for maintenance)
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
```

---

# NODE TROUBLESHOOTING - Production Deep Dive

## Common Production Node Issues

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PRODUCTION NODE ISSUES                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                │
│  │   DISK       │   │   MEMORY     │   │   CPU        │                │
│  │   PRESSURE   │   │   PRESSURE   │   │   PRESSURE   │                │
│  └──────────────┘   └──────────────┘   └──────────────┘                │
│                                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                │
│  │   NETWORK    │   │   PID        │   │   NODE       │                │
│  │   ISSUES     │   │   PRESSURE   │   │   NOT READY  │                │
│  └──────────────┘   └──────────────┘   └──────────────┘                │
│                                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                │
│  │   KUBELET    │   │   CONTAINER  │   │   CLOCK      │                │
│  │   FAILURES   │   │   RUNTIME    │   │   SKEW       │                │
│  └──────────────┘   └──────────────┘   └──────────────┘                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Node Status Overview

```bash
# ═══════════════════════════════════════════════════════════════════════
# STEP 1: GET NODE STATUS
# ═══════════════════════════════════════════════════════════════════════

# List all nodes with status
kubectl get nodes
# NAME           STATUS     ROLES    AGE   VERSION
# node-1         Ready      <none>   30d   v1.28.0
# node-2         NotReady   <none>   30d   v1.28.0   ← Problem!
# node-3         Ready      <none>   30d   v1.28.0

# Get more details (IP, OS, Container Runtime)
kubectl get nodes -o wide

# Check node conditions
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .status.conditions[*]}{.type}={.status}{"\t"}{end}{"\n"}{end}'

# Node Status Meanings:
# ─────────────────────────────────────────────────────────────────────
# Ready         → Node is healthy and ready to accept pods
# NotReady      → Node has issues (kubelet, network, resources)
# Unknown       → Node controller hasn't heard from node (5+ min)
# SchedulingDisabled → Node is cordoned (no new pods scheduled)
```

---

## Step 2: Check Node Conditions (The Key!)

```bash
# ═══════════════════════════════════════════════════════════════════════
# STEP 2: NODE CONDITIONS - MOST IMPORTANT!
# ═══════════════════════════════════════════════════════════════════════

kubectl describe node <node-name>

# Look for "Conditions" section:
# Conditions:
#   Type                 Status  Reason                       Message
#   ----                 ------  ------                       -------
#   MemoryPressure       False   KubeletHasSufficientMemory   ...
#   DiskPressure         False   KubeletHasNoDiskPressure     ...
#   PIDPressure          False   KubeletHasSufficientPID      ...
#   Ready                True    KubeletReady                 ...

# Get conditions in JSON format
kubectl get node <node-name> -o jsonpath='{.status.conditions[*]}' | jq .

# ┌─────────────────────────────────────────────────────────────────────┐
# │                    NODE CONDITIONS EXPLAINED                         │
# ├──────────────────┬──────────────────────────────────────────────────┤
# │ Condition        │ True = PROBLEM! (except Ready)                   │
# ├──────────────────┼──────────────────────────────────────────────────┤
# │ Ready            │ True = Node is healthy ✓                         │
# │                  │ False = Node has issues ✗                        │
# ├──────────────────┼──────────────────────────────────────────────────┤
# │ MemoryPressure   │ True = Running out of memory!                    │
# │                  │ Kubelet starts evicting pods                     │
# ├──────────────────┼──────────────────────────────────────────────────┤
# │ DiskPressure     │ True = Running out of disk!                      │
# │                  │ Kubelet stops accepting new pods                 │
# ├──────────────────┼──────────────────────────────────────────────────┤
# │ PIDPressure      │ True = Running out of process IDs!               │
# │                  │ Too many processes on node                       │
# ├──────────────────┼──────────────────────────────────────────────────┤
# │ NetworkUnavailable│ True = Network not configured!                  │
# │                  │ CNI plugin issue                                 │
# └──────────────────┴──────────────────────────────────────────────────┘
```

---

## Step 3: Disk Pressure Troubleshooting

```bash
# ═══════════════════════════════════════════════════════════════════════
# DISK PRESSURE - One of the most common production issues!
# ═══════════════════════════════════════════════════════════════════════

# Check if node has DiskPressure
kubectl describe node <node-name> | grep -A 5 "Conditions"

# ─────────────────────────────────────────────────────────────────────
# THRESHOLDS (Default kubelet settings):
# ─────────────────────────────────────────────────────────────────────
# imagefs.available < 15%    → DiskPressure = True
# nodefs.available  < 10%    → DiskPressure = True
# nodefs.inodesFree < 5%     → DiskPressure = True

# ═══════════════════════════════════════════════════════════════════════
# DEBUG ON THE NODE (SSH or kubectl debug)
# ═══════════════════════════════════════════════════════════════════════

# Option 1: SSH to node (if accessible)
ssh user@<node-ip>

# Option 2: Debug container (preferred in K8s)
kubectl debug node/<node-name> -it --image=ubuntu

# ─────────────────────────────────────────────────────────────────────
# DISK INVESTIGATION COMMANDS
# ─────────────────────────────────────────────────────────────────────

# Check overall disk usage
df -h
# Filesystem      Size  Used Avail Use% Mounted on
# /dev/sda1       100G   92G    8G  92% /           ← Problem!
# /dev/sdb1       500G  450G   50G  90% /var/lib/docker

# Check which directories are using space
du -sh /* 2>/dev/null | sort -rh | head -20

# Common culprits:
# /var/lib/docker     → Container images and layers
# /var/lib/containerd → Container runtime data
# /var/lib/kubelet    → Pod volumes, logs
# /var/log            → System and container logs

# ─────────────────────────────────────────────────────────────────────
# FIND LARGE FILES
# ─────────────────────────────────────────────────────────────────────

# Find files larger than 100MB
find / -type f -size +100M 2>/dev/null | head -20

# Check container logs size
du -sh /var/lib/docker/containers/*/

# Check kubelet logs
du -sh /var/log/pods/*/

# ─────────────────────────────────────────────────────────────────────
# CLEANUP ACTIONS
# ─────────────────────────────────────────────────────────────────────

# 1. Clean up unused Docker images (on the node)
docker system prune -a -f
# OR for containerd:
crictl rmi --prune

# 2. Clean up unused containers
docker container prune -f

# 3. Clean old logs
# Rotate and truncate large log files
truncate -s 0 /var/log/syslog
journalctl --vacuum-size=500M

# 4. Check for large emptyDir volumes
du -sh /var/lib/kubelet/pods/*/volumes/kubernetes.io~empty-dir/

# ─────────────────────────────────────────────────────────────────────
# KUBERNETES-LEVEL CLEANUP
# ─────────────────────────────────────────────────────────────────────

# Delete completed/failed pods (they still use disk)
kubectl delete pods --field-selector=status.phase=Succeeded -A
kubectl delete pods --field-selector=status.phase=Failed -A

# Delete old ReplicaSets (keep last 2-3)
kubectl get rs -A | awk '$3 == 0 && $4 == 0 {print $1, $2}' | \
  xargs -r -n2 sh -c 'kubectl delete rs $1 -n $0'

# Force garbage collection of images
kubectl patch node <node-name> -p '{"metadata":{"annotations":{"node.kubernetes.io/garbage-collect":"true"}}}'
```

---

## Step 4: Memory Pressure Troubleshooting

```bash
# ═══════════════════════════════════════════════════════════════════════
# MEMORY PRESSURE - Pods getting evicted!
# ═══════════════════════════════════════════════════════════════════════

# Check if node has MemoryPressure
kubectl describe node <node-name> | grep -A 1 "MemoryPressure"

# ─────────────────────────────────────────────────────────────────────
# THRESHOLDS (Default):
# ─────────────────────────────────────────────────────────────────────
# memory.available < 100Mi   → MemoryPressure = True (eviction starts)

# ═══════════════════════════════════════════════════════════════════════
# CHECK NODE MEMORY USAGE
# ═══════════════════════════════════════════════════════════════════════

# Kubernetes level - allocatable vs requested
kubectl describe node <node-name> | grep -A 10 "Allocated resources"
# Allocated resources:
#   Resource           Requests     Limits
#   --------           --------     ------
#   cpu                2100m (52%)  4000m (100%)
#   memory             3Gi (75%)    8Gi (200%)   ← Over-committed!

# ─────────────────────────────────────────────────────────────────────
# ON THE NODE
# ─────────────────────────────────────────────────────────────────────

# Check memory usage
free -h
#               total        used        free      shared  buff/cache   available
# Mem:           16Gi        14Gi       500Mi       100Mi        1.5Gi       1.5Gi
#                            ^^^^                                            ^^^^
#                         High usage!                                    Low available!

# Check memory usage over time
vmstat 1 5

# Find memory-hungry processes
ps aux --sort=-%mem | head -20

# Check for OOM killer activity
dmesg | grep -i "out of memory"
dmesg | grep -i "oom"
journalctl -k | grep -i "oom"

# ─────────────────────────────────────────────────────────────────────
# IDENTIFY MEMORY-HUNGRY PODS
# ─────────────────────────────────────────────────────────────────────

# Check pod memory usage on the node
kubectl top pods -A --sort-by=memory | head -20

# Check pods on specific node
kubectl get pods -A -o wide --field-selector spec.nodeName=<node-name>
kubectl top pods -A | grep -E "$(kubectl get pods -A -o wide --field-selector spec.nodeName=<node-name> --no-headers | awk '{print $2}' | paste -sd'|')"

# Check for pods without memory limits (dangerous!)
kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.containers[*].resources.limits.memory}{"\n"}{end}' | grep -v "Gi\|Mi"

# ─────────────────────────────────────────────────────────────────────
# IMMEDIATE RELIEF ACTIONS
# ─────────────────────────────────────────────────────────────────────

# 1. Evict non-critical pods manually
kubectl delete pod <pod-name> -n <namespace>

# 2. Cordon node to prevent new pods
kubectl cordon <node-name>

# 3. Drain node (move all pods away)
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# ─────────────────────────────────────────────────────────────────────
# LONG-TERM FIXES
# ─────────────────────────────────────────────────────────────────────

# 1. Set memory requests and limits on ALL pods
resources:
  requests:
    memory: "256Mi"
  limits:
    memory: "512Mi"

# 2. Add more nodes (scale cluster)
# For AKS:
az aks scale -g <rg> -n <cluster> --node-count 5

# 3. Use bigger VMs
# For AKS:
az aks nodepool update -g <rg> --cluster-name <cluster> -n <nodepool> \
  --node-vm-size Standard_D4s_v3

# 4. Implement ResourceQuotas per namespace
kubectl create quota mem-quota -n <namespace> --hard=requests.memory=4Gi,limits.memory=8Gi
```

---

## Step 5: CPU Pressure Troubleshooting

```bash
# ═══════════════════════════════════════════════════════════════════════
# CPU PRESSURE - Pods getting throttled!
# ═══════════════════════════════════════════════════════════════════════

# Note: Kubernetes doesn't have a "CPUPressure" condition by default
# But CPU issues cause pod throttling and slow performance

# ─────────────────────────────────────────────────────────────────────
# CHECK CPU USAGE
# ─────────────────────────────────────────────────────────────────────

# Kubernetes level
kubectl top nodes
# NAME     CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
# node-1   3800m        95%    12000Mi         75%    ← High CPU!

kubectl describe node <node-name> | grep -A 10 "Allocated resources"
# cpu                3500m (87%)  8000m (200%)   ← Over-committed!

# ─────────────────────────────────────────────────────────────────────
# ON THE NODE
# ─────────────────────────────────────────────────────────────────────

# Check CPU usage
top -bn1 | head -20

# Check load average
uptime
# 14:30:01 up 30 days,  load average: 8.50, 8.20, 7.90
#                                     ^^^^
#               Load > number of CPUs = overloaded

# Find CPU-hungry processes
ps aux --sort=-%cpu | head -20

# Check for CPU throttling in cgroups
cat /sys/fs/cgroup/cpu/kubepods/cpu.stat
# nr_throttled 12345   ← Number of times throttled
# throttled_time 98765 ← Time spent throttled (ns)

# ─────────────────────────────────────────────────────────────────────
# IDENTIFY CPU-HUNGRY PODS
# ─────────────────────────────────────────────────────────────────────

# Check pod CPU usage
kubectl top pods -A --sort-by=cpu | head -20

# Check pods without CPU limits
kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.containers[*].resources.limits.cpu}{"\n"}{end}' | grep -E "^\s*$"

# ─────────────────────────────────────────────────────────────────────
# FIXES
# ─────────────────────────────────────────────────────────────────────

# 1. Set CPU requests and limits
resources:
  requests:
    cpu: "250m"
  limits:
    cpu: "500m"

# 2. Use Horizontal Pod Autoscaler
kubectl autoscale deployment <name> --cpu-percent=70 --min=2 --max=10

# 3. Check if pods are doing unnecessary work
kubectl logs <pod-name> -f
```

---

## Step 6: PID Pressure Troubleshooting

```bash
# ═══════════════════════════════════════════════════════════════════════
# PID PRESSURE - Too many processes!
# ═══════════════════════════════════════════════════════════════════════

# Check if node has PIDPressure
kubectl describe node <node-name> | grep -A 1 "PIDPressure"

# ─────────────────────────────────────────────────────────────────────
# ON THE NODE
# ─────────────────────────────────────────────────────────────────────

# Check current PID usage
cat /proc/sys/kernel/pid_max          # Maximum PIDs allowed
cat /proc/loadavg | awk '{print $4}'  # Running/Total processes

# Count total processes
ps aux | wc -l

# Find processes by pod/container
ps aux | grep -E "pause|containerd"

# Check which container has most processes
for i in $(crictl ps -q); do
  echo -n "$i: "
  crictl inspect $i | jq -r '.info.pid' | xargs -I{} sh -c 'ls /proc/{}/task 2>/dev/null | wc -l'
done

# ─────────────────────────────────────────────────────────────────────
# FIXES
# ─────────────────────────────────────────────────────────────────────

# 1. Find and fix fork-bomb or runaway process pods
# 2. Set PID limits in pod spec (Kubernetes 1.20+)
spec:
  containers:
  - name: app
    resources:
      limits:
        pid: "100"  # Max 100 processes per container
```

---

## Step 7: Node NotReady Troubleshooting

```bash
# ═══════════════════════════════════════════════════════════════════════
# NODE NOTREADY - Node is unhealthy!
# ═══════════════════════════════════════════════════════════════════════

# Common reasons:
# 1. Kubelet not running
# 2. Container runtime (Docker/containerd) crashed
# 3. Network issues (can't reach API server)
# 4. Resource exhaustion (disk, memory)
# 5. Node rebooted or crashed

# ─────────────────────────────────────────────────────────────────────
# STEP-BY-STEP DIAGNOSIS
# ─────────────────────────────────────────────────────────────────────

# 1. Check node events
kubectl describe node <node-name> | tail -30

# 2. Check when node became NotReady
kubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type=="Ready")]}'

# 3. SSH to node (if possible) or use cloud console

# ─────────────────────────────────────────────────────────────────────
# ON THE NODE - Check services
# ─────────────────────────────────────────────────────────────────────

# Check kubelet status
systemctl status kubelet
journalctl -u kubelet -f --no-pager | tail -50

# Common kubelet issues:
# - Certificate expired
# - Can't reach API server
# - Disk pressure
# - Memory pressure

# Check container runtime
systemctl status containerd
# OR
systemctl status docker
journalctl -u containerd -f --no-pager | tail -50

# Check if kubelet can reach API server
curl -k https://<api-server>:6443/healthz

# ─────────────────────────────────────────────────────────────────────
# RESTART SERVICES
# ─────────────────────────────────────────────────────────────────────

# Restart kubelet
sudo systemctl restart kubelet

# Restart container runtime
sudo systemctl restart containerd
# OR
sudo systemctl restart docker

# ─────────────────────────────────────────────────────────────────────
# CHECK SYSTEM LOGS
# ─────────────────────────────────────────────────────────────────────

# General system logs
journalctl -xe --no-pager | tail -100
dmesg | tail -50

# Check for kernel panics or hardware issues
dmesg | grep -i "error\|fail\|warn"
```

---

## Step 8: Network Issues on Node

```bash
# ═══════════════════════════════════════════════════════════════════════
# NETWORK ISSUES - Pods can't communicate!
# ═══════════════════════════════════════════════════════════════════════

# Check NetworkUnavailable condition
kubectl describe node <node-name> | grep -A 1 "NetworkUnavailable"

# ─────────────────────────────────────────────────────────────────────
# CNI TROUBLESHOOTING
# ─────────────────────────────────────────────────────────────────────

# Check CNI pods (usually in kube-system)
kubectl get pods -n kube-system | grep -E "calico|flannel|weave|cilium|azure-cni"

# Check CNI pod logs
kubectl logs -n kube-system <cni-pod-name>

# ─────────────────────────────────────────────────────────────────────
# ON THE NODE
# ─────────────────────────────────────────────────────────────────────

# Check network interfaces
ip addr
ip link

# Check routing table
ip route

# Check iptables rules
iptables -L -n -v | head -50

# Test connectivity to API server
curl -k https://<api-server>:6443/healthz

# Test DNS resolution
nslookup kubernetes.default.svc.cluster.local

# Check CNI configuration
ls -la /etc/cni/net.d/
cat /etc/cni/net.d/*.conf

# Check CNI binaries
ls -la /opt/cni/bin/

# ─────────────────────────────────────────────────────────────────────
# FIXES
# ─────────────────────────────────────────────────────────────────────

# 1. Restart CNI pods
kubectl delete pod -n kube-system <cni-pod-name>

# 2. Restart kubelet (it re-initializes CNI)
sudo systemctl restart kubelet

# 3. Check if CNI is correctly installed
# For Azure CNI in AKS - usually managed automatically
```

---

## Step 9: Node Debugging Commands Cheat Sheet

```bash
# ═══════════════════════════════════════════════════════════════════════
#                    NODE DEBUG CHEAT SHEET
# ═══════════════════════════════════════════════════════════════════════

# ┌─────────────────────────────────────────────────────────────────────┐
# │ KUBECTL COMMANDS                                                     │
# ├─────────────────────────────────────────────────────────────────────┤

kubectl get nodes                                    # List nodes
kubectl get nodes -o wide                            # With IPs and OS
kubectl describe node <node>                         # Full details
kubectl top node                                     # Resource usage
kubectl top node <node>                              # Specific node
kubectl get events --field-selector involvedObject.kind=Node

# Get node conditions in one line
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}: {range .status.conditions[*]}{.type}={.status} {end}{"\n"}{end}'

# Get pods on specific node
kubectl get pods -A --field-selector spec.nodeName=<node>

# Cordon (no new pods)
kubectl cordon <node>

# Uncordon (allow pods again)
kubectl uncordon <node>

# Drain (move pods away)
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data

# Debug node with ephemeral container
kubectl debug node/<node> -it --image=busybox
kubectl debug node/<node> -it --image=nicolaka/netshoot

# ┌─────────────────────────────────────────────────────────────────────┐
# │ ON-NODE COMMANDS (via SSH or kubectl debug)                          │
# ├─────────────────────────────────────────────────────────────────────┤

# ═══ DISK ═══
df -h                                    # Disk usage
du -sh /* 2>/dev/null | sort -rh         # Directory sizes
find / -type f -size +100M 2>/dev/null   # Large files
docker system prune -a -f                # Clean Docker
crictl rmi --prune                       # Clean containerd images

# ═══ MEMORY ═══
free -h                                  # Memory usage
vmstat 1 5                               # Memory stats
ps aux --sort=-%mem | head -20           # Memory hogs
dmesg | grep -i "oom"                    # OOM killer

# ═══ CPU ═══
top -bn1 | head -20                      # CPU usage
uptime                                   # Load average
ps aux --sort=-%cpu | head -20           # CPU hogs

# ═══ NETWORK ═══
ip addr                                  # Network interfaces
ip route                                 # Routing table
netstat -tulpn                           # Listening ports
ss -tulpn                                # Listening ports (modern)

# ═══ SERVICES ═══
systemctl status kubelet                 # Kubelet status
systemctl status containerd              # Container runtime
journalctl -u kubelet --no-pager | tail  # Kubelet logs
journalctl -u containerd --no-pager | tail # Containerd logs

# ═══ SYSTEM ═══
dmesg | tail -50                         # Kernel messages
journalctl -xe --no-pager | tail         # System logs
cat /etc/os-release                      # OS version
uname -a                                 # Kernel version
```

---

## Node Issue Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    NODE TROUBLESHOOTING FLOWCHART                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  kubectl get nodes                                                       │
│         │                                                                │
│         ▼                                                                │
│  ┌──────────────────┐                                                   │
│  │ Node Status?     │                                                   │
│  └──────────────────┘                                                   │
│         │                                                                │
│    ┌────┴────────────────────┐                                          │
│    ▼                         ▼                                          │
│  Ready                    NotReady/Unknown                              │
│    │                         │                                          │
│    ▼                         ▼                                          │
│  kubectl describe node    Check:                                        │
│  Check conditions:        1. SSH to node                                │
│    │                      2. systemctl status kubelet                   │
│    │                      3. systemctl status containerd                │
│    │                      4. journalctl -u kubelet                      │
│    │                                                                    │
│    ├── DiskPressure=True ──► df -h, clean up disk                      │
│    │                         du -sh /*, docker prune                    │
│    │                                                                    │
│    ├── MemoryPressure=True ► free -h, find memory hogs                 │
│    │                         kubectl top pods, add limits               │
│    │                                                                    │
│    ├── PIDPressure=True ───► ps aux | wc -l                            │
│    │                         Find runaway process                       │
│    │                                                                    │
│    └── NetworkUnavailable ─► Check CNI pods                            │
│                              ip addr, ip route                          │
│                              Restart CNI/kubelet                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## AKS-Specific Node Troubleshooting

```bash
# ═══════════════════════════════════════════════════════════════════════
# AZURE AKS NODE TROUBLESHOOTING
# ═══════════════════════════════════════════════════════════════════════

# Check node pool status
az aks nodepool list -g <resource-group> --cluster-name <cluster> -o table

# Check node health in Azure
az aks show -g <resource-group> -n <cluster> --query "agentPoolProfiles[].{Name:name,Count:count,VMSize:vmSize,PowerState:powerState}"

# Get AKS node resource ID
kubectl get node <node-name> -o jsonpath='{.spec.providerID}'

# SSH to AKS node (via debug pod)
kubectl debug node/<node-name> -it --image=mcr.microsoft.com/cbl-mariner/busybox:2.0

# OR use AKS SSH access (requires configuration)
az aks command invoke -g <resource-group> -n <cluster> --command "ls /"

# Check AKS diagnostics
az aks get-credentials -g <resource-group> -n <cluster>
kubectl get events --sort-by='.lastTimestamp' -A | tail -50

# Scale node pool (add more nodes)
az aks nodepool scale -g <resource-group> --cluster-name <cluster> -n <nodepool> -c 5

# Upgrade node image (for security patches)
az aks nodepool upgrade -g <resource-group> --cluster-name <cluster> -n <nodepool> --node-image-only

# Restart nodes in nodepool (rolling restart)
az aks nodepool upgrade -g <resource-group> --cluster-name <cluster> -n <nodepool>

# Check VMSS (Virtual Machine Scale Set) behind AKS
az vmss list-instances -g MC_<resource-group>_<cluster>_<region> -n <vmss-name> -o table
```

---

## Resource Debugging

```bash
# Check resource usage
kubectl top pods
kubectl top pods --containers
kubectl top nodes

# Check resource requests/limits
kubectl describe pod <pod-name> | grep -A5 "Limits\|Requests"

# Check events cluster-wide
kubectl get events --sort-by=.lastTimestamp
kubectl get events -n production --sort-by=.lastTimestamp

# Check for OOMKilled
kubectl get pods -o jsonpath='{.items[*].status.containerStatuses[*].lastState.terminated.reason}'
```

---

## Quick Debug Cheat Sheet

```
┌─────────────────────────────────────────────────────────────────┐
│                    POD DEBUGGING FLOWCHART                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  kubectl get pods                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │ Pod Status?  │                                               │
│  └──────────────┘                                               │
│         │                                                        │
│    ┌────┴────┬─────────┬──────────────┐                        │
│    ▼         ▼         ▼              ▼                         │
│ Pending  ImagePull  CrashLoop    Running                        │
│    │     BackOff    BackOff      but errors                     │
│    │         │         │              │                         │
│    ▼         ▼         ▼              ▼                         │
│ describe  describe   logs         logs -f                       │
│ pod       pod        --previous   exec -it                      │
│ (events)  (events)                                              │
│    │         │         │              │                         │
│    ▼         ▼         ▼              ▼                         │
│ Check:    Check:    Check:        Check:                        │
│ -Resources -Image   -App crash   -App errors                    │
│ -Taints   -Registry -Exit code   -Connectivity                  │
│ -Selector -Secret   -Startup     -Config                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

# 4. AZ CLI - Azure Operations

## Authentication & Subscription

```bash
# Login (browser popup)
az login

# Login with service principal (CI/CD)
az login --service-principal -u <app-id> -p <password> --tenant <tenant-id>

# Login with managed identity (Azure VMs/AKS)
az login --identity

# Check current account
az account show

# List all subscriptions
az account list -o table

# Switch subscription
az account set --subscription "<subscription-name-or-id>"

# Verify switch
az account show --query name -o tsv
```

---

## Resource Groups

```bash
# List resource groups
az group list -o table

# Create resource group
az group create --name myResourceGroup --location eastus

# Delete resource group
az group delete --name myResourceGroup --yes --no-wait

# Check resources in group
az resource list --resource-group myResourceGroup -o table
```

---

## Virtual Machines

```bash
# List VMs
az vm list -o table

# Create VM (basic)
az vm create \
  --resource-group myResourceGroup \
  --name myVM \
  --image Ubuntu2204 \
  --admin-username azureuser \
  --generate-ssh-keys \
  --size Standard_B2s

# Create VM (production-grade)
az vm create \
  --resource-group myResourceGroup \
  --name myVM \
  --image Ubuntu2204 \
  --admin-username azureuser \
  --ssh-key-value ~/.ssh/id_rsa.pub \
  --size Standard_D2s_v3 \
  --vnet-name myVNet \
  --subnet mySubnet \
  --public-ip-address "" \
  --nsg myNSG \
  --storage-sku Premium_LRS

# Start/Stop/Restart VM
az vm start --resource-group myResourceGroup --name myVM
az vm stop --resource-group myResourceGroup --name myVM
az vm restart --resource-group myResourceGroup --name myVM

# Deallocate (stop billing)
az vm deallocate --resource-group myResourceGroup --name myVM

# Get VM IP
az vm list-ip-addresses --name myVM -o table

# SSH into VM
ssh azureuser@<public-ip>

# Delete VM
az vm delete --resource-group myResourceGroup --name myVM --yes
```

---

## AKS Cluster

```bash
# List AKS clusters
az aks list -o table

# Create AKS cluster (basic)
az aks create \
  --resource-group myResourceGroup \
  --name myAKSCluster \
  --node-count 3 \
  --generate-ssh-keys

# Create AKS cluster (production-grade)
az aks create \
  --resource-group myResourceGroup \
  --name myAKSCluster \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-managed-identity \
  --network-plugin azure \
  --network-policy azure \
  --vnet-subnet-id /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/<vnet>/subnets/<subnet> \
  --enable-cluster-autoscaler \
  --min-count 3 \
  --max-count 10 \
  --enable-addons monitoring \
  --zones 1 2 3

# Get credentials (configure kubectl)
az aks get-credentials --resource-group myResourceGroup --name myAKSCluster

# Get credentials (admin, for RBAC issues)
az aks get-credentials --resource-group myResourceGroup --name myAKSCluster --admin

# Scale cluster
az aks scale --resource-group myResourceGroup --name myAKSCluster --node-count 5

# Upgrade cluster
az aks get-upgrades --resource-group myResourceGroup --name myAKSCluster -o table
az aks upgrade --resource-group myResourceGroup --name myAKSCluster --kubernetes-version 1.28.0

# Start/Stop cluster (dev/test cost saving)
az aks stop --resource-group myResourceGroup --name myAKSCluster
az aks start --resource-group myResourceGroup --name myAKSCluster

# Delete cluster
az aks delete --resource-group myResourceGroup --name myAKSCluster --yes --no-wait
```

---

## AZ CLI Troubleshooting

```bash
# Check CLI version
az version

# Upgrade CLI
az upgrade

# Clear cache
az cache purge

# Enable debug output
az <command> --debug

# Output formats
az vm list -o table          # Table (human readable)
az vm list -o json           # JSON (scripting)
az vm list -o yaml           # YAML
az vm list -o tsv            # Tab-separated (scripting)

# Query specific fields (JMESPath)
az vm list --query "[].{Name:name, RG:resourceGroup, Size:hardwareProfile.vmSize}" -o table

# Check what's available in region
az vm list-sizes --location eastus -o table
az aks get-versions --location eastus -o table
```

---

# 5. TERRAFORM - Complete Guide

## Terraform Workflow

```bash
# 1. Initialize (download providers)
terraform init

# 2. Format code
terraform fmt

# 3. Validate syntax
terraform validate

# 4. Plan (preview changes)
terraform plan
terraform plan -out=tfplan            # Save plan

# 5. Apply (create/update resources)
terraform apply
terraform apply tfplan                 # Apply saved plan
terraform apply -auto-approve          # Skip confirmation (CI/CD)

# 6. Destroy (delete resources)
terraform destroy
terraform destroy -auto-approve
```

---

## Terraform File Structure

```
my-infrastructure/
├── main.tf                 # Main resources
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── providers.tf            # Provider configuration
├── terraform.tfvars        # Variable values (don't commit secrets!)
├── backend.tf              # Remote state configuration
└── modules/                # Reusable modules
    └── aks/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

---

## Basic Terraform Example (Azure)

**providers.tf:**
```hcl
terraform {
  required_version = ">= 1.0.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  
  # Remote state (production)
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "tfstatestore123"
    container_name       = "tfstate"
    key                  = "prod.terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}
```

**variables.tf:**
```hcl
variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "my-rg"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "environment" {
  description = "Environment name"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "tags" {
  description = "Tags for resources"
  type        = map(string)
  default = {
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}
```

**main.tf:**
```hcl
# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# AKS Cluster
resource "azurerm_kubernetes_cluster" "main" {
  name                = "my-aks-cluster"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = "myaks"
  kubernetes_version  = "1.28.0"

  default_node_pool {
    name                = "default"
    node_count          = 3
    vm_size             = "Standard_D2s_v3"
    enable_auto_scaling = true
    min_count           = 3
    max_count           = 10
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin = "azure"
    network_policy = "azure"
  }

  tags = var.tags
}
```

**outputs.tf:**
```hcl
output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.main.name
}

output "kube_config" {
  value     = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive = true
}
```

---

## Terraform Troubleshooting

```bash
# Debug mode
TF_LOG=DEBUG terraform apply

# Check state
terraform state list
terraform state show azurerm_kubernetes_cluster.main

# Remove resource from state (without deleting)
terraform state rm azurerm_resource_group.main

# Import existing resource
terraform import azurerm_resource_group.main /subscriptions/<sub>/resourceGroups/<name>

# Refresh state (sync with actual resources)
terraform refresh

# Unlock state (if stuck)
terraform force-unlock <lock-id>

# Target specific resource
terraform apply -target=azurerm_kubernetes_cluster.main

# Replace resource (force recreate)
terraform apply -replace=azurerm_kubernetes_cluster.main
```

---

## Common Terraform Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Error acquiring state lock` | Another process has lock | Wait or `force-unlock` |
| `Provider not found` | Missing provider | `terraform init` |
| `Resource already exists` | Resource exists but not in state | `terraform import` |
| `Cycle detected` | Circular dependency | Review resource dependencies |
| `Invalid count argument` | Count depends on unknown | Use `depends_on` or target |

---

# 6. AZURE DEVOPS YAML - CI/CD Pipelines

## Pipeline File Location

```
.azure-pipelines/
├── azure-pipelines.yml      # Main pipeline
├── templates/
│   ├── build.yml            # Reusable build template
│   └── deploy.yml           # Reusable deploy template
└── variables/
    ├── dev.yml              # Dev variables
    └── prod.yml             # Prod variables
```

---

## Basic CI Pipeline (Build)

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main
      - develop
  paths:
    include:
      - src/*
    exclude:
      - docs/*

pool:
  vmImage: 'ubuntu-latest'

variables:
  - name: buildConfiguration
    value: 'Release'
  - name: dockerRegistry
    value: 'myacr.azurecr.io'

stages:
  - stage: Build
    displayName: 'Build Stage'
    jobs:
      - job: BuildJob
        displayName: 'Build and Test'
        steps:
          - task: UseDotNet@2
            displayName: 'Use .NET 8'
            inputs:
              version: '8.x'

          - script: |
              dotnet restore
              dotnet build --configuration $(buildConfiguration)
              dotnet test --no-build --verbosity normal
            displayName: 'Build and Test'

          - task: Docker@2
            displayName: 'Build Docker Image'
            inputs:
              containerRegistry: 'myACRConnection'
              repository: 'myapp'
              command: 'buildAndPush'
              Dockerfile: '**/Dockerfile'
              tags: |
                $(Build.BuildId)
                latest
```

---

## Complete CI/CD Pipeline

```yaml
trigger:
  - main

pr:
  - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: 'my-variable-group'
  - name: imageRepository
    value: 'myapp'
  - name: dockerfilePath
    value: '$(Build.SourcesDirectory)/Dockerfile'
  - name: tag
    value: '$(Build.BuildId)'

stages:
  # ============ BUILD STAGE ============
  - stage: Build
    displayName: 'Build'
    jobs:
      - job: Build
        steps:
          - task: Docker@2
            displayName: 'Build and Push'
            inputs:
              containerRegistry: 'acr-connection'
              repository: '$(imageRepository)'
              command: 'buildAndPush'
              Dockerfile: '$(dockerfilePath)'
              tags: |
                $(tag)
                latest

          - publish: $(Build.SourcesDirectory)/k8s
            artifact: manifests
            displayName: 'Publish K8s Manifests'

  # ============ DEPLOY TO DEV ============
  - stage: DeployDev
    displayName: 'Deploy to Dev'
    dependsOn: Build
    condition: succeeded()
    jobs:
      - deployment: DeployDev
        displayName: 'Deploy to Dev'
        environment: 'dev'
        strategy:
          runOnce:
            deploy:
              steps:
                - download: current
                  artifact: manifests

                - task: KubernetesManifest@0
                  displayName: 'Deploy to AKS'
                  inputs:
                    action: 'deploy'
                    kubernetesServiceConnection: 'aks-dev-connection'
                    namespace: 'dev'
                    manifests: |
                      $(Pipeline.Workspace)/manifests/deployment.yaml
                      $(Pipeline.Workspace)/manifests/service.yaml
                    containers: |
                      $(containerRegistry)/$(imageRepository):$(tag)

  # ============ DEPLOY TO PROD ============
  - stage: DeployProd
    displayName: 'Deploy to Production'
    dependsOn: DeployDev
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployProd
        displayName: 'Deploy to Prod'
        environment: 'production'    # Requires approval in Azure DevOps
        strategy:
          runOnce:
            deploy:
              steps:
                - download: current
                  artifact: manifests

                - task: HelmDeploy@0
                  displayName: 'Helm Upgrade'
                  inputs:
                    connectionType: 'Kubernetes Service Connection'
                    kubernetesServiceConnection: 'aks-prod-connection'
                    namespace: 'production'
                    command: 'upgrade'
                    chartType: 'FilePath'
                    chartPath: '$(Pipeline.Workspace)/manifests/helm-chart'
                    releaseName: 'myapp'
                    overrideValues: 'image.tag=$(tag)'
                    install: true
                    waitForExecution: true
```

---

## Pipeline Templates (Reusable)

**templates/build.yml:**
```yaml
parameters:
  - name: dockerRegistry
    type: string
  - name: repository
    type: string
  - name: dockerfile
    type: string
    default: 'Dockerfile'

steps:
  - task: Docker@2
    displayName: 'Build and Push Docker Image'
    inputs:
      containerRegistry: ${{ parameters.dockerRegistry }}
      repository: ${{ parameters.repository }}
      command: 'buildAndPush'
      Dockerfile: ${{ parameters.dockerfile }}
      tags: |
        $(Build.BuildId)
        latest
```

**Using template:**
```yaml
stages:
  - stage: Build
    jobs:
      - job: Build
        steps:
          - template: templates/build.yml
            parameters:
              dockerRegistry: 'myACR'
              repository: 'myapp'
```

---

## Pipeline Troubleshooting

| Issue | Check | Fix |
|-------|-------|-----|
| **Service connection failed** | Project Settings → Service Connections | Verify credentials, re-authorize |
| **Variable not found** | Variables tab or Variable Groups | Check scope, link variable group |
| **Approval stuck** | Environments → Approvals | Check approvers, timeout settings |
| **Agent not available** | Agent pools | Check agent status, use hosted |
| **Artifact not found** | Publish/Download tasks | Ensure same artifact name |

---

# 7. ARM TEMPLATES - Azure Resource Manager

## ARM Template Structure

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": { },          // Input values
  "variables": { },           // Computed values
  "resources": [ ],           // Resources to deploy
  "outputs": { }              // Return values
}
```

---

## Complete ARM Template Example

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  
  "parameters": {
    "vmName": {
      "type": "string",
      "metadata": {
        "description": "Name of the virtual machine"
      }
    },
    "adminUsername": {
      "type": "string",
      "metadata": {
        "description": "Admin username"
      }
    },
    "adminPassword": {
      "type": "securestring",
      "metadata": {
        "description": "Admin password"
      }
    },
    "vmSize": {
      "type": "string",
      "defaultValue": "Standard_D2s_v3",
      "allowedValues": [
        "Standard_B2s",
        "Standard_D2s_v3",
        "Standard_D4s_v3"
      ]
    },
    "location": {
      "type": "string",
      "defaultValue": "[resourceGroup().location]"
    }
  },
  
  "variables": {
    "vnetName": "[concat(parameters('vmName'), '-vnet')]",
    "subnetName": "default",
    "nicName": "[concat(parameters('vmName'), '-nic')]",
    "publicIPName": "[concat(parameters('vmName'), '-pip')]",
    "nsgName": "[concat(parameters('vmName'), '-nsg')]"
  },
  
  "resources": [
    {
      "type": "Microsoft.Network/networkSecurityGroups",
      "apiVersion": "2021-02-01",
      "name": "[variables('nsgName')]",
      "location": "[parameters('location')]",
      "properties": {
        "securityRules": [
          {
            "name": "SSH",
            "properties": {
              "priority": 1000,
              "protocol": "Tcp",
              "access": "Allow",
              "direction": "Inbound",
              "sourceAddressPrefix": "*",
              "sourcePortRange": "*",
              "destinationAddressPrefix": "*",
              "destinationPortRange": "22"
            }
          }
        ]
      }
    },
    {
      "type": "Microsoft.Network/publicIPAddresses",
      "apiVersion": "2021-02-01",
      "name": "[variables('publicIPName')]",
      "location": "[parameters('location')]",
      "sku": {
        "name": "Standard"
      },
      "properties": {
        "publicIPAllocationMethod": "Static"
      }
    },
    {
      "type": "Microsoft.Network/virtualNetworks",
      "apiVersion": "2021-02-01",
      "name": "[variables('vnetName')]",
      "location": "[parameters('location')]",
      "properties": {
        "addressSpace": {
          "addressPrefixes": ["10.0.0.0/16"]
        },
        "subnets": [
          {
            "name": "[variables('subnetName')]",
            "properties": {
              "addressPrefix": "10.0.0.0/24",
              "networkSecurityGroup": {
                "id": "[resourceId('Microsoft.Network/networkSecurityGroups', variables('nsgName'))]"
              }
            }
          }
        ]
      },
      "dependsOn": [
        "[resourceId('Microsoft.Network/networkSecurityGroups', variables('nsgName'))]"
      ]
    },
    {
      "type": "Microsoft.Network/networkInterfaces",
      "apiVersion": "2021-02-01",
      "name": "[variables('nicName')]",
      "location": "[parameters('location')]",
      "properties": {
        "ipConfigurations": [
          {
            "name": "ipconfig1",
            "properties": {
              "privateIPAllocationMethod": "Dynamic",
              "publicIPAddress": {
                "id": "[resourceId('Microsoft.Network/publicIPAddresses', variables('publicIPName'))]"
              },
              "subnet": {
                "id": "[resourceId('Microsoft.Network/virtualNetworks/subnets', variables('vnetName'), variables('subnetName'))]"
              }
            }
          }
        ]
      },
      "dependsOn": [
        "[resourceId('Microsoft.Network/publicIPAddresses', variables('publicIPName'))]",
        "[resourceId('Microsoft.Network/virtualNetworks', variables('vnetName'))]"
      ]
    },
    {
      "type": "Microsoft.Compute/virtualMachines",
      "apiVersion": "2021-03-01",
      "name": "[parameters('vmName')]",
      "location": "[parameters('location')]",
      "properties": {
        "hardwareProfile": {
          "vmSize": "[parameters('vmSize')]"
        },
        "osProfile": {
          "computerName": "[parameters('vmName')]",
          "adminUsername": "[parameters('adminUsername')]",
          "adminPassword": "[parameters('adminPassword')]"
        },
        "storageProfile": {
          "imageReference": {
            "publisher": "Canonical",
            "offer": "0001-com-ubuntu-server-jammy",
            "sku": "22_04-lts-gen2",
            "version": "latest"
          },
          "osDisk": {
            "createOption": "FromImage",
            "managedDisk": {
              "storageAccountType": "Premium_LRS"
            }
          }
        },
        "networkProfile": {
          "networkInterfaces": [
            {
              "id": "[resourceId('Microsoft.Network/networkInterfaces', variables('nicName'))]"
            }
          ]
        }
      },
      "dependsOn": [
        "[resourceId('Microsoft.Network/networkInterfaces', variables('nicName'))]"
      ]
    }
  ],
  
  "outputs": {
    "vmId": {
      "type": "string",
      "value": "[resourceId('Microsoft.Compute/virtualMachines', parameters('vmName'))]"
    },
    "publicIP": {
      "type": "string",
      "value": "[reference(resourceId('Microsoft.Network/publicIPAddresses', variables('publicIPName'))).ipAddress]"
    }
  }
}
```

---

## Deploy ARM Templates

```bash
# Validate template
az deployment group validate \
  --resource-group myResourceGroup \
  --template-file template.json \
  --parameters parameters.json

# Deploy template
az deployment group create \
  --resource-group myResourceGroup \
  --template-file template.json \
  --parameters parameters.json

# Deploy with inline parameters
az deployment group create \
  --resource-group myResourceGroup \
  --template-file template.json \
  --parameters vmName=myVM adminUsername=azureuser

# What-if (preview changes)
az deployment group what-if \
  --resource-group myResourceGroup \
  --template-file template.json \
  --parameters parameters.json

# Check deployment status
az deployment group list --resource-group myResourceGroup -o table
az deployment group show --resource-group myResourceGroup --name <deployment-name>
```

---

## ARM Template Functions

| Function | Example | Description |
|----------|---------|-------------|
| `concat()` | `[concat(var1, '-', var2)]` | Concatenate strings |
| `resourceId()` | `[resourceId('Microsoft.Network/...', name)]` | Get resource ID |
| `reference()` | `[reference(resourceId(...)).property]` | Get resource property |
| `resourceGroup()` | `[resourceGroup().location]` | Get RG properties |
| `subscription()` | `[subscription().subscriptionId]` | Get subscription info |
| `parameters()` | `[parameters('vmName')]` | Get parameter value |
| `variables()` | `[variables('nicName')]` | Get variable value |

---

# COMPREHENSIVE PRODUCTION TROUBLESHOOTING GUIDE

---

## 1. Deployment Failures

### Common Deployment Failure Reasons

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT FAILURE CAUSES                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │ Image Pull       │  │ Resource         │  │ Probe            │      │
│  │ Failures         │  │ Constraints      │  │ Failures         │      │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘      │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │ Config/Secret    │  │ PVC Binding      │  │ Node             │      │
│  │ Missing          │  │ Issues           │  │ Affinity/Taints  │      │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Deployment Failure Debugging

```bash
# Check deployment status
kubectl get deployment <name> -n <namespace>
kubectl describe deployment <name> -n <namespace>

# Check rollout status
kubectl rollout status deployment/<name> -n <namespace>

# Check rollout history
kubectl rollout history deployment/<name>

# Check ReplicaSets
kubectl get rs -n <namespace>

# Find failed ReplicaSet
kubectl describe rs <replicaset-name>

# Check events
kubectl get events -n <namespace> --sort-by='.lastTimestamp' | tail -20

# Rollback if needed
kubectl rollout undo deployment/<name>
kubectl rollout undo deployment/<name> --to-revision=2
```

### Deployment Stuck in Progressing

```bash
# Check if pods are being created
kubectl get pods -l app=<app-label> -n <namespace>

# Check pod events
kubectl describe pod <pod-name> | tail -30

# Common reasons:
# - ResourceQuota exceeded
# - ImagePullBackOff
# - Insufficient CPU/memory on nodes
# - PVC not bound
# - NodeSelector/Affinity not matching
```

---

## 2. HPA (Horizontal Pod Autoscaler) Troubleshooting

### HPA Not Scaling

```bash
# Check HPA status
kubectl get hpa -n <namespace>
kubectl describe hpa <hpa-name> -n <namespace>

# Check current metrics
kubectl get hpa <hpa-name> -o yaml

# Check metrics-server is running
kubectl get pods -n kube-system | grep metrics-server
kubectl top pods -n <namespace>

# Check if metrics available
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/namespaces/<namespace>/pods"
```

### Common HPA Issues

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HPA TROUBLESHOOTING                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Issue                    │ Check                    │ Fix              │
│  ─────────────────────────┼──────────────────────────┼─────────────────│
│  "unknown" metrics        │ metrics-server running?  │ Install/restart  │
│                           │ kubectl top pods works?  │ metrics-server   │
│  ─────────────────────────┼──────────────────────────┼─────────────────│
│  Not scaling up           │ CPU/Memory requests set? │ Add resource     │
│                           │ Targets reached?         │ requests!        │
│  ─────────────────────────┼──────────────────────────┼─────────────────│
│  Not scaling down         │ cooldown period (5min)   │ Wait or adjust   │
│                           │ stabilization window     │ scaleDown policy │
│  ─────────────────────────┼──────────────────────────┼─────────────────│
│  Scaling too slow         │ Check scaling policies   │ Adjust policies  │
│                           │ Check maxReplicas        │                  │
│  ─────────────────────────┼──────────────────────────┼─────────────────│
│  Thrashing (up/down)      │ Stabilization window     │ Increase window  │
│                           │ Check metric volatility  │                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### HPA Debugging Commands

```bash
# Check if resource requests are set (REQUIRED for HPA!)
kubectl get pods -n <namespace> -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].resources.requests}{"\n"}{end}'

# Check HPA events
kubectl describe hpa <hpa-name> | grep -A 10 "Events"

# Check metrics-server logs
kubectl logs -n kube-system -l k8s-app=metrics-server

# Manual check of current CPU/memory
kubectl top pods -n <namespace> --containers

# Check custom metrics (if using)
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1" | jq .
```

### HPA Best Practices

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70    # Scale at 70% CPU
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5min before scaling down
      policies:
      - type: Percent
        value: 10                       # Scale down max 10% at a time
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0    # Scale up immediately
      policies:
      - type: Percent
        value: 100                      # Can double pods
        periodSeconds: 15
      - type: Pods
        value: 4                        # Or add 4 pods max
        periodSeconds: 15
      selectPolicy: Max
```

---

## 3. OOM (Out of Memory) Troubleshooting

### Detecting OOM Kills

```bash
# Check if pod was OOMKilled
kubectl describe pod <pod-name> | grep -i "OOMKilled"

# Check last state
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[*].lastState}'

# Check exit code (137 = OOMKilled)
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[*].lastState.terminated.exitCode}'
# 137 = SIGKILL (OOM)
# 139 = SIGSEGV (Segfault)
# 143 = SIGTERM (Graceful)

# Check events
kubectl get events -n <namespace> --field-selector reason=OOMKilling

# Check on node
kubectl debug node/<node> -it --image=ubuntu
dmesg | grep -i "oom\|killed"
journalctl -k | grep -i "oom"
```

### OOM Analysis

```bash
# Current memory usage
kubectl top pod <pod-name> --containers

# Memory limits vs usage
kubectl describe pod <pod-name> | grep -A 5 "Limits\|Requests"

# Check if limits are too low
kubectl get pod <pod-name> -o jsonpath='{.spec.containers[*].resources}'

# Historical memory usage (if Prometheus)
# Query: container_memory_usage_bytes{pod="<pod-name>"}
```

### OOM Fixes

```yaml
# 1. Increase memory limits
resources:
  requests:
    memory: "256Mi"   # What scheduler reserves
  limits:
    memory: "512Mi"   # Max before OOMKill

# 2. Set requests = limits (Guaranteed QoS)
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "512Mi"   # Same as request = Guaranteed
    cpu: "500m"

# 3. Don't set limits (Burstable, risky)
resources:
  requests:
    memory: "256Mi"
  # No limits = can use all available memory
```

### QoS Classes and OOM Priority

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    QoS CLASS & OOM KILL PRIORITY                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  QoS Class      │ Condition                    │ OOM Kill Order         │
│  ───────────────┼──────────────────────────────┼───────────────────────│
│  BestEffort     │ No requests/limits           │ FIRST to be killed    │
│  Burstable      │ Requests < Limits            │ SECOND                │
│  Guaranteed     │ Requests = Limits (all)      │ LAST to be killed     │
│                                                                          │
│  To check QoS class:                                                    │
│  kubectl get pod <pod> -o jsonpath='{.status.qosClass}'                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Requests Not Hitting / Service Issues

### Traffic Not Reaching Pods

```bash
# 1. Check service has endpoints
kubectl get endpoints <service-name> -n <namespace>
# Empty = NO PODS MATCHING SELECTOR!

# 2. Check selector matches
kubectl describe service <service-name>
kubectl get pods -l <label-selector>

# 3. Check pod is READY (not just Running)
kubectl get pods -n <namespace>
# READY 0/1 = readiness probe failing = no traffic

# 4. Check readiness probe
kubectl describe pod <pod-name> | grep -A 10 "Readiness"

# 5. Test from inside cluster
kubectl run tmp --rm -it --image=busybox -- wget -qO- <service>:<port>
```

### Service Debugging Checklist

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SERVICE NOT WORKING CHECKLIST                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  □ Service exists?              kubectl get svc <name>                  │
│  □ Endpoints populated?         kubectl get endpoints <name>            │
│  □ Selector matches pod labels? kubectl describe svc <name>             │
│  □ Pod is Ready?                kubectl get pods (check READY column)   │
│  □ Readiness probe passing?     kubectl describe pod <name>             │
│  □ Port numbers correct?        service.port vs container.port          │
│  □ targetPort matches container? Check service yaml                     │
│  □ NetworkPolicy blocking?      kubectl get networkpolicy               │
│  □ DNS resolving?               nslookup <service>.<namespace>          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Ingress Not Working

```bash
# Check ingress
kubectl get ingress -n <namespace>
kubectl describe ingress <name>

# Check ingress controller
kubectl get pods -n ingress-nginx  # or your ingress namespace
kubectl logs -n ingress-nginx <ingress-controller-pod>

# Check ingress class
kubectl get ingressclass

# Test backend service directly
kubectl port-forward svc/<backend-service> 8080:80
curl localhost:8080
```

---

## 5. Latency / Slowness Troubleshooting

### Identify Slowness Source

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LATENCY INVESTIGATION                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Request Path:                                                          │
│  Client → LB → Ingress → Service → Pod → App → DB/External             │
│                                                                          │
│  Check each hop:                                                        │
│  1. Is latency from external dependency? (DB, API)                     │
│  2. Is pod CPU throttled?                                              │
│  3. Is pod memory pressured (GC)?                                      │
│  4. Network latency between pods?                                      │
│  5. DNS resolution slow?                                               │
│  6. Ingress/LB overloaded?                                             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### CPU Throttling (Common Latency Cause!)

```bash
# Check if pod is being throttled
kubectl top pod <pod-name>

# Check limits
kubectl describe pod <pod-name> | grep -A 5 "Limits"

# On node - check cgroup throttling
kubectl debug node/<node> -it --image=ubuntu
cat /sys/fs/cgroup/cpu/kubepods/pod<pod-id>/cpu.stat
# nr_throttled = number of times throttled
# throttled_time = time spent throttled (nanoseconds)

# If throttled frequently = CPU limit too low!
```

### Slow DNS Resolution

```bash
# Test DNS resolution time
kubectl exec <pod> -- time nslookup <service>

# Check ndots setting (can cause multiple DNS lookups)
kubectl exec <pod> -- cat /etc/resolv.conf
# ndots:5 means names with <5 dots trigger search list

# Optimize DNS for known FQDNs
# Use: service.namespace.svc.cluster.local. (note trailing dot)
```

### Application-Level Latency

```bash
# Check application logs for slow queries
kubectl logs <pod-name> | grep -i "slow\|timeout\|latency"

# Check connections to external services
kubectl exec <pod> -- netstat -an | grep ESTABLISHED

# Test external dependency latency
kubectl exec <pod> -- curl -w "@-" -o /dev/null -s http://external-api <<'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
          time_total:  %{time_total}\n
EOF
```

---

## 6. Node Debugging Deep Dive

### Accessing the Node

```bash
# Method 1: kubectl debug (Preferred - no SSH needed)
kubectl debug node/<node-name> -it --image=ubuntu
kubectl debug node/<node-name> -it --image=nicolaka/netshoot  # Network tools
kubectl debug node/<node-name> -it --image=busybox

# Method 2: SSH (if configured)
ssh user@<node-ip>

# Method 3: Azure AKS command invoke
az aks command invoke -g <rg> -n <cluster> --command "ls /"
```

### chroot into Host Filesystem

```bash
# When using kubectl debug, you get a container
# The host filesystem is mounted at /host

kubectl debug node/<node-name> -it --image=ubuntu

# Inside the debug container:
chroot /host    # Now you're "on" the node itself!

# Now you can run:
systemctl status kubelet
journalctl -u kubelet
crictl ps
docker ps  # if using Docker
```

### crictl Commands (containerd)

```bash
# chroot into host first
kubectl debug node/<node-name> -it --image=ubuntu
chroot /host

# ═══════════════════════════════════════════════════════════════════════
# CRICTL - Container Runtime Interface CLI (for containerd)
# ═══════════════════════════════════════════════════════════════════════

# List all containers
crictl ps
crictl ps -a      # Include stopped

# List pods
crictl pods

# Get container logs
crictl logs <container-id>
crictl logs -f <container-id>     # Follow
crictl logs --tail=100 <container-id>

# Inspect container
crictl inspect <container-id>

# Inspect pod
crictl inspectp <pod-id>

# Execute in container
crictl exec -it <container-id> /bin/sh

# Get container stats
crictl stats
crictl stats <container-id>

# Pull image
crictl pull <image>

# List images
crictl images
crictl images -v    # Verbose

# Remove image
crictl rmi <image-id>

# Remove unused images
crictl rmi --prune

# Get image info
crictl inspecti <image-id>
```

### ctr Commands (containerd native)

```bash
# ctr is the native containerd CLI (lower level than crictl)
chroot /host

# List namespaces
ctr namespaces list

# List containers (in k8s.io namespace)
ctr -n k8s.io containers list

# List images
ctr -n k8s.io images list

# Check image usage
ctr -n k8s.io images check

# Export image
ctr -n k8s.io images export myimage.tar docker.io/library/nginx:latest

# Import image
ctr -n k8s.io images import myimage.tar
```

### Docker Commands (if using Docker runtime)

```bash
chroot /host

# List containers
docker ps
docker ps -a

# Container stats
docker stats

# Disk usage
docker system df
docker system df -v    # Verbose

# Cleanup
docker system prune -a -f    # Remove ALL unused
docker container prune -f    # Remove stopped containers
docker image prune -a -f     # Remove unused images
docker volume prune -f       # Remove unused volumes
docker network prune -f      # Remove unused networks
```

---

## 7. Disk Usage & Garbage Collection

### Check Disk Usage on Node

```bash
kubectl debug node/<node-name> -it --image=ubuntu
chroot /host

# Overall disk usage
df -h

# Find large directories
du -sh /* 2>/dev/null | sort -rh | head -20
du -sh /var/lib/containerd/* 2>/dev/null | sort -rh
du -sh /var/lib/docker/* 2>/dev/null | sort -rh
du -sh /var/lib/kubelet/* 2>/dev/null | sort -rh
du -sh /var/log/* 2>/dev/null | sort -rh

# Find large files
find / -type f -size +100M 2>/dev/null | head -20
```

### Container Runtime Disk Usage

```bash
chroot /host

# For containerd
crictl images                              # List images
crictl images | awk '{sum += $4} END {print sum}'  # Rough size

# For Docker
docker system df
# TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
# Images          50        10        15GB      12GB (80%)
# Containers      20        5         2GB       1.5GB (75%)
# Volumes         10        5         5GB       2GB (40%)
```

### Image Garbage Collection

```bash
# ═══════════════════════════════════════════════════════════════════════
# MANUAL CLEANUP
# ═══════════════════════════════════════════════════════════════════════

chroot /host

# Containerd - remove unused images
crictl rmi --prune

# Docker - remove unused images
docker image prune -a -f

# ═══════════════════════════════════════════════════════════════════════
# KUBELET GARBAGE COLLECTION (Automatic)
# ═══════════════════════════════════════════════════════════════════════

# Kubelet automatically garbage collects:
# - Containers: when disk usage > 85%
# - Images: when disk usage > 85%

# Check kubelet GC settings
cat /var/lib/kubelet/config.yaml | grep -A 10 "imageGC\|eviction"

# Default thresholds:
# imageGCHighThresholdPercent: 85  # Start GC when disk > 85%
# imageGCLowThresholdPercent: 80   # Stop GC when disk < 80%

# Eviction thresholds:
# imagefs.available < 15%  → Start evicting pods
# nodefs.available < 10%   → Start evicting pods
```

### Pod Log Cleanup

```bash
chroot /host

# Check pod logs size
du -sh /var/log/pods/*

# Check container logs size
du -sh /var/lib/docker/containers/*/
# OR
du -sh /var/log/containers/

# Truncate large log file
truncate -s 0 /var/log/<file>

# Configure log rotation in kubelet
# /var/lib/kubelet/config.yaml:
# containerLogMaxSize: "10Mi"
# containerLogMaxFiles: 5
```

---

## 8. Common Production Issue Patterns

### Pattern: Pods Evicted

```bash
# Check for evicted pods
kubectl get pods -A | grep Evicted
kubectl get pods -A --field-selector=status.phase=Failed | grep Evicted

# Why eviction?
kubectl describe pod <evicted-pod> | grep -A 5 "Status\|Reason\|Message"

# Common reasons:
# - Node disk pressure (imagefs/nodefs)
# - Node memory pressure
# - Pod exceeded ephemeral storage limit

# Cleanup evicted pods
kubectl delete pods --field-selector=status.phase=Failed -A
```

### Pattern: Pods Pending Forever

```bash
# Check pending pods
kubectl get pods -A --field-selector=status.phase=Pending

# Why pending?
kubectl describe pod <pending-pod> | grep -A 10 "Events"

# Common reasons checklist:
# □ No nodes have enough resources → kubectl describe nodes
# □ Node selector not matching → Check nodeSelector
# □ Taints not tolerated → Check tolerations
# □ PVC not bound → kubectl get pvc
# □ ResourceQuota exceeded → kubectl get resourcequota
# □ Pod affinity can't be satisfied → Check affinity rules
```

### Pattern: Random Pod Restarts

```bash
# Check restart counts
kubectl get pods -A --sort-by='.status.containerStatuses[0].restartCount' | tail -20

# Why restarting?
kubectl describe pod <pod> | grep -A 10 "Last State"
kubectl logs <pod> --previous

# Check for OOMKilled
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[*].lastState.terminated.reason}{"\n"}{end}' | grep OOM

# Check liveness probe
kubectl describe pod <pod> | grep -A 10 "Liveness"
```

### Pattern: Services Intermittently Failing

```bash
# Check all endpoints are healthy
kubectl get endpoints <service>

# Check if some pods are not ready
kubectl get pods -l <service-selector>

# Check readiness probe issues
for pod in $(kubectl get pods -l <selector> -o name); do
  kubectl describe $pod | grep -A 5 "Readiness"
done

# Check for network policies
kubectl get networkpolicy -n <namespace>
```

---

## 9. Complete Debug Session Example

```bash
# ═══════════════════════════════════════════════════════════════════════
# FULL NODE DEBUG SESSION
# ═══════════════════════════════════════════════════════════════════════

# 1. Start debug pod on node
kubectl debug node/<node-name> -it --image=nicolaka/netshoot

# 2. Enter host namespace
chroot /host

# 3. Check system resources
echo "=== DISK ===" && df -h
echo "=== MEMORY ===" && free -h
echo "=== CPU ===" && uptime
echo "=== PROCESSES ===" && ps aux | head -20

# 4. Check kubelet
systemctl status kubelet
journalctl -u kubelet --no-pager | tail -50

# 5. Check container runtime
systemctl status containerd
crictl ps
crictl pods

# 6. Check images and disk usage
crictl images
du -sh /var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/*

# 7. Check network
ip addr
ip route
iptables -L -n | head -30

# 8. Check for errors
dmesg | grep -i "error\|fail\|oom" | tail -20
journalctl -xe --no-pager | tail -50

# 9. Check conntrack
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max

# 10. Cleanup if needed
crictl rmi --prune
```

---

## 10. Quick Reference - Production Issues

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PRODUCTION ISSUES QUICK REFERENCE                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  SYMPTOM                     │  FIRST CHECK                             │
│  ────────────────────────────┼──────────────────────────────────────────│
│  Pod not starting            │  kubectl describe pod → Events           │
│  Pod restarting              │  kubectl logs --previous, check OOM      │
│  Service not working         │  kubectl get endpoints (empty?)          │
│  HPA not scaling             │  kubectl top pods (metrics working?)     │
│  Slow response               │  kubectl top pod (CPU throttled?)        │
│  Connection timeout          │  Check conntrack, CNI pods               │
│  Disk pressure               │  df -h, crictl rmi --prune               │
│  Memory pressure             │  free -h, check OOMKilled pods           │
│  Node NotReady               │  systemctl status kubelet                │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  NODE DEBUG QUICK START                                                 │
│  ─────────────────────                                                  │
│  kubectl debug node/<node> -it --image=ubuntu                           │
│  chroot /host                                                           │
│  systemctl status kubelet                                               │
│  crictl ps                                                              │
│  df -h && free -h && uptime                                            │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  CONTAINERD COMMANDS (crictl)                                           │
│  ───────────────────────────                                            │
│  crictl ps                    # List containers                         │
│  crictl pods                  # List pods                               │
│  crictl logs <id>             # Container logs                          │
│  crictl exec -it <id> sh      # Exec into container                    │
│  crictl images                # List images                             │
│  crictl rmi --prune           # Cleanup unused images                   │
│  crictl stats                 # Container stats                         │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  DISK CLEANUP COMMANDS                                                  │
│  ────────────────────                                                   │
│  crictl rmi --prune                         # Remove unused images      │
│  kubectl delete pods --field-selector=status.phase=Failed -A            │
│  journalctl --vacuum-size=500M              # Cleanup journal           │
│  truncate -s 0 /var/log/syslog              # Clear syslog              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# Quick Reference Card

```
┌──────────────────────────────────────────────────────────────────┐
│                    QUICK COMMAND REFERENCE                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  HELM                                                             │
│  ────                                                             │
│  helm list -A                    # List all releases              │
│  helm status <release>           # Check status                   │
│  helm history <release>          # See history                    │
│  helm rollback <release> <rev>   # Rollback                       │
│  helm upgrade --install          # Upsert                         │
│                                                                   │
│  KUBECTL                                                          │
│  ───────                                                          │
│  kubectl get pods -A             # All pods all namespaces        │
│  kubectl describe pod <pod>      # Details + events               │
│  kubectl logs <pod> --previous   # Crashed container logs         │
│  kubectl exec -it <pod> -- sh    # Shell into container           │
│  kubectl port-forward <pod> 8080:80                               │
│                                                                   │
│  AZ CLI                                                           │
│  ──────                                                           │
│  az login                        # Login                          │
│  az account set -s <sub>         # Switch subscription            │
│  az aks get-credentials -g -n    # Get kubeconfig                 │
│  az vm list -o table             # List VMs                       │
│                                                                   │
│  TERRAFORM                                                        │
│  ─────────                                                        │
│  terraform init                  # Initialize                     │
│  terraform plan                  # Preview                        │
│  terraform apply                 # Deploy                         │
│  terraform state list            # Check state                    │
│                                                                   │
│  AZURE DEVOPS                                                     │
│  ────────────                                                     │
│  trigger: [main]                 # Run on push to main            │
│  stages: → jobs: → steps:        # Pipeline structure             │
│  - deployment: → environment:    # Requires approval              │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

