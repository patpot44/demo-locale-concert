# IBM Concert Protect — Jeu de données de démonstration

## Contexte

Application fictive **TechCorp ERP v3.4.1** — système ERP critique (finance, RH, supply chain)  
Environnements : `prod-eu-west-1` (RHEL 8.9 + Windows Server 2022 + Kubernetes) et `staging-eu-west-1`

watsonx:

projectid = 7aa1b6d2-c471-4f38-9210-acbd2d76539b

```
export WATSONX_API_KEY=YOUR_WATSONX_API_KEY_PLACEHOLDER
export WATSONX_API_PROJECT_ID=7aa1b6d2-c471-4f38-9210-acbd2d76539b
export WATSONX_API_URL=https://eu-de.ml.cloud.ibm.com
export CONCERT_NAMESPACE=ibm-concert
```

```
github token in coud data watsonx instead
ghp_YOUR_GITHUB_TOKEN_HERE_PLACEHOLDER_1
```



---

## Fichiers à importer dans Concert Protect

| Fichier | Navigation Concert 3.0.x | File type à sélectionner | Format |
|---------|--------------------------|--------------------------|--------|
| `01_application_sbom.json` | `Dimensions > Application` > **Upload application SBOM** | Application SBOM | ConcertDef 2.0.0 JSON |
|  |  |  |  |
| `02_vm_scan.csv` | `Dimensions > Vulnerability` > **Upload vulnerability scan** | Vulnerability scan (VM) | CSV générique |
| `03_image_scan.csv` | `Dimensions > Vulnerability` > **Upload vulnerability scan** | Vulnerability scan (image) | CSV générique |
| `04_code_scan_sast.csv` (faire pour tous les repository) | `Dimensions > Vulnerability` > **Upload vulnerability scan** | Vulnerability scan (source code) | CSV générique |
| `09_dast_scan_exposure.json` ⚠️ **JSON uniquement** (scan source : ZAP ou Others) | `Protect > Vulnerability > Exposures` > **Upload exposures** > **Dynamic scan** | Vulnerability scan (dynamic) | JSON ZAP natif |
| `10_sast_scan_exposure.csv` | `Protect > Vulnerability > Exposures` > **Upload exposures** > **Static scan** | Vulnerability scan (static) | CSV Exposure |
| verifier profile |  |  |  |
| `05_compliance_oscal.json<br />05_compliance_trivy_v3_artifactname.json<br />05_compliance_trivy.json` | `Dimensions > Compliance` > **Upload compliance scan**<br />import mm si erreur, puis saisie des 19 assesment | Compliance assessment | JSON |
| `06_certificate_sbom.json` | `Dimensions > Certificate` > **Upload certificate data** | Certificate                      | ConcertDef 2.0.0 JSON |
| `08_package_sbom_cyclonedx.json` | `Dimensions > Sofware Composition` > **Upload CycloneDX** | CycloneDX | JSON                  |
| suivre la doc pour connecter watsonx.ai<br />https://www.ibm.com/docs/en/concert/3.0.x?topic=deployment-configuring-watsonxai-concert-premises |                                                              |                                  |  |

> **Raccourci :** depuis l'**Arena view**, utilisez **`Define and upload > Upload scan`** pour les scans de vulnérabilité.
>
> **Ordre d'import recommandé :** 01 → 07 → 02 → 03 → 04 → **09** → **10** → 05 → 06
>
> avant 5 faire létape suivante :

### Vérifier / créer le profil `k8s-cis-1.23`

#### 1. Naviguer vers les profils

Dans l'UI Concert :

```txt
Dimensions  →  Compliance  →  Profiles
```



#### 2. Vérifier si le profil existe déjà

Concert 3.0.x **inclut des profils intégrés** dont le catalogue Kubernetes. Cherche dans la liste un profil nommé exactement **`k8s-cis-1.23`**.

------

#### 3. Si le profil n'existe pas → le créer manuellement

1. Clique **Create profile** → **From resources**
2. **Name** : `k8s-cis-1.23` ← **doit être exactement ce nom** (c'est le `compliance_id` Trivy)
3. **Description** : `CIS Benchmark for Kubernetes v1.23`
4. **Version** : `1.23`
5. **Select catalogs** : sélectionne le catalogue Kubernetes (CIS) disponible
6. **Select controls** : sélectionne tous les contrôles KSV (Kubernetes Security)
7. Clique **Create**

------

#### 4. Vérifier aussi le catalog

Avant de créer le profil, il faut qu'un **catalog Kubernetes/CIS** existe :

```txt
Dimensions  →  Compliance  →  Catalogs
```



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

- [x] Host CVE `CVE-2024-3094` XZ Utils Backdoor : CVSS 10.0 + EPSS 0.97 → Risk Score 99 (supply chain confirmé par Gemini AI)
  

- [ ] `CVE-2024-25600` WordPress : CVSS 9.8 → **faux positif**, hors scope ERP → Accepted Risk

  :arrow_right: 04_code_scan_sast - Copy.csv (2).ok modifier pour ajouter

  cherchez-le dans **Dimensions → Vulnerability**. Une fois visible, vous pourrez le marquer **"Accepted Risk"** avec la justification :

  > *"WordPress Bricks Builder component not used in techcorp-erp production stack. False positive — out of application scope."*

  C'est exactement le scénario 2 du README : illustrer que Concert permet de **distinguer un vrai risque d'un faux positif** grâce au contexte applicatif.

- [ ] `CWE-312` Credentials en clair : CVSS 8.2, EPSS 0.0 → priorité humaine, pas auto-patch

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



## commande pour résoudre l'upload de `05_compliance`

```
# Récupérer les contrôles du catalogue et du profil k8s-cis-1.23
foreach ($endpoint in @(
    "/compliance/api/v1/catalogs/7f3a4a3f-70d7-48a8-b706-8aa3fb5230fb/controls?page_size=20",
    "/compliance/api/v1/profiles/3dc9abe6-d107-48e0-b659-2f62992cca76/controls?page_size=20",
    "/compliance/api/v1/profiles/3dc9abe6-d107-48e0-b659-2f62992cca76"
)) {
    $req = [System.Net.HttpWebRequest]::Create("$baseUrl$endpoint")
    $req.Method = "GET"
    $req.Headers.Add("Authorization", $authHeader)
    $req.Headers.Add("InstanceID", "0000-0000-0000-0000")
    try {
        $resp = $req.GetResponse()
        $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
        $body = $reader.ReadToEnd()
        Write-Host "=== $endpoint (OK) ===" 
        Write-Host $body.Substring(0, [Math]::Min(2000, $body.Length))
        Write-Host "..."
    } catch [System.Net.WebException] {
        $code = $_.Exception.Response.StatusCode
        $errReader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        Write-Host "=== $endpoint => $code : $($errReader.ReadToEnd()) ==="
    }
}
```





```
$ Add-Type @" using System.Net; using System.Security.Cryptography.X509Certificates; public class TrustAllCerts4 : ICertificatePolicy { public bool CheckValidationResult(ServicePoint sp, X509Certificate cert, WebRequest req, int problem) { return true; } } "@ [System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCerts4 [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12 $baseUrl = "https://172.22.147.223:12443" $authHeader = "C_API_KEY aWJtY29uY2VydDo0Y2Y1ZmFhYi04ZDEwLTRlNTEtOTZlYS1kNjUzY2QyM2QyOGM=" # Tester plusieurs endpoints possibles pour compliance foreach ($endpoint in @( "/compliance/api/v1/profiles", "/compliance/api/v1/catalogs", "/compliance/api/v1/postures", "/concert/api/v1/profiles", "/concert/api/v1/catalogs", "/protect/api/v1/profiles", "/protect/api/v1/catalogs" )) { $req = [System.Net.HttpWebRequest]::Create("$baseUrl$endpoint") $req.Method = "GET" $req.Headers.Add("Authorization", $authHeader) $req.Headers.Add("InstanceID", "0000-0000-0000-0000") try { $resp = $req.GetResponse() $reader = New-Object System.IO.StreamReader($resp.GetResponseStream()) $body = $reader.ReadToEnd() Write-Host "=== $endpoint (OK) ===" Write-Host ($body | Select-Object -First 500) } catch [System.Net.WebException] { $code = $_.Exception.Response.StatusCode Write-Host "=== $endpoint => $code ===" } }
=== /compliance/api/v1/profiles (OK) ===
{"data":[{"uuid":"3dc9abe6-d107-48e0-b659-2f62992cca76","catalog_ids":["7f3a4a3f-70d7-48a8-b706-8aa3fb5230fb"],"catalog_names":["Kubernetes Catalog"],"title":"k8s-cis-1.23","description":"CIS Benchmark for Kubernetes v1.23","version":"1.23","last_updated_by":"ibmconcert","last_updated_on":1787811361,"sample_data_upload":false,"mapped_profile":false,"allow_manual_assessment":false,"is_default":false,"user_app_role":"admin","application_ids":["24944671-7b0d-4ceb-9fe4-fa7b7f5e18f6"]},{"uuid":"ada71c7d-5bf7-4b2a-b65d-24bbc988c70b","catalog_ids":["7f3a4a3f-70d7-48a8-b706-8aa3fb5230fb"],"catalog_names":["Kubernetes Catalog"],"title":"Kubernetes Profile","description":"A profile of compliance controls for assessing the security and configuration of Kubernetes and OpenShift platforms.","version":"1.0.0","last_updated_by":"system","last_updated_on":1787617392,"sample_data_upload":false,"mapped_profile":false,"allow_manual_assessment":false,"is_default":true,"user_app_role":"viewer"}],"pagination":{"total_count":2,"total_pages":1,"page_size":25,"page_number":1}}

=== /compliance/api/v1/catalogs (OK) ===
{"data":[{"uuid":"7f3a4a3f-70d7-48a8-b706-8aa3fb5230fb","title":"Kubernetes Catalog","tags":[],"published_date":"2025-10-28T00:00:00Z","version":"1.0.0","description":"A catalog of compliance controls for assessing the security and configuration of Kubernetes and OpenShift platforms.","last_updated_by":"system","last_updated_on":1787617392,"component_definitions":[{"component_definition_id":"88cb105b-a46b-4fd2-9ee6-926e725fe241","component_definition_title":"Kube Component","component_definition_version":"1.0.0","source":"","validators":[{"validator_id":"54e423db-9617-44e6-be81-46dd0f98ceae","scanner_name":"kube scan","scanner_version":"1.0.0","source":"","benchmark":"kubesystem","description":"kube scan","additional_validator_payload":null,"last_updated_by":"system","last_updated_on":1787617392}]}],"sample_data_upload":false,"agent_metadata":null,"ciso_ai_agent_status":"","draft_catalog":false,"is_ai_generated_catalog":false,"is_default":true,"region":"Global","standard_type":"","industry_domain":""}],"pagination":{"total_count":1,"total_pages":1,"page_size":25,"page_number":1},"available_filters":{"region":[],"standard_type":[],"industry_domain":[],"tags":[]}}

=== /compliance/api/v1/postures (OK) ===
[]

=== /concert/api/v1/profiles => NotFound ===
=== /concert/api/v1/catalogs => NotFound ===
=== /protect/api/v1/profiles => NotFound ===
=== /protect/api/v1/catalogs => NotFound ===


Excellent ! Voilà les informations clés :

Profils existants dans Concert :

UUID	Titre	Catalogue
3dc9abe6-...	k8s-cis-1.23	Kubernetes Catalog
ada71c7d-...	Kubernetes Profile (default)	Kubernetes Catalog
Catalogue :

7f3a4a3f-... → Kubernetes Catalog avec scanner kube scan / benchmark kubesystem
Le problème est clair : notre fichier OSCAL utilise "profile-id": "k8s-cis-1.23" — le profil existe ! Mais les control-ids (KSV001, etc.) ne correspondent pas aux contrôles du catalogue. Récupérons les vrais control-ids du catalogue :
```



```
$ Add-Type @" using System.Net; using System.Security.Cryptography.X509Certificates; public class TrustAllCerts4 : ICertificatePolicy { public bool CheckValidationResult(ServicePoint sp, X509Certificate cert, WebRequest req, int problem) { return true; } } "@ [System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCerts4 [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12 
$baseUrl = "https://172.22.147.223:12443" 
$authHeader = "C_API_KEY aWJtY29uY2VydDo0Y2Y1ZmFhYi04ZDEwLTRlNTEtOTZlYS1kNjUzY2QyM2QyOGM=" # Tester plusieurs endpoints possibles pour compliance 
foreach ($endpoint in @( "/compliance/api/v1/profiles", "/compliance/api/v1/catalogs", "/compliance/api/v1/postures", "/concert/api/v1/profiles", "/concert/api/v1/catalogs", "/protect/api/v1/profiles", "/protect/api/v1/catalogs" )) 
{ $req = [System.Net.HttpWebRequest]::Create("$baseUrl$endpoint") $req.Method = "GET" $req.Headers.Add("Authorization", $authHeader) $req.Headers.Add("InstanceID", "0000-0000-0000-0000") try { $resp = $req.GetResponse() $reader = New-Object System.IO.StreamReader($resp.GetResponseStream()) $body = $reader.ReadToEnd() Write-Host "=== $endpoint (OK) ===" Write-Host ($body | Select-Object -First 500) } catch [System.Net.WebException] { $code = $_.Exception.Response.StatusCode Write-Host "=== $endpoint => $code ===" } }
=== /compliance/api/v1/profiles (OK) ===
{"data":[{"uuid":"3dc9abe6-d107-48e0-b659-2f62992cca76","catalog_ids":["7f3a4a3f-70d7-48a8-b706-8aa3fb5230fb"],"catalog_names":["Kubernetes Catalog"],"title":"k8s-cis-1.23","description":"CIS Benchmark for Kubernetes v1.23","version":"1.23","last_updated_by":"ibmconcert","last_updated_on":1787811361,"sample_data_upload":false,"mapped_profile":false,"allow_manual_assessment":false,"is_default":false,"user_app_role":"admin","application_ids":["24944671-7b0d-4ceb-9fe4-fa7b7f5e18f6"]},{"uuid":"ada71c7d-5bf7-4b2a-b65d-24bbc988c70b","catalog_ids":["7f3a4a3f-70d7-48a8-b706-8aa3fb5230fb"],"catalog_names":["Kubernetes Catalog"],"title":"Kubernetes Profile","description":"A profile of compliance controls for assessing the security and configuration of Kubernetes and OpenShift platforms.","version":"1.0.0","last_updated_by":"system","last_updated_on":1787617392,"sample_data_upload":false,"mapped_profile":false,"allow_manual_assessment":false,"is_default":true,"user_app_role":"viewer"}],"pagination":{"total_count":2,"total_pages":1,"page_size":25,"page_number":1}}

=== /compliance/api/v1/catalogs (OK) ===
{"data":[{"uuid":"7f3a4a3f-70d7-48a8-b706-8aa3fb5230fb","title":"Kubernetes Catalog","tags":[],"published_date":"2025-10-28T00:00:00Z","version":"1.0.0","description":"A catalog of compliance controls for assessing the security and configuration of Kubernetes and OpenShift platforms.","last_updated_by":"system","last_updated_on":1787617392,"component_definitions":[{"component_definition_id":"88cb105b-a46b-4fd2-9ee6-926e725fe241","component_definition_title":"Kube Component","component_definition_version":"1.0.0","source":"","validators":[{"validator_id":"54e423db-9617-44e6-be81-46dd0f98ceae","scanner_name":"kube scan","scanner_version":"1.0.0","source":"","benchmark":"kubesystem","description":"kube scan","additional_validator_payload":null,"last_updated_by":"system","last_updated_on":1787617392}]}],"sample_data_upload":false,"agent_metadata":null,"ciso_ai_agent_status":"","draft_catalog":false,"is_ai_generated_catalog":false,"is_default":true,"region":"Global","standard_type":"","industry_domain":""}],"pagination":{"total_count":1,"total_pages":1,"page_size":25,"page_number":1},"available_filters":{"region":[],"standard_type":[],"industry_domain":[],"tags":[]}}

=== /compliance/api/v1/postures (OK) ===
[]

=== /concert/api/v1/profiles => NotFound ===
=== /concert/api/v1/catalogs => NotFound ===
=== /protect/api/v1/profiles => NotFound ===
=== /protect/api/v1/catalogs => NotFound ===
```



Excellent ! Voilà les informations clés :

**Profils existants dans Concert :**

| UUID           | Titre                              | Catalogue          |
| -------------- | ---------------------------------- | ------------------ |
| `3dc9abe6-...` | **`k8s-cis-1.23`**                 | Kubernetes Catalog |
| `ada71c7d-...` | **`Kubernetes Profile`** (default) | Kubernetes Catalog |

**Catalogue :**

- `7f3a4a3f-...` → **Kubernetes Catalog** avec scanner `kube scan` / benchmark `kubesystem`

Le problème est clair : notre fichier OSCAL utilise `"profile-id": "k8s-cis-1.23"` — le profil existe ! Mais les `control-ids` (`KSV001`, etc.) ne correspondent pas aux contrôles du catalogue. Récupérons les vrais control-ids du catalogue :
