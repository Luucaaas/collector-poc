---
statut: acceptée (mise à jour le 2026-10-31, voir ADR 0007), sous réserve de la validation de l'intervenant (critère 5)
date: 2026-10-30
décideurs: Lucas (Lead Developer)
---

# 0006 — Kubernetes local (k3d), Helm et déploiement par script

Le nom du fichier mentionne Argo CD, retenu dans la première version de cet ADR. Il est conservé pour ne pas casser les liens.

## Contexte et problème

La consigne demande « une gestion du déploiement via un orchestrateur ou un fournisseur cloud » et la démonstration de la disponibilité et de la montée en charge. Le POC doit être **entièrement gratuit et sans crédits d'essai limités dans le temps**, reproductible par script pour le jury, et démontrable hors ligne le jour de la soutenance. Le poste de développement est un Mac (Apple Silicon) avec Docker Desktop. Le Lead Developer découvre Kubernetes, Helm et GitHub Actions : chaque composant ajouté est une compétence de plus à maîtriser et à défendre.

Où et comment déployer le POC ?

## Facteurs de décision

- Orchestrateur réel : plusieurs nœuds, auto-réparation, autoscaling, routage par Ingress, pour démontrer la disponibilité (ENF-16) et la scalabilité (ENF-29).
- Coût nul et durable, sans dépendance à des crédits d'essai.
- Reproductibilité : un script recrée l'environnement à l'identique (ENF-30).
- Proximité avec un Kubernetes managé, pour que la migration se fasse sans réécriture (ENF-31).
- **Le moins de composants possible** : chaque outil ajouté doit démontrer un critère de la grille (ADR 0007).
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

- **A. Script local** : `deploy/local/deploy.sh` exécute `helm upgrade --install` sur le cluster.
- **B. Pull (GitOps)** : Argo CD, installé dans le cluster, synchronise l'état du cluster avec le dépôt Git.
- **C. Push depuis la CI** : GitHub Actions exécute `helm upgrade` sur le cluster.

**Contrôleur d'Ingress et certificats**

- **Traefik**, installé et maintenu avec k3s, ou **ingress-nginx**.
- Certificat **mkcert** généré une fois et chargé comme Secret TLS, ou **cert-manager** qui émet et renouvelle les certificats.

## Décision

**k3d avec 1 server et 2 agents** sur le poste de développement. **Traefik** comme contrôleur d'Ingress, avec un certificat générique `*.127.0.0.1.sslip.io` généré par **mkcert** et chargé comme Secret TLS. Un **chart Helm générique** pour les deux services. Déploiement par le **script `deploy/local/deploy.sh` (option A)**, qui crée les Secrets à partir du `.env` local puis exécute `helm upgrade --install`.

**Écartés pour le POC, retenus pour la cible** : Argo CD (option B) et cert-manager. **Repli prévu** : Oracle OKE Always Free, avec le même chart, si l'intervenant refuse le cluster local comme « environnement managé » pour le critère 5.

### Conséquences

- ✅ Vrai Kubernetes multi-nœuds : on démontre l'auto-réparation d'un pod, l'HPA (le metrics-server est fourni par k3s) et le routage par Ingress.
- ✅ Gratuit, rapide à recréer (`k3d cluster create` en moins d'une minute), utilisable hors ligne pendant la soutenance.
- ✅ Traefik et ServiceLB sont fournis par k3s : aucun contrôleur à installer. mkcert produit en une commande un certificat accepté par le navigateur du Mac.
- ✅ Un seul chart Helm sert aux deux services : réplicas, sondes, HPA, ressources et secrets sont définis une fois.
- ✅ Le chart est indépendant du fournisseur, et les images sont multi-architecture (amd64 et arm64) : le passage vers OKE ou un Kubernetes managé européen ne change pas le code.
- ❌ **Ce n'est pas un environnement managé au sens strict** : le plan de contrôle tourne sur le poste. C'est un risque pour le critère 5, d'où la question posée à l'intervenant et le repli OKE.
- ❌ **Déploiement lancé depuis un poste** : pas de détection de dérive, et l'accès administrateur au cluster reste sur ce poste. La CI s'arrête à la publication des images sur GHCR (limite L12 d'`architecture-poc.md`).
- ❌ **Certificat manuel** : pas de renouvellement automatique, et la CA racine de mkcert sert à toute la démo (limite L11).
- ❌ Ressources limitées par Docker Desktop : la montée en charge démontrée reste modeste, et les résultats des tests de charge ne sont pas transposables tels quels en production.
- ❌ Sans règles de placement, deux réplicas d'un service peuvent se retrouver sur le même nœud : la démonstration de disponibilité porte donc sur la perte d'un pod, pas d'un nœud (limite L8).

### Confirmation

- Le script `deploy/local/check-tools.sh --cluster` crée un cluster de test et vérifie que les 3 nœuds sont `Ready`.
- Un protocole d'expérimentation couvre le cluster k3d, Traefik avec le certificat mkcert, et Keycloak derrière Traefik en HTTPS.
- `deploy/local/deploy.sh` déploie l'ensemble sur un cluster neuf en moins de 15 minutes (ENF-30).
- Pendant un test Locust, la suppression d'un pod et la montée en charge par l'HPA sont observées dans Grafana.

## Avantages et inconvénients des options

### Minikube

- ✅ Très documenté, cité par la consigne.
- ❌ Pensé pour un seul nœud : le mode multi-nœuds est moins naturel et plus gourmand que k3d.

### kind

- ✅ Léger, multi-nœuds, très utilisé en CI.
- ❌ Orienté tests de Kubernetes lui-même : pas de contrôleur d'Ingress, de répartiteur de charge ni de metrics-server intégrés, contrairement à k3s.

### docker-compose

- ✅ Le plus simple. Il servira au développement local rapide d'un service.
- ❌ Pas un orchestrateur : ni autoscaling, ni auto-réparation, ni répartition sur des nœuds. Ne répond pas au critère 5.

### Kubernetes managé avec crédits d'essai

- ✅ Vrai environnement managé.
- ❌ Crédits limités dans le temps : l'environnement risque de disparaître avant la soutenance. Coût réel ensuite. Écarté par la contrainte de gratuité.

### Oracle OKE Always Free

- ✅ Kubernetes managé, gratuit sans limite de durée, nœuds ARM.
- ❌ Ressources gratuites limitées, inscription avec vérification par carte bancaire, disponibilité des instances gratuites variable selon la région. Démonstration dépendante du réseau de la salle.
- Retenu comme **repli**, et non comme choix principal.

### GitOps avec Argo CD

- ✅ Git devient la source de vérité. Argo CD tire les manifests depuis le cluster, ce qui permet à une CI dans le cloud de livrer vers un cluster local sans jamais y accéder. Il détecte et corrige les dérives.
- ❌ Un composant de plus à installer, à configurer et à défendre, pour un critère (CI/CD) que la grille ne conditionne pas à un déploiement automatique : la consigne précise qu'on n'est pas pénalisé si le pipeline ne déploie pas.
- **Retenu pour la cible.**

### Push depuis la CI

- ✅ Simple pour un cluster accessible depuis Internet.
- ❌ Impossible vers un cluster local sans tunnel entrant, et la CI devrait détenir les identifiants d'administration du cluster.

### cert-manager

- ✅ Émission et renouvellement automatiques, émetteur ACME (Let's Encrypt) en production.
- ❌ Sans vrai domaine public, il faut de toute façon une CA locale. Un certificat mkcert de longue durée suffit à démontrer TLS en local.
- **Retenu pour la cible.**

### Traefik plutôt qu'ingress-nginx

- ✅ Traefik est installé par défaut par k3s et suit ses mises à jour. Il gère la ressource standard `Ingress` et propose des middlewares utiles : `StripPrefix` dans le POC, `RateLimit` et `Retry` pour la cible.
- ✅ Il implémente aussi Gateway API, le successeur d'`Ingress`, ce qui ménage une évolution sans changer de contrôleur.
- ❌ **ingress-nginx est retiré** : le SIG Network de Kubernetes a annoncé en novembre 2025 la fin de sa maintenance, sans correctifs de sécurité après mars 2026 ([annonce](https://www.kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/)). Déployer un composant exposé à Internet et non maintenu serait une faute pour un projet où la sécurité est une exigence de premier plan.
- ❌ Traefik ne génère pas d'en-tête `X-Request-ID` : les services le créent eux-mêmes (voir `contrats.md`).

> [!TIP]
> **À défendre à l'oral.** k3d donne un vrai Kubernetes multi-nœuds, gratuit et disponible hors ligne, sur lequel on démontre l'auto-réparation et la montée en charge. On n'y ajoute que ce qui sert un critère de la grille : Traefik et le metrics-server sont déjà fournis par k3s, un seul chart Helm sert aux deux services, un script suffit à déployer. Argo CD et cert-manager sont de bons outils, mais leur valeur est en production. Ils sont donc dans la cible, avec le risque de leur absence documenté.
