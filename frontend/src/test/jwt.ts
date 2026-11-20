/** Builds a fake (unsigned) access token carrying realm roles. */
export function fakeAccessToken(roles: string[]): string {
  const b64 = (o: object) => btoa(JSON.stringify(o)).replace(/=+$/, "").replace(/\+/g, "-").replace(/\//g, "_");
  return `${b64({ alg: "none" })}.${b64({ realm_access: { roles } })}.signature`;
}
