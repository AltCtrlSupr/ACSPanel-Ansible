SELECT domain.domain,GROUP_CONCAT(domain_alias.domain) AS alias,configuration,cgi,ssi,php,certificate,certificate_key,certificate_chain,certificate_authority,hostname,ip,username,value AS homedir,GROUP_CONCAT(DISTINCT(protected_dir)) AS protected
FROM httpd_host 
INNER JOIN domain ON domain_id=domain.id 
LEFT JOIN domain AS domain_alias ON domain_alias.parent_domain_id=domain.id
INNER JOIN service ON service_id=service.id 
INNER JOIN server ON server_id=server.id 
INNER JOIN ip_address ON service.ip_id=ip_address.id
INNER JOIN fos_user ON domain.user_id=fos_user.id
LEFT JOIN httpd_user ON httpd_host_id=httpd_host.id
INNER JOIN config_setting
WHERE 
( httpd_host.enabled=1 AND domain.enabled=1 AND service.enabled=1 AND server.enabled=1 AND ip_address.enabled=1 AND fos_user.enabled=1 AND (domain_alias.enabled=1 OR domain_alias.enabled IS NULL))
AND 
setting_key='home_base'
GROUP BY httpd_host.id
\G
