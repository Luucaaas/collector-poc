// Only use of Node in the journeys: reading environment variables (avoids adding @types/node).
declare const process: { env: Record<string, string | undefined> };
