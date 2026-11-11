# ZAP Scanning Report

ZAP by [Checkmarx](https://checkmarx.com/).


## Summary of Alerts

| Risk Level | Number of Alerts |
| --- | --- |
| High | 0 |
| Medium | 0 |
| Low | 1 |
| Informational | 4 |




## Insights

| Level | Reason | Site | Description | Statistic |
| --- | --- | --- | --- | --- |
| Medium | Exceeded High | https://api.127.0.0.1.sslip.io | Percentage of responses with status code 4xx | 100 % |
| Info | Informational | https://api.127.0.0.1.sslip.io | Percentage of endpoints with content type application/problem+json | 24 % |
| Info | Informational | https://api.127.0.0.1.sslip.io | Percentage of endpoints with content type text/plain | 75 % |
| Info | Informational | https://api.127.0.0.1.sslip.io | Percentage of endpoints with method GET | 74 % |
| Info | Informational | https://api.127.0.0.1.sslip.io | Percentage of endpoints with method POST | 18 % |
| Info | Informational | https://api.127.0.0.1.sslip.io | Percentage of endpoints with method PUT | 7 % |
| Info | Informational | https://api.127.0.0.1.sslip.io | Count of total endpoints | 177    |







## Alerts

| Name | Risk Level | Number of Instances |
| --- | --- | --- |
| Strict-Transport-Security Header Not Set | Low | 2 |
| A Client Error response code was returned by the server | Informational | 181 |
| Non-Storable Content | Informational | 5 |
| Storable and Cacheable Content | Informational | 2 |
| User Agent Fuzzer | Informational | Systemic |




## Alert Detail



### [ Strict-Transport-Security Header Not Set ](https://www.zaproxy.org/docs/alerts/10035/)



##### Low (High)

### Description

HTTP Strict Transport Security (HSTS) is a web security policy mechanism whereby a web server declares that complying user agents (such as a web browser) are to interact with it using only secure HTTPS connections (i.e. HTTP layered over TLS/SSL). HSTS is an IETF standards track protocol and is specified in RFC 6797.

* URL: https://api.127.0.0.1.sslip.io/notification/health/live
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/live`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/ready
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/ready`
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
* URL: https://api.127.0.0.1.sslip.io/.zap5555075977121294313
  * Node Name: `https://api.127.0.0.1.sslip.io/.zap5555075977121294313`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/197660837832113796
  * Node Name: `https://api.127.0.0.1.sslip.io/197660837832113796`
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
  * Node Name: `https://api.127.0.0.1.sslip.io/api-docs ()({category_ids:[]})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api/v1/me/interests
  * Node Name: `https://api.127.0.0.1.sslip.io/api/v1/me/interests`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api/v1/me/notifications
  * Node Name: `https://api.127.0.0.1.sslip.io/api/v1/me/notifications`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api/v1/me/preferences
  * Node Name: `https://api.127.0.0.1.sslip.io/api/v1/me/preferences`
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
  * Node Name: `https://api.127.0.0.1.sslip.io/docs/ ()({category_ids:[]})`
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
* URL: https://api.127.0.0.1.sslip.io/notification
  * Node Name: `https://api.127.0.0.1.sslip.io/notification`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/notification (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/.env
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/.env`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/.htaccess
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/.htaccess`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/185427310155490084
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/185427310155490084`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/.env
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/.env`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/.htaccess
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/.htaccess`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/3827331555768636747
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/3827331555768636747`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/trace.axd
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/trace.axd`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1 (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/.env
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/.env`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/.htaccess
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/.htaccess`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/2947851221513203003
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/2947851221513203003`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/.env
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/.env`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/.htaccess
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/.htaccess`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/9173588265916044009
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/9173588265916044009`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/actuator/health
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/actuator/health`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests ()({category_ids:[]})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests (class.module.classLoader.DefaultAssertio...)({category_ids:[]})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests/
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications%3Flimit=20&offset=0&class.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications (class.module.classLoader.DefaultAssertio...,limit,offset)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications%3Flimit=20&offset=0
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications (limit,offset)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications/
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences ()({new_article,price_changed})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences (class.module.classLoader.DefaultAssertio...)({new_article,price_changed})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences/
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/trace.axd
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/trace.axd`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/trace.axd
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/trace.axd`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/.env
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/.env`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/.htaccess
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/.htaccess`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/909403169081254649
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/909403169081254649`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/live
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/live`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/live%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/live (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/live/
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/live/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/ready
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/ready`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/ready%3Fclass.module.classLoader.DefaultAssertionStatus=nonsense
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/ready (class.module.classLoader.DefaultAssertio...)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/ready/
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/ready/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/trace.axd
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/trace.axd`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/trace.axd
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/trace.axd`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/openapi.json
  * Node Name: `https://api.127.0.0.1.sslip.io/openapi.json ()({category_ids:[]})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/openapi.yaml
  * Node Name: `https://api.127.0.0.1.sslip.io/openapi.yaml ()({category_ids:[]})`
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
  * Node Name: `https://api.127.0.0.1.sslip.io/swagger ()({category_ids:[]})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/swagger-ui/
  * Node Name: `https://api.127.0.0.1.sslip.io/swagger-ui/ ()({category_ids:[]})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/swagger-ui/index.html
  * Node Name: `https://api.127.0.0.1.sslip.io/swagger-ui/index.html ()({category_ids:[]})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/swagger.json
  * Node Name: `https://api.127.0.0.1.sslip.io/swagger.json ()({category_ids:[]})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/swagger.yaml
  * Node Name: `https://api.127.0.0.1.sslip.io/swagger.yaml ()({category_ids:[]})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/swagger/ui/index.html
  * Node Name: `https://api.127.0.0.1.sslip.io/swagger/ui/index.html ()({category_ids:[]})`
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
  * Node Name: `https://api.127.0.0.1.sslip.io/v2/api-docs ()({category_ids:[]})`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/v3/api-docs
  * Node Name: `https://api.127.0.0.1.sslip.io/v3/api-docs ()({category_ids:[]})`
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
* URL: https://api.127.0.0.1.sslip.io/zap2673275491035090742
  * Node Name: `https://api.127.0.0.1.sslip.io/zap2673275491035090742`
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
  * Node Name: `https://api.127.0.0.1.sslip.io/ (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo dbspgmf5x6fa...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/ (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo dbspgmf5x6fal9shc3nr',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification
  * Node Name: `https://api.127.0.0.1.sslip.io/notification ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo dbspgmf5x6fa...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo dbspgmf5x6fal9shc3nr',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo dbspgmf5x6fa...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo dbspgmf5x6fal9shc3nr',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1 ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1 (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo dbspgmf5x6fa...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1 (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo dbspgmf5x6fal9shc3nr',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo dbspgmf5x6fa...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo dbspgmf5x6fal9shc3nr',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests ()(------b3918f33-d7b6-41b0-947c-361eee330eae
Content-Disposition: form-data; name="1"

{}
------b3918f33-d7b6-41b0-947c-361eee330eae
Content-Disposition: form-data; name="0"

["$1:a:a"]
------b3918f33-d7b6-41b0-947c-361eee330eae--
)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo dbspgmf5x6fa...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo dbspgmf5x6fal9shc3nr',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo dbspgmf5x6fa...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo dbspgmf5x6fal9shc3nr',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications%3Flimit=20&offset=0
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications (limit,offset)(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo dbspgmf5x6fa...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo dbspgmf5x6fal9shc3nr',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `405`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo dbspgmf5x6fa...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo dbspgmf5x6fal9shc3nr',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/live
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/live ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/live%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/live (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo dbspgmf5x6fa...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/live%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/live (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo dbspgmf5x6fal9shc3nr',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/ready
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/ready ()(class.module.classLoader.DefaultAssertio...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/ready%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/ready (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('cmd.exe /C echo dbspgmf5x6fa...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/health/ready%3F-d+allow_url_include%253d1+-d+auto_prepend_file%253dphp://input
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/ready (-d allow_url_include=1 -d auto_prepend_f...)(<?php exec('echo dbspgmf5x6fal9shc3nr',$...)`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api/v1/me/interests
  * Node Name: `https://api.127.0.0.1.sslip.io/api/v1/me/interests ()({category_ids:[]})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/api/v1/me/preferences
  * Node Name: `https://api.127.0.0.1.sslip.io/api/v1/me/preferences ()({new_article,price_changed})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/computeMetadata/v1/
  * Node Name: `https://api.127.0.0.1.sslip.io/computeMetadata/v1/ ()({category_ids:[]})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/latest/meta-data/
  * Node Name: `https://api.127.0.0.1.sslip.io/latest/meta-data/ ()({category_ids:[]})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/metadata/instance
  * Node Name: `https://api.127.0.0.1.sslip.io/metadata/instance ()({category_ids:[]})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/metadata/v1
  * Node Name: `https://api.127.0.0.1.sslip.io/metadata/v1 ()({category_ids:[]})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests ()({category_ids:[]})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests/
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests/ ()({category_ids:[]})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences ()({new_article,price_changed})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences/
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences/ ()({new_article,price_changed})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/opc/v1/instance/
  * Node Name: `https://api.127.0.0.1.sslip.io/opc/v1/instance/ ()({category_ids:[]})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/opc/v2/instance/
  * Node Name: `https://api.127.0.0.1.sslip.io/opc/v2/instance/ ()({category_ids:[]})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/openstack/latest/meta_data.json
  * Node Name: `https://api.127.0.0.1.sslip.io/openstack/latest/meta_data.json ()({category_ids:[]})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``


Instances: 181

### Solution



### Reference



#### CWE Id: [ 388 ](https://cwe.mitre.org/data/definitions/388.html)


#### WASC Id: 20

#### Source ID: 4

### [ Non-Storable Content ](https://www.zaproxy.org/docs/alerts/10049/)



##### Informational (Medium)

### Description

The response contents are not storable by caching components such as proxy servers. If the response does not contain sensitive, personal or user-specific information, it may benefit from being stored and cached, to improve performance.

* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications%3Flimit=20&offset=0
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications (limit,offset)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests ()({category_ids:[]})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `PUT `
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences ()({new_article,price_changed})`
  * Method: `PUT`
  * Parameter: ``
  * Attack: ``
  * Evidence: `PUT `
  * Other Info: ``


Instances: 5

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

### [ Storable and Cacheable Content ](https://www.zaproxy.org/docs/alerts/10049/)



##### Informational (Medium)

### Description

The response contents are storable by caching components such as proxy servers, and may be retrieved directly from the cache, rather than from the origin server by the caching servers, in response to similar requests from other users. If the response data is sensitive, personal or user-specific, this may result in sensitive information being leaked. In some cases, this may even result in a user gaining complete control of the session of another user, depending on the configuration of the caching components in use in their environment. This is primarily an issue where "shared" caching servers such as "proxy" caches are configured on the local network. This configuration is typically found in corporate or educational environments, for instance.

* URL: https://api.127.0.0.1.sslip.io/notification/health/live
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/live`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: `In the absence of an explicitly specified caching lifetime directive in the response, a liberal lifetime heuristic of 1 year was assumed. This is permitted by rfc7234.`
* URL: https://api.127.0.0.1.sslip.io/notification/health/ready
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/health/ready`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: `In the absence of an explicitly specified caching lifetime directive in the response, a liberal lifetime heuristic of 1 year was assumed. This is permitted by rfc7234.`


Instances: 2

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

### [ User Agent Fuzzer ](https://www.zaproxy.org/docs/alerts/10104/)



##### Informational (Medium)

### Description

Check for differences in response based on fuzzed User Agent (eg. mobile sites, access as a Search Engine Crawler). Compares the response statuscode and the hashcode of the response body with the original response.

* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests ()({category_ids:[]})`
  * Method: `PUT`
  * Parameter: `Header User-Agent`
  * Attack: `Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)`
  * Evidence: ``
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/interests ()({category_ids:[]})`
  * Method: `PUT`
  * Parameter: `Header User-Agent`
  * Attack: `Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1)`
  * Evidence: ``
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences ()({new_article,price_changed})`
  * Method: `PUT`
  * Parameter: `Header User-Agent`
  * Attack: `Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)`
  * Evidence: ``
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences ()({new_article,price_changed})`
  * Method: `PUT`
  * Parameter: `Header User-Agent`
  * Attack: `Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)`
  * Evidence: ``
  * Other Info: ``
* URL: https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences
  * Node Name: `https://api.127.0.0.1.sslip.io/notification/api/v1/me/preferences ()({new_article,price_changed})`
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


