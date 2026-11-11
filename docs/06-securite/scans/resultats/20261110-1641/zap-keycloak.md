# ZAP Scanning Report

ZAP by [Checkmarx](https://checkmarx.com/).


## Summary of Alerts

| Risk Level | Number of Alerts |
| --- | --- |
| High | 0 |
| Medium | 5 |
| Low | 7 |
| Informational | 6 |




## Insights

| Level | Reason | Site | Description | Statistic |
| --- | --- | --- | --- | --- |
| Info | Informational | https://auth.127.0.0.1.sslip.io | Percentage of responses with status code 2xx | 55 % |
| Info | Informational | https://auth.127.0.0.1.sslip.io | Percentage of responses with status code 3xx | 22 % |
| Info | Informational | https://auth.127.0.0.1.sslip.io | Percentage of responses with status code 4xx | 22 % |
| Info | Informational | https://auth.127.0.0.1.sslip.io | Percentage of endpoints with content type application/json | 22 % |
| Info | Informational | https://auth.127.0.0.1.sslip.io | Percentage of endpoints with content type image/svg+xml | 11 % |
| Info | Informational | https://auth.127.0.0.1.sslip.io | Percentage of endpoints with content type text/css | 11 % |
| Info | Informational | https://auth.127.0.0.1.sslip.io | Percentage of endpoints with content type text/html | 22 % |
| Info | Informational | https://auth.127.0.0.1.sslip.io | Percentage of endpoints with content type text/javascript | 11 % |
| Info | Informational | https://auth.127.0.0.1.sslip.io | Percentage of endpoints with method GET | 100 % |
| Info | Informational | https://auth.127.0.0.1.sslip.io | Count of total endpoints | 9    |







## Alerts

| Name | Risk Level | Number of Instances |
| --- | --- | --- |
| Absence of Anti-CSRF Tokens | Medium | 1 |
| CSP: Failure to Define Directive with No Fallback | Medium | 2 |
| CSP: Wildcard Directive | Medium | 2 |
| CSP: script-src unsafe-inline | Medium | 2 |
| CSP: style-src unsafe-inline | Medium | 2 |
| Cookie No HttpOnly Flag | Low | 1 |
| Cookie with SameSite Attribute None | Low | 3 |
| Cross-Origin-Embedder-Policy Header Missing or Invalid | Low | 2 |
| Cross-Origin-Opener-Policy Header Missing or Invalid | Low | 2 |
| Cross-Origin-Resource-Policy Header Missing or Invalid | Low | 5 |
| Permissions Policy Header Not Set | Low | 3 |
| Strict-Transport-Security Header Not Set | Low | 2 |
| Modern Web Application | Informational | 2 |
| Non-Storable Content | Informational | 3 |
| Re-examine Cache-control Directives | Informational | 2 |
| Session Management Response Identified | Informational | 1 |
| Storable and Cacheable Content | Informational | 5 |
| Storable but Non-Cacheable Content | Informational | 1 |




## Alert Detail



### [ Absence of Anti-CSRF Tokens ](https://www.zaproxy.org/docs/alerts/10202/)



##### Medium (Low)

### Description

No Anti-CSRF tokens were found in a HTML submission form.
A cross-site request forgery is an attack that involves forcing a victim to send an HTTP request to a target destination without their knowledge or intent in order to perform an action as the victim. The underlying cause is application functionality using predictable URL/form actions in a repeatable way. The nature of the attack is that CSRF exploits the trust that a web site has for a user. By contrast, cross-site scripting (XSS) exploits the trust that a user has for a web site. Like XSS, CSRF attacks are not necessarily cross-site, but they can be. Cross-site request forgery is also known as CSRF, XSRF, one-click attack, session riding, confused deputy, and sea surf.

CSRF attacks are effective in a number of situations, including:
    * The victim has an active session on the target site.
    * The victim is authenticated via HTTP auth on the target site.
    * The victim is on the same local network as the target site.

CSRF has primarily been used to perform an action against a target site using the victim's privileges, but recent techniques have been discovered to disclose information by gaining access to the response. The risk of information disclosure is dramatically increased when the target site is vulnerable to XSS, because XSS can be used as a platform for CSRF, allowing the attack to operate within the bounds of the same-origin policy.

* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `<form id="kc-form-login" class="pf-v5-c-form pf-v5-u-w-100" onsubmit="login.disabled = true; return true;" action="https://auth.127.0.0.1.sslip.io/realms/collector/login-actions/authenticate?session_code=CnOAQD39HLESmBEmFWFMTNqrdTM1uULQeigw83C1FHg&amp;execution=e615b33b-5224-4aa2-b078-82cab5a30874&amp;client_id=collector-web&amp;tab_id=JCQMw2dfLDY&amp;client_data=<jeton-masqué>" method="post" novalidate="novalidate">`
  * Other Info: `No known Anti-CSRF token [anticsrf, CSRFToken, __RequestVerificationToken, csrfmiddlewaretoken, authenticity_token, OWASP_CSRFTOKEN, anoncsrf, csrf_token, _csrf, _csrfSecret, __csrf_magic, CSRF, _token, _csrf_token, _csrfToken] was found in the following HTML form: [Form 1: "id-hidden-input" "password" "username" ].`


Instances: 1

### Solution

Phase: Architecture and Design
Use a vetted library or framework that does not allow this weakness to occur or provides constructs that make this weakness easier to avoid.
For example, use anti-CSRF packages such as the OWASP CSRFGuard.

Phase: Implementation
Ensure that your application is free of cross-site scripting issues, because most CSRF defenses can be bypassed using attacker-controlled script.

Phase: Architecture and Design
Generate a unique nonce for each form, place the nonce into the form, and verify the nonce upon receipt of the form. Be sure that the nonce is not predictable (CWE-330).
Note that this can be bypassed using XSS.

Identify especially dangerous operations. When the user performs a dangerous operation, send a separate confirmation request to ensure that the user intended to perform that operation.
Note that this can be bypassed using XSS.

Use the ESAPI Session Management control.
This control includes a component for CSRF.

Do not use the GET method for any request that triggers a state change.

Phase: Implementation
Check the HTTP Referer header to see if the request originated from an expected page. This could break legitimate functionality, because users or proxies may have disabled sending the Referer for privacy reasons.

### Reference


* [ https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html ](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
* [ https://cwe.mitre.org/data/definitions/352.html ](https://cwe.mitre.org/data/definitions/352.html)


#### CWE Id: [ 352 ](https://cwe.mitre.org/data/definitions/352.html)


#### WASC Id: 9

#### Source ID: 3

### [ CSP: Failure to Define Directive with No Fallback ](https://www.zaproxy.org/docs/alerts/10055/)



##### Medium (High)

### Description

The Content Security Policy fails to define one of the directives that has no fallback. Missing/excluding them is the same as allowing anything.

* URL: https://auth.127.0.0.1.sslip.io/admin/master/console/
  * Node Name: `https://auth.127.0.0.1.sslip.io/admin/master/console/`
  * Method: `GET`
  * Parameter: `Content-Security-Policy`
  * Attack: ``
  * Evidence: `frame-src 'self'; frame-ancestors 'self'; object-src 'none';`
  * Other Info: `The directive(s): form-action is/are among the directives that do not fallback to default-src.`
* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: `Content-Security-Policy`
  * Attack: ``
  * Evidence: `frame-src 'self'; frame-ancestors 'self'; object-src 'none';`
  * Other Info: `The directive(s): form-action is/are among the directives that do not fallback to default-src.`


Instances: 2

### Solution

Ensure that your web server, application server, load balancer, etc. is properly configured to set the Content-Security-Policy header.

### Reference


* [ https://www.w3.org/TR/CSP/ ](https://www.w3.org/TR/CSP/)
* [ https://caniuse.com/#search=content+security+policy ](https://caniuse.com/#search=content+security+policy)
* [ https://content-security-policy.com/ ](https://content-security-policy.com/)
* [ https://github.com/HtmlUnit/htmlunit-csp ](https://github.com/HtmlUnit/htmlunit-csp)
* [ https://web.dev/articles/csp#resource-options ](https://web.dev/articles/csp#resource-options)


#### CWE Id: [ 693 ](https://cwe.mitre.org/data/definitions/693.html)


#### WASC Id: 15

#### Source ID: 3

### [ CSP: Wildcard Directive ](https://www.zaproxy.org/docs/alerts/10055/)



##### Medium (High)

### Description

Content Security Policy (CSP) is an added layer of security that helps to detect and mitigate certain types of attacks. Including (but not limited to) Cross Site Scripting (XSS), and data injection attacks. These attacks are used for everything from data theft to site defacement or distribution of malware. CSP provides a set of standard HTTP headers that allow website owners to declare approved sources of content that browsers should be allowed to load on that page — covered types are JavaScript, CSS, HTML frames, fonts, images and embeddable objects such as Java applets, ActiveX, audio and video files.

* URL: https://auth.127.0.0.1.sslip.io/admin/master/console/
  * Node Name: `https://auth.127.0.0.1.sslip.io/admin/master/console/`
  * Method: `GET`
  * Parameter: `Content-Security-Policy`
  * Attack: ``
  * Evidence: `frame-src 'self'; frame-ancestors 'self'; object-src 'none';`
  * Other Info: `The following directives either allow wildcard sources (or ancestors), are not defined, or are overly broadly defined:
script-src, style-src, img-src, connect-src, font-src, media-src, manifest-src, worker-src`
* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: `Content-Security-Policy`
  * Attack: ``
  * Evidence: `frame-src 'self'; frame-ancestors 'self'; object-src 'none';`
  * Other Info: `The following directives either allow wildcard sources (or ancestors), are not defined, or are overly broadly defined:
script-src, style-src, img-src, connect-src, font-src, media-src, manifest-src, worker-src`


Instances: 2

### Solution

Ensure that your web server, application server, load balancer, etc. is properly configured to set the Content-Security-Policy header.

### Reference


* [ https://www.w3.org/TR/CSP/ ](https://www.w3.org/TR/CSP/)
* [ https://caniuse.com/#search=content+security+policy ](https://caniuse.com/#search=content+security+policy)
* [ https://content-security-policy.com/ ](https://content-security-policy.com/)
* [ https://github.com/HtmlUnit/htmlunit-csp ](https://github.com/HtmlUnit/htmlunit-csp)
* [ https://web.dev/articles/csp#resource-options ](https://web.dev/articles/csp#resource-options)


#### CWE Id: [ 693 ](https://cwe.mitre.org/data/definitions/693.html)


#### WASC Id: 15

#### Source ID: 3

### [ CSP: script-src unsafe-inline ](https://www.zaproxy.org/docs/alerts/10055/)



##### Medium (High)

### Description

Content Security Policy (CSP) is an added layer of security that helps to detect and mitigate certain types of attacks. Including (but not limited to) Cross Site Scripting (XSS), and data injection attacks. These attacks are used for everything from data theft to site defacement or distribution of malware. CSP provides a set of standard HTTP headers that allow website owners to declare approved sources of content that browsers should be allowed to load on that page — covered types are JavaScript, CSS, HTML frames, fonts, images and embeddable objects such as Java applets, ActiveX, audio and video files.

* URL: https://auth.127.0.0.1.sslip.io/admin/master/console/
  * Node Name: `https://auth.127.0.0.1.sslip.io/admin/master/console/`
  * Method: `GET`
  * Parameter: `Content-Security-Policy`
  * Attack: ``
  * Evidence: `frame-src 'self'; frame-ancestors 'self'; object-src 'none';`
  * Other Info: `script-src includes unsafe-inline.`
* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: `Content-Security-Policy`
  * Attack: ``
  * Evidence: `frame-src 'self'; frame-ancestors 'self'; object-src 'none';`
  * Other Info: `script-src includes unsafe-inline.`


Instances: 2

### Solution

Ensure that your web server, application server, load balancer, etc. is properly configured to set the Content-Security-Policy header.

### Reference


* [ https://www.w3.org/TR/CSP/ ](https://www.w3.org/TR/CSP/)
* [ https://caniuse.com/#search=content+security+policy ](https://caniuse.com/#search=content+security+policy)
* [ https://content-security-policy.com/ ](https://content-security-policy.com/)
* [ https://github.com/HtmlUnit/htmlunit-csp ](https://github.com/HtmlUnit/htmlunit-csp)
* [ https://web.dev/articles/csp#resource-options ](https://web.dev/articles/csp#resource-options)


#### CWE Id: [ 693 ](https://cwe.mitre.org/data/definitions/693.html)


#### WASC Id: 15

#### Source ID: 3

### [ CSP: style-src unsafe-inline ](https://www.zaproxy.org/docs/alerts/10055/)



##### Medium (High)

### Description

Content Security Policy (CSP) is an added layer of security that helps to detect and mitigate certain types of attacks. Including (but not limited to) Cross Site Scripting (XSS), and data injection attacks. These attacks are used for everything from data theft to site defacement or distribution of malware. CSP provides a set of standard HTTP headers that allow website owners to declare approved sources of content that browsers should be allowed to load on that page — covered types are JavaScript, CSS, HTML frames, fonts, images and embeddable objects such as Java applets, ActiveX, audio and video files.

* URL: https://auth.127.0.0.1.sslip.io/admin/master/console/
  * Node Name: `https://auth.127.0.0.1.sslip.io/admin/master/console/`
  * Method: `GET`
  * Parameter: `Content-Security-Policy`
  * Attack: ``
  * Evidence: `frame-src 'self'; frame-ancestors 'self'; object-src 'none';`
  * Other Info: `style-src includes unsafe-inline.`
* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: `Content-Security-Policy`
  * Attack: ``
  * Evidence: `frame-src 'self'; frame-ancestors 'self'; object-src 'none';`
  * Other Info: `style-src includes unsafe-inline.`


Instances: 2

### Solution

Ensure that your web server, application server, load balancer, etc. is properly configured to set the Content-Security-Policy header.

### Reference


* [ https://www.w3.org/TR/CSP/ ](https://www.w3.org/TR/CSP/)
* [ https://caniuse.com/#search=content+security+policy ](https://caniuse.com/#search=content+security+policy)
* [ https://content-security-policy.com/ ](https://content-security-policy.com/)
* [ https://github.com/HtmlUnit/htmlunit-csp ](https://github.com/HtmlUnit/htmlunit-csp)
* [ https://web.dev/articles/csp#resource-options ](https://web.dev/articles/csp#resource-options)


#### CWE Id: [ 693 ](https://cwe.mitre.org/data/definitions/693.html)


#### WASC Id: 15

#### Source ID: 3

### [ Cookie No HttpOnly Flag ](https://www.zaproxy.org/docs/alerts/10010/)



##### Low (Medium)

### Description

A cookie has been set without the HttpOnly flag, which means that the cookie can be accessed by JavaScript. If a malicious script can be run on this page then the cookie will be accessible and can be transmitted to another site. If this is a session cookie then session hijacking may be possible.

* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: `KC_AUTH_SESSION_HASH`
  * Attack: ``
  * Evidence: `Set-Cookie: KC_AUTH_SESSION_HASH`
  * Other Info: ``


Instances: 1

### Solution

Ensure that the HttpOnly flag is set for all cookies.

### Reference


* [ https://owasp.org/www-community/HttpOnly ](https://owasp.org/www-community/HttpOnly)


#### CWE Id: [ 1004 ](https://cwe.mitre.org/data/definitions/1004.html)


#### WASC Id: 13

#### Source ID: 3

### [ Cookie with SameSite Attribute None ](https://www.zaproxy.org/docs/alerts/10054/)



##### Low (Medium)

### Description

A cookie has been set with its SameSite attribute set to "none", which means that the cookie can be sent as a result of a 'cross-site' request. The SameSite attribute is an effective counter measure to cross-site request forgery, cross-site script inclusion, and timing attacks.

* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: `AUTH_SESSION_ID`
  * Attack: ``
  * Evidence: `Set-Cookie: AUTH_SESSION_ID`
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: `KC_AUTH_SESSION_HASH`
  * Attack: ``
  * Evidence: `Set-Cookie: KC_AUTH_SESSION_HASH`
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: `KC_RESTART`
  * Attack: ``
  * Evidence: `Set-Cookie: KC_RESTART`
  * Other Info: ``


Instances: 3

### Solution

Ensure that the SameSite attribute is set to either 'lax' or ideally 'strict' for all cookies.

### Reference


* [ https://datatracker.ietf.org/doc/html/draft-ietf-httpbis-cookie-same-site ](https://datatracker.ietf.org/doc/html/draft-ietf-httpbis-cookie-same-site)


#### CWE Id: [ 1275 ](https://cwe.mitre.org/data/definitions/1275.html)


#### WASC Id: 13

#### Source ID: 3

### [ Cross-Origin-Embedder-Policy Header Missing or Invalid ](https://www.zaproxy.org/docs/alerts/90004/)



##### Low (Medium)

### Description

Cross-Origin-Embedder-Policy header is a response header that prevents a document from loading any cross-origin resources that don't explicitly grant the document permission (using CORP or CORS).

* URL: https://auth.127.0.0.1.sslip.io/admin/master/console/
  * Node Name: `https://auth.127.0.0.1.sslip.io/admin/master/console/`
  * Method: `GET`
  * Parameter: `Cross-Origin-Embedder-Policy`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: `Cross-Origin-Embedder-Policy`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``


Instances: 2

### Solution

Ensure that the application/web server sets the Cross-Origin-Embedder-Policy header appropriately, and that it sets the Cross-Origin-Embedder-Policy header to 'require-corp' for documents.
If possible, ensure that the end user uses a standards-compliant and modern web browser that supports the Cross-Origin-Embedder-Policy header (https://caniuse.com/mdn-http_headers_cross-origin-embedder-policy).

### Reference


* [ https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Embedder-Policy ](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Embedder-Policy)


#### CWE Id: [ 693 ](https://cwe.mitre.org/data/definitions/693.html)


#### WASC Id: 14

#### Source ID: 3

### [ Cross-Origin-Opener-Policy Header Missing or Invalid ](https://www.zaproxy.org/docs/alerts/90004/)



##### Low (Medium)

### Description

Cross-Origin-Opener-Policy header is a response header that allows a site to control if others included documents share the same browsing context. Sharing the same browsing context with untrusted documents might lead to data leak.

* URL: https://auth.127.0.0.1.sslip.io/admin/master/console/
  * Node Name: `https://auth.127.0.0.1.sslip.io/admin/master/console/`
  * Method: `GET`
  * Parameter: `Cross-Origin-Opener-Policy`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: `Cross-Origin-Opener-Policy`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``


Instances: 2

### Solution

Ensure that the application/web server sets the Cross-Origin-Opener-Policy header appropriately, and that it sets the Cross-Origin-Opener-Policy header to 'same-origin' for documents.
'same-origin-allow-popups' is considered as less secured and should be avoided.
If possible, ensure that the end user uses a standards-compliant and modern web browser that supports the Cross-Origin-Opener-Policy header (https://caniuse.com/mdn-http_headers_cross-origin-opener-policy).

### Reference


* [ https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Opener-Policy ](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Opener-Policy)


#### CWE Id: [ 693 ](https://cwe.mitre.org/data/definitions/693.html)


#### WASC Id: 14

#### Source ID: 3

### [ Cross-Origin-Resource-Policy Header Missing or Invalid ](https://www.zaproxy.org/docs/alerts/90004/)



##### Low (Medium)

### Description

Cross-Origin-Resource-Policy header is an opt-in header designed to counter side-channels attacks like Spectre. Resource should be specifically set as shareable amongst different origins.

* URL: https://auth.127.0.0.1.sslip.io/admin/master/console/
  * Node Name: `https://auth.127.0.0.1.sslip.io/admin/master/console/`
  * Method: `GET`
  * Parameter: `Cross-Origin-Resource-Policy`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: `Cross-Origin-Resource-Policy`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/resources/3wap5/admin/keycloak.v2/assets/main-DmoViYol.css
  * Node Name: `https://auth.127.0.0.1.sslip.io/resources/3wap5/admin/keycloak.v2/assets/main-DmoViYol.css`
  * Method: `GET`
  * Parameter: `Cross-Origin-Resource-Policy`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/resources/3wap5/admin/keycloak.v2/assets/main-LOOv6l_h.js
  * Node Name: `https://auth.127.0.0.1.sslip.io/resources/3wap5/admin/keycloak.v2/assets/main-LOOv6l_h.js`
  * Method: `GET`
  * Parameter: `Cross-Origin-Resource-Policy`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/resources/3wap5/admin/keycloak.v2/favicon.svg
  * Node Name: `https://auth.127.0.0.1.sslip.io/resources/3wap5/admin/keycloak.v2/favicon.svg`
  * Method: `GET`
  * Parameter: `Cross-Origin-Resource-Policy`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``


Instances: 5

### Solution

Ensure that the application/web server sets the Cross-Origin-Resource-Policy header appropriately, and that it sets the Cross-Origin-Resource-Policy header to 'same-origin' for all web pages.
'same-site' is considered as less secured and should be avoided.
If resources must be shared, set the header to 'cross-origin'.
If possible, ensure that the end user uses a standards-compliant and modern web browser that supports the Cross-Origin-Resource-Policy header (https://caniuse.com/mdn-http_headers_cross-origin-resource-policy).

### Reference


* [ https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Embedder-Policy ](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Embedder-Policy)


#### CWE Id: [ 693 ](https://cwe.mitre.org/data/definitions/693.html)


#### WASC Id: 14

#### Source ID: 3

### [ Permissions Policy Header Not Set ](https://www.zaproxy.org/docs/alerts/10063/)



##### Low (Medium)

### Description

Permissions Policy Header is an added layer of security that helps to restrict from unauthorized access or usage of browser/client features by web resources. This policy ensures the user privacy by limiting or specifying the features of the browsers can be used by the web resources. Permissions Policy provides a set of standard HTTP headers that allow website owners to limit which features of browsers can be used by the page such as camera, microphone, location, full screen etc.

* URL: https://auth.127.0.0.1.sslip.io/admin/master/console/
  * Node Name: `https://auth.127.0.0.1.sslip.io/admin/master/console/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/resources/3wap5/admin/keycloak.v2/assets/main-LOOv6l_h.js
  * Node Name: `https://auth.127.0.0.1.sslip.io/resources/3wap5/admin/keycloak.v2/assets/main-LOOv6l_h.js`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: ``


Instances: 3

### Solution

Ensure that your web server, application server, load balancer, etc. is configured to set the Permissions-Policy header.

### Reference


* [ https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Permissions-Policy ](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Permissions-Policy)
* [ https://developer.chrome.com/blog/feature-policy/ ](https://developer.chrome.com/blog/feature-policy/)
* [ https://scotthelme.co.uk/a-new-security-header-feature-policy/ ](https://scotthelme.co.uk/a-new-security-header-feature-policy/)
* [ https://w3c.github.io/webappsec-feature-policy/ ](https://w3c.github.io/webappsec-feature-policy/)
* [ https://www.smashingmagazine.com/2018/12/feature-policy/ ](https://www.smashingmagazine.com/2018/12/feature-policy/)


#### CWE Id: [ 693 ](https://cwe.mitre.org/data/definitions/693.html)


#### WASC Id: 15

#### Source ID: 3

### [ Strict-Transport-Security Header Not Set ](https://www.zaproxy.org/docs/alerts/10035/)



##### Low (High)

### Description

HTTP Strict Transport Security (HSTS) is a web security policy mechanism whereby a web server declares that complying user agents (such as a web browser) are to interact with it using only secure HTTPS connections (i.e. HTTP layered over TLS/SSL). HSTS is an IETF standards track protocol and is specified in RFC 6797.

* URL: https://auth.127.0.0.1.sslip.io/robots.txt
  * Node Name: `https://auth.127.0.0.1.sslip.io/robots.txt`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/sitemap.xml
  * Node Name: `https://auth.127.0.0.1.sslip.io/sitemap.xml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: ``


Instances: 2

### Solution

Ensure that your web server, application server, load balancer, etc. is configured to enforce Strict-Transport-Security.

### Reference


* [ https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Strict_Transport_Security_Cheat_Sheet.html ](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Strict_Transport_Security_Cheat_Sheet.html)
* [ https://owasp.org/www-community/Security_Headers ](https://owasp.org/www-community/Security_Headers)
* [ https://en.wikipedia.org/wiki/HTTP_Strict_Transport_Security ](https://en.wikipedia.org/wiki/HTTP_Strict_Transport_Security)
* [ https://caniuse.com/stricttransportsecurity ](https://caniuse.com/stricttransportsecurity)
* [ https://datatracker.ietf.org/doc/html/rfc6797 ](https://datatracker.ietf.org/doc/html/rfc6797)


#### CWE Id: [ 319 ](https://cwe.mitre.org/data/definitions/319.html)


#### WASC Id: 15

#### Source ID: 3

### [ Modern Web Application ](https://www.zaproxy.org/docs/alerts/10109/)



##### Informational (Medium)

### Description

The application appears to be a modern web application. If you need to explore it automatically then the Client Spider may well be more effective than the standard one.

* URL: https://auth.127.0.0.1.sslip.io/admin/master/console/
  * Node Name: `https://auth.127.0.0.1.sslip.io/admin/master/console/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `<script type="importmap">
      {
        "imports": {
          "react": "/resources/3wap5/common/keycloak/vendor/react/react.production.min.js",
          "react/jsx-runtime": "/resources/3wap5/common/keycloak/vendor/react/react-jsx-runtime.production.min.js",
          "react-dom": "/resources/3wap5/common/keycloak/vendor/react-dom/react-dom.production.min.js"
        }
      }
    </script>`
  * Other Info: `No links have been found while there are scripts, which is an indication that this is a modern web application.`
* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `<script type="importmap">
        {
            "imports": {
                "rfc4648": "/resources/3wap5/common/keycloak/vendor/rfc4648/rfc4648.js"
            }
        }
    </script>`
  * Other Info: `No links have been found while there are scripts, which is an indication that this is a modern web application.`


Instances: 2

### Solution

This is an informational alert and so no changes are required.

### Reference




#### Source ID: 3

### [ Non-Storable Content ](https://www.zaproxy.org/docs/alerts/10049/)



##### Informational (Medium)

### Description

The response contents are not storable by caching components such as proxy servers. If the response does not contain sensitive, personal or user-specific information, it may benefit from being stored and cached, to improve performance.

* URL: https://auth.127.0.0.1.sslip.io/
  * Node Name: `https://auth.127.0.0.1.sslip.io/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `302`
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/admin/
  * Node Name: `https://auth.127.0.0.1.sslip.io/admin/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `302`
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `no-store`
  * Other Info: ``


Instances: 3

### Solution

The content may be marked as storable by ensuring that the following conditions are satisfied:
The request method must be understood by the cache and defined as being cacheable ("GET", "HEAD", and "POST" are currently defined as cacheable)
The response status code must be understood by the cache (one of the 1XX, 2XX, 3XX, 4XX, or 5XX response classes are generally understood)
The "no-store" cache directive must not appear in the request or response header fields
For caching by "shared" caches such as "proxy" caches, the "private" response directive must not appear in the response
For caching by "shared" caches such as "proxy" caches, the "Authorization" header field must not appear in the request, unless the response explicitly allows it (using one of the "must-revalidate", "public", or "s-maxage" Cache-Control response directives)
In addition to the conditions above, at least one of the following conditions must also be satisfied by the response:
It must contain an "Expires" header field
It must contain a "max-age" response directive
For "shared" caches such as "proxy" caches, it must contain a "s-maxage" response directive
It must contain a "Cache Control Extension" that allows it to be cached
It must have a status code that is defined as cacheable by default (200, 203, 204, 206, 300, 301, 404, 405, 410, 414, 501).

### Reference


* [ https://datatracker.ietf.org/doc/html/rfc7234 ](https://datatracker.ietf.org/doc/html/rfc7234)
* [ https://datatracker.ietf.org/doc/html/rfc7231 ](https://datatracker.ietf.org/doc/html/rfc7231)
* [ https://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html ](https://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html)


#### CWE Id: [ 524 ](https://cwe.mitre.org/data/definitions/524.html)


#### WASC Id: 13

#### Source ID: 3

### [ Re-examine Cache-control Directives ](https://www.zaproxy.org/docs/alerts/10015/)



##### Informational (Low)

### Description

The cache-control header has not been set properly or is missing, allowing the browser and proxies to cache content. For static assets like css, js, or image files this might be intended, however, the resources should be reviewed to ensure that no sensitive content will be cached.

* URL: https://auth.127.0.0.1.sslip.io/admin/master/console/
  * Node Name: `https://auth.127.0.0.1.sslip.io/admin/master/console/`
  * Method: `GET`
  * Parameter: `cache-control`
  * Attack: ``
  * Evidence: `no-cache`
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: `cache-control`
  * Attack: ``
  * Evidence: `no-store, must-revalidate, max-age=0`
  * Other Info: ``


Instances: 2

### Solution

For secure content, ensure the cache-control HTTP header is set with "no-cache, no-store, must-revalidate". If an asset should be cached consider setting the directives "public, max-age, immutable".

### Reference


* [ https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#web-content-caching ](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#web-content-caching)
* [ https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control ](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control)
* [ https://grayduck.mn/2021/09/13/cache-control-recommendations/ ](https://grayduck.mn/2021/09/13/cache-control-recommendations/)


#### CWE Id: [ 525 ](https://cwe.mitre.org/data/definitions/525.html)


#### WASC Id: 13

#### Source ID: 3

### [ Session Management Response Identified ](https://www.zaproxy.org/docs/alerts/10112/)



##### Informational (Medium)

### Description

The given response has been identified as containing a session management token. The 'Other Info' field contains a set of header tokens that can be used in the Header Based Session Management Method. If the request is in a context which has a Session Management Method set to "Auto-Detect" then this rule will change the session management to use the tokens identified.

* URL: https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth%3Fclient_id=collector-web&response_type=code&scope=openid&redirect_uri=https%253A%252F%252Fapp.127.0.0.1.sslip.io%252F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
  * Node Name: `https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/auth (client_id,code_challenge,code_challenge_method,redirect_uri,response_type,scope,state)`
  * Method: `GET`
  * Parameter: `KC_RESTART`
  * Attack: ``
  * Evidence: `KC_RESTART`
  * Other Info: `cookie:KC_RESTART
cookie:KC_AUTH_SESSION_HASH
cookie:AUTH_SESSION_ID`


Instances: 1

### Solution

This is an informational alert rather than a vulnerability and so there is nothing to fix.

### Reference


* [ https://www.zaproxy.org/docs/desktop/addons/authentication-helper/session-mgmt-id/ ](https://www.zaproxy.org/docs/desktop/addons/authentication-helper/session-mgmt-id/)



#### Source ID: 3

### [ Storable and Cacheable Content ](https://www.zaproxy.org/docs/alerts/10049/)



##### Informational (Medium)

### Description

The response contents are storable by caching components such as proxy servers, and may be retrieved directly from the cache, rather than from the origin server by the caching servers, in response to similar requests from other users. If the response data is sensitive, personal or user-specific, this may result in sensitive information being leaked. In some cases, this may even result in a user gaining complete control of the session of another user, depending on the configuration of the caching components in use in their environment. This is primarily an issue where "shared" caching servers such as "proxy" caches are configured on the local network. This configuration is typically found in corporate or educational environments, for instance.

* URL: https://auth.127.0.0.1.sslip.io/resources/3wap5/admin/keycloak.v2/assets/main-DmoViYol.css
  * Node Name: `https://auth.127.0.0.1.sslip.io/resources/3wap5/admin/keycloak.v2/assets/main-DmoViYol.css`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `max-age=2592000`
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/resources/3wap5/admin/keycloak.v2/assets/main-LOOv6l_h.js
  * Node Name: `https://auth.127.0.0.1.sslip.io/resources/3wap5/admin/keycloak.v2/assets/main-LOOv6l_h.js`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `max-age=2592000`
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/resources/3wap5/admin/keycloak.v2/favicon.svg
  * Node Name: `https://auth.127.0.0.1.sslip.io/resources/3wap5/admin/keycloak.v2/favicon.svg`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `max-age=2592000`
  * Other Info: ``
* URL: https://auth.127.0.0.1.sslip.io/robots.txt
  * Node Name: `https://auth.127.0.0.1.sslip.io/robots.txt`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: `In the absence of an explicitly specified caching lifetime directive in the response, a liberal lifetime heuristic of 1 year was assumed. This is permitted by rfc7234.`
* URL: https://auth.127.0.0.1.sslip.io/sitemap.xml
  * Node Name: `https://auth.127.0.0.1.sslip.io/sitemap.xml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: `In the absence of an explicitly specified caching lifetime directive in the response, a liberal lifetime heuristic of 1 year was assumed. This is permitted by rfc7234.`


Instances: 5

### Solution

Validate that the response does not contain sensitive, personal or user-specific information. If it does, consider the use of the following HTTP response headers, to limit, or prevent the content being stored and retrieved from the cache by another user:
Cache-Control: no-cache, no-store, must-revalidate, private
Pragma: no-cache
Expires: 0
This configuration directs both HTTP 1.0 and HTTP 1.1 compliant caching servers to not store the response, and to not retrieve the response (without validation) from the cache, in response to a similar request.

### Reference


* [ https://datatracker.ietf.org/doc/html/rfc7234 ](https://datatracker.ietf.org/doc/html/rfc7234)
* [ https://datatracker.ietf.org/doc/html/rfc7231 ](https://datatracker.ietf.org/doc/html/rfc7231)
* [ https://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html ](https://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html)


#### CWE Id: [ 524 ](https://cwe.mitre.org/data/definitions/524.html)


#### WASC Id: 13

#### Source ID: 3

### [ Storable but Non-Cacheable Content ](https://www.zaproxy.org/docs/alerts/10049/)



##### Informational (Medium)

### Description

The response contents are storable by caching components such as proxy servers, but will not be retrieved directly from the cache, without validating the request upstream, in response to similar requests from other users.

* URL: https://auth.127.0.0.1.sslip.io/admin/master/console/
  * Node Name: `https://auth.127.0.0.1.sslip.io/admin/master/console/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `no-cache`
  * Other Info: ``


Instances: 1

### Solution



### Reference


* [ https://datatracker.ietf.org/doc/html/rfc7234 ](https://datatracker.ietf.org/doc/html/rfc7234)
* [ https://datatracker.ietf.org/doc/html/rfc7231 ](https://datatracker.ietf.org/doc/html/rfc7231)
* [ https://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html ](https://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html)


#### CWE Id: [ 524 ](https://cwe.mitre.org/data/definitions/524.html)


#### WASC Id: 13

#### Source ID: 3


