var httpProxy = require('http-proxy');

httpProxy.createProxyServer({target:'http://127.0.0.1:56789'}).listen(8000);

console.log('proxy listening on port 8000');