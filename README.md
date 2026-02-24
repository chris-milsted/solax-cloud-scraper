Playing with Claude to scrape my solax cloud data. 

https://global.solaxcloud.com/api/v2/dataAccess/realtimeInfo/get

When users request an interface, they must use tokenId to submit an API request to
SolaXCloud. The tokenId request path is [service-API].
Log in to SolaXCloud, click [service], enter the API page, and obtain tokenId. After the
request is successful, tokenId will be bound to the distributor/installer account.

You just need to pull the token id and the WiFi dongle serial number to use this. You can test these are correct similar to:

```bash
  curl --request POST \
  --url https://global.solaxcloud.com/api/v2/dataAccess/realtimeInfo/get \
  --header 'Content-Type: application/json' \
  --header 'tokenId: REDACTED' \
  --data '{"wifiSn":"REDACTED"}'
```

You should get data similar to:
```json
  {"success":true,"exception":"operation success","result":{"inverterSN":"REDACTED","sn":"REDACTED","acpower":0.0,"yieldtoday":17.8,"yieldtotal":16465.5,"feedinpower":0.0,"feedinenergy":0.0,"consumeenergy":0.0,"feedinpowerM2":null,"soc":null,"peps1":null,"peps2":null,"peps3":null,"inverterType":"8","inverterStatus":"100","uploadTime":"2026-02-17 17:41:14","batPower":null,"powerdc1":0.0,"powerdc2":0.0,"powerdc3":null,"powerdc4":null,"batStatus":null,"utcDateTime":"2026-02-17T17:41:14Z"},"code":0}
```
