# ZAP Scanning Report

ZAP by [Checkmarx](https://checkmarx.com/).


## Summary of Alerts

| Risk Level | Number of Alerts |
| --- | --- |
| High | 0 |
| Medium | 0 |
| Low | 2 |
| Informational | 4 |




## Insights

| Level | Reason | Site | Description | Statistic |
| --- | --- | --- | --- | --- |
| Medium | Exceeded High | https://api.127.0.0.1.sslip.io | Percentage of responses with status code 4xx | 97 % |
| Low | Warning |  | ZAP warnings logged - see the zap.log file for details | 30    |
| Info | Informational | http://api.127.0.0.1.sslip.io | Percentage of responses with status code 3xx | 100 % |
| Info | Informational | https://api.127.0.0.1.sslip.io | Percentage of responses with status code 2xx | 2 % |
| Info | Informational | https://api.127.0.0.1.sslip.io | Percentage of endpoints with content type application/json | 1 % |
| Info | Informational | https://api.127.0.0.1.sslip.io | Percentage of endpoints with content type application/problem+json | 31 % |
| Info | Informational | https://api.127.0.0.1.sslip.io | Percentage of endpoints with content type text/plain | 67 % |
| Info | Informational | https://api.127.0.0.1.sslip.io | Percentage of endpoints with method GET | 69 % |
| Info | Informational | https://api.127.0.0.1.sslip.io | Percentage of endpoints with method POST | 25 % |
| Info | Informational | https://api.127.0.0.1.sslip.io | Percentage of endpoints with method PUT | 4 % |
| Info | Informational | https://api.127.0.0.1.sslip.io | Count of total endpoints | 214    |







## Alerts

| Name | Risk Level | Number of Instances |
| --- | --- | --- |
| Cross-Origin-Resource-Policy Header Missing or Invalid | Low | 2 |
| Strict-Transport-Security Header Not Set | Low | 2 |
| A Client Error response code was returned by the server | Informational | 216 |
| Non-Storable Content | Informational | Systemic |
| Re-examine Cache-control Directives | Informational | 2 |
| User Agent Fuzzer | Informational | Systemic |




## Alert Detail



### [ Cross-Origin-Resource-Policy Header Missing or Invalid ](https://www.zaproxy.org/docs/alerts/90004/)



##### Low (Medium)

### Description

Cross-Origin-Resource-Policy header is an opt-in header designed to counter side-channels attacks like Spectre. Resource should be specifically set as shareable amongst different origins.

* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/categories
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/categories`
  * Method: `GET`
  * Parameter: `Cross-Origin-Resource-Policy`
  * Attack: ``
  * Evidence: `same-site`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/me
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/me`
  * Method: `GET`
  * Parameter: `Cross-Origin-Resource-Policy`
  * Attack: ``
  * Evidence: `same-site`
  * Other Info: ``


Instances: 2

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

### [ Strict-Transport-Security Header Not Set ](https://www.zaproxy.org/docs/alerts/10035/)



##### Low (High)

### Description

HTTP Strict Transport Security (HSTS) is a web security policy mechanism whereby a web server declares that complying user agents (such as a web browser) are to interact with it using only secure HTTPS connections (i.e. HTTP layered over TLS/SSL). HSTS is an IETF standards track protocol and is specified in RFC 6797.

* URL: https://api.127.0.0.1.sslip.io/catalog/health/live
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/live`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/ready
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/ready`
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

### [ A Client Error response code was returned by the server ](https://www.zaproxy.org/docs/alerts/100000/)



##### Informational (High)

### Description

A response code of 404 was returned by the server.
This may indicate that the application is failing to handle unexpected input correctly.
Raised by the 'Alert on HTTP Response Code Error' script

* URL: https://api.127.0.0.1.sslip.io
  * Node Name: `https://api.127.0.0.1.sslip.io`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io%3Faaa=bbb
  * Node Name: `https://api.127.0.0.1.sslip.io (aaa)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `400`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `400`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/
  * Node Name: `https://api.127.0.0.1.sslip.io/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/.DS_Store
  * Node Name: `https://api.127.0.0.1.sslip.io/.DS_Store`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/._darcs
  * Node Name: `https://api.127.0.0.1.sslip.io/._darcs`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/.bzr
  * Node Name: `https://api.127.0.0.1.sslip.io/.bzr`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/.env
  * Node Name: `https://api.127.0.0.1.sslip.io/.env`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/.git/config
  * Node Name: `https://api.127.0.0.1.sslip.io/.git/config`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/.hg
  * Node Name: `https://api.127.0.0.1.sslip.io/.hg`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/.htaccess
  * Node Name: `https://api.127.0.0.1.sslip.io/.htaccess`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/.idea/WebServers.xml
  * Node Name: `https://api.127.0.0.1.sslip.io/.idea/WebServers.xml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/.php_cs.cache
  * Node Name: `https://api.127.0.0.1.sslip.io/.php_cs.cache`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/.ssh/id_dsa
  * Node Name: `https://api.127.0.0.1.sslip.io/.ssh/id_dsa`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/.ssh/id_rsa
  * Node Name: `https://api.127.0.0.1.sslip.io/.ssh/id_rsa`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/.svn/entries
  * Node Name: `https://api.127.0.0.1.sslip.io/.svn/entries`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/.svn/wc.db
  * Node Name: `https://api.127.0.0.1.sslip.io/.svn/wc.db`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/.zap2292841273706402909
  * Node Name: `https://api.127.0.0.1.sslip.io/.zap2292841273706402909`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/1907177564215053157
  * Node Name: `https://api.127.0.0.1.sslip.io/1907177564215053157`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/BitKeeper
  * Node Name: `https://api.127.0.0.1.sslip.io/BitKeeper`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/CHANGELOG.txt
  * Node Name: `https://api.127.0.0.1.sslip.io/CHANGELOG.txt`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/CVS/root
  * Node Name: `https://api.127.0.0.1.sslip.io/CVS/root`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/DEADJOE
  * Node Name: `https://api.127.0.0.1.sslip.io/DEADJOE`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/FileZilla.xml
  * Node Name: `https://api.127.0.0.1.sslip.io/FileZilla.xml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/WEB-INF/applicationContext.xml
  * Node Name: `https://api.127.0.0.1.sslip.io/WEB-INF/applicationContext.xml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/WEB-INF/web.xml
  * Node Name: `https://api.127.0.0.1.sslip.io/WEB-INF/web.xml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/WS_FTP.INI
  * Node Name: `https://api.127.0.0.1.sslip.io/WS_FTP.INI`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/WS_FTP.ini
  * Node Name: `https://api.127.0.0.1.sslip.io/WS_FTP.ini`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/WinSCP.ini
  * Node Name: `https://api.127.0.0.1.sslip.io/WinSCP.ini`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/_framework/blazor.boot.json
  * Node Name: `https://api.127.0.0.1.sslip.io/_framework/blazor.boot.json`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/_wpeprivate/config.json
  * Node Name: `https://api.127.0.0.1.sslip.io/_wpeprivate/config.json`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/adminer.php
  * Node Name: `https://api.127.0.0.1.sslip.io/adminer.php`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api-docs
  * Node Name: `https://api.127.0.0.1.sslip.io/api-docs ()({price})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api/v1/articles
  * Node Name: `https://api.127.0.0.1.sslip.io/api/v1/articles`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api/v1/articles/article_id
  * Node Name: `https://api.127.0.0.1.sslip.io/api/v1/articles/article_id`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api/v1/articles/article_id/price-history
  * Node Name: `https://api.127.0.0.1.sslip.io/api/v1/articles/article_id/price-history`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api/v1/categories
  * Node Name: `https://api.127.0.0.1.sslip.io/api/v1/categories`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api/v1/shops
  * Node Name: `https://api.127.0.0.1.sslip.io/api/v1/shops`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api/v1/shops/me
  * Node Name: `https://api.127.0.0.1.sslip.io/api/v1/shops/me`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api/v1/shops/shop_id
  * Node Name: `https://api.127.0.0.1.sslip.io/api/v1/shops/shop_id`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/app/etc/local.xml
  * Node Name: `https://api.127.0.0.1.sslip.io/app/etc/local.xml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/.env
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/.env`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/.htaccess
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/.htaccess`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/3059821990135282088
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/3059821990135282088`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/.env
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/.env`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/.htaccess
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/.htaccess`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/5542489085793167238
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/5542489085793167238`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/trace.axd
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/trace.axd`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1 (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/.env
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/.env`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/.htaccess
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/.htaccess`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/8817292794510617276
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/8817292794510617276`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles%3Fcategory_id=&shop_id=&limit=20&offset=0&class.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles (category_id,class.module.classLoader.DefaultAssertio...,limit,offset,shop_id)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles%3Fcategory_id=&shop_id=&limit=20&offset=0
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles (category_id,limit,offset,shop_id)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/.env
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/.env`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/.htaccess
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/.htaccess`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/1458557767500322124
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/1458557767500322124`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/.env
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/.env`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/.htaccess
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/.htaccess`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/8015241967799456317
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/8015241967799456317`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/actuator/health
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/actuator/health`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price ()({price})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price (class.module.classLoader.DefaultAssertio...)({price})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price-history
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price-history`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price-history%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price-history (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price-history/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price-history/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/trace.axd
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/trace.axd`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/trace.axd
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/trace.axd`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/categories/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/categories/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops ()({"name":"ZAP","description":Zaproxy alias impedit expedita quisquam pariatur exercitationem. Nemo rerum eveniet dolores rem quia dignissimos.})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops (class.module.classLoader.DefaultAssertio...)({"name":"ZAP","description":Zaproxy alias impedit expedita quisquam pariatur exercitationem. Nemo rerum eveniet dolores rem quia dignissimos.})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/.env
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/.env`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/.htaccess
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/.htaccess`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/3192218153239886885
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/3192218153239886885`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/me/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/me/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/shop_id
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/shop_id`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/shop_id%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/shop_id (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/shop_id/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/shop_id/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/trace.axd
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/trace.axd`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/trace.axd
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/trace.axd`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/.env
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/.env`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/.htaccess
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/.htaccess`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/2279664206879405376
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/2279664206879405376`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/live
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/live`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/live%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/live (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/live/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/live/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/ready
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/ready`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/ready%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/ready (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/ready/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/ready/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/trace.axd
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/trace.axd`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/trace.axd
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/trace.axd`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/composer.json
  * Node Name: `https://api.127.0.0.1.sslip.io/composer.json`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/composer.lock
  * Node Name: `https://api.127.0.0.1.sslip.io/composer.lock`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/config/database.yml
  * Node Name: `https://api.127.0.0.1.sslip.io/config/database.yml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/config/databases.yml
  * Node Name: `https://api.127.0.0.1.sslip.io/config/databases.yml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/core
  * Node Name: `https://api.127.0.0.1.sslip.io/core`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/docs/
  * Node Name: `https://api.127.0.0.1.sslip.io/docs/ ()({price})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/elmah.axd
  * Node Name: `https://api.127.0.0.1.sslip.io/elmah.axd`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/filezilla.xml
  * Node Name: `https://api.127.0.0.1.sslip.io/filezilla.xml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/i.php
  * Node Name: `https://api.127.0.0.1.sslip.io/i.php`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/id_dsa
  * Node Name: `https://api.127.0.0.1.sslip.io/id_dsa`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/id_rsa
  * Node Name: `https://api.127.0.0.1.sslip.io/id_rsa`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/info.php
  * Node Name: `https://api.127.0.0.1.sslip.io/info.php`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/key.pem
  * Node Name: `https://api.127.0.0.1.sslip.io/key.pem`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/lfm.php
  * Node Name: `https://api.127.0.0.1.sslip.io/lfm.php`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/myserver.key
  * Node Name: `https://api.127.0.0.1.sslip.io/myserver.key`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/openapi.json
  * Node Name: `https://api.127.0.0.1.sslip.io/openapi.json ()({price})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/openapi.yaml
  * Node Name: `https://api.127.0.0.1.sslip.io/openapi.yaml ()({price})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/phpinfo.php
  * Node Name: `https://api.127.0.0.1.sslip.io/phpinfo.php`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/privatekey.key
  * Node Name: `https://api.127.0.0.1.sslip.io/privatekey.key`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/server-info
  * Node Name: `https://api.127.0.0.1.sslip.io/server-info`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/server-status
  * Node Name: `https://api.127.0.0.1.sslip.io/server-status`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/server.key
  * Node Name: `https://api.127.0.0.1.sslip.io/server.key`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/sftp-config.json
  * Node Name: `https://api.127.0.0.1.sslip.io/sftp-config.json`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/sitemanager.xml
  * Node Name: `https://api.127.0.0.1.sslip.io/sitemanager.xml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/sites/default/files/.ht.sqlite
  * Node Name: `https://api.127.0.0.1.sslip.io/sites/default/files/.ht.sqlite`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/sites/default/private/files/backup_migrate/scheduled/test.txt
  * Node Name: `https://api.127.0.0.1.sslip.io/sites/default/private/files/backup_migrate/scheduled/test.txt`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/swagger
  * Node Name: `https://api.127.0.0.1.sslip.io/swagger ()({price})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/swagger-ui/
  * Node Name: `https://api.127.0.0.1.sslip.io/swagger-ui/ ()({price})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/swagger-ui/index.html
  * Node Name: `https://api.127.0.0.1.sslip.io/swagger-ui/index.html ()({price})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/swagger.json
  * Node Name: `https://api.127.0.0.1.sslip.io/swagger.json ()({price})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/swagger.yaml
  * Node Name: `https://api.127.0.0.1.sslip.io/swagger.yaml ()({price})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/swagger/ui/index.html
  * Node Name: `https://api.127.0.0.1.sslip.io/swagger/ui/index.html ()({price})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/test.php
  * Node Name: `https://api.127.0.0.1.sslip.io/test.php`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/trace.axd
  * Node Name: `https://api.127.0.0.1.sslip.io/trace.axd`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/v2/api-docs
  * Node Name: `https://api.127.0.0.1.sslip.io/v2/api-docs ()({price})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/v3/api-docs
  * Node Name: `https://api.127.0.0.1.sslip.io/v3/api-docs ()({price})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/vb_test.php
  * Node Name: `https://api.127.0.0.1.sslip.io/vb_test.php`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/vim_settings.xml
  * Node Name: `https://api.127.0.0.1.sslip.io/vim_settings.xml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/winscp.ini
  * Node Name: `https://api.127.0.0.1.sslip.io/winscp.ini`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/ws_ftp.ini
  * Node Name: `https://api.127.0.0.1.sslip.io/ws_ftp.ini`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/zap4682071188466672729
  * Node Name: `https://api.127.0.0.1.sslip.io/zap4682071188466672729`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io
  * Node Name: `https://api.127.0.0.1.sslip.io ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/ (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo pzjbo2ack21q...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/ (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo pzjbo2ack21q2d9x02p8',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api/v1/articles
  * Node Name: `https://api.127.0.0.1.sslip.io/api/v1/articles ()({shop_id,category_id,title,description,photo_urls:[],price,shipping_fee,currency})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api/v1/categories
  * Node Name: `https://api.127.0.0.1.sslip.io/api/v1/categories ()({name})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api/v1/shops
  * Node Name: `https://api.127.0.0.1.sslip.io/api/v1/shops ()({"name":"ZAP","description":Zaproxy alias impedit expedita quisquam pariatur exercitationem. Nemo rerum eveniet dolores rem quia dignissimos.})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo pzjbo2ack21q...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo pzjbo2ack21q2d9x02p8',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo pzjbo2ack21q...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo pzjbo2ack21q2d9x02p8',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1 ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1 (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo pzjbo2ack21q...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1 (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo pzjbo2ack21q2d9x02p8',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles ()({shop_id,category_id,title,description,photo_urls:[],price,shipping_fee,currency})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo pzjbo2ack21q...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo pzjbo2ack21q2d9x02p8',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles%3Fcategory_id=&shop_id=&limit=20&offset=0
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles (category_id,limit,offset,shop_id)(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/ ()({shop_id,category_id,title,description,photo_urls:[],price,shipping_fee,currency})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo pzjbo2ack21q...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo pzjbo2ack21q2d9x02p8',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price ()(------95ad45ac-07aa-47a6-b8b2-05633af07dd5
Content-Disposition: form-data; name="1"

{}
------95ad45ac-07aa-47a6-b8b2-05633af07dd5
Content-Disposition: form-data; name="0"

["$1:a:a"]
------95ad45ac-07aa-47a6-b8b2-05633af07dd5--
)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo pzjbo2ack21q...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo pzjbo2ack21q2d9x02p8',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price-history
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price-history ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price-history%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price-history (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo pzjbo2ack21q...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price-history%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price-history (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo pzjbo2ack21q2d9x02p8',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/categories
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/categories ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `403`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/categories
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/categories ()({name})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `403`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/categories%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/categories (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo pzjbo2ack21q...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `403`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/categories%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/categories (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo pzjbo2ack21q2d9x02p8',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `403`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/categories/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/categories/ ()({name})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops ()({"name":"ZAP","description":Zaproxy alias impedit expedita quisquam pariatur exercitationem. Nemo rerum eveniet dolores rem quia dignissimos.})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo pzjbo2ack21q...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo pzjbo2ack21q2d9x02p8',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/ ()({"name":"ZAP","description":Zaproxy alias impedit expedita quisquam pariatur exercitationem. Nemo rerum eveniet dolores rem quia dignissimos.})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/me
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/me ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/me%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/me (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo pzjbo2ack21q...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/me%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/me (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo pzjbo2ack21q2d9x02p8',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/shop_id
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/shop_id ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/shop_id%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/shop_id (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo pzjbo2ack21q...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/shop_id%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/shop_id (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo pzjbo2ack21q2d9x02p8',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo pzjbo2ack21q...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo pzjbo2ack21q2d9x02p8',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/live
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/live ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/live%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/live (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo pzjbo2ack21q...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/live%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/live (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo pzjbo2ack21q2d9x02p8',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/ready
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/ready ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/ready%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/ready (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo pzjbo2ack21q...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/ready%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/ready (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo pzjbo2ack21q2d9x02p8',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api/v1/articles/article_id/price
  * Node Name: `https://api.127.0.0.1.sslip.io/api/v1/articles/article_id/price ()({price})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price ()({price})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price/
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price/ ()({price})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/computeMetadata/v1/
  * Node Name: `https://api.127.0.0.1.sslip.io/computeMetadata/v1/ ()({price})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/latest/meta-data/
  * Node Name: `https://api.127.0.0.1.sslip.io/latest/meta-data/ ()({price})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/metadata/instance
  * Node Name: `https://api.127.0.0.1.sslip.io/metadata/instance ()({price})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/metadata/v1
  * Node Name: `https://api.127.0.0.1.sslip.io/metadata/v1 ()({price})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/opc/v1/instance/
  * Node Name: `https://api.127.0.0.1.sslip.io/opc/v1/instance/ ()({price})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/opc/v2/instance/
  * Node Name: `https://api.127.0.0.1.sslip.io/opc/v2/instance/ ()({price})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/openstack/latest/meta_data.json
  * Node Name: `https://api.127.0.0.1.sslip.io/openstack/latest/meta_data.json ()({price})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``


Instances: 216

### Solution



### Reference



#### CWE Id: [ 388 ](https://cwe.mitre.org/data/definitions/388.html)


#### WASC Id: 20

#### Source ID: 4

### [ Non-Storable Content ](https://www.zaproxy.org/docs/alerts/10049/)



##### Informational (Medium)

### Description

The response contents are not storable by caching components such as proxy servers. If the response does not contain sensitive, personal or user-specific information, it may benefit from being stored and cached, to improve performance.

* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/categories
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/categories`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `authorization:`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/live
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/live`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `authorization:`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/health/ready
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/health/ready`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `authorization:`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/categories
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/categories ()({name})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `authorization:`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops ()({"name":"ZAP","description":Zaproxy alias impedit expedita quisquam pariatur exercitationem. Nemo rerum eveniet dolores rem quia dignissimos.})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `authorization:`
  * Other Info: ``

Instances: Systemic


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

* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/categories
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/categories`
  * Method: `GET`
  * Parameter: `cache-control`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/me
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops/me`
  * Method: `GET`
  * Parameter: `cache-control`
  * Attack: ``
  * Evidence: ``
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

### [ User Agent Fuzzer ](https://www.zaproxy.org/docs/alerts/10104/)



##### Informational (Medium)

### Description

Check for differences in response based on fuzzed User Agent (eg. mobile sites, access as a Search Engine Crawler). Compares the response statuscode and the hashcode of the response body with the original response.

* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles ()({shop_id,category_id,title,description,photo_urls:[],price,shipping_fee,currency})`
  * Method: `POST`
  * Parameter: `Header User-Agent`
  * Attack: `Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1)`
  * Evidence: ``
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/categories
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/categories ()({name})`
  * Method: `POST`
  * Parameter: `Header User-Agent`
  * Attack: `Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1)`
  * Evidence: ``
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops ()({"name":"ZAP","description":Zaproxy alias impedit expedita quisquam pariatur exercitationem. Nemo rerum eveniet dolores rem quia dignissimos.})`
  * Method: `POST`
  * Parameter: `Header User-Agent`
  * Attack: `Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)`
  * Evidence: ``
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/shops
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/shops ()({"name":"ZAP","description":Zaproxy alias impedit expedita quisquam pariatur exercitationem. Nemo rerum eveniet dolores rem quia dignissimos.})`
  * Method: `POST`
  * Parameter: `Header User-Agent`
  * Attack: `Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1)`
  * Evidence: ``
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price
  * Node Name: `https://api.127.0.0.1.sslip.io/catalog/api/v1/articles/article_id/price ()({price})`
  * Method: `PUT`
  * Parameter: `Header User-Agent`
  * Attack: `Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1)`
  * Evidence: ``
  * Other Info: ``

Instances: Systemic


### Solution



### Reference


* [ https://owasp.org/www-project-web-security-testing-guide/ ](https://owasp.org/www-project-web-security-testing-guide/)



#### Source ID: 1


