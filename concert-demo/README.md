# IBM Concert Protect — Jeu de données de démonstration

## Contexte

Application fictive **TechCorp ERP v3.4.1** — système ERP critique (finance, RH, supply chain)  
Environnements : `prod-eu-west-1` (RHEL 8.9 + Windows Server 2022 + Kubernetes) et `staging-eu-west-1`

---

## Fichiers à importer dans Concert Protect

| Fichier | Navigation Concert 3.0.x | File type à sélectionner | Format |
|---------|--------------------------|--------------------------|--------|
| `01_application_sbom.json` | `Dimensions > Application` > **Upload application SBOM** | Application SBOM | ConcertDef 2.0.0 JSON |
|  |  |  |  |
| `02_vm_scan.csv` | `Dimensions > Vulnerability` > **Upload vulnerability scan** | Vulnerability scan (VM) | CSV générique |
| `03_image_scan.csv` | `Dimensions > Vulnerability` > **Upload vulnerability scan** | Vulnerability scan (image) | CSV générique |
| `04_code_scan_sast.csv` | `Dimensions > Vulnerability` > **Upload vulnerability scan** | Vulnerability scan (source code) | CSV générique |
| `05_compliance_assessment.json` | `Dimensions > Compliance` > **Upload compliance scan** | Compliance assessment | JSON |
| `06_certificate_sbom.json` | `Dimensions > Certificate` > **Upload certificate data** | Certificate | ConcertDef 2.0.0 JSON |

> **Raccourci :** depuis l'**Arena view**, utilisez **`Define and upload > Upload scan`** pour les scans de vulnérabilité.
>
> **Ordre d'import recommandé :** 01 -**> 7**→ 02 → 03 → 04 → 05 → 06

---

## Scénarios de démonstration

### 1. Automatisation du patching et réactivité

**Données clés :**
- `CVE-2024-47176` (VM Scan, Risk Score 98) → Auto-patch déclenché → ticket `INC0042001` ouvert dans ServiceNow
- `CVE-2024-38063` (VM Scan, Risk Score 96) → Patch Windows planifié fenêtre maintenance 2025-07-20 02h00
- `CVE-2024-4577` PHP RCE (VM Scan, Risk Score 91) → Patch automatique appliqué

**Message démo :** Concert Protect détecte les CVEs critiques avec exploit disponible et déclenche automatiquement le patching sans intervention humaine, avec ouverture de ticket ServiceNow traçable.

---

### 2. Pertinence et priorisation des actions

**Données clés — Contrast Risk Score vs CVSS brut :**
- `CVE-2024-3094` XZ Utils Backdoor : CVSS 10.0 + EPSS 0.97 → Risk Score 99 (supply chain confirmé par Gemini AI)
- `CVE-2024-25600` WordPress : CVSS 9.8 → **faux positif**, hors scope ERP → Accepted Risk
- `CWE-312` Credentials en clair : CVSS 8.2, EPSS 0.0 → priorité humaine, pas auto-patch

**Message démo :** Concert Protect ne se limite pas au score CVSS. Il combine EPSS, contexte applicatif, exploitabilité réelle et analyse Gemini AI pour distinguer ce qui mérite une action immédiate de ce qui peut attendre.

---

### 3. Intégration GitLab / GitHub / Google Gemini / ServiceNow

**GitHub :**
- Repos `erp-core-api`, `erp-finance-module`, `erp-web-app` (Code Scan SAST)
- PR automatiques créées par Dependabot : `pull/312`, `pull/315`, `pull/318`
- GitHub Advanced Security détecte Log4Shell et Spring4Shell

**GitLab :**
- Repos `erp-hr-module`, `erp-db-migrations` (GitLab SAST Semgrep)
- Merge request automatique : `erp-db-migrations/-/merge_requests/44`

**Google Gemini AI :**
- Analyse `CVE-2024-3094` → risque supply chain confirmé
- Analyse `cis-k8s-1.2.1` → exposition API anonyme marquée URGENT
- Analyse `cis-rhel8-5.2.11` → risque cryptographique élevé
- Intégration mTLS expirée (`cert:erp-gemini-api-mtls`) → bloquée, action immédiate

**ServiceNow :**
- Tickets ouverts automatiquement : `INC0042001` à `INC0046004`
- Mapping sévérité Concert → Impact/Urgency/Priority ServiceNow
- Workflow patching : Open → In Review → Patch Scheduled → Patch Applied

---

### 4. Sources de données de scan exploitées

| Source | Type | Fichier démo |
|--------|------|-------------|
| OpenSCAP 1.3.9 | Compliance OS | `05_compliance_assessment.json` |
| kube-bench 0.8.0 | Compliance Kubernetes | `05_compliance_assessment.json` |
| GitHub Advanced Security | Code SAST | `04_code_scan_sast.csv` |
| GitLab SAST (Semgrep) | Code SAST | `04_code_scan_sast.csv` |
| SonarQube | Code SAST | `04_code_scan_sast.csv` |
| Dependabot (GitHub) | Dépendances | `04_code_scan_sast.csv` |
| Trivy / Aqua Security (simulated) | Image scan | `03_image_scan.csv` |
| NVD + EPSS (NVD sync) | Metadata CVE | `02_vm_scan.csv` + `03_image_scan.csv` |

---

### 5. Évaluation des risques et des impacts

**Concert Risk Score = CVSS × EPSS × Contexte environnemental**

Exemples de la démo :
- `CVE-2024-6387` OpenSSH : CVSS 8.1 + EPSS 0.76 → Risk Score 89 (prod) vs 74 (staging)
- `CVE-2024-24786` Go Protobuf : CVSS 7.5 + EPSS 0.42 → Risk Score 61 → patch planifié non urgent
- Certificat `erp-gemini-api-mtls` : expiré depuis 13 jours + algorithme SHA-1 → Risk Critical

---

### 6. Seuil de risque → patch automatique vs action manuelle

| Risk Score | Exploit dispo | Auto-Patch | Décision |
|------------|---------------|------------|----------|
| ≥ 90 + exploit | Oui | ✅ Oui | Patch automatique immédiat |
| 70–89 + exploit | Oui | ❌ Non | Ticket ServiceNow + validation staging |
| 70–89 sans exploit | Non | ⏱ Planifié | Fenêtre maintenance prochaine |
| < 70 | N/A | ❌ Non | Backlog / planification trimestrielle |
| Faux positif | N/A | ❌ Non | Accepted Risk avec justification |

---

### 7. Workflow de patching complet

```
Ingestion scan (VM/Image/Code)
      ↓
Concert calcule Risk Score (CVSS × EPSS × contexte)
      ↓
Gemini AI analyse exploitabilité et contexte métier
      ↓
     [Risk ≥ 90 + exploit]           [Risk 70-89]             [Risk < 70]
           ↓                               ↓                       ↓
  Patch auto déclenché           Ticket ServiceNow         Backlog sécurité
  (RHEL Patching / Windows        INC créé automatique      planification
   Patching Workflow)             + assigné au bon owner    trimestrielle
           ↓                               ↓
  Test post-patch (staging)      Review équipe sécurité
  Concert valide l'absence        ↓
  du CVE après patch             Approbation manuelle
           ↓                               ↓
  Ticket SNow fermé auto          Patch fenêtre maint.
  Concert Arena mis à jour              ↓
                                  Test staging (Concert
                                  vérifie CVE absent)
                                        ↓
                                  Déploiement prod
                                  Ticket SNow fermé
```

---

## CVEs marquants pour la démo (top 5)

| CVE | CVSS | Risk Score | Impact démo |
|-----|------|------------|-------------|
| CVE-2024-3094 XZ Backdoor | 10.0 | 99 | Supply chain — Gemini détecte, patch immédiat |
| CVE-2024-47176 CUPS RCE | 9.9 | 98 | Auto-patch VM → SNow ticket auto |
| CVE-2021-44228 Log4Shell | 10.0 | 99 | Code scan GitHub → PR auto + patch |
| cis-k8s-1.2.1 API anonyme | Critical | Critical | Compliance → SNow + Gemini URGENT |
| cert erp-gemini-api-mtls | — | Critical | Certificat expiré → intégration IA coupée |
