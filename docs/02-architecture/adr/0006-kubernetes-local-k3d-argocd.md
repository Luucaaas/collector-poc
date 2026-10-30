---
statut: acceptée, sous réserve de la validation de l'intervenant (critère 5)
date: 2026-10-30
décideurs: Lucas (Lead Developer)
---

# 0006 — Kubernetes local (k3d) et déploiement GitOps avec Argo CD

## Contexte et problème

La consigne demande « une gestion du déploiement via un orchestrateur ou un fournisseur cloud » et la démonstration de la disponibilité et de la montée en charge. Le POC doit être **entièrement gratuit et sans crédits d'essai limités dans le temps**, reproductible par script pour le jury, et démontrable hors ligne le jour de la soutenance. Le poste de développement est un Mac (Apple Silicon) avec Docker Desktop.

Où et comment déployer le POC ?

## Facteurs de décision

- Orchestrateur réel : plusieurs nœuds, répartition des réplicas, autoscaling, NetworkPolicies, pour démontrer la disponibilité (ENF-16) et la scalabilité (ENF-29).
- Coût nul et durable, sans dépendance à des crédits d'essai.
- Reproductibilité : un script recrée l'environnement à l'identique (ENF-30).
- Proximité avec un Kubernetes managé, pour que la migration se fasse sans réécriture (ENF-31).
- Déploiement traçable et auditable, sans manipulation manuelle du cluster.
- Démonstration fiable, sans dépendre du réseau de la salle.

## Options étudiées

**Orchestration**

1. **k3d** : k3s, une distribution Kubernetes certifiée CNCF, dont chaque nœud tourne dans un conteneur Docker.
2. **Minikube** (un nœud par défaut, plusieurs nœuds possibles).
3. **kind** (Kubernetes in Docker, orienté tests).
4. **docker-compose**.
5. **Kubernetes managé avec crédits d'essai** (AKS, GKE, EKS).
6. **Oracle OKE Always Free** (Kubernetes managé gratuit, sans limite de durée).

**Déploiement**

- **A. Push** : la CI exécute `helm upgrade` sur le cluster.
- **B. Pull (GitOps)** : Argo CD, installé dans le cluster, synchronise l'état du cluster avec le dépôt Git.

## Décision

**k3d avec 1 server et 2 agents** sur le poste de développement, ingress-nginx et cert-manager (CA locale générée par mkcert, domaines `*.127.0.0.1.sslip.io`), charts **Helm** pour l'infrastructure et les services, et **Argo CD en GitOps (option B)**.

**Repli prévu : Oracle OKE Always Free**, avec les mêmes charts Helm, si l'intervenant refuse le cluster local comme « environnement managé » pour le critère 5.

### Conséquences

- ✅ Vrai Kubernetes multi-nœuds : on démontre la répartition des réplicas, l'arrêt d'un nœud, l'HPA et les NetworkPolicies (k3s embarque un contrôleur de NetworkPolicies).
- ✅ Gratuit, rapide à recréer (`k3d cluster create` en moins d'une minute), utilisable hors ligne pendant la soutenance.
- ✅ **Le GitOps résout la question du déploiement vers un poste local** : GitHub Actions ne peut pas joindre le Mac, mais Argo CD, depuis le cluster, tire les manifests de GitHub et les images de GHCR. Aucun port entrant n'est ouvert, et le cluster n'a jamais besoin d'exposer ses identifiants à la CI.
- ✅ Git devient la source de vérité : chaque déploiement correspond à un commit, et un retour arrière revient à un `git revert`. Argo CD détecte et corrige toute dérive.
- ✅ Les charts Helm sont indépendants du fournisseur et les images sont multi-architecture (amd64 et arm64) : le passage vers OKE ou un Kubernetes managé européen ne change pas le code.
- ❌ **Ce n'est pas un environnement managé au sens strict** : le plan de contrôle tourne sur le poste. C'est un risque pour le critère 5, d'où la question posée à l'intervenant et le repli OKE.
- ❌ Ressources limitées par Docker Desktop (8 Go de mémoire et 4 CPU au minimum) : la montée en charge démontrée reste modeste, et les résultats des tests de charge ne sont pas transposables tels quels en production.
- ❌ Les volumes `local-path` de k3s sont liés au disque d'un nœud. Les composants avec état sont donc placés sur le nœud server, et la démonstration d'arrêt porte sur un agent.
- ❌ Les « nœuds » partagent le même hôte : la panne simulée d'un nœud ne reproduit pas une panne matérielle réelle.

### Confirmation

- Le script `deploy/local/check-tools.sh --cluster` crée un cluster de test et vérifie que les 3 nœuds sont `Ready`.
- Un protocole d'expérimentation couvre le cluster k3d, ingress-nginx et cert-manager (certificat émis automatiquement pour un Ingress), puis l'installation d'Argo CD et la synchronisation d'une application depuis le dépôt.
- La démonstration de disponibilité arrête un agent pendant un test de charge et mesure le taux d'erreur.

## Avantages et inconvénients des options

### Minikube

- ✅ Très documenté, cité par la consigne.
- ❌ Pensé pour un seul nœud : le mode multi-nœuds est moins naturel et plus gourmand que k3d.

### kind

- ✅ Léger, multi-nœuds, très utilisé en CI.
- ❌ Orienté tests de Kubernetes lui-même : pas de répartiteur de charge ni de provisionneur de stockage aussi intégrés que dans k3s.

### docker-compose

- ✅ Le plus simple. Il sera d'ailleurs utilisé pour le développement local rapide d'un service.
- ❌ Pas un orchestrateur : ni répartition sur des nœuds, ni autoscaling, ni NetworkPolicies, ni auto-réparation. Ne répond pas au critère 5.

### Kubernetes managé avec crédits d'essai

- ✅ Vrai environnement managé.
- ❌ Crédits limités dans le temps : l'environnement risque de disparaître avant la soutenance. Coût réel ensuite. Écarté par la contrainte de gratuité.

### Oracle OKE Always Free

- ✅ Kubernetes managé, gratuit sans limite de durée, nœuds ARM.
- ❌ Ressources gratuites limitées, inscription avec vérification par carte bancaire, disponibilité des instances gratuites variable selon la région. Démonstration dépendante du réseau de la salle.
- Retenu comme **repli**, et non comme choix principal.

### Déploiement en push (`helm upgrade` depuis la CI)

- ✅ Simple à mettre en place pour un cluster accessible depuis Internet.
- ❌ Impossible vers un cluster local sans tunnel entrant. La CI devrait détenir les identifiants d'administration du cluster. Aucune détection de dérive.

> [!TIP]
> **À défendre à l'oral.** k3d donne un vrai Kubernetes multi-nœuds, gratuit et disponible hors ligne, sur lequel on démontre la disponibilité et la montée en charge. Le GitOps n'est pas un gadget : c'est ce qui permet à une CI dans le cloud de déployer vers un cluster local sans jamais y accéder, avec Git comme source de vérité. La limite (pas un environnement managé) est identifiée, soumise à l'intervenant, et le repli OKE réutilise les mêmes charts.
