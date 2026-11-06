// Seul usage de Node dans les parcours : lire les variables d'environnement (évite d'ajouter @types/node).
declare const process: { env: Record<string, string | undefined> };
